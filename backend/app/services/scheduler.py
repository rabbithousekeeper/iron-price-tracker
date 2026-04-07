"""定期データ取得スケジューラー

APSchedulerを使用して各APIから週1回データを取得する
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
    """全データソースからデータを取得するジョブ"""
    logger.info("定期データ取得を開始します...")
    db = SessionLocal()
    try:
        # World Bank API
        try:
            count = _run_async(fetch_worldbank_prices(db))
            logger.info(f"World Bank: {count}件取得完了")
        except Exception as e:
            logger.error(f"World Bankデータ取得失敗: {e}")

        # EIA API
        try:
            count = _run_async(fetch_eia_prices(db))
            logger.info(f"EIA: {count}件取得完了")
        except Exception as e:
            logger.error(f"EIAデータ取得失敗: {e}")

        # 経産省CSV
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
    scheduler.add_job(
        fetch_all_data,
        trigger=IntervalTrigger(hours=settings.FETCH_INTERVAL_HOURS),
        id="fetch_all_data",
        name="全データソースからの定期取得",
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
