from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

engine = create_engine(settings.database_url_fixed, pool_pre_ping=True)
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
    """テーブルを作成"""
    Base.metadata.create_all(bind=engine)
