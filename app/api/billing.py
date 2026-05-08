from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.schemas.billing import (
    TopupRequest,
    PromoRequest,
    BalanceResponse,
    TransactionResponse
)
from app.services.billing_service import (
    get_balance,
    topup_balance,
    activate_promo,
    get_history
)


router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/balance", response_model=BalanceResponse)
def balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return BalanceResponse(balance=get_balance(db, current_user.id))


@router.post("/topup", response_model=BalanceResponse)
def topup(
    data: TopupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        new_balance = topup_balance(db, current_user.id, data.amount)
        return BalanceResponse(balance=new_balance)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/promo", response_model=BalanceResponse)
def promo(
    data: PromoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        new_balance = activate_promo(db, current_user.id, data.code)
        return BalanceResponse(balance=new_balance)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=list[TransactionResponse])
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_history(db, current_user.id)