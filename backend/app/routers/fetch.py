"""手動データ取得エンドポイント"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.worldbank import fetch_worldbank_prices
from app.services.eia import fetch_eia_prices
from app.services.meti import fetch_meti_prices

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fetch", tags=["fetch"])


@router.post("/all")
async def trigger_fetch_all(db: Session = Depends(get_db)):
    """全データソースからデータを手動取得"""
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
