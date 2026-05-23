"""Logger for the logging service itself."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
from utils import send_log  # noqa: F401
