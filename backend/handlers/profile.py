"""GET/PUT /me - read or create the signed-in user's FoodLoop profile."""
import os

from common import db, domain, util
from common.domain import choice, phone, text
from common.http import api
from common.util import Conflict


@api
def handler(req):
    uid = req.require_user()
    if req.method == "GET":
        return {"profile": db.get_profile(uid), "isAdmin": req.is_admin, "email": req.email}
    return save_profile(req, uid)


def save_profile(req, uid):
    body = req.json()
    role = choice(body, "role", domain.ROLES)
    is_org = role != "CUSTOMER"
    item = {
        "userId": uid,
        "email": req.email or "",
        "role": role,
        "displayName": text(body, "displayName", min_len=2, max_len=60),
        "phone": phone(body.get("phone"), required=is_org),
        "district": choice(body, "district", domain.DISTRICTS),
    }
    if is_org:
        item["orgName"] = text(body, "orgName", min_len=2, max_len=80)
        item["address"] = text(body, "address", min_len=5, max_len=150)
        item["registrationNo"] = text(body, "registrationNo", max_len=40, required=False)
        if role == "BUSINESS":
            item["businessType"] = choice(body, "businessType", domain.BUSINESS_TYPES)

    existing = db.get_profile(uid)
    now = util.now_iso()
    if existing and existing["role"] != role and existing["role"] != "CUSTOMER" and existing.get("status") == "APPROVED":
        raise Conflict("Approved organisations cannot change account type", "role_locked")

    if existing and existing["role"] == role:
        status = existing["status"]  # editing details never changes verification status
    elif not is_org:
        status = "ACTIVE"
    else:
        status = "APPROVED" if os.environ.get("AUTO_APPROVE_ORGS", "false") == "true" else "PENDING"

    item["status"] = status
    item["createdAt"] = existing["createdAt"] if existing else now
    item["updatedAt"] = now
    db.table(db.PROFILES).put_item(Item=item)
    return {"profile": item}
