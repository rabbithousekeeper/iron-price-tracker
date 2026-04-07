from datetime import date, datetime

from sqlalchemy import String, Float, Date, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CommodityPrice(Base):
    """商品価格レコード"""

    __tablename__ = "commodity_prices"
    __table_args__ = (
        UniqueConstraint("product_id", "price_date", name="uq_product_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    price_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # 'worldbank', 'eia', 'meti'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FetchLog(Base):
    """データ取得ログ"""

    __tablename__ = "fetch_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # 'success', 'error'
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    records_count: Mapped[int] = mapped_column(Integer, default=0)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
