"""POST /pickup/verify - store staff enter the customer's pickup code to hand over the food."""
import re
from decimal import Decimal

from botocore.exceptions import ClientError

from common import db, domain, util
from common.db import Key
from common.http import api
from common.util import Conflict, NotFound, ValidationError


@api
def handler(req):
    uid = req.require_user()
    domain.require_profile(uid, roles=["BUSINESS"])
    code = re.sub(r"[^A-Z0-9]", "", str(req.json().get("pickupCode", "")).upper())
    if len(code) < 6:
        raise ValidationError("Enter the pickup code, e.g. FL-K7M4Q", "pickupCode_invalid")

    found = db.table(db.RESERVATIONS).query(
        IndexName="ByPickupCode", KeyConditionExpression=Key("pickupCode").eq(code), Limit=1
    )["Items"]
    # Same message for "unknown" and "someone else's" so codes cannot be probed across stores.
    if not found or found[0]["ownerId"] != uid:
        raise NotFound("No reservation with that code at your store", "code_not_found")
    res = found[0]
    if res["reservationStatus"] == "COLLECTED":
        raise Conflict("Already collected", "already_collected")
    if res["reservationStatus"] != "RESERVED":
        raise Conflict(f"Reservation is {res['reservationStatus'].lower()}", "not_collectable")
    now = util.now_iso()
    if now >= res["pickupBy"]:
        raise Conflict("The pickup window has closed", "pickup_window_closed")

    qty = int(res["quantity"])
    donated = qty if res["listingType"] == "DONATION" else 0
    saved = (Decimal(res["originalUnitPrice"]) - Decimal(res["unitPrice"])) * qty if res["listingType"] == "DISCOUNTED" else Decimal(0)
    try:
        db.client().transact_write_items(TransactItems=[
            {"Update": {
                "TableName": db.name(db.RESERVATIONS),
                "Key": {"reservationId": res["reservationId"]},
                "UpdateExpression": "SET reservationStatus = :c, collectedAt = :now",
                "ConditionExpression": "reservationStatus = :r",
                "ExpressionAttributeValues": {":c": "COLLECTED", ":r": "RESERVED", ":now": now},
            }},
            {"Update": {
                "TableName": db.name(db.LISTINGS),
                "Key": {"listingId": res["listingId"]},
                "UpdateExpression": "ADD collectedQuantity :q",
                "ExpressionAttributeValues": {":q": qty},
            }},
            {"Update": {
                "TableName": db.name(db.IMPACT),
                "Key": {"metric": "global"},
                "UpdateExpression": "ADD itemsRescued :q, itemsDonated :d, lkrSaved :s",
                "ExpressionAttributeValues": {":q": qty, ":d": donated, ":s": saved},
            }},
        ])
    except ClientError as e:
        if e.response["Error"]["Code"] == "TransactionCanceledException":
            raise Conflict("Already collected", "already_collected")
        raise
    res["reservationStatus"] = "COLLECTED"
    res.pop("pickupCode", None)
    return {"reservation": res}
