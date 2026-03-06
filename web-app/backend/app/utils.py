"""
Utility functions for the web app.
"""
from datetime import datetime
import re
import pytz
from fastapi import HTTPException, Request

from app.config import settings

_MOBILE_UA_RE = re.compile(
    r"Android|iPhone|iPod|iPad|BlackBerry|IEMobile|Opera Mini",
    re.IGNORECASE,
)


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


def require_mobile_request(request: Request) -> None:
    """Reject non-mobile requests when REQUIRE_MOBILE is enabled."""
    if not settings.REQUIRE_MOBILE:
        return
    user_agent = request.headers.get("user-agent", "")
    if _MOBILE_UA_RE.search(user_agent):
        return
    raise HTTPException(
        status_code=403,
        detail="This study requires a mobile device.",
    )
