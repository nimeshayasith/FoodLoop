"""POST /listings - an approved business publishes a discounted deal or a free donation.

After the row is written we start one Step Functions execution for the listing. That
execution owns the listing's lifecycle (wait -> check stock -> convert -> expire).
"""
import json
import os
import uuid
from datetime import timedelta
from decimal import Decimal

import boto3

from common import db, domain, util
from common.domain import choice, integer, price, text
from common.http import api
from common.util import ValidationError

_sfn = None


def sfn():
    global _sfn
    if _sfn is None:
        _sfn = boto3.client("stepfunctions")
    return _sfn


@api
def handler(req):
    uid = req.require_user()
    profile = domain.require_profile(uid, roles=["BUSINESS"])
    item = build_item(req.json(), uid, profile)

    table = db.table(db.LISTINGS)
    table.put_item(Item=item, ConditionExpression="attribute_not_exists(listingId)")
    try:
        execution = sfn().start_execution(
            stateMachineArn=os.environ["STATE_MACHINE_ARN"],
            name=item["listingId"],  # unique per listing -> a retry can never start a second workflow
            input=json.dumps({
                "listingId": item["listingId"],
                "listingType": item["listingType"],
                "saleDeadline": item.get("saleDeadline", item["collectionDeadline"]),
                "collectionDeadline": item["collectionDeadline"],
                "autoDonateRemaining": item["autoDonateRemaining"],
            }),
        )
    except Exception:
        table.delete_item(Key={"listingId": item["listingId"]})  # never leave a listing without a lifecycle
        raise
    table.update_item(
        Key={"listingId": item["listingId"]},
        UpdateExpression="SET sfnExecutionArn = :a",
        ExpressionAttributeValues={":a": execution["executionArn"]},
    )
    item["sfnExecutionArn"] = execution["executionArn"]
    return 201, {"listing": domain.listing_view(item, owner=True)}


def build_item(body, uid, profile):
    now = util.now_utc()
    now_s = util.iso(now)
    ltype = choice(body, "listingType", domain.LISTING_TYPES)
    total = integer(body, "totalQuantity", minimum=1, maximum=10000)
    horizon = now + timedelta(days=domain.MAX_HORIZON_DAYS)
    earliest = now + timedelta(seconds=domain.MIN_LEAD_SECONDS)

    def when(field):
        value = util.parse_iso(body.get(field), field)
        if value > horizon:
            raise ValidationError(f"{field} must be within {domain.MAX_HORIZON_DAYS} days", f"{field}_too_far")
        return value

    item = {
        "listingId": "LST" + uuid.uuid4().hex[:10].upper(),
        "ownerId": uid,
        "orgName": profile["orgName"],
        "orgDistrict": profile["district"],
        "orgAddress": profile["address"],
        "orgWhatsapp": profile["phone"],
        "productName": text(body, "productName", min_len=2, max_len=80),
        "description": text(body, "description", max_len=300, required=False),
        "category": choice(body, "category", domain.CATEGORIES),
        "unit": text(body, "unit", max_len=20, required=False, default="item"),
        "pickupInstructions": text(body, "pickupInstructions", max_len=200, required=False),
        "listingType": ltype,
        "totalQuantity": total,
        "availableQuantity": total,
        "collectedQuantity": 0,
        "autoDonateRemaining": False,
        "status": "ACTIVE",
        "createdAt": now_s,
    }

    collection = when("collectionDeadline")
    if ltype == "DISCOUNTED":
        original, discounted = price(body, "originalPrice"), price(body, "discountedPrice")
        if discounted >= original:
            raise ValidationError("discountedPrice must be lower than originalPrice", "discount_invalid")
        sale = when("saleDeadline")
        if sale < earliest:
            raise ValidationError("saleDeadline must be at least 30 seconds from now", "saleDeadline_too_soon")
        if collection < sale:
            raise ValidationError("collectionDeadline cannot be before saleDeadline", "collectionDeadline_invalid")
        item.update(originalPrice=original, discountedPrice=discounted, saleDeadline=util.iso(sale))
        item["maxPerCustomer"] = integer(body, "maxPerCustomer", minimum=1, maximum=total, default=min(5, total))
        if body.get("autoDonateRemaining") is True:
            donation = when("donationDeadline")
            if donation < collection:
                raise ValidationError("donationDeadline cannot be before collectionDeadline", "donationDeadline_invalid")
            item.update(autoDonateRemaining=True, donationDeadline=util.iso(donation))
    else:
        if collection < earliest:
            raise ValidationError("collectionDeadline must be at least 30 seconds from now", "collectionDeadline_too_soon")
        item.update(originalPrice=Decimal(0), discountedPrice=Decimal(0))
        item["maxPerCustomer"] = integer(body, "maxPerCustomer", minimum=1, maximum=total, default=total)
    item["collectionDeadline"] = util.iso(collection)

    if body.get("bestBeforeDate"):
        best = util.parse_iso(body["bestBeforeDate"], "bestBeforeDate")
        last = max(collection, util.parse_iso(item["donationDeadline"]) if item.get("donationDeadline") else collection)
        if last > best:
            raise ValidationError("Collection deadlines must not be after the food's best-before/use-by time", "food_safety_deadline")
        item["bestBeforeDate"] = util.iso(best)

    image_key = body.get("imageKey")
    if image_key:
        if not isinstance(image_key, str) or not image_key.startswith(f"images/{uid}/"):
            raise ValidationError("Invalid imageKey", "imageKey_invalid")
        item["imageKey"] = image_key
    return item
