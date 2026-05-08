from app.core.database import SessionLocal
from app.models.user import User
from app.models.billing import Transaction, PromoCode
from app.core.security import hash_password

db = SessionLocal()

user = db.query(User).filter(User.email == "test@test.com").first()
if not user:
    user = User(
        email="test@test.com",
        hashed_password=hash_password("secret123"),
        balance=75,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

transactions = [
    Transaction(user_id=user.id, amount=100,  type="credit", description="Пополнение"),
    Transaction(user_id=user.id, amount=-1,   type="debit",  description="Предсказание job#1"),
    Transaction(user_id=user.id, amount=-1,   type="debit",  description="Предсказание job#2"),
    Transaction(user_id=user.id, amount=50,   type="promo",  description="Промокод WELCOME100"),
    Transaction(user_id=user.id, amount=-1,   type="debit",  description="Предсказание job#3"),
]
for t in transactions:
    db.add(t)

db.commit()
print("Тестовые данные созданы")
db.close()