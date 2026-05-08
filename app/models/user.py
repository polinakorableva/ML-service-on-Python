from sqlalchemy import Column, Integer, String, Numeric, DateTime, func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"  # имя таблицы в PostgreSQL

    id              = Column(Integer, primary_key=True)
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    balance         = Column(Numeric(10, 2), default=0, nullable=False)
    role            = Column(String, default="user")
    created_at      = Column(DateTime, server_default=func.now())