from pydantic import BaseModel
from datetime import datetime


class TopupRequest(BaseModel):
    amount: float


class PromoRequest(BaseModel):
    code: str


class BalanceResponse(BaseModel):
    balance: float


class TransactionResponse(BaseModel):
    id: int
    amount: float
    type: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True