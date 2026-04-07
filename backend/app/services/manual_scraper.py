"""手動スクレイピングサービス

日本鉄鋼連盟（JISF）、日本鉄リサイクル工業会（JISRI）、東京製鐵（Tokyo Steel）、
日本鉄源協会（Tetsugen）から鉄鋼・鉄スクラップ価格データをスクレイピングで取得する。

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

# 日本鉄鋼連盟（JISF）の統計ページ
JISF_BASE_URL = "https://www.jisf.or.jp"
JISF_STATS_URL = f"{JISF_BASE_URL}/data/iandsteel/"

# 日本鉄リサイクル工業会（JISRI）の市況ページ
JISRI_BASE_URL = "https://www.jisri.or.jp"
JISRI_MARKET_URL = f"{JISRI_BASE_URL}/kakaku"

# 東京製鐵株式会社の公表価格ページ
TOKYO_STEEL_BASE_URL = "https://www.tokyosteel.co.jp"
# 日本鉄源協会（Tetsugen）のスクラップ価格ページ（httpのみ）
TETSUGEN_URL = "http://tetsugen.or.jp/kiso/2sukurap.htm"

TOKYO_STEEL_SCRAP_URL = f"{TOKYO_STEEL_BASE_URL}/scrapprice/"
TOKYO_STEEL_SALES_URL = f"{TOKYO_STEEL_BASE_URL}/salesprice/"

# スクレイピング対象の鉄鋼製品マッピング
JISF_PRODUCTS = {
    "hot_rolled_coil": {
        "product_id": "hot_rolled_coil",
        "keywords": ["熱延鋼板", "熱延コイル", "ホットコイル", "HR"],
        "description": "熱延鋼板価格",
    },
    "cold_rolled_coil": {
        "product_id": "cold_rolled_coil",
        "keywords": ["冷延鋼板", "冷延コイル", "CR"],
        "description": "冷延鋼板価格",
    },
    "h_beam": {
        "product_id": "h_beam",
        "keywords": ["H形鋼", "H鋼", "Ｈ形鋼"],
        "description": "H形鋼価格",
    },
    "rebar": {
        "product_id": "rebar",
        "keywords": ["異形棒鋼", "鉄筋", "D16"],
        "description": "異形棒鋼価格",
    },
    "steel_plate": {
        "product_id": "steel_plate",
        "keywords": ["厚板", "鋼板", "厚鋼板"],
        "description": "厚板価格",
    },
}

# 鉄スクラップ製品マッピング
JISRI_PRODUCTS = {
    "h2_scrap": {
        "product_id": "h2_scrap",
        "keywords": ["H2", "Ｈ２", "新断ち"],
        "description": "H2（新断ち）鉄スクラップ",
    },
    "hs_scrap": {
        "product_id": "hs_scrap",
        "keywords": ["HS", "ＨＳ", "プレス"],
        "description": "HS（プレス）鉄スクラップ",
    },
    "h1_scrap": {
        "product_id": "h1_scrap",
        "keywords": ["H1", "Ｈ１"],
        "description": "H1鉄スクラップ",
    },
    "shredder_scrap": {
        "product_id": "shredder_scrap",
        "keywords": ["シュレッダー", "シュレッダーA"],
        "description": "シュレッダー鉄スクラップ",
    },
}

# 東京製鐵 鉄スクラップ購入価格マッピング
TOKYO_STEEL_SCRAP_PRODUCTS = {
    "h2_scrap": {
        "product_id": "h2_scrap",
        "keywords": ["H2", "Ｈ２", "新断ち", "新断"],
        "description": "東京製鐵 H2鉄スクラップ購入価格",
    },
    "hs_scrap": {
        "product_id": "hs_scrap",
        "keywords": ["HS", "ＨＳ", "プレス"],
        "description": "東京製鐵 HS鉄スクラップ購入価格",
    },
}

# 東京製鐵 鋼材販売価格マッピング
TOKYO_STEEL_PRODUCT_PRODUCTS = {
    "hot_rolled_coil": {
        "product_id": "hot_rolled_coil",
        "keywords": ["熱延", "熱延鋼板", "ホットコイル"],
        "description": "東京製鐵 熱延鋼板販売価格",
    },
    "h_beam": {
        "product_id": "h_beam",
        "keywords": ["H形鋼", "H鋼", "Ｈ形鋼"],
        "description": "東京製鐵 H形鋼販売価格",
    },
    "rebar": {
        "product_id": "rebar",
        "keywords": ["異形棒鋼", "鉄筋", "D16", "D13"],
        "description": "東京製鐵 異形棒鋼販売価格",
    },
    "steel_plate": {
        "product_id": "steel_plate",
        "keywords": ["厚板", "厚鋼板"],
        "description": "東京製鐵 厚板販売価格",
    },
}


async def fetch_jisf_prices(db: Session) -> int:
    """日本鉄鋼連盟から鉄鋼製品価格をスクレイピング

    鉄鋼連盟の公開統計ページからHTML解析で価格データを取得する。
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
            # 鉄鋼連盟の統計ページを取得
            resp = await client.get(JISF_STATS_URL)
            resp.raise_for_status()

            # HTMLからエンコーディングを考慮してデコード
            content = _decode_html(resp.content)
            records = _parse_jisf_html(content)

            if records:
                total_saved += _upsert_records(db, records)
                logger.info(f"日本鉄鋼連盟: {len(records)}件取得")
            else:
                logger.warning("日本鉄鋼連盟: 解析可能なデータが見つかりませんでした")

        except httpx.HTTPStatusError as e:
            msg = f"日本鉄鋼連盟HTTPエラー: {e.response.status_code}"
            logger.error(msg)
            errors.append(msg)
        except Exception as e:
            msg = f"日本鉄鋼連盟取得エラー: {str(e)}"
            logger.error(msg)
            errors.append(msg)

    # 取得ログを記録
    log = FetchLog(
        source="jisf",
        status="success" if not errors else "error",
        message="; ".join(errors) if errors else f"{total_saved}件取得",
        records_count=total_saved,
    )
    db.add(log)
    db.commit()

    return total_saved


