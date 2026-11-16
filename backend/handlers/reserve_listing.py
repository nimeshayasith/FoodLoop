"""POST /listings/{id}/reserve - atomically take stock and create a reservation.

Overselling is prevented by a DynamoDB transaction: the stock decrement only succeeds if
enough units remain AND the listing is still open, and it commits together with the reservation.
"""
import secrets
import uuid

from botocore.exceptions import ClientError

from common import db, domain, util
from common.db import Key
from common.http import api
from common.util import Conflict, Forbidden, NotFound

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I - easy to read out at a counter


def new_pickup_code():
    for _ in range(5):
        code = "FL" + "".join(secrets.choice(CODE_ALPHABET) for _ in range(5))
        clash = db.table(db.RESERVATIONS).query(
            IndexName="ByPickupCode", KeyConditionExpression=Key("pickupCode").eq(code), Limit=1
        )
        if not clash["Items"]:
            return code
    raise Conflict("Could not allocate a pickup code, please retry", "code_unavailable")


@api
def handler(req):
    uid = req.require_user()
    listing_id = req.param("id")
    qty = domain.integer(req.json(), "quantity", minimum=1, maximum=1000)
    profile = domain.require_profile(uid, roles=["CUSTOMER", "CHARITY"])

    item = db.get_listing(listing_id, consistent=True)
    if not item:
        raise NotFound("Listing not found")
    if item["listingType"] == "DONATION" and profile["role"] != "CHARITY":
        raise Forbidden("Donations are reserved for verified charities and community groups", "charity_only")
    now = util.now_iso()
    if not domain.is_reservable(item, now):
        raise Conflict("This listing is closed or sold out", "listing_closed")

    # fairness: cap per customer so nobody can hoard a bargain
    mine = db.query_all(
        db.table(db.RESERVATIONS),
        IndexName="ByUser",
        KeyConditionExpression=Key("userId").eq(uid),
    )
    already = sum(
        int(r["quantity"]) for r in mine
        if r["listingId"] == listing_id and r["reservationStatus"] in ("RESERVED", "COLLECTED")
    )
    limit = int(item.get("maxPerCustomer", item["totalQuantity"]))
    if already + qty > limit:
        raise Conflict(f"Limit is {limit} per customer (you already hold {already})", "limit_exceeded")

    unit_price = item["discountedPrice"]
    reservation = {
        "reservationId": "RSV" + uuid.uuid4().hex[:10].upper(),
        "listingId": listing_id,
        "ownerId": item["ownerId"],
        "userId": uid,
        "customerName": profile["displayName"],
        "customerPhone": profile.get("phone", ""),
        "customerRole": profile["role"],
        "quantity": qty,
        "listingType": item["listingType"],
        "unitPrice": unit_price,
        "originalUnitPrice": item["originalPrice"],
        "totalPrice": unit_price * qty,
        "productName": item["productName"],
        "unit": item.get("unit", "item"),
        "orgName": item["orgName"],
        "orgAddress": item["orgAddress"],
        "orgWhatsapp": item["orgWhatsapp"],
        "imageKey": item.get("imageKey", ""),
        "pickupBy": item["collectionDeadline"],  # snapshot: later phases never shorten a customer's window
        "pickupCode": new_pickup_code(),
        "reservationStatus": "RESERVED",
        "createdAt": now,
    }
    try:
        db.client().transact_write_items(TransactItems=[
            {"Update": {
                "TableName": db.name(db.LISTINGS),
                "Key": {"listingId": listing_id},
                "UpdateExpression": "SET availableQuantity = availableQuantity - :q",
                "ConditionExpression": (
                    "#st = :active AND availableQuantity >= :q AND "
                    "((listingType = :disc AND saleDeadline > :now) OR (listingType = :don AND collectionDeadline > :now))"
                ),
                "ExpressionAttributeNames": {"#st": "status"},
                "ExpressionAttributeValues": {
                    ":q": qty, ":active": "ACTIVE", ":disc": "DISCOUNTED", ":don": "DONATION", ":now": now,
                },
            }},
            {"Put": {
                "TableName": db.name(db.RESERVATIONS),
                "Item": reservation,
                "ConditionExpression": "attribute_not_exists(reservationId)",
            }},
        ])
    except ClientError as e:
        if e.response["Error"]["Code"] == "TransactionCanceledException":
            raise Conflict("Not enough stock left - refresh and try again", "stock_changed")
        raise
    return 201, {"reservation": reservation}
