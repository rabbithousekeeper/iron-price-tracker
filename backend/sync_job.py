"""Render Cron Job用 同期スクリプト

定期実行（0 */6 * * *）でGarminデータを自動同期する。
セッションをDBから復元し、全データを取得・保存する。
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_sync():
    """同期処理を実行"""
    from app.database import SessionLocal, init_db, load_session, save_session, add_sync_log
    from app.database import upsert_activity, upsert_sleep, upsert_daily_health, upsert_body_composition
    from app.garmin_client import garmin_client
    from app.config import settings
    from datetime import date, timedelta

    # DB初期化
    init_db()
    db = SessionLocal()

    try:
        # セッション復元
        session_data = load_session(db)
        if not session_data:
            logger.error("保存済みセッションがありません。POST /sync/init でセットアップしてください。")
            add_sync_log(db, "error", message="セッションなし")
            return

        if not garmin_client.login_with_session(session_data):
            # パスワードでの再ログインを試行
            try:
                new_session = garmin_client.login_with_credentials()
                save_session(db, new_session)
            except Exception as e:
                logger.error(f"再ログインに失敗: {e}")
                add_sync_log(db, "error", message=f"再ログイン失敗: {e}")
                return

        days_back = settings.SYNC_DAYS_BACK
        today = date.today()
        start_date = today - timedelta(days=days_back)

        activity_count = 0
        sleep_count = 0
        health_count = 0
        body_count = 0

        # アクティビティ取得
        try:
            activities = garmin_client.fetch_activities(limit=settings.ACTIVITY_LIMIT)
            for act in activities:
                upsert_activity(db, act)
                activity_count += 1
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"アクティビティ同期エラー: {e}")

        # 日別データ取得
        for i in range(days_back):
            target = start_date + timedelta(days=i)

            try:
                sleep_data = garmin_client.fetch_sleep(target)
                if sleep_data:
                    upsert_sleep(db, target, sleep_data)
                    sleep_count += 1
            except Exception as e:
                logger.warning(f"睡眠データ同期エラー ({target}): {e}")

            try:
                health_data = garmin_client.fetch_daily_stats(target)
                if health_data:
                    hrv_data = garmin_client.fetch_hrv(target)
                    if hrv_data and isinstance(hrv_data, dict):
                        health_data["hrvStatus"] = hrv_data.get("hrvSummary", {}).get("status")
                        health_data["hrvValue"] = hrv_data.get("hrvSummary", {}).get("weeklyAvg")
                    upsert_daily_health(db, target, health_data)
                    health_count += 1
            except Exception as e:
                logger.warning(f"健康データ同期エラー ({target}): {e}")

        db.commit()

        # 体組成データ
        try:
            body_list = garmin_client.fetch_body_composition(start_date, today)
            for entry in body_list:
                cal_date = entry.get("calendarDate")
                if cal_date:
                    body_date = date.fromisoformat(cal_date)
                    upsert_body_composition(db, body_date, entry)
                    body_count += 1
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"体組成同期エラー: {e}")

        # セッション更新
        updated_session = garmin_client.get_session_data()
        if updated_session:
            save_session(db, updated_session)

        add_sync_log(
            db, "ok",
            activities=activity_count,
            sleep_days=sleep_count,
            health_days=health_count,
            body_days=body_count,
            message="Cron同期完了",
        )

        logger.info(
            f"同期完了: activities={activity_count}, sleep={sleep_count}, "
            f"health={health_count}, body={body_count}"
        )

    except Exception as e:
        logger.error(f"同期処理エラー: {e}")
        try:
            add_sync_log(db, "error", message=str(e))
        except Exception:
            pass
    finally:
        db.close()


if __name__ == "__main__":
    run_sync()
