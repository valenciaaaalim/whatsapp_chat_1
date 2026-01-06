"""
Utility functions for the web app.
"""
from datetime import datetime
import pytz


def get_singapore_time():
    """Get current time in Singapore timezone."""
    sgt = pytz.timezone('Asia/Singapore')
    return datetime.now(sgt)

