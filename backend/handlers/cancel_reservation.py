"""POST /reservations/{id}/cancel - customer releases stock back to the listing."""
from botocore.exceptions import ClientError

from common import db, util
from common.http import api
from common.util import Conflict, Forbidden, NotFound


@api
def handler(req):
    uid = req.require_user()
    rid = req.param("id")
    res = db.table(db.RESERVATIONS).get_item(Key={"reservationId": rid}, ConsistentRead=True).get("Item")
    if not res:
        raise NotFound("Reservation not found")
    if res["userId"] != uid:
        raise Forbidden("This is not your reservation")
    now = util.now_iso()
    if res["reservationStatus"] != "RESERVED" or now >= res["pickupBy"]:
        raise Conflict("This reservation can no longer be cancelled", "not_cancellable")

    cancel = {
        "TableName": db.name(db.RESERVATIONS),
        "Key": {"reservationId": rid},
        "UpdateExpression": "SET reservationStatus = :c, cancelledAt = :now",
        "ConditionExpression": "reservationStatus = :r AND userId = :u",
        "ExpressionAttributeValues": {":c": "CANCELLED", ":r": "RESERVED", ":u": uid, ":now": now},
    }
    listing = db.get_listing(res["listingId"], consistent=True)
    items = [{"Update": cancel}]
    if listing and listing["status"] == "ACTIVE":  # only return stock to a listing that is still open
        items.append({"Update": {
            "TableName": db.name(db.LISTINGS),
            "Key": {"listingId": res["listingId"]},
            "UpdateExpression": "ADD availableQuantity :q",
            "ConditionExpression": "#st = :active",
            "ExpressionAttributeNames": {"#st": "status"},
            "ExpressionAttributeValues": {":q": int(res["quantity"]), ":active": "ACTIVE"},
        }})
    try:
        db.client().transact_write_items(TransactItems=items)
    except ClientError as e:
        if e.response["Error"]["Code"] == "TransactionCanceledException":
            raise Conflict("Could not cancel - the reservation or listing changed", "cancel_failed")
        raise
    return {"cancelled": True}
