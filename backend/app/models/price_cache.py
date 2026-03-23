import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PriceCache(Base):
    __tablename__ = "price_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100))
    latest_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    price_change: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    price_change_pct: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    source: Mapped[str] = mapped_column(String(20), default="akshare")
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
