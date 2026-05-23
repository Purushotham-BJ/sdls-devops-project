"""
backend/api-gateway/app.py
API Gateway — entry point.
Registers auth blueprint (public) and gateway blueprint (JWT-protected).
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env from project root (two dirs up from this file)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from auth   import auth_bp
from routes import gateway_bp

# ── Logging configuration ─────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("api-gateway")

# ── App factory ───────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(auth_bp)    # /login  — public
app.register_blueprint(gateway_bp) # /api/*  — JWT-protected

logger.info("API Gateway initialised (JWT auth enabled)")

if __name__ == "__main__":
    port = int(os.getenv("SDLS_API_GATEWAY_PORT", 5000))
    logger.info("API Gateway starting on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1",
            threaded=True, use_reloader=False)
