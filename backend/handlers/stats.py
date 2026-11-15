"""GET /stats (public) - impact counters for the landing page."""
from common import db
from common.http import api


@api
def handler(req):
    item = db.table(db.IMPACT).get_item(Key={"metric": "global"}).get("Item") or {}
    return {
        "itemsRescued": item.get("itemsRescued", 0),
        "itemsDonated": item.get("itemsDonated", 0),
        "lkrSaved": item.get("lkrSaved", 0),
    }
