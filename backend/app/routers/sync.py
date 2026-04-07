"""同期エンドポイント

POST /sync     → Garminから全データを手動取得・保存
POST /sync/init → 2FA初回セットアップ用（OTPでセッション確立）
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import (
    get_db, save_session, load_session,
    upsert_activity, upsert_sleep, upsert_daily_health,
    upsert_body_composition, add_sync_log,
)
from app.garmin_client import garmin_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sync", tags=["sync"])


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """API Key認証"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


class OTPRequest(BaseModel):
    """2FA OTPリクエスト"""
    otp: str


@router.post("/init")
def sync_init(body: OTPRequest, db: Session = Depends(get_db),
              _: str = Depends(verify_api_key)):
    """2FA初回セットアップ: OTPでログインしセッションをDBに保存"""
    try:
        session_data = garmin_client.login_with_otp(body.otp)
        save_session(db, session_data)
        return {"status": "ok", "message": "セッションを保存しました。以降は自動同期が可能です。"}
    except Exception as e:
        logger.error(f"OTPログインエラー: {e}")
        raise HTTPException(status_code=400, detail=f"OTPログインに失敗しました: {e}")


@router.post("")
def sync_all(db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    """Garminから全データを取得して保存"""
    # セッション復元またはログイン
    if not garmin_client.client:
        session_data = load_session(db)
        if session_data:
            if not garmin_client.login_with_session(session_data):
                # セッション切れの場合、パスワードで再ログイン試行
                try:
                    new_session = garmin_client.login_with_credentials()
                    save_session(db, new_session)
                except Exception as e:
                    add_sync_log(db, "error", message=f"ログインに失敗: {e}")
                    raise HTTPException(
                        status_code=401,
                        detail="セッションが無効です。POST /sync/init でOTPを使用して再認証してください。"
                    )
        else:
            # セッションなし→パスワードログイン試行
            try:
                new_session = garmin_client.login_with_credentials()
                save_session(db, new_session)
            except Exception as e:
                add_sync_log(db, "error", message=f"ログインに失敗: {e}")
                raise HTTPException(
                    status_code=401,
                    detail="ログインに失敗しました。POST /sync/init でOTPを使用してセットアップしてください。"
                )

    days_back = settings.SYNC_DAYS_BACK
    today = date.today()
    start_date = today - timedelta(days=days_back)

    activity_count = 0
    sleep_count = 0
    health_count = 0
    body_count = 0

    try:
        # アクティビティ取得
        try:
            activities = garmin_client.fetch_activities(limit=settings.ACTIVITY_LIMIT)
            for act in activities:
                upsert_activity(db, act)
                activity_count += 1
            db.commit()
            logger.info(f"アクティビティ: {activity_count}件保存")
        except Exception as e:
            db.rollback()
            logger.error(f"アクティビティ同期エラー: {e}")

        # 日別データ取得（睡眠・健康データ）
        for i in range(days_back):
            target = start_date + timedelta(days=i)

            # 睡眠データ
            try:
                sleep_data = garmin_client.fetch_sleep(target)
                if sleep_data:
                    upsert_sleep(db, target, sleep_data)
                    sleep_count += 1
            except Exception as e:
                logger.warning(f"睡眠データ同期エラー ({target}): {e}")

            # 日別健康データ
            try:
                health_data = garmin_client.fetch_daily_stats(target)
                if health_data:
                    # HRVデータを補完
                    hrv_data = garmin_client.fetch_hrv(target)
                    if hrv_data:
                        if isinstance(hrv_data, dict):
                            health_data["hrvStatus"] = hrv_data.get("hrvSummary", {}).get("status")
                            health_data["hrvValue"] = hrv_data.get("hrvSummary", {}).get("weeklyAvg")
                    upsert_daily_health(db, target, health_data)
                    health_count += 1
            except Exception as e:
                logger.warning(f"健康データ同期エラー ({target}): {e}")

        db.commit()

        # 体組成データ取得
        try:
            body_list = garmin_client.fetch_body_composition(start_date, today)
            for entry in body_list:
                # 日付の抽出
                cal_date = entry.get("calendarDate")
                if cal_date:
                    body_date = date.fromisoformat(cal_date)
                    upsert_body_composition(db, body_date, entry)
                    body_count += 1
            db.commit()
            logger.info(f"体組成: {body_count}件保存")
        except Exception as e:
            db.rollback()
            logger.error(f"体組成同期エラー: {e}")

        # セッション更新（ログイン状態を最新に保つ）
        updated_session = garmin_client.get_session_data()
        if updated_session:
            save_session(db, updated_session)

        # 同期ログ記録
        add_sync_log(
            db, "ok",
            activities=activity_count,
            sleep_days=sleep_count,
            health_days=health_count,
            body_days=body_count,
            message="同期完了",
        )

        return {
            "status": "ok",
            "activities": activity_count,
            "sleep_days": sleep_count,
            "health_days": health_count,
            "body_days": body_count,
        }

    except Exception as e:
        db.rollback()
        add_sync_log(db, "error", message=str(e))
        logger.error(f"同期処理エラー: {e}")
        raise HTTPException(status_code=500, detail=f"同期処理中にエラーが発生しました: {e}")
