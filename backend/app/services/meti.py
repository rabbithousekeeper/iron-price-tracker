"""経済産業省 資源エネルギー庁の公開CSVから石油化学系データを取得するサービス

対象: ナフサ、エチレン、プロピレン、ベンゼン等の石油化学製品
データ元: 経済産業省 資源エネルギー庁 石油製品価格調査
"""

import io
import logging
from datetime import date, datetime

import httpx
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.price import CommodityPrice, FetchLog

logger = logging.getLogger(__name__)

# 経産省エネルギー庁の石油製品価格調査CSV URL
# 石油製品価格調査（週次・月次）
METI_CSV_URLS: list[dict] = [
    {
        "url": "https://www.enecho.meti.go.jp/statistics/petroleum_and_lpgas/pl007/results/csv/s_naphtha.csv",
        "product_id": "naphtha_domestic",
        "description": "国産ナフサ基準価格",
        "price_column": None,  # CSVの構造に応じて動的に判定
    },
]

# 石油化学製品マッピング（CSVカラム名 → プロダクトID）
PETROCHEMICAL_PRODUCTS = {
    "naphtha": {"product_id": "naphtha", "keywords": ["ナフサ", "naphtha"]},
    "ethylene": {"product_id": "ethylene", "keywords": ["エチレン", "ethylene"]},
    "propylene": {"product_id": "propylene", "keywords": ["プロピレン", "propylene"]},
    "benzene": {"product_id": "benzene", "keywords": ["ベンゼン", "benzene"]},
}


async def fetch_meti_prices(db: Session) -> int:
    """経産省の公開CSVから石油化学系データを取得してDBに保存

    経産省の統計データは年度ごとに公開されるため、
    利用可能なCSVを取得して解析する
    """
    total_saved = 0
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        # 石油製品価格調査のページからデータを取得
        try:
            saved = await _fetch_meti_petroleum_stats(client, db)
            total_saved += saved
        except Exception as e:
            logger.error(f"経産省石油製品統計取得エラー: {e}")
            errors.append(f"petroleum_stats: {str(e)}")

        # 石油化学製品の国内価格データ（経産省生産動態統計等）
        try:
            saved = await _fetch_meti_petrochemical_stats(client, db)
            total_saved += saved
        except Exception as e:
            logger.error(f"経産省石油化学統計取得エラー: {e}")
            errors.append(f"petrochemical_stats: {str(e)}")

    # 取得ログを記録
    log = FetchLog(
        source="meti",
        status="success" if not errors else "partial_error",
        message="; ".join(errors) if errors else None,
        records_count=total_saved,
    )
    db.add(log)
    db.commit()

    return total_saved


async def _fetch_meti_petroleum_stats(client: httpx.AsyncClient, db: Session) -> int:
    """経産省 石油製品価格調査CSVを取得・解析"""
    saved = 0

    # 石油製品価格調査（月次価格）
    # 経産省の統計CSVのURLパターン
    current_year = date.today().year
    urls_to_try = [
        f"https://www.enecho.meti.go.jp/statistics/petroleum_and_lpgas/pl007/results/csv/sekiyu_{year}.csv"
        for year in range(current_year, current_year - 3, -1)
    ]

    for url in urls_to_try:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                continue

            # CSV解析（日本語エンコーディング対応）
            content = resp.content
            for encoding in ["shift_jis", "cp932", "utf-8", "utf-8-sig"]:
                try:
                    text = content.decode(encoding)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                logger.warning(f"CSVのエンコーディングを判定できません: {url}")
                continue

            records = _parse_meti_csv(text)
            if records:
                saved += _upsert_records(db, records)

        except httpx.HTTPStatusError:
            continue
        except Exception as e:
            logger.warning(f"経産省CSV取得エラー ({url}): {e}")

    return saved


async def _fetch_meti_petrochemical_stats(
    client: httpx.AsyncClient,
    db: Session,
) -> int:
    """経産省 生産動態統計等から石油化学製品価格を取得"""
    saved = 0

    # 化学工業統計（月次）
    current_year = date.today().year
    urls_to_try = [
        f"https://www.meti.go.jp/statistics/tyo/seidou/result/csv/b2011_kag_{year}.csv"
        for year in range(current_year, current_year - 3, -1)
    ]

    for url in urls_to_try:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                continue

            content = resp.content
            for encoding in ["shift_jis", "cp932", "utf-8", "utf-8-sig"]:
                try:
                    text = content.decode(encoding)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            else:
                continue

            records = _parse_petrochemical_csv(text)
            if records:
                saved += _upsert_records(db, records)

        except Exception as e:
            logger.warning(f"経産省化学統計取得エラー ({url}): {e}")

    return saved


def _parse_meti_csv(text: str) -> list[dict]:
    """経産省CSVを解析して価格レコードリストに変換"""
    records = []

    try:
        df = pd.read_csv(io.StringIO(text), header=None, encoding="utf-8")
    except Exception:
        return records

    # CSVの構造を動的に判定
    # 一般的な経産省CSVは、最初の数行がヘッダー、その後にデータ行
    for _, row in df.iterrows():
        row_values = [str(v).strip() for v in row.values if pd.notna(v)]
        row_text = " ".join(row_values).lower()

        # ナフサ関連の行を検出
        for product_key, product_info in PETROCHEMICAL_PRODUCTS.items():
            if any(kw.lower() in row_text or kw in row_text for kw in product_info["keywords"]):
                # 数値データを抽出
                for val in row.values:
                    if pd.notna(val):
                        try:
                            price = float(str(val).replace(",", ""))
                            if price > 100:  # 価格らしい値のみ
                                records.append({
                                    "product_id": product_info["product_id"],
                                    "price_date": date.today(),
                                    "price": price,
                                    "source": "meti",
                                    "created_at": datetime.utcnow(),
                                })
                                break
                        except ValueError:
                            continue

    return records


def _parse_petrochemical_csv(text: str) -> list[dict]:
    """石油化学統計CSVを解析"""
    records = []

    try:
        df = pd.read_csv(io.StringIO(text), header=None, encoding="utf-8")
    except Exception:
        return records

    for _, row in df.iterrows():
        row_values = [str(v).strip() for v in row.values if pd.notna(v)]
        row_text = " ".join(row_values)

        for product_key, product_info in PETROCHEMICAL_PRODUCTS.items():
            if any(kw in row_text for kw in product_info["keywords"]):
                for val in row.values:
                    if pd.notna(val):
                        try:
                            price = float(str(val).replace(",", ""))
                            if price > 100:
                                records.append({
                                    "product_id": product_info["product_id"],
                                    "price_date": date.today(),
                                    "price": price,
                                    "source": "meti",
                                    "created_at": datetime.utcnow(),
                                })
                                break
                        except ValueError:
                            continue

    return records


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
