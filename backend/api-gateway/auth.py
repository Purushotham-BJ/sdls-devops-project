"""
backend/api-gateway/auth.py
JWT Authentication layer for the API Gateway.

Responsibilities:
  - POST /login  → issue a signed JWT token
  - jwt_required → Flask decorator that validates Bearer tokens on protected routes
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Blueprint, request, jsonify

# ── Config (from environment) ────────────────────────────────────────────────
SECRET_KEY  = os.getenv("JWT_SECRET_KEY",  "CHANGE_ME_IN_PRODUCTION")
ALGORITHM   = os.getenv("JWT_ALGORITHM",   "HS256")
EXPIRE_MINS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

logger = logging.getLogger("api-gateway.auth")

auth_bp = Blueprint("auth", __name__)

# ---------------------------------------------------------------------------
# Demo user store — replace with a real DB query in production.
# Passwords are stored as plain text here ONLY for demo clarity.
# Production must hash with bcrypt / argon2.
# ---------------------------------------------------------------------------
DEMO_USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user":  {"password": "user123",  "role": "viewer"},
}


# ── Token generation ─────────────────────────────────────────────────────────

def generate_token(username: str, role: str) -> str:
    """Create a signed JWT with expiry."""
    now     = datetime.now(timezone.utc)
    payload = {
        "sub":  username,
        "role": role,
        "iat":  now,
        "exp":  now + timedelta(minutes=EXPIRE_MINS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── Token verification ────────────────────────────────────────────────────────

def verify_token(token: str) -> dict:
    """
    Decode and validate a JWT.
    Returns the decoded payload dict, or raises jwt.PyJWTError on failure.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ── Decorator ────────────────────────────────────────────────────────────────

def jwt_required(f):
    """
    Flask route decorator — validates the Authorization: Bearer <token> header.
    Aborts with 401 if token is missing, malformed, or expired.
    Injects `current_user` (dict with sub/role) into the wrapped function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            logger.warning("Missing or malformed Authorization header")
            return jsonify({
                "success": False,
                "message": "Authorization header missing. Use: Authorization: Bearer <token>"
            }), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = verify_token(token)
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token")
            return jsonify({"success": False, "message": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token: %s", e)
            return jsonify({"success": False, "message": "Invalid token."}), 401

        # Make user info available to the route function via Flask's g
        from flask import g
        g.current_user = payload
        return f(*args, **kwargs)

    return decorated


# ── /login endpoint ───────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /login
    Body: {"username": "admin", "password": "admin123"}
    Returns: {"success": true, "token": "<jwt>", "expires_in": 3600}
    """
    body     = request.get_json(silent=True) or {}
    username = body.get("username", "").strip()
    password = body.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "username and password are required"}), 400

    user = DEMO_USERS.get(username)
    if not user or user["password"] != password:
        logger.warning("Failed login attempt for user: %s", username)
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    token = generate_token(username, user["role"])
    logger.info("Successful login for user: %s (role=%s)", username, user["role"])

    return jsonify({
        "success":    True,
        "message":    "Login successful",
        "token":      token,
        "token_type": "Bearer",
        "expires_in": EXPIRE_MINS * 60,
        "user":       {"username": username, "role": user["role"]},
    }), 200
