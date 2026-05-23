"""
Order service business logic helpers.
The main pipeline lives in order_routes.py.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from trace_generator import generate_trace_id  # noqa: F401
