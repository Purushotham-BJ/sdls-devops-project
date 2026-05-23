"""
frontend/dashboard/app.py
Dashboard — Flask backend.

Key design:
  - On login: authenticates the user AND fetches a JWT from the API Gateway,
    storing it in the server-side session.
  - Every /proxy/* route adds the JWT automatically — the browser never sees
    or needs to manage a token at all.
  - Tokens are refreshed transparently when they expire.
"""
import os
import logging
import requests
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, Response)
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
API_GATEWAY_URL  = os.getenv("API_GATEWAY_URL",  "http://localhost:5000")
LOGGING_URL      = os.getenv("LOGGING_SERVICE_URL", "http://localhost:5005")
APP_PORT   = int(os.getenv("SDLS_DASHBOARD_PORT", 5006))

# Dashboard login credentials (separate from JWT — these guard the UI)
DASH_USER = os.getenv("DASHBOARD_USERNAME", "admin")
DASH_PASS = os.getenv("DASHBOARD_PASSWORD", "admin123")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("dashboard")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "dashboard-secret-change-me")
CORS(app)


# ── Auth helpers ──────────────────────────────────────────────────────────────

def is_logged_in():
    return session.get("logged_in", False)


def get_jwt_token():
    """Return the stored JWT, refreshing it if missing or expired."""
    token = session.get("jwt_token")
    if not token:
        token = _fetch_jwt()
    return token


def _fetch_jwt():
    """
    Call POST /login on the API Gateway using the dashboard credentials,
    store the returned JWT in the session, and return it.
    Returns None if the gateway is unreachable.
    """
    username = session.get("username", DASH_USER)
    password = session.get("password", DASH_PASS)
    try:
        resp = requests.post(
            f"{API_GATEWAY_URL}/login",
            json={"username": username, "password": password},
            timeout=5,
        )
        if resp.status_code == 200:
            token = resp.json().get("token")
            session["jwt_token"] = token
            logger.info("JWT token fetched for user=%s", username)
            return token
        logger.warning("Gateway login failed: %s", resp.text)
    except Exception as e:
        logger.error("Could not reach API Gateway for JWT: %s", e)
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def _auth_headers():
    """Build headers with the JWT Bearer token — used by all proxy calls."""
    token = get_jwt_token()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# ── Login / Logout ────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == DASH_USER and password == DASH_PASS:
            session["logged_in"] = True
            session["username"]  = username
            session["password"]  = password   # stored so _fetch_jwt can use it

            # Pre-fetch JWT immediately so first page load is instant
            token = _fetch_jwt()
            if not token:
                # Gateway down — still allow dashboard access (read-only degraded mode)
                logger.warning("API Gateway unreachable during login — degraded mode")

            return redirect(url_for("index"))
        error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Pages ─────────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/dashboard")
@login_required
def index():
    return render_template("index.html")

@app.route("/logs")
@login_required
def logs():
    return render_template("logs.html")

@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")

@app.route("/errors")
@login_required
def errors():
    return render_template("errors.html")


# ── Proxy routes — JWT is added SERVER-SIDE, browser never handles tokens ─────

@app.route("/proxy/order", methods=["POST"])
@login_required
def proxy_order():
    """Place an order — JWT is attached automatically."""
    try:
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/order",
            json=request.get_json(silent=True) or {},
            headers=_auth_headers(),
            timeout=40,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "API Gateway unreachable"}), 503
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/proxy/simulate", methods=["POST"])
@login_required
def proxy_simulate():
    """Bulk simulate — JWT attached automatically."""
    try:
        resp = requests.post(
            f"{API_GATEWAY_URL}/api/simulate/bulk",
            json=request.get_json(silent=True) or {},
            headers=_auth_headers(),
            timeout=60,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "API Gateway unreachable"}), 503
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/proxy/inventory", methods=["GET"])
@login_required
def proxy_inventory():
    """Inventory query — JWT attached automatically."""
    try:
        resp = requests.get(
            f"{API_GATEWAY_URL}/api/inventory",
            headers=_auth_headers(),
            timeout=10,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/proxy/logs", methods=["GET"])
@login_required
def proxy_logs():
    """Forward log queries to logging service (no JWT needed for internal service)."""
    try:
        params = request.args.to_dict()
        resp   = requests.get(f"{LOGGING_URL}/api/logs", params=params, timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "logs": [], "message": str(e)}), 500


@app.route("/proxy/analytics/<path:subpath>", methods=["GET"])
@login_required
def proxy_analytics(subpath):
    """Forward analytics queries."""
    try:
        params = request.args.to_dict()
        resp   = requests.get(f"{LOGGING_URL}/api/analytics/{subpath}",
                              params=params, timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "data": None, "message": str(e)}), 500


@app.route("/proxy/alerts", methods=["GET"])
@login_required
def proxy_alerts():
    try:
        resp = requests.get(f"{LOGGING_URL}/api/alerts", timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "alerts": [], "message": str(e)}), 500


@app.route("/proxy/health", methods=["GET"])
@login_required
def proxy_health_all():
    """Check health of all services and return a combined status."""
    services = {
        "api-gateway":          f"{API_GATEWAY_URL}/health",
        "logging-service":      f"{LOGGING_URL}/health",
        "order-service":        f"{os.getenv('ORDER_SERVICE_URL','http://localhost:5001')}/health",
        "payment-service":      f"{os.getenv('PAYMENT_SERVICE_URL','http://localhost:5002')}/health",
        "inventory-service":    f"{os.getenv('INVENTORY_SERVICE_URL','http://localhost:5003')}/health",
        "notification-service": f"{os.getenv('NOTIFICATION_SERVICE_URL','http://localhost:5004')}/health",
    }
    results = {}
    for name, url in services.items():
        try:
            r = requests.get(url, timeout=3)
            results[name] = "healthy" if r.status_code == 200 else "unhealthy"
        except Exception:
            results[name] = "unreachable"
    return jsonify({"services": results}), 200


@app.route("/health")
def health():
    return jsonify({"service": "dashboard", "status": "healthy"}), 200


@app.route("/favicon.ico")
def favicon():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#2c3e50"/><polygon points="50,20 70,80 30,80" fill="#3498db"/></svg>'
    return Response(svg, mimetype="image/svg+xml")


if __name__ == "__main__":
    logger.info("Dashboard starting on port %d", APP_PORT)
    app.run(host="0.0.0.0", port=APP_PORT,
            debug=os.getenv("FLASK_DEBUG", "0") == "1",
            threaded=True, use_reloader=False)
