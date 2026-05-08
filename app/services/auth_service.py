from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings


def register_user(db: Session, email: str, password: str) -> User:
    """
    Регистрирует нового пользователя.
    Бросает ValueError если email уже занят.
    """
    print("PASSWORD:", password)
    print("LEN:", len(password))
    print("TYPE:", type(password))
    # Проверяем что такого email ещё нет
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("Пользователь с таким email уже существует")

    # Создаём объект пользователя
    user = User(
        email=email,
        hashed_password=hash_password(password),
        balance=settings.INITIAL_CREDITS,
        role="user"
    )

    # Сохраняем в БД
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def login_user(db: Session, email: str, password: str) -> str:
    """
    Проверяет логин и пароль.
    Возвращает JWT-токен или бросает ValueError.
    """
    # Ищем пользователя по email
    user = db.query(User).filter(User.email == email).first()

    # Проверяем пользователя и пароль одной ошибкой — не раскрываем что именно неверно
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Неверный email или пароль")

    return create_access_token(user.id)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Возвращает пользователя по id или None."""
    return db.query(User).filter(User.id == user_id).first()