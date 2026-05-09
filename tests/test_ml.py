import pytest
import io
import joblib
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sklearn.linear_model import LogisticRegression
from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.billing import PromoCode
from app.models.ml_model import MLModel
from app.models.job import PredictionJob
from datetime import datetime, timedelta


# ── База данных для тестов ─────────────────────────────────────────────────

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    """Подменяем реальную PostgreSQL на SQLite в памяти."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Чистая БД перед каждым тестом."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Сессия тестовой БД."""
    database = TestingSessionLocal()
    yield database
    database.close()


@pytest.fixture
def client():
    """HTTP-клиент с подменённой БД."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Пользователи ───────────────────────────────────────────────────────────

@pytest.fixture
def test_user(db):
    """Обычный пользователь с балансом 50."""
    user = User(
        email="test@test.com",
        hashed_password=hash_password("secret123"),
        balance=50,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    """Администратор."""
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("adminpass"),
        balance=100,
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_token(test_user):
    """JWT-токен для обычного пользователя."""
    return create_access_token(test_user.id)


@pytest.fixture
def admin_token(admin_user):
    """JWT-токен для администратора."""
    return create_access_token(admin_user.id)


@pytest.fixture
def auth_headers(user_token):
    """
    Заголовки авторизации готовые для передачи в client.get/post.
    Использование: client.get("/auth/me", headers=auth_headers)
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Заголовки авторизации для администратора."""
    return {"Authorization": f"Bearer {admin_token}"}


# ── ML-модели ──────────────────────────────────────────────────────────────

@pytest.fixture
def sklearn_model_bytes():
    """
    Создаёт обученную sklearn-модель и возвращает её как байты.
    Используется для тестирования загрузки модели.
    """
    # Обучаем простую модель на минимальных данных
    X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    y = np.array([0, 0, 1, 1])
    model = LogisticRegression()
    model.fit(X, y)

    # Сериализуем модель в байты (как если бы сохранили в файл)
    buffer = io.BytesIO()   # BytesIO — файл в памяти, не на диске
    joblib.dump(model, buffer)
    buffer.seek(0)          # перемотка в начало буфера перед чтением

    return buffer.getvalue()  # возвращаем байты


@pytest.fixture
def test_model(db, test_user, tmp_path, sklearn_model_bytes):
    """
    Создаёт файл модели на диске и запись в БД.
    tmp_path — встроенная pytest фикстура, временная папка для теста.
    """
    # Сохраняем байты модели во временный файл
    model_file = tmp_path / "test_model.pkl"
    model_file.write_bytes(sklearn_model_bytes)

    # Создаём запись в БД
    ml_model = MLModel(
        user_id=test_user.id,
        name="test_model.pkl",
        file_path=str(model_file)   # str() потому что SQLAlchemy ожидает строку
    )
    db.add(ml_model)
    db.commit()
    db.refresh(ml_model)
    return ml_model


@pytest.fixture
def pending_job(db, test_user, test_model):
    """Задача предсказания в статусе pending."""
    job = PredictionJob(
        user_id=test_user.id,
        model_id=test_model.id,
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# ── Промокоды ──────────────────────────────────────────────────────────────

@pytest.fixture
def promo_active(db):
    """Многоразовый активный промокод."""
    promo = PromoCode(
        code="TEST100",
        credits=100,
        max_uses=10,
        used_count=0,
        expires_at=None
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo


@pytest.fixture
def promo_expired(db):
    """Просроченный промокод."""
    promo = PromoCode(
        code="EXPIRED",
        credits=100,
        max_uses=10,
        used_count=0,
        expires_at=datetime.utcnow() - timedelta(days=1)
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo


@pytest.fixture
def promo_exhausted(db):
    """Исчерпанный промокод."""
    promo = PromoCode(
        code="USED",
        credits=100,
        max_uses=1,
        used_count=1,
        expires_at=None
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return promo