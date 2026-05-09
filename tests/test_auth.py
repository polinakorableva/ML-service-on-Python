import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

class TestPasswordHashing:
    """Тесты хешироания паролей."""

    def test_hash_is_not_plain_password(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"

    def test_hash_is_string(self):
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)

    def test_same_password_gives_different_hashes(self):
        hash1 = hash_password("mypassword")
        hash2 = hash_password("mypassword")
        assert hash1 != hash2

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_empty_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("", hashed) is False


class TestJWT:
    def test_create_token_returns_string(self):
        token = create_access_token(user_id=1)
        assert isinstance(token, str)

    def test_token_has_three_parts(self):
        token = create_access_token(user_id=1)
        parts = token.split(".")
        assert len(parts) == 3

    def test_decode_returns_correct_user_id(self):
        token = create_access_token(user_id=42)
        user_id = decode_access_token(token)
        assert user_id == 42

    def test_decode_invalid_token_returns_none(self):
        result = decode_access_token("this.is.invalid")
        assert result is None

    def test_decode_empty_string_returns_none(self):
        result = decode_access_token("")
        assert result is None

    def test_decode_garbage_returns_none(self):
        result = decode_access_token("notavalidjwtatall")
        assert result is None


class TestRegister:

    def test_register_success(self, client):
        response = client.post("/auth/register", json={
            "email": "new@test.com",
            "password": "password123"
        })

        assert response.status_code == 201

        data = response.json()
        assert data["email"] == "new@test.com"
        assert data["balance"] == 10.0   # INITIAL_CREDITS
        assert data["role"] == "user"

    def test_register_no_password_in_response(self, client):
        response = client.post("/auth/register", json={
            "email": "new@test.com",
            "password": "password123"
        })

        data = response.json()

        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user):
        response = client.post("/auth/register", json={
            "email": "test@test.com",   
            "password": "anotherpassword"
        })

        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    def test_register_missing_email(self, client):
        response = client.post("/auth/register", json={
            "password": "password123"
        })

        assert response.status_code == 422

    def test_register_missing_password(self, client):
        response = client.post("/auth/register", json={
            "email": "new@test.com"
        })

        assert response.status_code == 422


class TestLogin:

    def test_login_success(self, client, test_user):
        response = client.post("/auth/login", json={
            "email": "test@test.com",
            "password": "secret123"
        })

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_token_is_valid_jwt(self, client, test_user):
        response = client.post("/auth/login", json={
            "email": "test@test.com",
            "password": "secret123"
        })

        token = response.json()["access_token"]
        user_id = decode_access_token(token)

        assert user_id == test_user.id

    def test_login_wrong_password(self, client, test_user):
        response = client.post("/auth/login", json={
            "email": "test@test.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401

    def test_login_wrong_email(self, client, test_user):
        response = client.post("/auth/login", json={
            "email": "nobody@test.com",
            "password": "secret123"
        })

        assert response.status_code == 401

    def test_login_error_message_same_for_wrong_email_and_password(
        self, client, test_user
    ):
        response_bad_email = client.post("/auth/login", json={
            "email": "nobody@test.com",
            "password": "secret123"
        })
        response_bad_password = client.post("/auth/login", json={
            "email": "test@test.com",
            "password": "wrongpassword"
        })

        assert response_bad_email.json()["detail"] == \
               response_bad_password.json()["detail"]


class TestGetMe:
    """Тесты эндпоинта GET /auth/me."""

    def test_get_me_success(self, client, test_user, auth_headers):
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert data["email"] == "test@test.com"
        assert data["id"] == test_user.id

    def test_get_me_without_token(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 403

    def test_get_me_invalid_token(self, client):
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code in [401, 403]

    def test_get_me_no_password_in_response(self, client, auth_headers):
        response = client.get("/auth/me", headers=auth_headers)
        data = response.json()
        assert "hashed_password" not in data
        assert "password" not in data