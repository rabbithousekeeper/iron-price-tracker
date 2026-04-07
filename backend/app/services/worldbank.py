"""World Bank Commodity Prices API からデータを取得するサービス

対象商品: 銅、アルミニウム、亜鉛、ニッケル、鉛、錫、鉄鉱石
API: https://api.worldbank.org/v2/en/indicator/{CODE}?format=json&source=89
source=89 = Commodity Markets ("Pink Sheet") データ
"""

import logging
from datetime import date, datetime

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.price import CommodityPrice, FetchLog

logger = logging.getLogger(__name__)

# World Bank Commodity Markets (source=89) 指標コードマッピング
WORLDBANK_COMMODITIES: dict[str, dict] = {
    "copper": {
        "product_id": "copper",
        "indicator_code": "PCOPP",
        "description": "銅（LME, $/mt）",
    },
    "aluminum": {
        "product_id": "aluminum",
        "indicator_code": "PALUM",
        "description": "アルミニウム（LME, $/mt）",
    },
    "zinc": {
        "product_id": "zinc",
        "indicator_code": "PZINC",
        "description": "亜鉛（LME, $/mt）",
    },
    "nickel": {
        "product_id": "nickel",
        "indicator_code": "PNICK",
        "description": "ニッケル（LME, $/mt）",
    },
    "lead": {
        "product_id": "lead",
        "indicator_code": "PLEAD",
        "description": "鉛（LME, $/mt）",
    },
    "tin": {
        "product_id": "tin",
        "indicator_code": "PTIN",
        "description": "錫（LME, $/mt）",
    },
    "iron_ore": {
        "product_id": "iron_ore",
        "indicator_code": "PIORECR",
        "description": "鉄鉱石（62% Fe, CFR China, $/dmt）",
    },
}


def _parse_wb_date(date_str: str) -> date | None:
    """World Bank APIの日付文字列をdateオブジェクトに変換

    source=89のdate形式:
    - 月次: "2024M06" → 2024-06-01
    - 年次: "2024" → 2024-12-31
    """
    try:
        if "M" in date_str:
            # 月次データ: "2024M06"
            year_str, month_str = date_str.split("M")
            return date(int(year_str), int(month_str), 1)
        elif len(date_str) == 4:
            # 年次データ: "2024"
            return date(int(date_str), 12, 31)
    except (ValueError, TypeError, IndexError):
        pass
    return None


async def fetch_worldbank_prices(
    db: Session,
    start_year: int | None = None,
) -> int:
    """World Bank Commodity Markets APIから非鉄金属・鉄鉱石の価格を取得してDBに保存

    source=89（Commodity Markets / Pink Sheet）を使用。
    エンドポイント: /v2/en/indicator/{CODE}?format=json&source=89
    """
    if start_year is None:
        start_year = date.today().year - 2

    total_saved = 0
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for key, commodity in WORLDBANK_COMMODITIES.items():
            try:
                indicator_code = commodity["indicator_code"]
                url = (
                    f"https://api.worldbank.org/v2/en/indicator/{indicator_code}"
                    f"?format=json&source=89"
                    f"&date={start_year}:{date.today().year}"
                    f"&per_page=300"
                )

                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                # レスポンス: [pagination_meta, [data_entries]] の2要素配列
                if not isinstance(data, list) or len(data) < 2:
                    logger.warning(f"World Bank {key}: 予期しないレスポンス形式")
                    continue

                entries = data[1]
                if not entries:
                    logger.warning(f"World Bank {key}: データエントリなし")
                    continue

                # 最初のエントリをログに出力（デバッグ用）
                logger.debug(f"World Bank {key} サンプル: {entries[0]}")

                records_to_upsert = []
                for entry in entries:
                    value = entry.get("value")
                    date_str = entry.get("date")

                    # valueがNone（欠損値）のエントリはスキップ
                    if value is None or date_str is None:
                        continue

                    price_date = _parse_wb_date(str(date_str))
                    if price_date is None:
                        logger.debug(f"World Bank {key}: 日付パース失敗: {date_str}")
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
                else:
                    logger.warning(f"World Bank {key}: 有効なレコードなし（{len(entries)}件中）")

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