async def fetch_jisri_prices(db: Session) -> int:
    """日本鉄リサイクル工業会から鉄スクラップ価格をスクレイピング

    鉄リサイクル工業会の市況ページからHTML解析で価格データを取得する。
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
            resp = await client.get(JISRI_MARKET_URL)
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


async def fetch_tokyo_steel_prices(db: Session) -> int:
    """東京製鐵から鉄スクラップ購入価格・鋼材販売価格をスクレイピング

    東京製鐵の公表価格ページからHTML解析で価格データを取得する。
    robots.txt不存在（禁止なし）、月1回以内のアクセス。
    """
    total_saved = 0
    errors: list[str] = []

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PriceTracker/1.0; +https://github.com/rabbithousekeeper/iron-price-tracker)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ja,en;q=0.9",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        # スクラップ購入価格ページ
        try:
            resp = await client.get(TOKYO_STEEL_SCRAP_URL)
            resp.raise_for_status()
            content = _decode_html(resp.content)
            records = _parse_tokyo_steel_html(content, TOKYO_STEEL_SCRAP_PRODUCTS)
            if records:
                total_saved += _upsert_records(db, records)
                logger.info(f"東京製鐵（スクラップ）: {len(records)}件取得")
            else:
                logger.warning("東京製鐵（スクラップ）: 解析可能なデータが見つかりませんでした")
        except httpx.HTTPStatusError as e:
            msg = f"東京製鐵（スクラップ）HTTPエラー: {e.response.status_code}"
            logger.error(msg)
            errors.append(msg)
        except Exception as e:
            msg = f"東京製鐵（スクラップ）取得エラー: {str(e)}"
            logger.error(msg)
            errors.append(msg)

        # 鋼材販売価格ページ
        try:
            resp = await client.get(TOKYO_STEEL_SALES_URL)
            resp.raise_for_status()
            content = _decode_html(resp.content)
            records = _parse_tokyo_steel_html(content, TOKYO_STEEL_PRODUCT_PRODUCTS)
            if records:
                total_saved += _upsert_records(db, records)
                logger.info(f"東京製鐵（鋼材）: {len(records)}件取得")
            else:
                logger.warning("東京製鐵（鋼材）: 解析可能なデータが見つかりませんでした")
        except httpx.HTTPStatusError as e:
            msg = f"東京製鐵（鋼材）HTTPエラー: {e.response.status_code}"
            logger.error(msg)
            errors.append(msg)
        except Exception as e:
            msg = f"東京製鐵（鋼材）取得エラー: {str(e)}"
            logger.error(msg)
            errors.append(msg)

    # 取得ログを記録
    log = FetchLog(
        source="tokyo_steel",
        status="success" if not errors else "error",
        message="; ".join(errors) if errors else f"{total_saved}件取得",
        records_count=total_saved,
    )
    db.add(log)
    db.commit()

    return total_saved


async def fetch_tetsugen_prices(db: Session) -> int:
    """日本鉄源協会からH2鉄スクラップ炉前価格（三地区平均）をスクレイピング

    http://tetsugen.or.jp/kiso/2sukurap.htm の年度別月次テーブルを解析。
    1987年度〜現在までの長期データを取得する。
    """
    total_saved = 0
    errors: list[str] = []

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PriceTracker/1.0)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ja,en;q=0.9",
    }

    # httpのみ（httpsなし）
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        try:
            resp = await client.get(TETSUGEN_URL)
            resp.raise_for_status()

            content = _decode_html(resp.content)
            records = _parse_tetsugen_html(content)

            if records:
                total_saved += _upsert_records(db, records)
                logger.info(f"日本鉄源協会: {len(records)}件取得")
            else:
                logger.warning("日本鉄源協会: 解析可能なデータが見つかりませんでした")

        except httpx.HTTPStatusError as e:
            msg = f"日本鉄源協会HTTPエラー: {e.response.status_code}"
            logger.error(msg)
            errors.append(msg)
        except Exception as e:
            msg = f"日本鉄源協会取得エラー: {str(e)}"
            logger.error(msg)
            errors.append(msg)

    # 取得ログを記録
    log = FetchLog(
        source="tetsugen",
        status="success" if not errors else "error",
        message="; ".join(errors) if errors else f"{total_saved}件取得",
        records_count=total_saved,
    )
    db.add(log)
    db.commit()

    return total_saved


async def fetch_manual_all(db: Session) -> dict:
    """全手動ソースからデータを取得（手動エンドポイント用）"""
    results = {}

    # 日本鉄鋼連盟
    try:
        count = await fetch_jisf_prices(db)
        results["jisf"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"日本鉄鋼連盟取得エラー: {e}")
        results["jisf"] = {"status": "error", "message": str(e)}

    # 日本鉄リサイクル工業会
    try:
        count = await fetch_jisri_prices(db)
        results["jisri"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"日本鉄リサイクル工業会取得エラー: {e}")
        results["jisri"] = {"status": "error", "message": str(e)}

    # 東京製鐵
    try:
        count = await fetch_tokyo_steel_prices(db)
        results["tokyo_steel"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"東京製鐵取得エラー: {e}")
        results["tokyo_steel"] = {"status": "error", "message": str(e)}

    # 日本鉄源協会
    try:
        count = await fetch_tetsugen_prices(db)
        results["tetsugen"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"日本鉄源協会取得エラー: {e}")
        results["tetsugen"] = {"status": "error", "message": str(e)}

    return results


def _decode_html(content: bytes) -> str:
    """HTMLコンテンツをデコード（日本語エンコーディング対応）"""
    for encoding in ["utf-8", "shift_jis", "cp932", "euc-jp", "utf-8-sig"]:
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode("utf-8", errors="replace")


def _parse_jisf_html(html: str) -> list[dict]:
    """日本鉄鋼連盟のHTMLから鉄鋼製品価格を抽出

    テーブル構造からキーワードマッチで価格行を検出し、
    数値データを抽出する。
    """
    records = []

    # テーブル行を抽出（<tr>タグ）
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE)

    for row in rows:
        # セルの内容を抽出
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
        if not cells:
            continue

        # HTMLタグを除去してテキスト化
        cell_texts = [re.sub(r"<[^>]+>", "", cell).strip() for cell in cells]
        row_text = " ".join(cell_texts)

        # 製品キーワードにマッチするか確認
        for key, product in JISF_PRODUCTS.items():
            if any(kw in row_text for kw in product["keywords"]):
                # 数値を抽出（カンマ区切り対応）
                price = _extract_price_from_cells(cell_texts)
                if price is not None:
                    records.append({
                        "product_id": product["product_id"],
                        "price_date": date.today(),
                        "price": price,
                        "source": "jisf",
                        "created_at": datetime.utcnow(),
                    })
                break

    return records


def _parse_jisri_html(html: str) -> list[dict]:
    """日本鉄リサイクル工業会のHTMLから鉄スクラップ価格を抽出

    市況ページのテーブル構造からスクラップ品種別の価格を検出する。
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

        for key, product in JISRI_PRODUCTS.items():
            if any(kw in row_text for kw in product["keywords"]):
                price = _extract_price_from_cells(cell_texts)
                if price is not None:
                    records.append({
                        "product_id": product["product_id"],
                        "price_date": date.today(),
                        "price": price,
                        "source": "jisri",
                        "created_at": datetime.utcnow(),
                    })
                break

    return records


