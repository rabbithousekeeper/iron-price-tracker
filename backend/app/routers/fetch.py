"""手動データ取得エンドポイント"""

import logging
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CommodityPrice
from app.services.worldbank import fetch_worldbank_prices
from app.services.eia import fetch_eia_prices
from app.services.meti import fetch_meti_prices
from app.services.manual_scraper import (
    fetch_jisri_prices,
    fetch_manual_all,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fetch", tags=["fetch"])


def _is_db_empty(db: Session) -> bool:
    """DBにデータが存在するかチェック"""
    count = db.query(func.count(CommodityPrice.id)).scalar()
    return count == 0


@router.post("/auto")
async def trigger_fetch_auto(db: Session = Depends(get_db)):
    """World Bank API（銅・アルミ・亜鉛・ニッケル・鉛・錫・鉄鉱石）と
    EIA API（ナフサ・原油）を即時実行。

    DBが空なら過去20年分、データがあれば直近1年のみ取得。
    """
    db_empty = _is_db_empty(db)
    current_year = date.today().year

    if db_empty:
        # 過去20年分取得
        start_year = current_year - 20
        logger.info(f"DBが空のため、過去20年分のデータを取得します（{start_year}～{current_year}）")
    else:
        # 直近1年のみ取得
        start_year = current_year - 1
        logger.info(f"既存データあり。直近1年分のデータを取得します（{start_year}～{current_year}）")

    results = {}

    # World Bank API（銅・アルミ・亜鉛・ニッケル・鉛・錫・鉄鉱石）
    try:
        count = await fetch_worldbank_prices(db, start_year=start_year)
        results["worldbank"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"World Bank取得エラー: {e}")
        results["worldbank"] = {"status": "error", "message": str(e)}

    # EIA API（ナフサ・原油）
    try:
        count = await fetch_eia_prices(db, start_year=start_year)
        results["eia"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"EIA取得エラー: {e}")
        results["eia"] = {"status": "error", "message": str(e)}

    return {
        "status": "completed",
        "db_was_empty": db_empty,
        "start_year": start_year,
        "results": results,
    }


@router.post("/all")
async def trigger_fetch_all(db: Session = Depends(get_db)):
    """全自動データソースからデータを手動取得（World Bank, EIA, 経産省）"""
    results = {}

    try:
        results["worldbank"] = await fetch_worldbank_prices(db)
    except Exception as e:
        logger.error(f"World Bank取得エラー: {e}")
        results["worldbank"] = {"error": str(e)}

    try:
        results["eia"] = await fetch_eia_prices(db)
    except Exception as e:
        logger.error(f"EIA取得エラー: {e}")
        results["eia"] = {"error": str(e)}

    try:
        results["meti"] = await fetch_meti_prices(db)
    except Exception as e:
        logger.error(f"経産省取得エラー: {e}")
        results["meti"] = {"error": str(e)}

    return {"status": "completed", "results": results}


@router.post("/manual")
async def trigger_fetch_manual(db: Session = Depends(get_db)):
    """手動スクレイピングでスクラップ価格を取得

    対象:
    - 日本鉄リサイクル工業会（JISRI）: H2鉄スクラップ地域別月次価格
    ※日本鉄鋼連盟（JISF）は2023年4月で価格掲載を終了したため対象外
    """
    results = await fetch_manual_all(db)
    return {"status": "completed", "results": results}


@router.post("/manual/jisri")
async def trigger_fetch_jisri(db: Session = Depends(get_db)):
    """日本鉄リサイクル工業会から鉄スクラップ価格を手動取得"""
    count = await fetch_jisri_prices(db)
    return {"status": "success", "source": "jisri", "records_saved": count}


@router.post("/worldbank")
async def trigger_fetch_worldbank(db: Session = Depends(get_db)):
    """World Bank APIからデータを手動取得"""
    count = await fetch_worldbank_prices(db)
    return {"status": "success", "source": "worldbank", "records_saved": count}


@router.post("/eia")
async def trigger_fetch_eia(db: Session = Depends(get_db)):
    """EIA APIからデータを手動取得"""
    count = await fetch_eia_prices(db)
    return {"status": "success", "source": "eia", "records_saved": count}


@router.post("/meti")
async def trigger_fetch_meti(db: Session = Depends(get_db)):
    """経産省CSVからデータを手動取得"""
    count = await fetch_meti_prices(db)
    return {"status": "success", "source": "meti", "records_saved": count}
