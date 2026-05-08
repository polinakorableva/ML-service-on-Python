from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.billing import PromoCode

db = SessionLocal()

promos = [
    PromoCode(
        code="WELCOME100",
        credits=100,
        max_uses=1000,
        expires_at=None
    ),
    PromoCode(
        code="ONCE50",
        credits=50,
        max_uses=1,
        expires_at=None
    ),
    PromoCode(
        code="EXPIRED",
        credits=999,
        max_uses=1000,
        expires_at=datetime.utcnow() - timedelta(days=1)
    ),
]

for promo in promos:
    # Не создаём если уже есть
    exists = db.query(PromoCode).filter(PromoCode.code == promo.code).first()
    if not exists:
        db.add(promo)

db.commit()
print("Промокоды созданы:")
for p in db.query(PromoCode).all():
    print(f"  {p.code}: {p.credits} кредитов, max_uses={p.max_uses}")

db.close()