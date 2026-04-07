"""価格データAPIエンドポイント"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CommodityPrice, FetchLog

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("/")
def get_prices(
    product_id: str | None = Query(None, description="商品ID（指定なしで全商品）"),
    start_date: date | None = Query(None, description="開始日（YYYY-MM-DD）"),
    end_date: date | None = Query(None, description="終了日（YYYY-MM-DD）"),
    source: str | None = Query(None, description="データソース（worldbank, eia, meti）"),
    limit: int = Query(1000, ge=1, le=10000, description="取得件数上限"),
    db: Session = Depends(get_db),
):
    """価格データを取得

    フロントエンドのPriceRecord形式に合わせてレスポンスを返す
    """
    query = db.query(CommodityPrice).order_by(
        CommodityPrice.product_id,
        CommodityPrice.price_date,
    )

    if product_id:
        query = query.filter(CommodityPrice.product_id == product_id)
    if start_date:
        query = query.filter(CommodityPrice.price_date >= start_date)
    if end_date:
        query = query.filter(CommodityPrice.price_date <= end_date)
    if source:
        query = query.filter(CommodityPrice.source == source)

    records = query.limit(limit).all()

    return {
        "count": len(records),
        "records": [
            {
                "productId": r.product_id,
                "date": r.price_date.isoformat(),
                "dateLabel": _format_date_label(r.price_date),
                "price": r.price,
                "source": r.source,
            }
            for r in records
        ],
    }


@router.get("/latest")
def get_latest_prices(
    db: Session = Depends(get_db),
):
    """各商品の最新価格を取得"""
    # 各product_idの最新日付を取得するサブクエリ
    subquery = (
        db.query(
            CommodityPrice.product_id,
            func.max(CommodityPrice.price_date).label("max_date"),
        )
        .group_by(CommodityPrice.product_id)
        .subquery()
    )

    records = (
        db.query(CommodityPrice)
        .join(
            subquery,
            (CommodityPrice.product_id == subquery.c.product_id)
            & (CommodityPrice.price_date == subquery.c.max_date),
        )
        .all()
    )

    return {
        "count": len(records),
        "records": [
            {
                "productId": r.product_id,
                "date": r.price_date.isoformat(),
                "dateLabel": _format_date_label(r.price_date),
                "price": r.price,
                "source": r.source,
            }
            for r in records
        ],
    }


@router.get("/sources")
def get_available_sources(db: Session = Depends(get_db)):
    """利用可能なデータソースと最終取得日時を返す"""
    logs = (
        db.query(FetchLog)
        .order_by(FetchLog.fetched_at.desc())
        .limit(20)
        .all()
    )

    # ソースごとの最新ログ
    latest_by_source: dict[str, dict] = {}
    for log in logs:
        if log.source not in latest_by_source:
            latest_by_source[log.source] = {
                "source": log.source,
                "status": log.status,
                "lastFetched": log.fetched_at.isoformat() if log.fetched_at else None,
                "recordsCount": log.records_count,
                "message": log.message,
            }

    return {"sources": list(latest_by_source.values())}


def _format_date_label(d: date) -> str:
    """日付を日本語表示用ラベルに変換"""
    return f"{d.year}年{d.month}月{d.day}日"
