"""価格トラッカー バックエンドAPI

FastAPIアプリケーションのエントリーポイント
Supabase PostgreSQL + Render Web Serviceとしてデプロイ可能な構成
"""

import asyncio
import logging
from contextlib import asynccontextmanager

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


async def _initial_data_fetch():
    """DBが空の場合に初回データを取得するバックグラウンドタスク"""
    db = SessionLocal()
    try:
        record_count = db.query(func.count(CommodityPrice.id)).scalar() or 0
        if record_count > 0:
            logger.info(f"DBにレコードが{record_count}件存在します。初回データ取得をスキップします。")
            return

        logger.info("DBが空のため初回データ取得を開始します")

        # World Bank API（2005年〜）
        try:
            wb_count = await fetch_worldbank_prices(db, start_year=2005)
            logger.info(f"初回データ取得 World Bank: {wb_count}件保存")
        except Exception as e:
            logger.error(f"初回データ取得 World Bankエラー: {e}")

        # EIA API
        try:
            eia_count = await fetch_eia_prices(db)
            logger.info(f"初回データ取得 EIA: {eia_count}件保存")
        except Exception as e:
            logger.error(f"初回データ取得 EIAエラー: {e}")

        logger.info("初回データ取得が完了しました")
    except Exception as e:
        logger.error(f"初回データ取得中に予期しないエラー: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時: Supabase DB初期化とスケジューラー開始
    logger.info("価格トラッカーAPI起動中（Supabase PostgreSQL接続）...")
    logger.info(f"USE_REAL_DATA: {settings.USE_REAL_DATA}")
    init_db()
    start_scheduler()
    # バックグラウンドで初回データ取得（起動を遅延させない）
    asyncio.create_task(_initial_data_fetch())
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
