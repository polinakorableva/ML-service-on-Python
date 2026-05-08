from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.core.database import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    name       = Column(String, nullable=False)
    file_path  = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())