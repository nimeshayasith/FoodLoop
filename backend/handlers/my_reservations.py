"""GET /me/reservations - the signed-in user's reservations, newest first."""
from common import db, util
from common.db import Key
from common.http import api


@api
def handler(req):
    uid = req.require_user()
    items = db.query_all(
        db.table(db.RESERVATIONS),
        IndexName="ByUser",
        KeyConditionExpression=Key("userId").eq(uid),
        ScanIndexForward=False,
        Limit=100,
    )
    now = util.now_iso()
    for r in items:
        r["canCancel"] = r["reservationStatus"] == "RESERVED" and now < r["pickupBy"]
    return {"reservations": items[:100]}
