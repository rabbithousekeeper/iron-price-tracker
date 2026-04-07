"""Garmin Connect接続・データ取得クライアント

garminconnectライブラリを使用してGarmin Connectから各種データを取得する。
セッションをDBに保存してRenderのephemeral FS対策を行う。
2FA（OTP）に対応した初回セットアップフローを提供する。
"""

import json
import logging
from datetime import date, timedelta

from garminconnect import Garmin

from app.config import settings

logger = logging.getLogger(__name__)


class GarminClient:
    """Garmin Connect APIクライアント"""

    def __init__(self):
        self.client: Garmin | None = None

    def login_with_session(self, session_data: dict) -> bool:
        """保存済みセッションで再ログイン"""
        try:
            self.client = Garmin()
            self.client.login(session_data)
            logger.info("セッションからの再ログインに成功しました")
            return True
        except Exception as e:
            logger.warning(f"セッションからの再ログインに失敗: {e}")
            self.client = None
            return False

    def login_with_credentials(self) -> dict:
        """メール/パスワードでログイン（2FAなしの場合）。セッションデータを返す"""
        self.client = Garmin(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
        self.client.login()
        session_data = self.client.session_data
        logger.info("認証情報によるログインに成功しました")
        return session_data

    def login_with_otp(self, otp: str) -> dict:
        """2FA OTPを使用してログイン。セッションデータを返す"""
        self.client = Garmin(settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD)
        self.client.login(prompt_mfa=lambda: otp)
        session_data = self.client.session_data
        logger.info("OTPを使用したログインに成功しました")
        return session_data

    def get_session_data(self) -> dict | None:
        """現在のセッションデータを取得"""
        if self.client:
            return self.client.session_data
        return None

    def fetch_activities(self, limit: int = 200) -> list[dict]:
        """アクティビティ一覧を取得"""
        if not self.client:
            raise RuntimeError("Garminにログインしていません")
        try:
            activities = self.client.get_activities(0, limit)
            logger.info(f"アクティビティを{len(activities)}件取得しました")
            return activities
        except Exception as e:
            logger.error(f"アクティビティ取得エラー: {e}")
            raise

    def fetch_sleep(self, target_date: date) -> dict | None:
        """指定日の睡眠データを取得"""
        if not self.client:
            raise RuntimeError("Garminにログインしていません")
        try:
            data = self.client.get_sleep_data(target_date.isoformat())
            return data
        except Exception as e:
            logger.warning(f"睡眠データ取得エラー ({target_date}): {e}")
            return None

    def fetch_daily_stats(self, target_date: date) -> dict | None:
        """指定日の日別統計データを取得"""
        if not self.client:
            raise RuntimeError("Garminにログインしていません")
        try:
            data = self.client.get_stats(target_date.isoformat())
            return data
        except Exception as e:
            logger.warning(f"日別統計取得エラー ({target_date}): {e}")
            return None

    def fetch_hrv(self, target_date: date) -> dict | None:
        """指定日のHRVデータを取得"""
        if not self.client:
            raise RuntimeError("Garminにログインしていません")
        try:
            data = self.client.get_hrv_data(target_date.isoformat())
            return data
        except Exception as e:
            logger.warning(f"HRVデータ取得エラー ({target_date}): {e}")
            return None

    def fetch_body_composition(self, start_date: date, end_date: date) -> list[dict]:
        """期間内の体組成データを取得"""
        if not self.client:
            raise RuntimeError("Garminにログインしていません")
        try:
            data = self.client.get_body_composition(
                start_date.isoformat(), end_date.isoformat()
            )
            # レスポンスにdateWeightListがある場合はそれを返す
            if isinstance(data, dict):
                return data.get("dateWeightList", [])
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"体組成データ取得エラー: {e}")
            return []


# シングルトンインスタンス
garmin_client = GarminClient()
