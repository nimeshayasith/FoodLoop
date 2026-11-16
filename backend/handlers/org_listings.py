"""Business dashboard: GET /org/listings and GET /org/listings/{id}/reservations."""
from common import db, domain
from common.db import Key
from common.http import api
from common.util import Forbidden, NotFound


@api
def handler(req):
    uid = req.require_user()
    domain.require_profile(uid, roles=["BUSINESS"], approved=False)
    if req.route.endswith("/reservations"):
        return listing_reservations(req, uid)
    items = db.query_all(
        db.table(db.LISTINGS),
        IndexName="ByOwner",
        KeyConditionExpression=Key("ownerId").eq(uid),
        ScanIndexForward=False,
    )
    return {"listings": [domain.listing_view(i, owner=True) for i in items[:100]]}


def listing_reservations(req, uid):
    listing = db.get_listing(req.param("id"))
    if not listing:
        raise NotFound("Listing not found")
    if listing["ownerId"] != uid:
        raise Forbidden("Not your listing")
    rows = db.query_all(
        db.table(db.RESERVATIONS),
        IndexName="ByListing",
        KeyConditionExpression=Key("listingId").eq(listing["listingId"]),
        ScanIndexForward=False,
    )
    for r in rows:
        r.pop("pickupCode", None)  # staff verify the code the customer shows; the code is never listed
    return {"reservations": rows}
