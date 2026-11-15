"""GET /listings/{id} (public)."""
from common import db, domain
from common.http import api
from common.util import NotFound


@api
def handler(req):
    item = db.get_listing(req.param("id"))
    if not item:
        raise NotFound("Listing not found")
    return {"listing": domain.listing_view(item)}
