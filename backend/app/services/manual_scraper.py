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

# Westmetall LME価格ページ
WESTMETALL_NI_URL = "https://www.westmetall.com/en/markdaten.php?action=table&field=LME_Ni_cash"
WESTMETALL_SN_URL = "https://www.westmetall.com/en/markdaten.php?action=table&field=LME_Sn_cash"

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
        "User-Agent": "iron-price-tracker/1.0",
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


async def fetch_westmetall_prices(db: Session) -> int:
    """WestmetallからLMEニッケル・錫の日次価格をスクレイピング"""
    total_saved = 0
    errors: list[str] = []

    targets = [
        {"url": WESTMETALL_NI_URL, "product_id": "nickel", "label": "ニッケル"},
        {"url": WESTMETALL_SN_URL, "product_id": "tin", "label": "錫"},
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PriceTracker/1.0)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en,ja;q=0.9",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        for target in targets:
            try:
                resp = await client.get(target["url"])
                resp.raise_for_status()
                content = _decode_html(resp.content)
                records = _parse_westmetall_html(content, target["product_id"])
                if records:
                    total_saved += _upsert_records(db, records)
                    logger.info(f"Westmetall {target['label']}: {len(records)}件取得")
                else:
                    logger.warning(f"Westmetall {target['label']}: 解析可能なデータが見つかりませんでした")
            except httpx.HTTPStatusError as e:
                msg = f"Westmetall {target['label']} HTTPエラー: {e.response.status_code}"
                logger.error(msg)
                errors.append(msg)
            except Exception as e:
                msg = f"Westmetall {target['label']} 取得エラー: {str(e)}"
                logger.error(msg)
                errors.append(msg)

    log = FetchLog(
        source="westmetall",
        status="success" if not errors else "error",
        message="; ".join(errors) if errors else f"{total_saved}件取得",
        records_count=total_saved,
    )
    db.add(log)
    db.commit()

    return total_saved


