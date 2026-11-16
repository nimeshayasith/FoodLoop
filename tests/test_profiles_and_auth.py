from conftest import call, make_profile

from handlers import admin, profile, reserve_listing, create_listing


def test_customer_profile_is_active_and_org_is_auto_approved():
    assert make_profile("cust1", "CUSTOMER")["status"] == "ACTIVE"
    assert make_profile("shop1", "BUSINESS")["status"] == "APPROVED"


def test_orgs_stay_pending_when_auto_approve_is_off(monkeypatch):
    monkeypatch.setenv("AUTO_APPROVE_ORGS", "false")
    assert make_profile("shop1", "BUSINESS")["status"] == "PENDING"


def test_phone_is_normalised_for_whatsapp_links():
    assert make_profile("c1", "CUSTOMER", phone="077 123 4567")["phone"] == "94771234567"


def test_bad_phone_and_district_rejected():
    status, body = call(profile.handler, method="PUT", user="c2",
                        body={"role": "CUSTOMER", "displayName": "Nim", "district": "Colombo", "phone": "12345"})
    assert status == 400 and body["error"] == "phone_invalid"
    status, body = call(profile.handler, method="PUT", user="c2",
                        body={"role": "CUSTOMER", "displayName": "Nim", "district": "Atlantis"})
    assert status == 400


def test_endpoints_require_a_signed_in_user():
    status, body = call(create_listing.handler, method="POST", body={})
    assert status == 401


def test_role_cannot_be_escalated_by_body_fields():
    # status/role-style fields in the body are ignored; verification status is server-side only
    monkey_body = {"role": "CUSTOMER", "displayName": "Mal", "district": "Galle", "status": "APPROVED"}
    status, body = call(profile.handler, method="PUT", user="mal", body=monkey_body)
    assert body["profile"]["status"] == "ACTIVE"


def test_admin_approval_flow(monkeypatch):
    monkeypatch.setenv("AUTO_APPROVE_ORGS", "false")
    make_profile("charity1", "CHARITY")
    status, _ = call(admin.handler, user="someone", route="GET /admin/profiles")
    assert status == 403
    status, body = call(admin.handler, user="boss", groups=["admin"], route="GET /admin/profiles")
    assert [p["userId"] for p in body["profiles"]] == ["charity1"]
    status, body = call(admin.handler, method="POST", user="boss", groups=["admin"], params={"userId": "charity1"},
                        route="POST /admin/profiles/{userId}/decision", body={"decision": "approve"})
    assert body["status"] == "APPROVED"


def test_pending_business_cannot_publish(monkeypatch, clock):
    from conftest import listing_body

    monkeypatch.setenv("AUTO_APPROVE_ORGS", "false")
    make_profile("shop1", "BUSINESS")
    status, body = call(create_listing.handler, method="POST", user="shop1", body=listing_body(clock))
    assert status == 403 and body["error"] == "pending_verification"
