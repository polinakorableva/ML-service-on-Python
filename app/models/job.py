from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, func
from app.core.database import Base


class PredictionJob(Base):
    __tablename__ = "prediction_jobs"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_id   = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    status     = Column(String, default="pending")
    result     = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())