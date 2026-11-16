# FoodLoop - project documentation

*Buy Smart. Share Surplus. Waste Less.*

| | |
|---|---|
| Live site | https://de9dfsc26bz0s.cloudfront.net |
| Code | https://github.com/nimeshayasith/FoodLoop |
| Region / stack | `ap-south-1` (Mumbai) / `foodloop` |
| Built for | AWS Builder Center weekend challenge "No Pipeline, No Problem" |

## 1. Overview
FoodLoop connects supermarkets, bakeries, restaurants and producers in Sri Lanka with shoppers and charities. Stores list surplus food as a discounted
**Smart Deal** or a free **Donation**. When a Smart Deal's sale ends, an **AWS Step Functions** workflow converts unsold stock into a free donation for verified charities.
It is fully serverless and deployed by hand with the SAM CLI (no CI/CD pipeline).

## 2. Users and what they can do
| Role | Can | Cannot |
|---|---|---|
| Visitor (not signed in) | Browse listings, see impact counters | Reserve |
| `CUSTOMER` | Reserve Smart Deals (max per customer), see pickup codes, cancel | Reserve donations, publish |
| `CHARITY` | Reserve free donations and deals | Publish |
| `BUSINESS` (approved) | Publish listings (with photo), see reservations, verify pickup codes | Reserve |
| `admin` (Cognito group) | Approve / reject businesses and charities | - |

Role and approval status live in the **Profiles** table and are decided on the server, never taken from the request.

## 3. Using the app (screenshots in [`screenshots/`](screenshots/))
1. **Browse** (`02-browse-en.png`): filter by type, district, category or search text.
2. **Reserve** (`08`, `10`): open a listing, choose a quantity, get a pickup code such as `FL-V45YK`. Pay at the store for deals; donations are free.
3. **Store dashboard** (`13`, `14`): see every listing with Total / Left / Reserved / Collected, and who reserved.
4. **Verify a pickup** (`15`): type the customer's code; the app says "Hand over 2 x Fresh bread packets to ...". A code works once.
5. **New listing** (`16`): choose Smart Deal or Donation, set deadlines, upload a photo (JPG/PNG/WebP, 3 MB max), optionally tick
   **Donate unsold items automatically**. The **Demo timings** button sets 2 / 3 / 6 minutes for demonstrations.
6. **Language**: English, Sinhala, Tamil from the menu (`03`, `04`).

### Listing life cycle
`ACTIVE` (Smart Deal, sale open) -> *sale ends* -> if stock left and opted in: `DONATION` (price 0, "converted") -> `EXPIRED`. Otherwise `ACTIVE` -> `EXPIRED` at the
collection deadline. On expiry, uncollected reservations become `NO_SHOW` and `unclaimedQuantity` is recorded. Rules: deadlines can never be after best-before; the public API hides listings past their reserve deadline even if a workflow is late.
Diagram and eligibility rules: [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 4. Architecture summary
S3 + CloudFront (website and private photos) · API Gateway HTTP API with Cognito JWT authorizer · Lambda (Python 3.13, arm64, 15 functions, least-privilege IAM per function) ·
DynamoDB (Listings, Reservations, Profiles, Impact) · Step Functions Standard (one execution per listing) · Cognito (users, `admin` group).
Full diagram, data model and security notes: [`ARCHITECTURE.md`](ARCHITECTURE.md).

### API
| Method and path | Who |
|---|---|
| GET `/listings`, `/listings/{id}`, `/stats` | public |
| GET / PUT `/me` | signed in |
| POST `/listings/{id}/reserve`, GET `/me/reservations`, POST `/reservations/{id}/cancel` | customer / charity |
| POST `/uploads/presign`, POST `/listings`, GET `/org/listings`, GET `/org/listings/{id}/reservations`, POST `/pickup/verify` | approved business |
| GET `/admin/profiles`, POST `/admin/profiles/{userId}/decision` | `admin` group |

Errors are JSON `{"error": "<code>", "message": "..."}`: 401 no/invalid token, 403 wrong role (`wrong_role`, `charity_only`, `admin_only`), 409 conflict (for example "Already collected").

## 5. Design rules the code must keep
No oversell (reserve / cancel / pickup are DynamoDB transactions) · identity only from the JWT · UTC timestamps `YYYY-MM-DDTHH:MM:SSZ` ·
workflow Lambdas are idempotent · food-safety guard (no deadline after best-before) · serverless only, no pipeline · least-privilege IAM ·
never use DynamoDB TTL to close listings. The full list is in section 4 of [`CLAUDE.md`](../CLAUDE.md).

## 6. Set up, deploy, operate
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q                          # 37 passed
sam validate --lint
./scripts/deploy.sh                # build, deploy, upload site, invalidate CloudFront; prints SiteUrl
python scripts/seed.py --stack foodloop --region ap-south-1 --demo
./scripts/make-admin.sh you@example.com
./scripts/teardown.sh              # delete everything, stops all cost
```
Windows: use Git Bash for `deploy.sh`; run the seed script with `python`. Useful commands: `sam logs -n ReserveListingFunction --stack-name foodloop --tail`,
`aws stepfunctions list-executions --state-machine-arn <StateMachineArn output>`.

**Demo accounts** (created by the seed script; demo only, never use in production): `customer@`, `shop@`, `charity@`, `admin@foodloop.example`. The password is printed by the script and defined at the top of `scripts/seed.py`.

## 7. Test evidence
| What | Result |
|---|---|
| Backend unit / integration tests | **37 passed** (moto: DynamoDB, S3, Step Functions) |
| `sam validate --lint` | valid |
| Live smoke test (16 Nov 2026) | 16 of 17 checks pass, sign-up partially tested: [`SMOKE_TEST_REPORT.md`](SMOKE_TEST_REPORT.md) |
| Live workflow run | 2-minute listing converted about 1 s after the deadline; execution succeeded in 5 min 4 s |

## 8. Known limitations
No online payments (pay at store) · table scan on the admin listing and in-memory filtering suit a pilot, not national scale · no-shows are not re-released ·
Sinhala / Tamil are drafts and cover customer-facing screens · no SMS or push (WhatsApp links instead) · single region, default CloudFront domain, no WAF ·
the **Demo timings** button uses the browser clock, so check the PC clock first (see the smoke test report).

## 9. Real-world rollout
Food-safety terms, privacy, charity verification and a pilot plan: [`ROLLOUT_SRI_LANKA.md`](ROLLOUT_SRI_LANKA.md).
Redeploy with `AUTO_APPROVE_ORGS=false` before inviting real stores or charities.

## 10. Document index
| File | Purpose |
|---|---|
| [`ARTICLE_DRAFT.md`](ARTICLE_DRAFT.md) | Builder Center article (problem, solution, architecture, screenshots, learnings) |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Services, state machine, data model, security |
| [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) | 3-minute video script |
| [`SMOKE_TEST_REPORT.md`](SMOKE_TEST_REPORT.md) | Live test results and findings |
| [`AWS_CONSOLE_SCREENSHOTS.md`](AWS_CONSOLE_SCREENSHOTS.md) | Console screenshots you still need to capture |
| [`ROLLOUT_SRI_LANKA.md`](ROLLOUT_SRI_LANKA.md) | Pilot plan and legal / food-safety checklist |
