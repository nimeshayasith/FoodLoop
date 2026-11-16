"""Step Functions task: close the listing and mark uncollected reservations as no-shows."""
from botocore.exceptions import ClientError

from common import db, util
from common.db import Key


def handler(event, context=None):
    now = util.now_iso()
    try:
        resp = db.table(db.LISTINGS).update_item(
            Key={"listingId": event["listingId"]},
            UpdateExpression="SET #st = :exp, expiredAt = :now, unclaimedQuantity = availableQuantity",
            ConditionExpression="#st = :active",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":exp": "EXPIRED", ":active": "ACTIVE", ":now": now},
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"expired": False, "reason": "already_closed"}
        raise

    no_shows = 0
    for r in db.query_all(db.table(db.RESERVATIONS), IndexName="ByListing",
                          KeyConditionExpression=Key("listingId").eq(event["listingId"])):
        if r["reservationStatus"] != "RESERVED":
            continue
        try:
            db.table(db.RESERVATIONS).update_item(
                Key={"reservationId": r["reservationId"]},
                UpdateExpression="SET reservationStatus = :n, expiredAt = :now",
                ConditionExpression="reservationStatus = :r",
                ExpressionAttributeValues={":n": "NO_SHOW", ":r": "RESERVED", ":now": now},
            )
            no_shows += 1
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
    return {"expired": True, "unclaimedQuantity": int(resp["Attributes"]["unclaimedQuantity"]), "noShows": no_shows}
