"""価格トラッカー バックエンドAPI

FastAPIアプリケーションのエントリーポイント
Supabase PostgreSQL + Render Web Serviceとしてデプロイ可能な構成
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import prices, fetch
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時: Supabase DB初期化とスケジューラー開始
    logger.info("価格トラッカーAPI起動中（Supabase PostgreSQL接続）...")
    logger.info(f"USE_REAL_DATA: {settings.USE_REAL_DATA}")
    init_db()
    start_scheduler()
    logger.info("APIサーバー起動完了")
    yield
    # 終了時: スケジューラー停止
    stop_scheduler()
    logger.info("APIサーバー終了")


app = FastAPI(
    title="価格トラッカー API / Price Tracker API",
    description="鉄鋼・非鉄金属・石油化学製品の市況価格データAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(prices.router)
app.include_router(fetch.router)


@app.get("/")
def root():
    return {
        "name": "価格トラッカー API / Price Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
