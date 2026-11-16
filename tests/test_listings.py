import pytest
from conftest import call, listing_body, make_profile

from handlers import create_listing, get_listing, list_listings, presign_upload


@pytest.fixture
def shop():
    make_profile("shop1", "BUSINESS")
    return "shop1"


def publish(clock, shop, **over):
    status, body = call(create_listing.handler, method="POST", user=shop, body=listing_body(clock, **over))
    return status, body


def test_create_listing_starts_a_workflow_and_is_publicly_visible(clock, shop):
    status, body = publish(clock, shop)
    assert status == 201
    listing = body["listing"]
    assert listing["availableQuantity"] == 100 and listing["state"] == "SALE_OPEN"
    assert listing["sfnExecutionArn"].startswith("arn:aws:states")
    status, body = call(list_listings.handler, route="GET /listings")
    assert [l["listingId"] for l in body["listings"]] == [listing["listingId"]]
    assert "ownerId" not in body["listings"][0] and "sfnExecutionArn" not in body["listings"][0]


def test_filters_by_type_district_and_search(clock, shop):
    publish(clock, shop)
    publish(clock, shop, listingType="DONATION", productName="Fruit boxes", category="Fruits & vegetables",
            collectionDeadline=clock.at(hours=3), bestBeforeDate=None)
    names = lambda **q: sorted(l["productName"] for l in call(list_listings.handler, query=q)[1]["listings"])
    assert names() == ["Bread packets", "Fruit boxes"]
    assert names(type="DONATION") == ["Fruit boxes"]
    assert names(district="Kandy") == []
    assert names(q="bread") == ["Bread packets"]


@pytest.mark.parametrize("over,code", [
    ({"discountedPrice": 250}, "discount_invalid"),
    ({"saleDeadline": "tomorrow"}, "invalid_timestamp"),
    ({"collectionDeadline": None}, "invalid_timestamp"),
    ({"totalQuantity": 0}, "totalQuantity_invalid"),
    ({"productName": "x"}, "productName_invalid"),
    ({"category": "Weapons"}, "category_invalid"),
])
def test_validation(clock, shop, over, code):
    status, body = publish(clock, shop, **over)
    assert status == 400 and body["error"] == code


def test_deadlines_must_be_ordered_and_inside_best_before(clock, shop):
    status, body = publish(clock, shop, collectionDeadline=clock.at(hours=1))
    assert body["error"] == "collectionDeadline_invalid"
    status, body = publish(clock, shop, donationDeadline=clock.at(hours=30), bestBeforeDate=clock.at(hours=24))
    assert body["error"] == "food_safety_deadline"
    status, body = publish(clock, shop, saleDeadline=clock.at(seconds=5))
    assert body["error"] == "saleDeadline_too_soon"


def test_expired_listing_is_hidden_even_before_the_workflow_runs(clock, shop):
    publish(clock, shop)
    clock.advance(hours=2, minutes=1)  # sale deadline passed, workflow has not run yet
    assert call(list_listings.handler)[1]["listings"] == []


def test_get_listing_404(clock):
    status, _ = call(get_listing.handler, params={"id": "nope"})
    assert status == 404


def test_presign_returns_a_constrained_post_policy(shop):
    status, body = call(presign_upload.handler, method="POST", user=shop, body={"contentType": "image/jpeg"})
    assert status == 200
    assert body["key"].startswith("images/shop1/") and body["key"].endswith(".jpg")
    assert body["fields"]["Content-Type"] == "image/jpeg" and body["maxBytes"] == 3 * 1024 * 1024
    status, body = call(presign_upload.handler, method="POST", user=shop, body={"contentType": "text/html"})
    assert status == 400


def test_image_key_must_belong_to_the_uploader(clock, shop):
    status, body = publish(clock, shop, imageKey="images/someone-else/x.jpg")
    assert body["error"] == "imageKey_invalid"
    status, body = publish(clock, shop, imageKey="images/shop1/x.jpg")
    assert status == 201
