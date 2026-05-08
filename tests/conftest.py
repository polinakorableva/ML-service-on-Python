import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.billing import PromoCode
from datetime import datetime, timedelta

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    database = TestingSessionLocal()
    yield database
    database.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    user = User(
        email="test@test.com",
        hashed_password="fakehash",
        balance=50,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def promo_active(db):
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