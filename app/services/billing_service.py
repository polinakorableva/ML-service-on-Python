from datetime import datetime
from app.schemas import user
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.billing import Transaction, PromoCode, PromoUsage
from decimal import Decimal


def get_balance(db: Session, user_id: int) -> float:
    user = db.query(User).filter(User.id == user_id).first()
    return float(user.balance)


def topup_balance(db: Session, user_id: int, amount: float) -> float:

    if amount <= 0:
        raise ValueError("Сумма пополнения должна быть больше нуля")

    if amount > 100_000:
        raise ValueError("Сумма пополнения не может превышать 100 000")

    user = db.query(User).filter(User.id == user_id).first()

    user.balance += Decimal(str(amount))

    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        type="credit",
        description=f"Пополнение баланса на {amount} кредитов"
    )
    db.add(transaction)

    db.commit()
    db.refresh(user)

    return float(user.balance)


def activate_promo(db: Session, user_id: int, code: str) -> float:
    promo = (
        db.query(PromoCode)
        .filter(PromoCode.code == code.upper().strip())
        .first()
    )

    if promo is None:
        raise ValueError("Промокод не найден")
    if promo.expires_at is not None:
        if datetime.utcnow() > promo.expires_at:
            raise ValueError("Срок действия промокода истёк")
    if promo.used_count >= promo.max_uses:
        raise ValueError("Промокод уже использован максимальное количество раз")
    usage = PromoUsage(user_id=user_id, promo_id=promo.id)
    db.add(usage)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ValueError("Вы уже активировали этот промокод")

    # Шаг 5 — начисляем кредиты и инкрементируем счётчик
    user = db.query(User).filter(User.id == user_id).first()
    user.balance += Decimal(str(promo.credits))
    promo.used_count += 1

    # Записываем транзакцию
    transaction = Transaction(
        user_id=user_id,
        amount=float(promo.credits),
        type="promo",
        description=f"Промокод {promo.code}: +{promo.credits} кредитов"
    )
    db.add(transaction)

    db.commit()
    db.refresh(user)

    return float(user.balance)


def get_history(db: Session, user_id: int) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .all()
    )