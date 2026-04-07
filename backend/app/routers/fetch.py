"""手動データ取得エンドポイント"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.worldbank import fetch_worldbank_prices
from app.services.eia import fetch_eia_prices
from app.services.meti import fetch_meti_prices
from app.services.manual_scraper import (
    fetch_jisf_prices,
    fetch_jisri_prices,
    fetch_tokyo_steel_prices,
    fetch_manual_all,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fetch", tags=["fetch"])


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
    """手動スクレイピングで鉄鋼・スクラップ価格を取得

    対象:
    - 日本鉄鋼連盟（JISF）: 熱延鋼板、冷延鋼板、H形鋼、異形棒鋼、厚板
    - 日本鉄リサイクル工業会（JISRI）: H2、HS、H1、シュレッダー鉄スクラップ
    """
    results = await fetch_manual_all(db)
    return {"status": "completed", "results": results}


@router.post("/manual/jisf")
async def trigger_fetch_jisf(db: Session = Depends(get_db)):
    """日本鉄鋼連盟から鉄鋼製品価格を手動取得"""
    count = await fetch_jisf_prices(db)
    return {"status": "success", "source": "jisf", "records_saved": count}


@router.post("/manual/jisri")
async def trigger_fetch_jisri(db: Session = Depends(get_db)):
    """日本鉄リサイクル工業会から鉄スクラップ価格を手動取得"""
    count = await fetch_jisri_prices(db)
    return {"status": "success", "source": "jisri", "records_saved": count}


@router.post("/manual/tokyo-steel")
async def trigger_fetch_tokyo_steel(db: Session = Depends(get_db)):
    """東京製鐵から鉄スクラップ購入価格・鋼材販売価格を手動取得"""
    count = await fetch_tokyo_steel_prices(db)
    return {"status": "success", "source": "tokyo_steel", "records_saved": count}


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
