"""
Order Service Routes
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

import time, requests
from flask import Blueprint, request, jsonify
from utils import send_log
from constants import SERVICE_URLS, STATUS_SUCCESS, STATUS_ERROR, STATUS_INFO, STATUS_WARNING

order_bp = Blueprint("order", __name__)

PAYMENT_URL      = SERVICE_URLS["payment-service"]
INVENTORY_URL    = SERVICE_URLS["inventory-service"]
NOTIFICATION_URL = SERVICE_URLS["notification-service"]


@order_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "order-service", "status": "healthy"}), 200


@order_bp.route("/api/order/create", methods=["POST"])
def create_order():
    data       = request.get_json(silent=True) or {}
    trace_id   = data.get("trace_id", "UNKNOWN")
    product_id = data.get("product_id", "PROD-001")
    quantity   = data.get("quantity", 1)
    customer_id = data.get("customer_id", "CUST-0001")
    start      = time.time()

    send_log(trace_id, "order-service", STATUS_INFO,
             f"Order received for product {product_id}, qty={quantity}",
             0, {"product_id": product_id, "quantity": quantity, "customer_id": customer_id})

    # ── Step 1: Check inventory ──────────────────────────────────────────────
    try:
        inv_resp = requests.post(
            f"{INVENTORY_URL}/api/inventory/check",
            json={"trace_id": trace_id, "product_id": product_id, "quantity": quantity},
            timeout=10
        )
        inv_data = inv_resp.json()
        if not inv_data.get("success"):
            elapsed = int((time.time() - start) * 1000)
            send_log(trace_id, "order-service", STATUS_ERROR,
                     f"Inventory check failed: {inv_data.get('message')}", elapsed)
            return jsonify({"success": False, "trace_id": trace_id,
                            "message": inv_data.get("message", "Inventory check failed")}), 400
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        send_log(trace_id, "order-service", STATUS_ERROR,
                 f"Inventory service unreachable: {e}", elapsed)
        return jsonify({"success": False, "trace_id": trace_id,
                        "message": "Inventory service unavailable"}), 503

    send_log(trace_id, "order-service", STATUS_SUCCESS,
             "Inventory verified successfully", int((time.time() - start) * 1000))

    # ── Step 2: Process payment ──────────────────────────────────────────────
    try:
        pay_resp = requests.post(
            f"{PAYMENT_URL}/api/payment/process",
            json={"trace_id": trace_id, "product_id": product_id,
                  "quantity": quantity, "customer_id": customer_id},
            timeout=10
        )
        pay_data = pay_resp.json()
        if not pay_data.get("success"):
            elapsed = int((time.time() - start) * 1000)
            send_log(trace_id, "order-service", STATUS_ERROR,
                     f"Payment failed: {pay_data.get('message')}", elapsed)
            # Notify about failure
            _notify(trace_id, customer_id, product_id, success=False,
                    reason=pay_data.get("message", "Payment declined"))
            return jsonify({"success": False, "trace_id": trace_id,
                            "message": pay_data.get("message", "Payment failed")}), 402
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        send_log(trace_id, "order-service", STATUS_ERROR,
                 f"Payment service unreachable: {e}", elapsed)
        return jsonify({"success": False, "trace_id": trace_id,
                        "message": "Payment service unavailable"}), 503

    send_log(trace_id, "order-service", STATUS_SUCCESS,
             "Payment processed successfully", int((time.time() - start) * 1000))

    # ── Step 3: Deduct inventory ─────────────────────────────────────────────
    try:
        requests.post(
            f"{INVENTORY_URL}/api/inventory/deduct",
            json={"trace_id": trace_id, "product_id": product_id, "quantity": quantity},
            timeout=10
        )
    except Exception as e:
        send_log(trace_id, "order-service", STATUS_WARNING,
                 f"Inventory deduction failed (non-critical): {e}", 0)

    # ── Step 4: Notify customer ──────────────────────────────────────────────
    _notify(trace_id, customer_id, product_id, success=True)

    elapsed = int((time.time() - start) * 1000)
    send_log(trace_id, "order-service", STATUS_SUCCESS,
             "Order completed successfully", elapsed,
             {"product_id": product_id, "customer_id": customer_id})

    return jsonify({
        "success": True,
        "trace_id": trace_id,
        "message": "Order placed successfully",
        "order_id": f"ORD-{trace_id[:8]}"
    }), 200


def _notify(trace_id, customer_id, product_id, success, reason=""):
    try:
        requests.post(
            f"{NOTIFICATION_URL}/api/notification/send",
            json={"trace_id": trace_id, "customer_id": customer_id,
                  "product_id": product_id, "success": success, "reason": reason},
            timeout=5
        )
    except Exception:
        pass  # Notification is non-critical
