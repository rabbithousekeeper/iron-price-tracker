import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """アプリケーション設定"""

    # データベース接続URL（Render PostgreSQL）
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://localhost:5432/price_tracker",
    )

    # EIA API キー（https://www.eia.gov/opendata/ で取得）
    EIA_API_KEY: str = os.getenv("EIA_API_KEY", "")

    # CORS許可オリジン（カンマ区切り）
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:4173",
        ).split(",")
    ]

    # データ取得スケジュール（cron式）
    FETCH_INTERVAL_HOURS: int = int(os.getenv("FETCH_INTERVAL_HOURS", "168"))  # 週1回=168時間

    # RenderのPostgreSQLはpostgres://で始まるが、SQLAlchemyはpostgresql://が必要
    @property
    def database_url_fixed(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
