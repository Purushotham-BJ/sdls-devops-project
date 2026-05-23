"""
tests/test_health_checks.py
Integration-style health check tests (run against live containers).
Also includes unit tests for route structure.
"""
import sys, os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "api-gateway"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "shared"))

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("ORDER_SERVICE_URL",        "http://localhost:5001")
os.environ.setdefault("PAYMENT_SERVICE_URL",      "http://localhost:5002")
os.environ.setdefault("INVENTORY_SERVICE_URL",    "http://localhost:5003")
os.environ.setdefault("NOTIFICATION_SERVICE_URL", "http://localhost:5004")
os.environ.setdefault("LOGGING_SERVICE_URL",      "http://localhost:5005")

from auth   import auth_bp
from routes import gateway_bp
from flask  import Flask


@pytest.fixture
def app():
    application = Flask(__name__)
    application.register_blueprint(auth_bp)
    application.register_blueprint(gateway_bp)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


class TestGatewayHealth:
    def test_health_endpoint_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_structure(self, client):
        data = client.get("/health").get_json()
        assert data["service"] == "api-gateway"
        assert data["status"]  == "healthy"


class TestProtectedRoutes:
    """Ensure that protected routes reject requests without a valid JWT."""

    def test_order_without_token_returns_401(self, client):
        resp = client.post("/api/order", json={"product_id": "PROD-001", "quantity": 1})
        assert resp.status_code == 401

    def test_payment_without_token_returns_401(self, client):
        resp = client.post("/api/payment", json={})
        assert resp.status_code == 401

    def test_inventory_without_token_returns_401(self, client):
        resp = client.get("/api/inventory")
        assert resp.status_code == 401

    def test_simulate_without_token_returns_401(self, client):
        resp = client.post("/api/simulate/bulk", json={"count": 1})
        assert resp.status_code == 401

    def test_malformed_auth_header_returns_401(self, client):
        resp = client.post("/api/order",
                           headers={"Authorization": "NotBearer abc123"},
                           json={})
        assert resp.status_code == 401


class TestAuthThenRoute:
    """Login → use token → hit protected route."""

    def test_login_then_access_protected_route(self, client):
        # Login
        login_resp = client.post("/login",
                                 json={"username": "admin", "password": "admin123"})
        assert login_resp.status_code == 200
        token = login_resp.get_json()["token"]

        # Use token — route will fail (downstream service not running) but must NOT be 401
        resp = client.post("/api/order",
                           headers={"Authorization": f"Bearer {token}"},
                           json={"product_id": "PROD-001", "quantity": 1})
        # 503 (service unreachable) is acceptable; 401 is not
        assert resp.status_code != 401, "Valid token should not get 401"
