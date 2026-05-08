from app.core.database import SessionLocal
from app.models.user import User
from app.models.billing import PromoCode

db = SessionLocal()

user_count = db.query(User).count()
print(f"Пользователей в БД: {user_count}")

promo = PromoCode(code="WELCOME100", credits=100, max_uses=1000)
db.add(promo)
db.commit()
print(f"Промокод создан: {promo.id}")

found = db.query(PromoCode).filter(PromoCode.code == "WELCOME100").first()
print(f"Промокод найден: {found.code}, кредитов: {found.credits}")

db.close()