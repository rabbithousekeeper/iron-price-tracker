"""アプリケーション設定

環境変数からGarmin認証情報・DB接続・API設定を読み込む
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """アプリケーション設定"""

    # Garmin Connect認証情報
    GARMIN_EMAIL: str = os.getenv("GARMIN_EMAIL", "")
    GARMIN_PASSWORD: str = os.getenv("GARMIN_PASSWORD", "")

    # Supabase PostgreSQL接続URL
    SUPABASE_DB_URL: str = os.getenv(
        "SUPABASE_DB_URL",
        os.getenv("DATABASE_URL", "postgresql://localhost:5432/garmin_tracker"),
    )

    # API認証キー
    API_KEY: str = os.getenv("API_KEY", "")

    # データ取得設定
    FETCH_INTERVAL_HOURS: int = int(os.getenv("FETCH_INTERVAL_HOURS", "6"))
    ACTIVITY_LIMIT: int = int(os.getenv("ACTIVITY_LIMIT", "200"))
    SYNC_DAYS_BACK: int = int(os.getenv("SYNC_DAYS_BACK", "30"))

    # タイムゾーン
    TZ: str = os.getenv("TZ", "Asia/Tokyo")

    # CORS許可オリジン
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:8000",
        ).split(",")
    ]

    @property
    def database_url(self) -> str:
        """Supabase/PostgreSQL接続URLを正規化"""
        url = self.SUPABASE_DB_URL
        # postgres:// → postgresql://（SQLAlchemy互換）
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
