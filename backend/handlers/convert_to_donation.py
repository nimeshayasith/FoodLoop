"""Step Functions task: flip leftover discounted stock into a free donation listing.

Idempotent: the conditional update succeeds at most once, so Step Functions retries are safe.
"""
from botocore.exceptions import ClientError

from common import db, util


def handler(event, context=None):
    table = db.table(db.LISTINGS)
    item = db.get_listing(event["listingId"], consistent=True)
    try:
        resp = table.update_item(
            Key={"listingId": event["listingId"]},
            UpdateExpression=(
                "SET listingType = :don, discountedPrice = :zero, convertedFromDiscount = :t, "
                "collectionDeadline = donationDeadline, maxPerCustomer = totalQuantity, convertedAt = :now"
            ),
            ConditionExpression="#st = :active AND listingType = :disc AND availableQuantity > :zero "
                                "AND attribute_exists(donationDeadline)",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={
                ":don": "DONATION", ":disc": "DISCOUNTED", ":zero": 0, ":t": True,
                ":active": "ACTIVE", ":now": util.now_iso(),
            },
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        return {"converted": False, "quantity": 0, "donationDeadline": item["collectionDeadline"] if item else util.now_iso()}
    new = resp["Attributes"]
    return {"converted": True, "quantity": int(new["availableQuantity"]), "donationDeadline": new["collectionDeadline"]}
