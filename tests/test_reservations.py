import pytest
from conftest import call, listing_body, make_profile

from handlers import (cancel_reservation, create_listing, list_listings, my_reservations, org_listings,
                      reserve_listing, stats, verify_pickup)


@pytest.fixture
def setup(clock):
    make_profile("shop1", "BUSINESS")
    make_profile("alice", "CUSTOMER")
    make_profile("bob", "CUSTOMER")
    make_profile("hope", "CHARITY")
    _, body = call(create_listing.handler, method="POST", user="shop1", body=listing_body(clock, totalQuantity=10, maxPerCustomer=4))
    return body["listing"]["listingId"]


def reserve(listing_id, user, qty):
    return call(reserve_listing.handler, method="POST", user=user, params={"id": listing_id}, body={"quantity": qty})


def test_reserve_reduces_stock_and_issues_a_pickup_code(setup):
    status, body = reserve(setup, "alice", 3)
    assert status == 201
    res = body["reservation"]
    assert res["pickupCode"].startswith("FL") and res["totalPrice"] == 300
    _, listing = call(list_listings.handler)
    assert listing["listings"][0]["availableQuantity"] == 7


def test_cannot_oversell(setup):
    assert reserve(setup, "alice", 4)[0] == 201
    assert reserve(setup, "bob", 4)[0] == 201
    assert reserve(setup, "hope", 4)[0] == 409  # only 2 left
    assert reserve(setup, "hope", 2)[0] == 201
    status, body = reserve(setup, "bob", 1)
    assert status == 409  # sold out


def test_stale_read_cannot_oversell(setup, monkeypatch):
    """Simulates the race: another customer takes the last stock between our read and our write.

    The pre-check passes on stale data, so only the DynamoDB transaction's condition
    (availableQuantity >= :q) stands between us and overselling. (A real multi-threaded test is not
    possible with moto, which implements transactions without locking.)
    """
    from common import db

    stale = dict(db.get_listing(setup))
    assert reserve(setup, "alice", 4)[0] == 201
    assert reserve(setup, "bob", 4)[0] == 201
    assert reserve(setup, "hope", 2)[0] == 201  # stock is now 0
    make_profile("late", "CUSTOMER")
    with monkeypatch.context() as m:
        m.setattr(db, "get_listing", lambda *a, **k: stale)  # handler still sees 10 in stock
        status, body = reserve(setup, "late", 1)
    assert status == 409 and body["error"] == "stock_changed"
    assert db.get_listing(setup)["availableQuantity"] == 0
    assert len(db.table(db.RESERVATIONS).scan()["Items"]) == 3  # the failed attempt left nothing behind


def test_per_customer_limit(setup):
    assert reserve(setup, "alice", 3)[0] == 201
    status, body = reserve(setup, "alice", 2)
    assert status == 409 and body["error"] == "limit_exceeded"


def test_donations_are_charity_only(clock):
    make_profile("shop1", "BUSINESS")
    make_profile("alice", "CUSTOMER")
    make_profile("hope", "CHARITY")
    _, body = call(create_listing.handler, method="POST", user="shop1", body=listing_body(
        clock, listingType="DONATION", collectionDeadline=clock.at(hours=2), autoDonateRemaining=False, bestBeforeDate=None))
    lid = body["listing"]["listingId"]
    status, body = reserve(lid, "alice", 1)
    assert status == 403 and body["error"] == "charity_only"
    assert reserve(lid, "hope", 5)[0] == 201


def test_business_cannot_reserve(setup):
    assert reserve(setup, "shop1", 1)[0] == 403


def test_cancel_returns_stock(setup):
    rid = reserve(setup, "alice", 4)[1]["reservation"]["reservationId"]
    assert call(cancel_reservation.handler, method="POST", user="bob", params={"id": rid})[0] == 403
    assert call(cancel_reservation.handler, method="POST", user="alice", params={"id": rid})[0] == 200
    assert call(list_listings.handler)[1]["listings"][0]["availableQuantity"] == 10
    assert call(cancel_reservation.handler, method="POST", user="alice", params={"id": rid})[0] == 409  # twice


def test_my_reservations(setup):
    reserve(setup, "alice", 1)
    _, body = call(my_reservations.handler, user="alice", route="GET /me/reservations")
    assert len(body["reservations"]) == 1 and body["reservations"][0]["canCancel"] is True
    assert call(my_reservations.handler, user="bob")[1]["reservations"] == []


def test_pickup_verification_and_impact_stats(setup):
    res = reserve(setup, "alice", 2)[1]["reservation"]
    # another store cannot redeem it, and the response does not reveal whether the code exists
    make_profile("shop2", "BUSINESS")
    status, body = call(verify_pickup.handler, method="POST", user="shop2", body={"pickupCode": res["pickupCode"]})
    assert status == 404 and body["error"] == "code_not_found"
    status, body = call(verify_pickup.handler, method="POST", user="shop1", body={"pickupCode": "FL-" + res["pickupCode"][2:].lower()})
    assert status == 200 and body["reservation"]["reservationStatus"] == "COLLECTED"
    assert call(verify_pickup.handler, method="POST", user="shop1", body={"pickupCode": res["pickupCode"]})[0] == 409
    _, s = call(stats.handler)
    assert s == {"itemsRescued": 2, "itemsDonated": 0, "lkrSaved": 200}
    _, mine = call(org_listings.handler, user="shop1", route="GET /org/listings")
    assert mine["listings"][0]["collectedQuantity"] == 2


def test_pickup_window_is_enforced(setup, clock):
    res = reserve(setup, "alice", 1)[1]["reservation"]
    clock.advance(hours=3, minutes=1)
    status, body = call(verify_pickup.handler, method="POST", user="shop1", body={"pickupCode": res["pickupCode"]})
    assert status == 409 and body["error"] == "pickup_window_closed"


def test_org_sees_reservations_without_codes(setup):
    reserve(setup, "alice", 1)
    status, body = call(org_listings.handler, user="shop1", params={"id": setup},
                        route="GET /org/listings/{id}/reservations")
    assert status == 200 and "pickupCode" not in body["reservations"][0]
    assert call(org_listings.handler, user="shop2", params={"id": setup}, route="GET /org/listings/{id}/reservations")[0] in (403,)
