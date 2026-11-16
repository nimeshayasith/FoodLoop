"""Shared helpers: time, errors and JSON encoding."""
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"  # the only timestamp format we store (Step Functions Wait needs it)

logger = logging.getLogger("foodloop")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------- errors
class ApiError(Exception):
    status = 400
    code = "bad_request"

    def __init__(self, message, code=None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class ValidationError(ApiError):
    status = 400
    code = "validation_error"


class Unauthorized(ApiError):
    status = 401
    code = "unauthorized"


class Forbidden(ApiError):
    status = 403
    code = "forbidden"


class NotFound(ApiError):
    status = 404
    code = "not_found"


class Conflict(ApiError):
    status = 409
    code = "conflict"


# ------------------------------------------------------------------ time
def now_utc():
    # Always call through the module (util.now_utc()) so tests can freeze time.
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt):
    return dt.astimezone(timezone.utc).strftime(ISO_FMT)


def now_iso():
    return iso(now_utc())


def parse_iso(value, field="timestamp"):
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{field} must be an ISO-8601 timestamp", "invalid_timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError(f"{field} must be an ISO-8601 timestamp", "invalid_timestamp")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0)


# ------------------------------------------------------------------ json
def _default(o):
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    raise TypeError(f"Cannot serialise {type(o)}")


def dumps(obj):
    return json.dumps(obj, default=_default, separators=(",", ":"))
