"""手動スクレイピングサービス

日本鉄リサイクル工業会（JISRI）から鉄スクラップ価格データをスクレイピングで取得する。
※日本鉄鋼連盟（JISF）は2023年4月で鋼材市中価格の掲載を終了したため対象外。

POST /api/fetch/manual エンドポイントから呼び出される手動取得専用。
"""

import logging
import re
from datetime import date, datetime

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.price import CommodityPrice, FetchLog

logger = logging.getLogger(__name__)

# 日本鉄リサイクル工業会（JISRI）の価格推移表ページ
JISRI_BASE_URL = "https://www.jisri.or.jp"
JISRI_PRICE_URL = f"{JISRI_BASE_URL}/kakaku"

# H2鉄スクラップの地域別マッピング（JISRI価格推移表から取得可能なデータ）
JISRI_REGIONS = {
    "h2_scrap_hokkaido": {
        "product_id": "h2_scrap_hokkaido",
        "keywords": ["北海道"],
        "description": "H2鉄スクラップ（北海道）",
    },
    "h2_scrap_tohoku": {
        "product_id": "h2_scrap_tohoku",
        "keywords": ["東北"],
        "description": "H2鉄スクラップ（東北）",
    },
    "h2_scrap_kanto": {
        "product_id": "h2_scrap_kanto",
        "keywords": ["関東"],
        "description": "H2鉄スクラップ（関東）",
    },
    "h2_scrap_chubu": {
        "product_id": "h2_scrap_chubu",
        "keywords": ["中部"],
        "description": "H2鉄スクラップ（中部）",
    },
    "h2_scrap_kansai": {
        "product_id": "h2_scrap_kansai",
        "keywords": ["関西"],
        "description": "H2鉄スクラップ（関西）",
    },
    "h2_scrap_chushikoku": {
        "product_id": "h2_scrap_chushikoku",
        "keywords": ["中四国", "中国・四国"],
        "description": "H2鉄スクラップ（中四国）",
    },
    "h2_scrap_kyushu": {
        "product_id": "h2_scrap_kyushu",
        "keywords": ["九州"],
        "description": "H2鉄スクラップ（九州）",
    },
    "h2_scrap_average": {
        "product_id": "h2_scrap_average",
        "keywords": ["三地区平均", "三地区", "平均"],
        "description": "H2鉄スクラップ（三地区平均）",
    },
}


async def fetch_jisri_prices(db: Session) -> int:
    """日本鉄リサイクル工業会からH2鉄スクラップ地域別月次価格をスクレイピング

    価格推移表ページ（https://www.jisri.or.jp/kakaku）から
    H2鉄スクラップの地域別価格データを取得する。
    """
    total_saved = 0
    errors: list[str] = []

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PriceTracker/1.0)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ja,en;q=0.9",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        try:
            resp = await client.get(JISRI_PRICE_URL)
            resp.raise_for_status()

            content = _decode_html(resp.content)
            records = _parse_jisri_html(content)

            if records:
                total_saved += _upsert_records(db, records)
                logger.info(f"日本鉄リサイクル工業会: {len(records)}件取得")
            else:
                logger.warning("日本鉄リサイクル工業会: 解析可能なデータが見つかりませんでした")

        except httpx.HTTPStatusError as e:
            msg = f"日本鉄リサイクル工業会HTTPエラー: {e.response.status_code}"
            logger.error(msg)
            errors.append(msg)
        except Exception as e:
            msg = f"日本鉄リサイクル工業会取得エラー: {str(e)}"
            logger.error(msg)
            errors.append(msg)

    # 取得ログを記録
    log = FetchLog(
        source="jisri",
        status="success" if not errors else "error",
        message="; ".join(errors) if errors else f"{total_saved}件取得",
        records_count=total_saved,
    )
    db.add(log)
    db.commit()

    return total_saved


async def fetch_manual_all(db: Session) -> dict:
    """手動ソースからデータを取得（手動エンドポイント用）

    ※日本鉄鋼連盟（JISF）は2023年4月で価格掲載を終了したため対象外。
    """
    results = {}

    # 日本鉄リサイクル工業会
    try:
        count = await fetch_jisri_prices(db)
        results["jisri"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"日本鉄リサイクル工業会取得エラー: {e}")
        results["jisri"] = {"status": "error", "message": str(e)}

    return results


def _decode_html(content: bytes) -> str:
    """HTMLコンテンツをデコード（日本語エンコーディング対応）"""
    for encoding in ["utf-8", "shift_jis", "cp932", "euc-jp", "utf-8-sig"]:
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode("utf-8", errors="replace")


def _parse_jisri_html(html: str) -> list[dict]:
    """日本鉄リサイクル工業会のHTMLからH2鉄スクラップ地域別価格を抽出

    価格推移表のテーブル構造から地域別の月次価格を検出する。
    """
    records = []

    # テーブル行を抽出
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE)

    for row in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
        if not cells:
            continue

        cell_texts = [re.sub(r"<[^>]+>", "", cell).strip() for cell in cells]
        row_text = " ".join(cell_texts)

        # 地域キーワードにマッチするか確認
        for key, region in JISRI_REGIONS.items():
            if any(kw in row_text for kw in region["keywords"]):
                price = _extract_price_from_cells(cell_texts)
                if price is not None:
                    records.append({
                        "product_id": region["product_id"],
                        "price_date": date.today(),
                        "price": price,
                        "source": "jisri",
                        "created_at": datetime.utcnow(),
                    })
                break

    return records


def _extract_price_from_cells(cells: list[str]) -> float | None:
    """セルリストから価格らしい数値を後方から探索して抽出

    テーブルの右側に最新価格がある想定で、後ろから走査する。
    """
    for cell in reversed(cells):
        cleaned = cell.replace(",", "").replace("，", "").replace(" ", "").replace("\u3000", "")
        # 数値パターンにマッチ（小数点含む）
        match = re.search(r"(\d+\.?\d*)", cleaned)
        if match:
            value = float(match.group(1))
            # 鉄鋼・スクラップ価格の妥当な範囲（円/トン想定: 1,000〜1,000,000）
            if 1000 <= value <= 1_000_000:
                return value
    return None


def _upsert_records(db: Session, records: list[dict]) -> int:
    """レコードをUPSERTしてDBに保存"""
    if not records:
        return 0

    stmt = pg_insert(CommodityPrice).values(records)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_product_date",
        set_={"price": stmt.excluded.price, "created_at": stmt.excluded.created_at},
    )
    db.execute(stmt)
    db.commit()
    return len(records)
