"""EIA (U.S. Energy Information Administration) API からデータを取得するサービス

対象商品: ナフサ、原油
API: https://api.eia.gov/v2/
APIキー取得: https://www.eia.gov/opendata/register.php
"""

import logging
from datetime import date, datetime

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.models.price import CommodityPrice, FetchLog

logger = logging.getLogger(__name__)

# EIA APIのシリーズID
EIA_SERIES: dict[str, dict] = {
    "crude_oil": {
        "product_id": "crude_oil",
        "route": "petroleum/pri/spt/data/",
        "params": {
            "frequency": "weekly",
            "data[]": "value",
            "facets[series][]": "RWTC",  # WTI Crude Oil
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 500,
        },
        "description": "WTI原油スポット価格（$/bbl）",
    },
    "naphtha": {
        "product_id": "naphtha",
        "route": "petroleum/pri/spt/data/",
        "params": {
            "frequency": "weekly",
            "data[]": "value",
            "facets[series][]": "EER_EPD2F_PF4_Y35NY_DPG",  # NYH Naphtha
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 500,
        },
        "description": "ナフサ価格（$/gal → 円/kL換算）",
    },
}

# ナフサはEIA直接データが無い場合の代替シリーズ
EIA_NAPHTHA_FALLBACK = {
    "route": "petroleum/pri/spt/data/",
    "params": {
        "frequency": "weekly",
        "data[]": "value",
        "facets[series][]": "RBRTE",  # Brent原油（ナフサの代替指標として）
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 500,
    },
}


async def fetch_eia_prices(db: Session, start_year: int | None = None) -> int:
    """EIA APIから原油・ナフサ価格を取得してDBに保存

    start_yearを指定すると、その年以降のデータのみ取得する。
    """
    api_key = settings.EIA_API_KEY
    if not api_key:
        logger.warning("EIA_API_KEYが設定されていません。EIAデータ取得をスキップします。")
        log = FetchLog(
            source="eia",
            status="skipped",
            message="EIA_API_KEY not configured",
            records_count=0,
        )
        db.add(log)
        db.commit()
        return 0

    if start_year is None:
        start_year = date.today().year - 2

    total_saved = 0
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for key, series in EIA_SERIES.items():
            try:
                url = f"https://api.eia.gov/v2/{series['route']}"
                # start_yearに応じてlengthを調整（1年あたり約52週）
                years_to_fetch = date.today().year - start_year + 1
                adjusted_length = max(500, years_to_fetch * 52)
                params = {**series["params"], "api_key": api_key, "length": adjusted_length}

                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                response_data = data.get("response", {}).get("data", [])
                if not response_data:
                    # ナフサの場合はフォールバックを試行
                    if key == "naphtha":
                        logger.info("ナフサ直接データなし。Brent原油をフォールバックとして使用")
                        fallback_params = {
                            **EIA_NAPHTHA_FALLBACK["params"],
                            "api_key": api_key,
                        }
                        fallback_url = f"https://api.eia.gov/v2/{EIA_NAPHTHA_FALLBACK['route']}"
                        resp = await client.get(fallback_url, params=fallback_params)
                        resp.raise_for_status()
                        data = resp.json()
                        response_data = data.get("response", {}).get("data", [])

                    if not response_data:
                        logger.warning(f"EIAデータなし: {key}")
                        continue

                records_to_upsert = []
                for entry in response_data:
                    value = entry.get("value")
                    period = entry.get("period")
                    if value is None or period is None:
                        continue

                    try:
                        price_date = date.fromisoformat(period)
                    except (ValueError, TypeError):
                        continue

                    # start_year以降のデータのみ取得
                    if price_date.year < start_year:
                        continue

                    records_to_upsert.append({
                        "product_id": series["product_id"],
                        "price_date": price_date,
                        "price": float(value),
                        "source": "eia",
                        "created_at": datetime.utcnow(),
                    })

                if records_to_upsert:
                    stmt = pg_insert(CommodityPrice).values(records_to_upsert)
                    stmt = stmt.on_conflict_do_update(
                        constraint="uq_product_date",
                        set_={"price": stmt.excluded.price, "created_at": stmt.excluded.created_at},
                    )
                    db.execute(stmt)
                    db.commit()
                    total_saved += len(records_to_upsert)
                    logger.info(f"EIA {key}: {len(records_to_upsert)}件保存")

            except Exception as e:
                logger.error(f"EIA {key} 取得エラー: {e}")
                errors.append(f"{key}: {str(e)}")

    # 取得ログを記録
    log = FetchLog(
        source="eia",
        status="success" if not errors else "partial_error",
        message="; ".join(errors) if errors else None,
        records_count=total_saved,
    )
    db.add(log)
    db.commit()

    return total_saved