def _parse_tokyo_steel_html(html: str, products: dict) -> list[dict]:
    """東京製鐵のHTMLから価格データを抽出

    テーブル構造からキーワードマッチで価格行を検出し、数値データを抽出する。
    """
    records = []

    # テーブル行を抽出（<tr>タグ）
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE)

    for row in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
        if not cells:
            continue

        cell_texts = [re.sub(r"<[^>]+>", "", cell).strip() for cell in cells]
        row_text = " ".join(cell_texts)

        for key, product in products.items():
            if any(kw in row_text for kw in product["keywords"]):
                price = _extract_price_from_cells(cell_texts)
                if price is not None:
                    records.append({
                        "product_id": product["product_id"],
                        "price_date": date.today(),
                        "price": price,
                        "source": "tokyo_steel",
                        "created_at": datetime.utcnow(),
                    })
                break

    return records


def _parse_tetsugen_html(html: str) -> list[dict]:
    """日本鉄源協会のHTMLからH2鉄スクラップ炉前価格（三地区平均）を抽出

    テーブル構造（tables[0]）:
    - Row3: ヘッダー（cell[2]=4月〜cell[10]=12月, cell[11]=1月, cell[12]=2月, cell[13]=3月）
    - Row4〜: データ（cell[1]=年度, cell[2〜13]=月次価格）
    - 年度をまたぐ: cell[2〜10]は年度年の4月〜12月、cell[11〜13]は翌年の1月〜3月
    """
    records = []

    # 最初のテーブルを取得
    tables = re.findall(r"<table[^>]*>(.*?)</table>", html, re.DOTALL | re.IGNORECASE)
    if not tables:
        return records

    table_html = tables[0]
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE)

    # 月マッピング: cell index → 月番号
    # cell[2]=4月, cell[3]=5月, ..., cell[10]=12月, cell[11]=1月, cell[12]=2月, cell[13]=3月
    CELL_TO_MONTH = {
        2: 4, 3: 5, 4: 6, 5: 7, 6: 8, 7: 9, 8: 10, 9: 11, 10: 12,
        11: 1, 12: 2, 13: 3,
    }

    # Row4以降（index 3〜）がデータ行
    for row in rows[3:]:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
        if len(cells) < 14:
            continue

        cell_texts = [re.sub(r"<[^>]+>", "", cell).strip() for cell in cells]

        # cell[1] = 年度（例: "1987"）
        fiscal_year_str = cell_texts[1].strip()
        fiscal_year_match = re.search(r"(\d{4})", fiscal_year_str)
        if not fiscal_year_match:
            continue
        fiscal_year = int(fiscal_year_match.group(1))

        # cell[2〜13] = 月次価格
        for cell_idx, month in CELL_TO_MONTH.items():
            if cell_idx >= len(cell_texts):
                continue

            price_text = cell_texts[cell_idx]
            price = _parse_tetsugen_price(price_text)
            if price is None:
                continue

            # cell[11〜13]（1月〜3月）は翌年
            year = fiscal_year + 1 if month <= 3 else fiscal_year
            price_date = date(year, month, 1)

            records.append({
                "product_id": "iron_scrap",
                "price_date": price_date,
                "price": price,
                "source": "tetsugen",
                "created_at": datetime.utcnow(),
            })

    return records


def _parse_tetsugen_price(text: str) -> float | None:
    """鉄源協会の価格テキストを数値に変換

    カンマ・括弧を除去してfloat変換。空文字はスキップ。
    例: "14,400" → 14400.0, "(12,000)" → 12000.0, "" → None
    """
    if not text:
        return None

    # 括弧・カンマ・全角スペース除去
    cleaned = text.replace(",", "").replace("，", "").replace("(", "").replace(")", "")
    cleaned = cleaned.replace("（", "").replace("）", "").replace("\u3000", "").replace(" ", "")

    if not cleaned:
        return None

    m = re.search(r"(\d+\.?\d*)", cleaned)
    if m:
        return float(m.group(1))
    return None


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
