"""Yahoo Finance API からコモディティ価格データを取得するサービス

対象商品: 銅、アルミニウム、亜鉛、鉛、鉄鉱石
（ニッケル・錫はYahoo Financeに先物シンボルがないため対象外）
API: https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=1mo&range=20y

※ファイル名は他ファイルからのimport互換性のためworldbank.pyを維持
"""

import logging
from datetime import date, datetime

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.price import CommodityPrice, FetchLog

logger = logging.getLogger(__name__)

# USD/lb → USD/t 換算係数（1トン = 2204.62ポンド）
LB_TO_TONNE = 2204.62

# Yahoo Finance シンボル → プロダクトIDのマッピング（動作確認済みのみ）
YAHOO_COMMODITIES: list[dict] = [
    {
        "symbol": "HG=F",
        "product_id": "copper",
        "description": "銅先物（COMEX, USD/lb）",
        "lb_to_tonne": True,
    },
    {
        "symbol": "ALI=F",
        "product_id": "aluminum",
        "description": "アルミニウム先物（COMEX, USD/lb）",
        "lb_to_tonne": True,
    },
    {
        "symbol": "ZNC=F",
        "product_id": "zinc",
        "description": "亜鉛先物（USD/lb）",
        "lb_to_tonne": True,
    },
    {
        "symbol": "LL=F",
        "product_id": "lead",
        "description": "鉛先物（USD/lb）",
        "lb_to_tonne": True,
    },
    {
        "symbol": "TIO=F",
        "product_id": "iron_ore",
        "description": "鉄鉱石先物（SGX, USD/t）",
        "lb_to_tonne": False,
    },
]

# Yahoo Finance Chart APIベースURL
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart"


async def fetch_worldbank_prices(
    db: Session,
    start_year: int | None = None,
) -> int:
    """Yahoo Finance APIからコモディティ価格を取得してDBに保存

    関数名は既存のimport互換性のため維持。
    start_yearが現在から10年以上前の場合はrange=20y（全取得）、
    それ以外はrange=2y（直近更新）を使用。
    """
    if start_year is None:
        start_year = date.today().year - 2

    # start_yearに応じてrange指定を決定
    years_back = date.today().year - start_year
    data_range = "20y" if years_back >= 10 else "2y"

    total_saved = 0
    errors: list[str] = []

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PriceTracker/1.0)",
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        for commodity in YAHOO_COMMODITIES:
            symbol = commodity["symbol"]
            product_id = commodity["product_id"]

            try:
                url = f"{YAHOO_CHART_URL}/{symbol}"
                params = {
                    "interval": "1mo",
                    "range": data_range,
                }

                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                # レスポンス解析
                chart = data.get("chart", {})
                error = chart.get("error")
                if error:
                    msg = f"Yahoo Finance {symbol}: APIエラー: {error}"
                    logger.error(msg)
                    errors.append(msg)
                    continue

                results = chart.get("result")
                if not results:
                    logger.warning(f"Yahoo Finance {symbol}: resultなし")
                    continue

                result = results[0]
                timestamps = result.get("timestamp")
                quotes = result.get("indicators", {}).get("quote", [])

                if not timestamps or not quotes:
                    logger.warning(f"Yahoo Finance {symbol}: timestamp/quoteなし")
                    continue

                close_prices = quotes[0].get("close", [])

                records_to_upsert = []
                for i, ts in enumerate(timestamps):
                    # 終値がnullのデータポイントはスキップ
                    if i >= len(close_prices) or close_prices[i] is None:
                        continue

                    price = close_prices[i]

                    # USD/lb → USD/t 換算
                    if commodity["lb_to_tonne"]:
                        price = price * LB_TO_TONNE

                    # Unixタイムスタンプ → date
                    price_date = date.fromtimestamp(ts)

                    records_to_upsert.append({
                        "product_id": product_id,
                        "price_date": price_date,
                        "price": round(price, 2),
                        "source": "yahoo_finance",
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
                    logger.info(f"Yahoo Finance {symbol} ({product_id}): {len(records_to_upsert)}件保存")
                else:
                    logger.warning(f"Yahoo Finance {symbol}: 有効なレコードなし")

            except Exception as e:
                logger.error(f"Yahoo Finance {symbol} 取得エラー: {e}")
                errors.append(f"{symbol}: {str(e)}")

    # 取得ログを記録
    log = FetchLog(
        source="yahoo_finance",
        status="success" if not errors else "partial_error",
        message="; ".join(errors) if errors else None,
        records_count=total_saved,
    )
    db.add(log)
    db.commit()

    return total_saved
