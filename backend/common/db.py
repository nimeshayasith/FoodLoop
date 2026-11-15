"""DynamoDB access helpers. Table names come from environment variables set in template.yaml."""
import os

import boto3
from boto3.dynamodb.conditions import Key  # noqa: F401  (re-exported for handlers)

LISTINGS = "LISTINGS_TABLE"
RESERVATIONS = "RESERVATIONS_TABLE"
PROFILES = "PROFILES_TABLE"
IMPACT = "IMPACT_TABLE"

_resource = None


def resource():
    global _resource
    if _resource is None:
        _resource = boto3.resource("dynamodb")
    return _resource


def reset():
    """Drop the cached resource (used by tests)."""
    global _resource
    _resource = None


def table(env_name):
    return resource().Table(os.environ[env_name])


def name(env_name):
    return os.environ[env_name]


def client():
    # The resource's client accepts plain Python types in transact_write_items.
    return resource().meta.client


def query_all(tbl, **kwargs):
    """Follow LastEvaluatedKey until the query is exhausted."""
    items = []
    while True:
        resp = tbl.query(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            return items
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def get_profile(user_id):
    return table(PROFILES).get_item(Key={"userId": user_id}).get("Item")


def get_listing(listing_id, consistent=False):
    return table(LISTINGS).get_item(Key={"listingId": listing_id}, ConsistentRead=consistent).get("Item")
