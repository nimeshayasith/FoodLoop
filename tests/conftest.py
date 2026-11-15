"""Test fixtures: moto-backed AWS with tables built straight from template.yaml (no drift)."""
import json
import os
import sys
from pathlib import Path

import boto3
import pytest
import yaml
from moto import mock_aws

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

TABLES = {  # logical id in template.yaml -> env var used by the Lambdas
    "ListingsTable": "LISTINGS_TABLE",
    "ReservationsTable": "RESERVATIONS_TABLE",
    "ProfilesTable": "PROFILES_TABLE",
    "ImpactTable": "IMPACT_TABLE",
}


class _Loader(yaml.SafeLoader):
    pass


def _any_tag(loader, suffix, node):  # CloudFormation short-form tags (!Ref, !Sub, ...) are irrelevant here
    return None


_Loader.add_multi_constructor("!", _any_tag)


def template_resources():
    return yaml.load((ROOT / "template.yaml").read_text(), Loader=_Loader)["Resources"]


@pytest.fixture(autouse=True)
def aws(monkeypatch):
    for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(k, "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("AUTO_APPROVE_ORGS", "true")
    monkeypatch.setenv("IMAGE_BUCKET", "foodloop-test-images")

    with mock_aws():
        from common import db

        db.reset()
        ddb = boto3.client("dynamodb")
        resources = template_resources()
        for logical, env in TABLES.items():
            props = dict(resources[logical]["Properties"])
            name = f"test-{logical}"
            kwargs = dict(
                TableName=name,
                AttributeDefinitions=props["AttributeDefinitions"],
                KeySchema=props["KeySchema"],
                BillingMode=props["BillingMode"],
            )
            if "GlobalSecondaryIndexes" in props:
                kwargs["GlobalSecondaryIndexes"] = props["GlobalSecondaryIndexes"]
            ddb.create_table(**kwargs)
            monkeypatch.setenv(env, name)

        boto3.client("s3", region_name="ap-south-1").create_bucket(
            Bucket="foodloop-test-images",
            CreateBucketConfiguration={"LocationConstraint": "ap-south-1"},
        )
        sfn = boto3.client("stepfunctions")
        machine = sfn.create_state_machine(
            name="test-lifecycle",
            definition=json.dumps({"StartAt": "x", "States": {"x": {"Type": "Pass", "End": True}}}),
            roleArn="arn:aws:iam::123456789012:role/test",
        )
        monkeypatch.setenv("STATE_MACHINE_ARN", machine["stateMachineArn"])
        yield


# ------------------------------------------------------------- helpers
class Clock:
    """Freeze/advance the time the Lambdas see (they all call util.now_utc())."""

    def __init__(self, monkeypatch):
        from datetime import datetime, timezone

        self.now = datetime(2026, 11, 16, 8, 0, 0, tzinfo=timezone.utc)
        from common import util

        monkeypatch.setattr(util, "now_utc", lambda: self.now)

    def advance(self, **kw):
        from datetime import timedelta

        self.now += timedelta(**kw)

    def at(self, **kw):
        from datetime import timedelta

        from common import util

        return util.iso(self.now + timedelta(**kw))


@pytest.fixture
def clock(monkeypatch):
    return Clock(monkeypatch)


def call(handler, *, method="GET", route=None, user=None, body=None, params=None, query=None, groups=None):
    """Invoke an API handler the way API Gateway (HTTP API v2) would."""
    claims = {}
    if user:
        claims = {"sub": user, "email": f"{user}@example.com"}
        if groups:
            claims["cognito:groups"] = "[" + " ".join(groups) + "]"
    event = {
        "routeKey": route or f"{method} /",
        "requestContext": {"http": {"method": method}, "authorizer": {"jwt": {"claims": claims}} if user else {}},
        "pathParameters": params or {},
        "queryStringParameters": query or {},
        "body": json.dumps(body) if body is not None else None,
    }
    resp = handler(event, None)
    return resp["statusCode"], json.loads(resp["body"])


def make_profile(user, role, **extra):
    from handlers import profile

    body = {"role": role, "displayName": f"User {user}", "district": "Colombo", "phone": "0771234567"}
    if role != "CUSTOMER":
        body.update(orgName=f"Org {user}", address="12 Galle Road, Colombo 03")
    if role == "BUSINESS":
        body["businessType"] = "Bakery"
    body.update(extra)
    status, data = call(profile.handler, method="PUT", route="PUT /me", user=user, body=body)
    assert status == 200, data
    return data["profile"]


def listing_body(clock, **over):
    body = {
        "listingType": "DISCOUNTED", "productName": "Bread packets", "category": "Bakery", "unit": "packet",
        "totalQuantity": 100, "originalPrice": 200, "discountedPrice": 100,
        "saleDeadline": clock.at(hours=2), "collectionDeadline": clock.at(hours=3),
        "autoDonateRemaining": True, "donationDeadline": clock.at(hours=5),
        "bestBeforeDate": clock.at(hours=24), "maxPerCustomer": 10,
    }
    body.update(over)
    return body