async def fetch_boj_cgpi_prices(db: Session) -> int:
    """日本銀行 企業物価指数（CGPI）を時系列統計API経由で取得

    API: https://www.stat-search.boj.or.jp/api/v1/
    DB: PR01（企業物価指数）

    手順:
    1. getMetadata APIで品目キーワード検索 → 系列コード特定
    2. getDataCode APIで月次指数データ取得
    """
    total_saved = 0
    errors: list[str] = []

    # 検索キーワード → product_id マッピング
    # 複数キーワードで検索し、最初にヒットしたものを使用
    target_searches = [
        {
            "product_id": "tool_steel",
            "keywords": ["特殊鋼熱間圧延鋼材", "特殊鋼棒鋼", "特殊鋼小棒", "特殊鋼"],
            "description": "特殊鋼関連指数",
        },
        {
            "product_id": "stainless_sheet",
            "keywords": ["ステンレス鋼冷間仕上鋼材", "ステンレス鋼板", "ステンレス鋼"],
            "description": "ステンレス鋼関連指数",
        },
    ]

    boj_api_base = "https://www.stat-search.boj.or.jp/api/v1"

    async with httpx.AsyncClient(timeout=60.0) as client:
        for target in target_searches:
            series_code = None

            # ステップ1: メタデータ検索で系列コードを特定
            for keyword in target["keywords"]:
                try:
                    resp = await client.get(
                        f"{boj_api_base}/getMetadata",
                        params={"db": "PR01", "lang": "jp", "format": "json", "searchWord": keyword},
                    )
                    resp.raise_for_status()
                    meta = resp.json()

                    # レスポンス構造: {"RESULTSET": [{SERIES_CODE, NAME_OF_TIME_SERIES_J, FREQUENCY, ...}, ...]}
                    entries = meta.get("RESULTSET", [])

                    if entries:
                        # キーワードが NAME_OF_TIME_SERIES_J に含まれるエントリのみ対象
                        matched = [e for e in entries
                                   if e.get("SERIES_CODE")
                                   and keyword in e.get("NAME_OF_TIME_SERIES_J", "")]

                        if not matched:
                            continue

                        # 月次データ(M)を優先
                        monthly = [e for e in matched if e.get("FREQUENCY", "") == "M"]
                        entry = monthly[0] if monthly else matched[0]
                        series_code = entry.get("SERIES_CODE")
                        code_name = entry.get("NAME_OF_TIME_SERIES_J", keyword)
                        logger.info(f"日銀CGPI {target['description']}: コード={series_code} ({code_name})")
                        break

                except Exception as e:
                    logger.debug(f"日銀CGPI メタデータ検索失敗 ({keyword}): {e}")
                    continue

            if not series_code:
                msg = f"日銀CGPI: {target['description']}の系列コードが見つかりません"
                logger.warning(msg)
                errors.append(msg)
                continue

            # ステップ2: データ取得
            try:
                resp = await client.get(
                    f"{boj_api_base}/getDataCode",
                    params={
                        "db": "PR01",
                        "code": series_code,
                        "format": "json",
                        "lang": "jp",
                        "startDate": "202001",
                        "endDate": date.today().strftime("%Y%m"),
                    },
                )
                resp.raise_for_status()
                result = resp.json()

                # レスポンス構造: {"RESULTSET": [{SERIES_CODE, VALUES: {SURVEY_DATES: [...], VALUES: [...]}, ...}]}
                series_list = result.get("RESULTSET", [])

                records_to_upsert = []
                for series in series_list:
                    # VALUES はオブジェクト（その中に SURVEY_DATES と VALUES がネスト）
                    values_obj = series.get("VALUES", {})
                    if not isinstance(values_obj, dict):
                        continue
                    survey_dates = values_obj.get("SURVEY_DATES", [])
                    values = values_obj.get("VALUES", [])

                    for i, survey_date in enumerate(survey_dates):
                        if i >= len(values):
                            break

                        value = values[i]
                        if value is None or value == "":
                            continue

                        try:
                            price = float(value)
                        except (ValueError, TypeError):
                            continue

                        # 日付パース: "202401" → date(2024, 1, 1)
                        survey_date_str = str(survey_date)
                        try:
                            if len(survey_date_str) >= 6:
                                year = int(survey_date_str[:4])
                                month = int(survey_date_str[4:6])
                                price_date = date(year, month, 1)
                            else:
                                continue
                        except (ValueError, IndexError):
                            continue

                        records_to_upsert.append({
                            "product_id": target["product_id"],
                            "price_date": price_date,
                            "price": price,
                            "source": "boj_cgpi",
                            "created_at": datetime.utcnow(),
                        })

                if records_to_upsert:
                    total_saved += _upsert_records(db, records_to_upsert)
                    logger.info(f"日銀CGPI {target['description']}: {len(records_to_upsert)}件保存")
                else:
                    logger.warning(f"日銀CGPI {target['description']}: 有効なデータポイントなし")

            except Exception as e:
                msg = f"日銀CGPI {target['description']} データ取得エラー: {str(e)}"
                logger.error(msg)
                errors.append(msg)

    # 取得ログを記録
    log = FetchLog(
        source="boj_cgpi",
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

    # Westmetall（LMEニッケル・錫）
    try:
        count = await fetch_westmetall_prices(db)
        results["westmetall"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"Westmetall取得エラー: {e}")
        results["westmetall"] = {"status": "error", "message": str(e)}

    # 日本銀行 企業物価指数（CGPI）
    try:
        count = await fetch_boj_cgpi_prices(db)
        results["boj_cgpi"] = {"status": "success", "records": count}
    except Exception as e:
        logger.error(f"日銀CGPI取得エラー: {e}")
        results["boj_cgpi"] = {"status": "error", "message": str(e)}

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

    HTML構造（https://www.jisri.or.jp/kakaku）:
    - テーブル: table.kakaku-tbl01
    - データ行: tr > th（日付 "2026年3月"） + td×8（価格列）
    - td[7]（最後の列）= 関東・中部・関西三地区平均
    - 価格形式: "48,500～50,000" → 平均値、"45,000中心" → その値
    - product_id: "iron_scrap"
    """
    records = []

    # kakaku-tbl01テーブル内の行を抽出
    table_match = re.search(
        r'<table[^>]*class="[^"]*kakaku-tbl01[^"]*"[^>]*>(.*?)</table>',
        html, re.DOTALL | re.IGNORECASE,
    )
    if not table_match:
        # フォールバック: テーブル全体から探す
        table_html = html
    else:
        table_html = table_match.group(1)

    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE)

    for row in rows:
        # th（日付列）を抽出
        th_match = re.search(r"<th[^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
        if not th_match:
            continue
        th_text = re.sub(r"<[^>]+>", "", th_match.group(1)).strip()

        # "YYYY年M月" 形式の日付をパース
        date_match = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", th_text)
        if not date_match:
            continue
        price_date = date(int(date_match.group(1)), int(date_match.group(2)), 1)

        # td列を抽出
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
        if len(tds) < 8:
            continue

        # 最後の列（td[7]）= 三地区平均価格
        price_text = re.sub(r"<[^>]+>", "", tds[7]).strip()
        price = _parse_jisri_price(price_text)
        if price is not None:
            records.append({
                "product_id": "iron_scrap",
                "price_date": price_date,
                "price": price,
                "source": "jisri",
                "created_at": datetime.utcnow(),
            })

    return records


def _parse_jisri_price(text: str) -> float | None:
    """JISRIの価格テキストを数値に変換

    "48,500～50,000" → (48500 + 50000) / 2 = 49250.0
    "45,000中心" → 45000.0
    "48,500" → 48500.0
    """
    if not text:
        return None

    # カンマ・全角スペース除去
    cleaned = text.replace(",", "").replace("，", "").replace("\u3000", "").replace(" ", "")

    # "～" で範囲指定されている場合は平均値
    if "～" in cleaned or "~" in cleaned:
        parts = re.split(r"[～~]", cleaned)
        nums = []
        for part in parts:
            m = re.search(r"(\d+\.?\d*)", part)
            if m:
                nums.append(float(m.group(1)))
        if len(nums) == 2:
            return (nums[0] + nums[1]) / 2
        elif len(nums) == 1:
            return nums[0]
        return None

    # "中心" が付いている場合は数値部分を取得
    cleaned = cleaned.replace("中心", "")

    m = re.search(r"(\d+\.?\d*)", cleaned)
    if m:
        return float(m.group(1))
    return None


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


def _parse_westmetall_html(html: str, product_id: str) -> list[dict]:
    """WestmetallのHTMLからLME日次価格を抽出

    テーブル19個（年別）、各行: td[0]=日付("02. April 2026"), td[1]=Cash価格(USD/t)
    """
    records = []

    month_map = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }

    tables = re.findall(r"<table[^>]*>(.*?)</table>", html, re.DOTALL | re.IGNORECASE)
    for table_html in tables:
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE)
        for row in rows:
            tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL | re.IGNORECASE)
            if len(tds) < 2:
                continue

            date_text = re.sub(r"<[^>]+>", "", tds[0]).strip()
            price_text = re.sub(r"<[^>]+>", "", tds[1]).strip()

            date_match = re.match(r"(\d{1,2})\.\s*(\w+)\s+(\d{4})", date_text)
            if not date_match:
                continue

            day = int(date_match.group(1))
            month = month_map.get(date_match.group(2).lower())
            year = int(date_match.group(3))
            if month is None:
                continue

            try:
                price_date = date(year, month, day)
            except ValueError:
                continue

            price_cleaned = price_text.replace(",", "").strip()
            if not price_cleaned:
                continue
            try:
                price = float(price_cleaned)
            except ValueError:
                continue

            records.append({
                "product_id": product_id,
                "price_date": price_date,
                "price": price,
                "source": "westmetall",
                "created_at": datetime.utcnow(),
            })

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
