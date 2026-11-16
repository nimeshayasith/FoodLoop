"""Admin console API (Cognito group `admin`): list pending organisations and approve/reject them."""
from boto3.dynamodb.conditions import Attr

from common import db, util
from common.http import api
from common.util import Forbidden, NotFound, ValidationError


@api
def handler(req):
    req.require_user()
    if not req.is_admin:
        raise Forbidden("Admins only", "admin_only")
    if req.method == "GET":
        status = (req.query.get("status") or "PENDING").upper()
        resp = db.table(db.PROFILES).scan(FilterExpression=Attr("status").eq(status))  # tiny table: scan is fine
        return {"profiles": sorted(resp["Items"], key=lambda p: p["createdAt"])}

    target = req.param("userId")
    decision = str(req.json().get("decision", "")).upper()
    if decision not in ("APPROVE", "REJECT"):
        raise ValidationError("decision must be APPROVE or REJECT", "decision_invalid")
    status = "APPROVED" if decision == "APPROVE" else "REJECTED"
    profile = db.get_profile(target)
    if not profile or profile["role"] == "CUSTOMER":
        raise NotFound("Organisation profile not found")
    db.table(db.PROFILES).update_item(
        Key={"userId": target},
        UpdateExpression="SET #s = :s, reviewedBy = :a, reviewedAt = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": status, ":a": req.user_id, ":t": util.now_iso()},
    )
    return {"userId": target, "status": status}
