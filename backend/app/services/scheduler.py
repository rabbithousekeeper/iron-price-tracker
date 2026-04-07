"""定期データ取得スケジューラー

APSchedulerを使用して週1回、以下のAPIからデータを自動取得する:
- World Bank API: 銅・アルミ・亜鉛・ニッケル・鉛・錫・鉄鉱石
- EIA API: ナフサ・原油
- 経産省CSV: 石油化学系（ナフサ、エチレン、プロピレン、ベンゼン）
"""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import SessionLocal
from app.services.worldbank import fetch_worldbank_prices
from app.services.eia import fetch_eia_prices
from app.services.meti import fetch_meti_prices

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_async(coro):
    """同期コンテキストから非同期関数を実行"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def fetch_all_data():
    """全自動データソースからデータを取得するジョブ

    週1回実行:
    1. World Bank API → 銅、アルミ、亜鉛、ニッケル、鉛、錫、鉄鉱石
    2. EIA API → ナフサ、原油
    3. 経産省CSV → 石油化学系（ナフサ、エチレン、プロピレン、ベンゼン）
    """
    if not settings.USE_REAL_DATA:
        logger.info("USE_REAL_DATA=false のため、定期データ取得をスキップします")
        return

    logger.info("定期データ取得を開始します...")
    db = SessionLocal()
    try:
        # World Bank API（銅・アルミ・亜鉛・ニッケル・鉛・錫・鉄鉱石）
        try:
            count = _run_async(fetch_worldbank_prices(db))
            logger.info(f"World Bank: {count}件取得完了")
        except Exception as e:
            logger.error(f"World Bankデータ取得失敗: {e}")

        # EIA API（ナフサ・原油）
        try:
            count = _run_async(fetch_eia_prices(db))
            logger.info(f"EIA: {count}件取得完了")
        except Exception as e:
            logger.error(f"EIAデータ取得失敗: {e}")

        # 経産省CSV（石油化学系）
        try:
            count = _run_async(fetch_meti_prices(db))
            logger.info(f"経産省: {count}件取得完了")
        except Exception as e:
            logger.error(f"経産省データ取得失敗: {e}")

        logger.info("定期データ取得が完了しました")
    finally:
        db.close()


def start_scheduler():
    """スケジューラーを開始"""
    if not settings.USE_REAL_DATA:
        logger.info("USE_REAL_DATA=false のため、スケジューラーを開始しません")
        return

    scheduler.add_job(
        fetch_all_data,
        trigger=IntervalTrigger(hours=settings.FETCH_INTERVAL_HOURS),
        id="fetch_all_data",
        name="全データソースからの定期取得（週1回）",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"スケジューラー開始: {settings.FETCH_INTERVAL_HOURS}時間ごとにデータ取得"
    )


def stop_scheduler():
    """スケジューラーを停止"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("スケジューラーを停止しました")
