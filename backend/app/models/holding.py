import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# 申万一级行业分类
SECTOR_CHOICES = (
    "银行", "非银金融", "房地产", "建筑装饰", "建筑材料",
    "钢铁", "采掘", "有色金属", "化工", "石油石化",
    "国防军工", "机械设备", "电气设备", "通信", "计算机",
    "电子", "传媒", "医药生物", "农林牧渔", "食品饮料",
    "纺织服饰", "轻工制造", "商业贸易", "休闲服务", "综合",
    "公用事业", "交通运输", "汽车", "家用电器",
)


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="申万一级行业分类")
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    latest_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    latest_price_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="首次买入日期")
    cost_method: Mapped[str] = mapped_column(
        Enum("fifo", "average", name="cost_method_enum", create_constraint=True),
        default="fifo",
        nullable=False,
        comment="成本计算方法: fifo=先进先出, average=平均成本",
    )
    account: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
