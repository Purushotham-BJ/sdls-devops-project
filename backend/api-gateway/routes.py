"""
backend/api-gateway/routes.py
All API routes — every route here is JWT-protected via @jwt_required.
The gateway:
  1. Validates the JWT
  2. Generates/forwards trace IDs
  3. Logs request/response at both ends
  4. Forwards to the correct downstream service
"""
import sys
import os
import time
import logging
import requests
from flask import Blueprint, request, jsonify, g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
from trace_generator import generate_trace_id
from utils           import send_log
from constants       import SERVICE_URLS, STATUS_SUCCESS, STATUS_ERROR, STATUS_INFO
from auth            import jwt_required

gateway_bp = Blueprint("gateway", __name__)
logger     = logging.getLogger("api-gateway.routes")

ORDER_SERVICE_URL   = SERVICE_URLS["order-service"]
LOGGING_SERVICE_URL = SERVICE_URLS["logging-service"]


# ── Health (public — no JWT needed) ──────────────────────────────────────────
@gateway_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "api-gateway", "status": "healthy"}), 200


# ── POST /api/order ───────────────────────────────────────────────────────────
@gateway_bp.route("/api/order", methods=["POST"])
@jwt_required
def place_order():
    """
    Protected: place an order.
    Requires: Authorization: Bearer <token>
    """
    trace_id = generate_trace_id()
    start    = time.time()
    user     = g.current_user  # injected by @jwt_required

    logger.info("[%s] Incoming /api/order from user=%s", trace_id, user.get("sub"))
    send_log(trace_id, "api-gateway", STATUS_INFO,
             f"Incoming order request from user={user.get('sub')}",
             0, {"endpoint": "/api/order", "method": "POST"})

    payload              = request.get_json(silent=True) or {}
    payload["trace_id"]  = trace_id
    payload["requested_by"] = user.get("sub")

    try:
        resp    = requests.post(f"{ORDER_SERVICE_URL}/api/order/create",
                                json=payload, timeout=40)
        elapsed = int((time.time() - start) * 1000)
        result  = resp.json()

        if resp.status_code == 200:
            send_log(trace_id, "api-gateway", STATUS_SUCCESS,
                     "Order pipeline completed", elapsed)
        else:
            send_log(trace_id, "api-gateway", STATUS_ERROR,
                     f"Order pipeline failed: {result.get('message', 'unknown')}", elapsed)

        return jsonify({**result, "trace_id": trace_id}), resp.status_code

    except requests.exceptions.ConnectionError:
        elapsed = int((time.time() - start) * 1000)
        send_log(trace_id, "api-gateway", STATUS_ERROR, "Order service unreachable", elapsed)
        return jsonify({"success": False, "trace_id": trace_id,
                        "message": "Order service is unreachable"}), 503
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        send_log(trace_id, "api-gateway", STATUS_ERROR, f"Unexpected error: {e}", elapsed)
        return jsonify({"success": False, "trace_id": trace_id, "message": str(e)}), 500


# ── POST /api/payment ─────────────────────────────────────────────────────────
@gateway_bp.route("/api/payment", methods=["POST"])
@jwt_required
def process_payment():
    """Protected: direct payment endpoint (bypass order service)."""
    trace_id = generate_trace_id()
    start    = time.time()
    payload  = request.get_json(silent=True) or {}
    payload["trace_id"] = trace_id

    PAYMENT_URL = SERVICE_URLS["payment-service"]
    try:
        resp    = requests.post(f"{PAYMENT_URL}/api/payment/process",
                                json=payload, timeout=20)
        elapsed = int((time.time() - start) * 1000)
        send_log(trace_id, "api-gateway", STATUS_SUCCESS if resp.ok else STATUS_ERROR,
                 "Payment forwarded", elapsed)
        return jsonify({**resp.json(), "trace_id": trace_id}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "trace_id": trace_id, "message": str(e)}), 500


# ── GET /api/inventory ────────────────────────────────────────────────────────
@gateway_bp.route("/api/inventory", methods=["GET"])
@jwt_required
def get_inventory():
    """Protected: query current inventory levels."""
    trace_id     = generate_trace_id()
    INVENTORY_URL = SERVICE_URLS["inventory-service"]
    try:
        resp = requests.get(f"{INVENTORY_URL}/api/inventory/list", timeout=10)
        return jsonify({**resp.json(), "trace_id": trace_id}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "trace_id": trace_id, "message": str(e)}), 500


# ── POST /api/simulate/bulk ───────────────────────────────────────────────────
@gateway_bp.route("/api/simulate/bulk", methods=["POST"])
@jwt_required
def bulk_simulate():
    """Protected: trigger N random orders for demo / load testing."""
    data    = request.get_json(silent=True) or {}
    count   = min(int(data.get("count", 5)), 50)  # cap at 50 to prevent abuse
    results = []

    for i in range(count):
        trace_id = generate_trace_id()
        payload  = {
            "trace_id":    trace_id,
            "product_id":  f"PROD-{(i % 5) + 1:03d}",
            "quantity":    (i % 3) + 1,
            "customer_id": f"CUST-{(i % 10) + 1:04d}",
        }
        try:
            resp = requests.post(f"{ORDER_SERVICE_URL}/api/order/create",
                                 json=payload, timeout=40)
            results.append({"trace_id": trace_id, "status": resp.status_code})
        except Exception as e:
            results.append({"trace_id": trace_id, "status": "error", "detail": str(e)})

    logger.info("Bulk simulation completed: %d orders", count)
    return jsonify({"simulated": count, "results": results}), 200
