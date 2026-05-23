"""
Central Logging Service Routes
Provides endpoints for: ingesting logs, querying, analytics, alerts.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from flask import Blueprint, request, jsonify
from mongo_handler import insert_log, get_logs, get_logs_by_trace
from analytics   import get_overview, get_service_breakdown, get_timeline, get_trace_summary
from alert_engine import get_active_alerts
from flask import current_app

log_bp = Blueprint("logs", __name__)


# ── Ingest ───────────────────────────────────────────────────────────────────

@log_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "logging-service", "status": "healthy"}), 200


@log_bp.route("/api/logs", methods=["POST"])
def ingest_log():
    """Receive a single log entry from any service."""
    doc = request.get_json(silent=True)
    if not doc:
        return jsonify({"success": False, "message": "Empty body"}), 400
    try:
        insert_log(doc)
        current_app.socketio.emit("new_log", doc)
        return jsonify({"success": True, "message": "Log stored"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ── Query ────────────────────────────────────────────────────────────────────

@log_bp.route("/api/logs", methods=["GET"])
def query_logs():
    """
    Query logs with optional filters.
    ?service=payment-service&status=ERROR&trace_id=ABC&limit=50
    """
    service  = request.args.get("service")
    status   = request.args.get("status")
    trace_id = request.args.get("trace_id")
    limit    = int(request.args.get("limit", 100))

    logs = get_logs(limit=limit, service=service, status=status, trace_id=trace_id)
    return jsonify({"success": True, "count": len(logs), "logs": logs}), 200


@log_bp.route("/api/logs/trace/<trace_id>", methods=["GET"])
def trace_detail(trace_id):
    """Get full event flow for a specific trace ID."""
    summary = get_trace_summary(trace_id)
    return jsonify({"success": True, "data": summary}), 200


# ── Analytics ────────────────────────────────────────────────────────────────

@log_bp.route("/api/analytics/overview", methods=["GET"])
def overview():
    try:
        data = get_overview()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "data": {
            "total_requests": 0, "total_errors": 0, "success_count": 0,
            "error_rate": 0, "active_services": 0
        }}), 200


@log_bp.route("/api/analytics/services", methods=["GET"])
def services():
    try:
        data = get_service_breakdown()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "data": []}), 200


@log_bp.route("/api/analytics/timeline", methods=["GET"])
def timeline():
    hours = int(request.args.get("hours", 24))
    try:
        data = get_timeline(hours)
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "data": []}), 200


# ── Alerts ───────────────────────────────────────────────────────────────────

@log_bp.route("/api/alerts", methods=["GET"])
def alerts():
    try:
        data = get_active_alerts()
        return jsonify({"success": True, "count": len(data), "alerts": data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "alerts": []}), 200
