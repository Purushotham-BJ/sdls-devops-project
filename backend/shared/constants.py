"""
shared/constants.py
Centralised config — values are read from environment variables (set via .env)
so that nothing is hardcoded and each deployment can override freely.
"""
import os

# ── Service ports ────────────────────────────────────────────────────────────
PORTS = {
    "api-gateway":          int(os.getenv("SDLS_API_GATEWAY_PORT",          5000)),
    "order-service":        int(os.getenv("SDLS_ORDER_SERVICE_PORT",        5001)),
    "payment-service":      int(os.getenv("SDLS_PAYMENT_SERVICE_PORT",      5002)),
    "inventory-service":    int(os.getenv("SDLS_INVENTORY_SERVICE_PORT",    5003)),
    "notification-service": int(os.getenv("SDLS_NOTIFICATION_SERVICE_PORT", 5004)),
    "logging-service":      int(os.getenv("SDLS_LOGGING_SERVICE_PORT",      5005)),
    "dashboard":            int(os.getenv("SDLS_DASHBOARD_PORT",            5006)),
}

# ── Internal service URLs (override with env vars for Docker/K8s) ────────────
SERVICE_URLS = {
    "api-gateway":          os.getenv("API_GATEWAY_URL",          "http://localhost:5000"),
    "order-service":        os.getenv("ORDER_SERVICE_URL",        "http://localhost:5001"),
    "payment-service":      os.getenv("PAYMENT_SERVICE_URL",      "http://localhost:5002"),
    "inventory-service":    os.getenv("INVENTORY_SERVICE_URL",    "http://localhost:5003"),
    "notification-service": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:5004"),
    "logging-service":      os.getenv("LOGGING_SERVICE_URL",      "http://localhost:5005"),
    "dashboard":            os.getenv("DASHBOARD_URL",            "http://localhost:5006"),
}

LOGGING_SERVICE_URL = SERVICE_URLS["logging-service"]

# ── Log status tokens ─────────────────────────────────────────────────────────
STATUS_SUCCESS = "SUCCESS"
STATUS_ERROR   = "ERROR"
STATUS_WARNING = "WARNING"
STATUS_INFO    = "INFO"

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGO_URI       = os.getenv("MONGO_URI",  "mongodb://localhost:27017")
MONGO_DB        = os.getenv("MONGO_DB",   "distributed_logging")
LOGS_COLLECTION = "logs"

# ── JWT ───────────────────────────────────────────────────────────────────────
JWT_SECRET_KEY                 = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
JWT_ALGORITHM                  = os.getenv("JWT_ALGORITHM",  "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60))
