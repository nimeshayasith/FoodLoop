"""GET /listings (public) - reservable listings, soonest-ending first."""
from common import db, domain, util
from common.db import Key
from common.http import api

MAX_RESULTS = 100


@api
def handler(req):
    q = req.query
    wanted_type = (q.get("type") or "").upper()
    district = q.get("district") or ""
    category = q.get("category") or ""
    search = (q.get("q") or "").strip().lower()

    items = db.query_all(
        db.table(db.LISTINGS),
        IndexName="ByStatus",
        KeyConditionExpression=Key("status").eq("ACTIVE"),
    )
    now = util.now_iso()
    results = []
    for item in items:
        if not domain.is_reservable(item, now):
            continue  # hides expired/sold-out rows even if the workflow has not closed them yet
        if wanted_type in domain.LISTING_TYPES and item["listingType"] != wanted_type:
            continue
        if district and item["orgDistrict"] != district:
            continue
        if category and item["category"] != category:
            continue
        if search and search not in f'{item["productName"]} {item["orgName"]} {item.get("description", "")}'.lower():
            continue
        results.append(item)
    results.sort(key=domain.reserve_by)
    return {"listings": [domain.listing_view(i) for i in results[:MAX_RESULTS]]}
