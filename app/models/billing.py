from sqlalchemy import (
    Column, Integer, String, Numeric,
    ForeignKey, DateTime, func, UniqueConstraint
)
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount      = Column(Numeric(10, 2), nullable=False)
    type        = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at  = Column(DateTime, server_default=func.now())


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id         = Column(Integer, primary_key=True)
    code       = Column(String, unique=True, nullable=False, index=True)
    credits    = Column(Numeric(10, 2), nullable=False)
    max_uses   = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)


class PromoUsage(Base):
    __tablename__ = "promo_usages"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    promo_id     = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    activated_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "promo_id", name="uq_user_promo"),
    )