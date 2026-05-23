"""
tests/test_jwt_auth.py
Unit tests for JWT authentication layer.
Run with: pytest tests/ -v
"""
import sys
import os
import pytest

# Point to api-gateway so we can import auth.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "api-gateway"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "shared"))

# Override secret before importing auth so tests use known values
os.environ["JWT_SECRET_KEY"]                  = "test-secret-key-for-pytest"
os.environ["JWT_ALGORITHM"]                   = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

import jwt
from auth import generate_token, verify_token, auth_bp
from flask import Flask


@pytest.fixture
def app():
    """Create a minimal Flask app with the auth blueprint."""
    application = Flask(__name__)
    application.register_blueprint(auth_bp)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


# ── Token generation tests ────────────────────────────────────────────────────

class TestTokenGeneration:
    def test_generate_token_returns_string(self):
        token = generate_token("testuser", "admin")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_contains_correct_username(self):
        token = generate_token("alice", "viewer")
        payload = verify_token(token)
        assert payload["sub"] == "alice"

    def test_token_contains_correct_role(self):
        token = generate_token("bob", "admin")
        payload = verify_token(token)
        assert payload["role"] == "admin"

    def test_token_has_expiry(self):
        token = generate_token("user", "viewer")
        payload = verify_token(token)
        assert "exp" in payload
        assert "iat" in payload

    def test_different_users_get_different_tokens(self):
        t1 = generate_token("alice", "admin")
        t2 = generate_token("bob",   "viewer")
        assert t1 != t2


# ── Token verification tests ──────────────────────────────────────────────────

class TestTokenVerification:
    def test_valid_token_verifies(self):
        token   = generate_token("alice", "admin")
        payload = verify_token(token)
        assert payload["sub"] == "alice"

    def test_tampered_token_raises(self):
        token       = generate_token("alice", "admin")
        bad_token   = token[:-5] + "XXXXX"
        with pytest.raises(jwt.PyJWTError):
            verify_token(bad_token)

    def test_token_signed_with_wrong_key_raises(self):
        # sign with different key
        payload = {"sub": "eve", "role": "admin"}
        bad_token = jwt.encode(payload, "wrong-key", algorithm="HS256")
        with pytest.raises(jwt.PyJWTError):
            verify_token(bad_token)

    def test_expired_token_raises(self):
        from datetime import datetime, timedelta, timezone
        payload = {
            "sub":  "alice",
            "role": "admin",
            "iat":  datetime.now(timezone.utc) - timedelta(hours=2),
            "exp":  datetime.now(timezone.utc) - timedelta(hours=1),   # already expired
        }
        expired = jwt.encode(payload, "test-secret-key-for-pytest", algorithm="HS256")
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_token(expired)


# ── /login endpoint tests ─────────────────────────────────────────────────────

class TestLoginEndpoint:
    def test_valid_login_returns_200(self, client):
        resp = client.post("/login", json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200

    def test_valid_login_returns_token(self, client):
        resp = client.post("/login", json={"username": "admin", "password": "admin123"})
        data = resp.get_json()
        assert data["success"] is True
        assert "token" in data
        assert data["token_type"] == "Bearer"

    def test_wrong_password_returns_401(self, client):
        resp = client.post("/login", json={"username": "admin", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_unknown_user_returns_401(self, client):
        resp = client.post("/login", json={"username": "ghost", "password": "abc"})
        assert resp.status_code == 401

    def test_missing_fields_returns_400(self, client):
        resp = client.post("/login", json={"username": "admin"})
        assert resp.status_code == 400

    def test_empty_body_returns_400(self, client):
        resp = client.post("/login", json={})
        assert resp.status_code == 400
