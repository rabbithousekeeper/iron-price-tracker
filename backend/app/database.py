from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# Supabase PostgreSQL接続エンジン
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI依存性注入用のDBセッション生成"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Supabase上にテーブルを作成（存在しない場合のみ）"""
    Base.metadata.create_all(bind=engine)
