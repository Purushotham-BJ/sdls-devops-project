"""
Service-level logger helper.
Delegates to shared/utils.py send_log().
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from utils import send_log  # noqa: F401 — re-exported for use within this service
