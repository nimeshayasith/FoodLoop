#!/usr/bin/env python3
"""Create demo accounts and sample listings in a deployed FoodLoop stack.

    ./scripts/seed.py --stack foodloop --region ap-south-1            # accounts + sample listings
    ./scripts/seed.py --stack foodloop --region ap-south-1 --demo     # + a 2/3/6-minute listing for the live demo

Accounts are created through the Cognito admin API (no email verification needed), profiles are written
straight to DynamoDB as APPROVED, and listings go through the real HTTP API so validation and the
Step Functions workflow behave exactly as in production. DEMO PASSWORDS ONLY - never use in production.
"""
import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import boto3

PASSWORD = "FoodLoop-Demo-2026"
USERS = {
    "admin@foodloop.example": {"group": "admin"},
    "shop@foodloop.example": {"profile": {"role": "BUSINESS", "displayName": "Nimal Perera", "orgName": "Sunrise Bakery & Supermarket",
        "address": "45 Galle Road, Colombo 03", "district": "Colombo", "phone": "94771234567", "businessType": "Supermarket"}},
    "charity@foodloop.example": {"profile": {"role": "CHARITY", "displayName": "Kamala Silva", "orgName": "Hope Community Kitchen",
        "address": "8 Temple Road, Kandy", "district": "Kandy", "phone": "94712345678", "registrationNo": "NGO/DEMO/001"}},
    "customer@foodloop.example": {"profile": {"role": "CUSTOMER", "displayName": "Saman Fernando", "district": "Colombo", "phone": "94701234567"}},
}


def iso(minutes):
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack", default="foodloop")
    ap.add_argument("--region", default="ap-south-1")
    ap.add_argument("--demo", action="store_true", help="also publish a short-timer listing for the live Step Functions demo")
    ap.add_argument("--demo-only", action="store_true", help="only publish a fresh short-timer demo listing (skip the 3 regular samples)")
    args = ap.parse_args()

    cfn = boto3.client("cloudformation", region_name=args.region)
    out = {o["OutputKey"]: o["OutputValue"] for o in cfn.describe_stacks(StackName=args.stack)["Stacks"][0]["Outputs"]}
    idp = boto3.client("cognito-idp", region_name=args.region)
    profiles = boto3.resource("dynamodb", region_name=args.region).Table(out["ProfilesTableName"])

    sub = {}
    for email, cfg in USERS.items():
        try:
            idp.admin_create_user(UserPoolId=out["UserPoolId"], Username=email, MessageAction="SUPPRESS",
                                  UserAttributes=[{"Name": "email", "Value": email}, {"Name": "email_verified", "Value": "true"}])
        except idp.exceptions.UsernameExistsException:
            pass
        idp.admin_set_user_password(UserPoolId=out["UserPoolId"], Username=email, Password=PASSWORD, Permanent=True)
        user = idp.admin_get_user(UserPoolId=out["UserPoolId"], Username=email)
        sub[email] = next(a["Value"] for a in user["UserAttributes"] if a["Name"] == "sub")
        if cfg.get("group"):
            idp.admin_add_user_to_group(UserPoolId=out["UserPoolId"], Username=email, GroupName=cfg["group"])
        if cfg.get("profile"):
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            status = "ACTIVE" if cfg["profile"]["role"] == "CUSTOMER" else "APPROVED"
            profiles.put_item(Item={"userId": sub[email], "email": email, "status": status, "createdAt": now, "updatedAt": now, **cfg["profile"]})
        print(f"  ✓ {email}")

    def token(email):
        auth = idp.initiate_auth(ClientId=out["UserPoolClientId"], AuthFlow="USER_PASSWORD_AUTH",
                                 AuthParameters={"USERNAME": email, "PASSWORD": PASSWORD})
        return auth["AuthenticationResult"]["IdToken"]

    def post(path, body, tok):
        req = urllib.request.Request(out["ApiUrl"] + path, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": tok})
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise SystemExit(f"\nAPI error {e.code} on POST {path}: {e.read().decode(errors='replace')}\n"
                             f"(this machine's UTC clock reads {iso(0)} - if that is wrong, fix the Windows clock and retry)")

    tok = token("shop@foodloop.example")
    samples = [
        dict(listingType="DISCOUNTED", productName="Fresh bread packets", category="Bakery", unit="packet", totalQuantity=100,
             originalPrice=200, discountedPrice=100, maxPerCustomer=5, saleDeadline=iso(60 * 5), collectionDeadline=iso(60 * 6),
             autoDonateRemaining=True, donationDeadline=iso(60 * 9), description="Baked this morning. Best collected before closing time."),
        dict(listingType="DISCOUNTED", productName="Rice & curry lunch packs", category="Cooked meals", unit="pack", totalQuantity=30,
             originalPrice=550, discountedPrice=275, maxPerCustomer=3, saleDeadline=iso(60 * 3), collectionDeadline=iso(60 * 4),
             autoDonateRemaining=False),
        dict(listingType="DONATION", productName="Fruit & vegetable boxes", category="Fruits & vegetables", unit="box", totalQuantity=25,
             maxPerCustomer=25, collectionDeadline=iso(60 * 8), pickupInstructions="Ask for the community donations table."),
    ]
    if args.demo_only:
        samples = []
    if args.demo or args.demo_only:
        samples.append(dict(listingType="DISCOUNTED", productName="DEMO: end-of-day pastries", category="Bakery", unit="box", totalQuantity=20,
                            originalPrice=800, discountedPrice=400, maxPerCustomer=20, saleDeadline=iso(2), collectionDeadline=iso(3),
                            autoDonateRemaining=True, donationDeadline=iso(6)))
    for body in samples:
        res = post("/listings", body, tok)
        print(f"  ✓ listing {res['listing']['listingId']}  {body['productName']}")

    print(f"\nOpen {out['SiteUrl']}\nDemo logins (password: {PASSWORD}):\n  " + "\n  ".join(USERS))


if __name__ == "__main__":
    main()
