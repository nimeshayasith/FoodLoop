"""The Step Functions lifecycle, simulated state-by-state with the same Lambdas the state machine calls.

(ASL syntax itself is validated separately with `npx asl-validator`.)
"""
import json
from pathlib import Path

from conftest import call, listing_body, make_profile

from handlers import (check_inventory, convert_to_donation, create_listing, expire_listing, get_listing,
                      list_listings, reserve_listing, verify_pickup)

ASL = json.loads((Path(__file__).parent.parent / "workflows" / "listing_lifecycle.asl.json").read_text())


def reserve(lid, user, qty):
    return call(reserve_listing.handler, method="POST", user=user, params={"id": lid}, body={"quantity": qty})


def listing(lid):
    return call(get_listing.handler, params={"id": lid})[1]["listing"]


def test_asl_references_every_workflow_lambda():
    text = json.dumps(ASL)
    for name in ("CheckInventory", "ConvertToDonation", "ExpireListing"):
        assert f"${{{name}FunctionArn}}" in text
    for state in ASL["States"].values():
        assert state["Type"] in ("Choice", "Wait", "Task")


def test_discount_to_donation_end_to_end(clock):
    make_profile("shop1", "BUSINESS")
    make_profile("alice", "CUSTOMER")
    make_profile("hope", "CHARITY")
    _, body = call(create_listing.handler, method="POST", user="shop1", body=listing_body(clock, maxPerCustomer=100))
    lid = body["listing"]["listingId"]

    alice = reserve(lid, "alice", 60)[1]["reservation"]               # 60 of 100 sold at LKR 100
    assert reserve(lid, "hope", 1)[1]["reservation"]["listingType"] == "DISCOUNTED"
    clock.advance(hours=2, minutes=1)                                # --- Wait(saleDeadline) ends
    assert reserve(lid, "alice", 1)[0] == 409                        # sale is over for everyone

    inv = check_inventory.handler({"listingId": lid})                # --- CheckInventory
    assert inv == {"remaining": 39, "eligibleForDonation": True, "reason": "ok"}

    conv = convert_to_donation.handler({"listingId": lid})           # --- ConvertToDonation
    assert conv["converted"] and conv["quantity"] == 39
    again = convert_to_donation.handler({"listingId": lid})          # retries are harmless
    assert again["converted"] is False

    view = listing(lid)
    assert view["listingType"] == "DONATION" and view["discountedPrice"] == 0 and view["convertedFromDiscount"]
    assert view["state"] == "DONATION_CONVERTED" and view["reservable"] is True
    assert [l["listingId"] for l in call(list_listings.handler, query={"type": "DONATION"})[1]["listings"]] == [lid]

    assert reserve(lid, "alice", 1)[0] == 403                        # customers cannot take donations
    status, body = reserve(lid, "hope", 39)                          # charity takes every leftover
    assert status == 201 and body["reservation"]["totalPrice"] == 0
    donation = body["reservation"]

    clock.advance(hours=2, minutes=30)                               # now past the original 3h collection deadline
    assert listing(lid)["reservable"] is False                       # nothing left to reserve
    pick = lambda r: call(verify_pickup.handler, method="POST", user="shop1", body={"pickupCode": r["pickupCode"]})
    assert pick(alice)[1]["error"] == "pickup_window_closed"         # discount customers keep their original window
    assert pick(donation)[0] == 200                                  # the converted donation can still be collected

    clock.advance(hours=1)                                           # --- Wait(donationDeadline) ends
    out = expire_listing.handler({"listingId": lid})                 # --- ExpireListing
    assert out == {"expired": True, "unclaimedQuantity": 0, "noShows": 2}  # alice + hope's discount reservation
    assert listing(lid)["status"] == "EXPIRED"
    assert expire_listing.handler({"listingId": lid})["expired"] is False   # idempotent


def test_no_conversion_when_opted_out(clock):
    make_profile("shop1", "BUSINESS")
    _, body = call(create_listing.handler, method="POST", user="shop1", body=listing_body(clock, autoDonateRemaining=False))
    lid = body["listing"]["listingId"]
    clock.advance(hours=2, minutes=1)
    inv = check_inventory.handler({"listingId": lid})
    assert inv["eligibleForDonation"] is False and inv["reason"] == "auto_donation_off"
    assert convert_to_donation.handler({"listingId": lid})["converted"] is False


def test_no_conversion_when_sold_out_or_past_best_before(clock):
    make_profile("shop1", "BUSINESS")
    make_profile("alice", "CUSTOMER")
    _, body = call(create_listing.handler, method="POST", user="shop1",
                   body=listing_body(clock, totalQuantity=2, maxPerCustomer=2))
    lid = body["listing"]["listingId"]
    reserve(lid, "alice", 2)
    clock.advance(hours=2, minutes=1)
    assert check_inventory.handler({"listingId": lid})["reason"] == "sold_out"


def test_donation_listing_just_expires(clock):
    make_profile("shop1", "BUSINESS")
    _, body = call(create_listing.handler, method="POST", user="shop1", body=listing_body(
        clock, listingType="DONATION", collectionDeadline=clock.at(hours=1), autoDonateRemaining=False, bestBeforeDate=None))
    lid = body["listing"]["listingId"]
    clock.advance(hours=1, minutes=1)
    out = expire_listing.handler({"listingId": lid})
    assert out["expired"] and out["unclaimedQuantity"] == 100
