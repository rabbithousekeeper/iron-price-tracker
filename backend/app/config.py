import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """アプリケーション設定"""

    # Supabase PostgreSQL接続URL
    SUPABASE_DB_URL: str = os.getenv(
        "SUPABASE_DB_URL",
        os.getenv("DATABASE_URL", "postgresql://localhost:5432/price_tracker"),
    )

    # EIA API キー（https://www.eia.gov/opendata/ で取得）
    EIA_API_KEY: str = os.getenv("EIA_API_KEY", "")

    # 本番データ取得フラグ（Falseの場合はモックデータを使用）
    USE_REAL_DATA: bool = os.getenv("USE_REAL_DATA", "true").lower() in ("true", "1", "yes")

    # CORS許可オリジン（カンマ区切り）
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:4173",
        ).split(",")
    ]

    # データ取得スケジュール（週1回=168時間）
    FETCH_INTERVAL_HOURS: int = int(os.getenv("FETCH_INTERVAL_HOURS", "168"))

    @property
    def database_url(self) -> str:
        """Supabase/PostgreSQL接続URLを正規化"""
        url = self.SUPABASE_DB_URL
        # Supabase/RenderのPostgreSQLはpostgres://で始まる場合があるが、
        # SQLAlchemyはpostgresql://が必要
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
