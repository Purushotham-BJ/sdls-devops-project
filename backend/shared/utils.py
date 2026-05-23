import time
import requests
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from constants import LOGGING_SERVICE_URL
from log_format import create_log


def send_log(trace_id, service_name, status, message, response_time=0, extra=None):
    """
    Send a structured log entry to the central logging service.
    Falls back to printing on failure so services remain functional.
    """
    log_entry = create_log(trace_id, service_name, status, message, response_time, extra)
    try:
        requests.post(
            f"{LOGGING_SERVICE_URL}/api/logs",
            json=log_entry,
            timeout=2
        )
    except Exception as e:
        print(f"[{service_name}] Could not send log to logging service: {e}")
        print(f"[LOG] {log_entry}")
    return log_entry


def measure_time(func, *args, **kwargs):
    """Measure execution time of a function in milliseconds."""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = int((time.time() - start) * 1000)
    return result, elapsed


def success_response(data, message="OK", status_code=200):
    """Standard success response format."""
    return {"success": True, "message": message, "data": data}, status_code


def error_response(message, status_code=500):
    """Standard error response format."""
    return {"success": False, "message": message, "data": None}, status_code
