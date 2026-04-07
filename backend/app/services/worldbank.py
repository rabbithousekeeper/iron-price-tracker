"""World Bank Commodity Prices API からデータを取得するサービス

対象商品: 銅、アルミニウム、亜鉛、ニッケル、鉛、錫、鉄鉱石
API: https://api.worldbank.org/v2/en/indicator/{CODE}?format=json&source=89
"""

import logging
from datetime import date, datetime

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.price import CommodityPrice, FetchLog

logger = logging.getLogger(__name__)

# World Bank商品コード → プロダクトIDのマッピング
# World Bank Commodity Markets ("Pink Sheet") データ
WORLDBANK_COMMODITIES: dict[str, dict] = {
    "copper": {
        "product_id": "copper",
        "indicator": "COPPER",
        "description": "銅（LME, $/mt）",
    },
    "aluminum": {
        "product_id": "aluminum",
        "indicator": "ALUMINUM",
        "description": "アルミニウム（LME, $/mt）",
    },
    "zinc": {
        "product_id": "zinc",
        "indicator": "ZINC",
        "description": "亜鉛（LME, $/mt）",
    },
    "nickel": {
        "product_id": "nickel",
        "indicator": "NICKEL",
        "description": "ニッケル（LME, $/mt）",
    },
    "lead": {
        "product_id": "lead",
        "indicator": "LEAD",
        "description": "鉛（LME, $/mt）",
    },
    "tin": {
        "product_id": "tin",
        "indicator": "TIN",
        "description": "錫（LME, $/mt）",
    },
    "iron_ore": {
        "product_id": "iron_ore",
        "indicator": "IRON_ORE",
        "description": "鉄鉱石（62% Fe, CFR China, $/dmt）",
    },
}

# World Bank Commodity Markets API エンドポイント
COMMODITY_API_URL = "https://api.worldbank.org/v2/country/all/indicator/COMMODITY_PRICES"
# 代替: Pink Sheet monthly prices CSV
PINK_SHEET_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "5d903e848db1d1b83e0ec8f744e55571-0350012021/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)


async def fetch_worldbank_prices(
    db: Session,
    start_year: int | None = None,
) -> int:
    """World Bank APIから非鉄金属・鉄鉱石の価格を取得してDBに保存

    World Bank Indicators APIを使用（月次データ）
    """
    if start_year is None:
        start_year = date.today().year - 2

    total_saved = 0
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for key, commodity in WORLDBANK_COMMODITIES.items():
            try:
                # World Bank Commodity Markets (source=89) 指標コード
                indicator_map = {
                    "COPPER": "PCOPP",
                    "ALUMINUM": "PALUM",
                    "ZINC": "PZINC",
                    "NICKEL": "PNICK",
                    "LEAD": "PLEAD",
                    "TIN": "PTIN",
                    "IRON_ORE": "PIORECR",
                }

                indicator_code = indicator_map.get(commodity["indicator"])
                if not indicator_code:
                    logger.warning(f"指標コードが見つかりません: {commodity['indicator']}")
                    continue

                url = (
                    f"https://api.worldbank.org/v2/en/indicator/{indicator_code}"
                    f"?format=json&source=89"
                    f"&date={start_year}:{date.today().year}"
                    f"&per_page=300"
                )

                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                if not data or len(data) < 2 or not data[1]:
                    logger.warning(f"World Bankデータなし: {key}")
                    continue

                records_to_upsert = []
                for entry in data[1]:
                    value = entry.get("value")
                    date_str = entry.get("date")
                    if value is None or date_str is None:
                        continue

                    # 年次データの場合は年末日、月次は月末日を設定
                    try:
                        if len(date_str) == 4:
                            price_date = date(int(date_str), 12, 31)
                        elif "M" in date_str:
                            year, month = date_str.split("M")
                            price_date = date(int(year), int(month), 1)
                        else:
                            price_date = date(int(date_str), 12, 31)
                    except (ValueError, TypeError):
                        continue

                    records_to_upsert.append({
                        "product_id": commodity["product_id"],
                        "price_date": price_date,
                        "price": float(value),
                        "source": "worldbank",
                        "created_at": datetime.utcnow(),
                    })

                # UPSERT（重複時は更新）
                if records_to_upsert:
                    stmt = pg_insert(CommodityPrice).values(records_to_upsert)
                    stmt = stmt.on_conflict_do_update(
                        constraint="uq_product_date",
                        set_={"price": stmt.excluded.price, "created_at": stmt.excluded.created_at},
                    )
                    db.execute(stmt)
                    db.commit()
                    total_saved += len(records_to_upsert)
                    logger.info(f"World Bank {key}: {len(records_to_upsert)}件保存")

            except Exception as e:
                logger.error(f"World Bank {key} 取得エラー: {e}")
                errors.append(f"{key}: {str(e)}")

    # 取得ログを記録
    log = FetchLog(
        source="worldbank",
        status="success" if not errors else "partial_error",
        message="; ".join(errors) if errors else None,
        records_count=total_saved,
    )
    db.add(log)
    db.commit()

    return total_saved
