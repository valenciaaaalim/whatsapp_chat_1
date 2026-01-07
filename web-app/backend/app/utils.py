"""
Utility functions for the web app.
"""
from datetime import datetime
import pytz


def get_singapore_time():
    """Get current time in Singapore timezone."""
    sgt = pytz.timezone('Asia/Singapore')
    return datetime.now(sgt)


def ensure_singapore_tz(value: datetime | None) -> datetime | None:
    """Ensure datetime is Asia/Singapore aware; localize if naive."""
    if value is None:
        return None
    sgt = pytz.timezone('Asia/Singapore')
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return sgt.localize(value)
    return value.astimezone(sgt)
