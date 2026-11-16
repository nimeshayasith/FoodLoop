"""HTTP API (payload v2) request/response helpers shared by all API Lambdas."""
import base64
import functools
import json

from common import util
from common.util import ApiError, Unauthorized, ValidationError

MAX_BODY_BYTES = 20_000


class Request:
    def __init__(self, event):
        self.event = event
        ctx = event.get("requestContext") or {}
        self.method = (ctx.get("http") or {}).get("method", "")
        self.route = event.get("routeKey", "")
        self.params = event.get("pathParameters") or {}
        self.query = event.get("queryStringParameters") or {}
        jwt = (ctx.get("authorizer") or {}).get("jwt") or {}
        self.claims = jwt.get("claims") or {}

    # ----- identity (comes from the verified Cognito JWT, never from the body)
    @property
    def user_id(self):
        return self.claims.get("sub")

    @property
    def email(self):
        return self.claims.get("email")

    @property
    def groups(self):
        raw = self.claims.get("cognito:groups") or []
        if isinstance(raw, str):
            raw = raw.strip("[]").replace(",", " ").split()
        return list(raw)

    @property
    def is_admin(self):
        return "admin" in self.groups

    def require_user(self):
        if not self.user_id:
            raise Unauthorized("Sign in required")
        return self.user_id

    # ----- body
    def json(self):
        body = self.event.get("body")
        if not body:
            return {}
        if self.event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8", "replace")
        if len(body) > MAX_BODY_BYTES:
            raise ValidationError("Request body too large", "body_too_large")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise ValidationError("Body must be valid JSON", "invalid_json")
        if not isinstance(data, dict):
            raise ValidationError("Body must be a JSON object", "invalid_json")
        return data

    def param(self, name):
        value = self.params.get(name)
        if not value:
            raise ValidationError(f"Missing path parameter {name}")
        return value


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": util.dumps(body),
    }


def api(fn):
    """Wrap a handler(req) -> body | (status, body); map ApiError to JSON errors."""

    @functools.wraps(fn)
    def wrapper(event, context=None):
        try:
            result = fn(Request(event))
            status, body = result if isinstance(result, tuple) else (200, result)
            return response(status, body)
        except ApiError as e:
            return response(e.status, {"error": e.code, "message": e.message})
        except Exception:  # noqa: BLE001 - last-resort guard, details go to CloudWatch
            util.logger.exception("Unhandled error")
            return response(500, {"error": "server_error", "message": "Something went wrong"})

    return wrapper
