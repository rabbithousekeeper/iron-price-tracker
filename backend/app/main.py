"""価格トラッカー バックエンドAPI

FastAPIアプリケーションのエントリーポイント
Supabase PostgreSQL + Render Web Serviceとしてデプロイ可能な構成
"""

import logging
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func

from app.config import settings
from app.database import init_db, SessionLocal
from app.models.price import CommodityPrice
from app.routers import prices, fetch
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.worldbank import fetch_worldbank_prices
from app.services.eia import fetch_eia_prices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _auto_fetch_if_empty():
    """DBが空の場合、World BankとEIAのデータを自動取得（過去20年分）"""
    db = SessionLocal()
    try:
        count = db.query(func.count(CommodityPrice.id)).scalar()
        if count > 0:
            logger.info(f"DB内に{count}件のデータあり。起動時自動取得をスキップ")
            return

        logger.info("DBが空のため、起動時にWorld Bank・EIAデータを自動取得します")
        current_year = date.today().year
        start_year = current_year - 20

        try:
            wb_count = await fetch_worldbank_prices(db, start_year=start_year)
            logger.info(f"起動時World Bank自動取得: {wb_count}件")
        except Exception as e:
            logger.error(f"起動時World Bank取得失敗: {e}")

        try:
            eia_count = await fetch_eia_prices(db, start_year=start_year)
            logger.info(f"起動時EIA自動取得: {eia_count}件")
        except Exception as e:
            logger.error(f"起動時EIA取得失敗: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時: Supabase DB初期化とスケジューラー開始
    logger.info("価格トラッカーAPI起動中（Supabase PostgreSQL接続）...")
    logger.info(f"USE_REAL_DATA: {settings.USE_REAL_DATA}")
    init_db()

    # DBが空なら自動データ取得
    if settings.USE_REAL_DATA:
        await _auto_fetch_if_empty()

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
