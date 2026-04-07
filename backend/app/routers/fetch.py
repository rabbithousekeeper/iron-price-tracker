"""データ取得エンドポイント"""

import logging
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CommodityPrice
from app.services.worldbank import fetch_worldbank_prices
from app.services.eia import fetch_eia_prices
from app.services.meti import fetch_meti_prices
from app.services.manual_scraper import (
    fetch_jisf_prices,
    fetch_jisri_prices,
    fetch_tokyo_steel_prices,
    fetch_tetsugen_prices,
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


@router.post("/auto")
async def trigger_fetch_auto(
    db: Session = Depends(get_db),
    force_full: bool = Query(False, description="trueの場合、DBの件数に関わらず2005年から全件取得する"),
):
    """Yahoo Finance + EIA APIからデータを自動取得

    force_full=true: 2005年から全件取得（range=20y相当）
    force_full=false: DBのレコード件数が0なら2005年〜全取得、1件以上なら直近1年のみ更新
    """
    results = {}
    record_count = db.query(func.count(CommodityPrice.id)).scalar() or 0

    if force_full:
        # 強制全取得
        start_year = 2005
        logger.info(f"force_full=true: {start_year}年から全データを取得します（DB: {record_count}件）")
    elif record_count == 0:
        # DB空: 2005年から全取得
        start_year = 2005
        logger.info(f"DBレコード0件: {start_year}年から全データを取得します")
    else:
        # データあり: 直近1年のみ
        start_year = date.today().year - 1
        logger.info(f"DBレコード{record_count}件: {start_year}年から直近データを更新します")

    # World Bank API（銅・アルミ・亜鉛・ニッケル・鉛・錫・鉄鉱石）
    try:
        count = await fetch_worldbank_prices(db, start_year=start_year)
        results["worldbank"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"World Bank取得エラー: {e}")
        results["worldbank"] = {"status": "error", "message": str(e)}

    # EIA API（原油WTI）
    try:
        count = await fetch_eia_prices(db)
        results["eia"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"EIA取得エラー: {e}")
        results["eia"] = {"status": "error", "message": str(e)}

    return {
        "status": "completed",
        "db_records_before": record_count,
        "fetch_mode": "full" if force_full or record_count == 0 else "incremental",
        "start_year": start_year,
        "results": results,
    }


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


@router.post("/manual/tetsugen")
async def trigger_fetch_tetsugen(db: Session = Depends(get_db)):
    """日本鉄源協会からH2鉄スクラップ炉前価格（三地区平均）を手動取得"""
    count = await fetch_tetsugen_prices(db)
    return {"status": "success", "source": "tetsugen", "records_saved": count}


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
