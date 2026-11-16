"""Step Functions task: how much is left, and may it be donated?"""
from common import db, util


def handler(event, context=None):
    item = db.get_listing(event["listingId"], consistent=True)
    if not item:
        return {"remaining": 0, "eligibleForDonation": False, "reason": "listing_missing"}
    remaining = int(item["availableQuantity"])
    eligible, reason = True, "ok"
    now = util.now_iso()
    if item["status"] != "ACTIVE" or item["listingType"] != "DISCOUNTED":
        eligible, reason = False, "not_an_open_discount"
    elif remaining <= 0:
        eligible, reason = False, "sold_out"
    elif not item.get("autoDonateRemaining") or not item.get("donationDeadline"):
        eligible, reason = False, "auto_donation_off"
    elif item["donationDeadline"] <= now:
        eligible, reason = False, "donation_window_over"
    elif item.get("bestBeforeDate") and item["donationDeadline"] > item["bestBeforeDate"]:
        eligible, reason = False, "past_best_before"  # food-safety guard
    return {"remaining": remaining, "eligibleForDonation": eligible, "reason": reason}
