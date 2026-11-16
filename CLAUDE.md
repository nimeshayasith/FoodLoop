# CLAUDE.md - FoodLoop: step-by-step guide

> Read this first. It is the single source of truth for building, deploying, demoing and submitting FoodLoop.
> **Tagline:** FoodLoop - Buy Smart. Share Surplus. Waste Less.

## 0. Mission and hard deadlines

FoodLoop connects supermarkets, bakeries, restaurants and producers with shoppers and charities in **Sri Lanka**.
Stores list surplus food at a discount (**Smart Deal**) or for free (**Donation**). When a Smart Deal's sale ends,
**AWS Step Functions automatically converts unsold stock into a free donation** for verified charities.

| Item | Value |
|---|---|
| Challenge | AWS Builder Center weekend challenge **"No Pipeline, No Problem"** (Nov 13-16, 2026) |
| Rule of the theme | Serverless AWS services only: no servers, no CI/CD pipeline. We deploy by hand with the SAM CLI |
| **Deadline** | **Mon Nov 16, 2026, 1:00 PM PT = Tue Nov 17, 2:30 AM Sri Lanka time** |
| Target region | `ap-south-1` (Mumbai) - closest AWS region to Sri Lanka |
| Prizes | Check the challenge page. A Builder Center spotlight for this theme mentioned $100 in AWS credits and a Builder Backpack (unconfirmed) |

**Verify the official rules yourself** on the challenge page on builder.aws.com. Previous AWS weekend challenges required
a published Builder Center article (500+ words, a required title prefix and tag, a description of the build, screenshots or
video, and a *public* repo/link at evaluation time). The exact requirements for this challenge could not be fetched while this
repo was built, so treat step 9 as a checklist to reconcile with the official page.

## 1. Where things stand (honest status)

| Area | State |
|---|---|
| Backend (15 Lambdas, Python 3.13) | Written; **37 pytest tests pass** against moto (DynamoDB/S3/Step Functions mocks) |
| `template.yaml` (SAM) | Passes `sam validate --lint` and `cfn-lint`; `sam build` succeeds |
| Step Functions ASL | Validated with `asl-validator`; lifecycle simulated end-to-end in `tests/test_workflow.py` |
| Frontend (React + Vite + Tailwind) | Builds; rendered and checked in headless Chrome against a mock API (desktop + mobile) |
| **Real AWS deployment** | **NOT done yet.** Nobody has run `./scripts/deploy.sh` against a real account. Do step 3 now and expect to fix small things |
| Cognito email / sign-up flow | Untested against real Cognito (uses plain `fetch`, no SDK) |
| Sinhala / Tamil UI text | Draft translations - have a native speaker review before public launch |

## 2. Step-by-step plan (time-boxed for the deadline)

### Step 1 - Prerequisites (15 min)
1. An AWS account with admin-ish permissions you can use from the CLI. Check billing alerts are on.
2. Install: AWS CLI v2, **AWS SAM CLI**, Node 20+, Python 3.13 (Lambda runtime is `python3.13`; SAM builds locally).
3. `aws configure` (or SSO), then `export AWS_REGION=ap-south-1`.
4. `git clone https://github.com/nimeshayasith/FoodLoop.git && cd FoodLoop`

### Step 2 - Run the tests (5 min)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q                       # expect: 37 passed
sam validate --lint             # expect: valid SAM template
```

### Step 3 - Deploy (10-15 min; first CloudFront creation is the slow part)
```bash
./scripts/deploy.sh             # sam build + sam deploy + frontend build + S3 sync + CloudFront invalidation
```
It prints the public **SiteUrl**. By default `AutoApproveOrgs=true` so judges can register a business/charity and
try everything immediately. For real-world use deploy with `AUTO_APPROVE_ORGS=false` (see step 8).

If deploy fails, read the CloudFormation event that failed (`aws cloudformation describe-stack-events --stack-name foodloop`)
- see section 7.

### Step 4 - Seed demo data (2 min)
```bash
./scripts/seed.py --stack foodloop --region ap-south-1 --demo
```
Creates 4 demo logins (password printed by the script - **demo only**), approved profiles, 3 sample listings and one
short-timer listing (sale ends in 2 min, collection 3 min, donation 6 min) for the live Step Functions demo.
Make your own account an admin: `./scripts/make-admin.sh you@example.com`.

### Step 5 - Smoke test (15 min) - do all of these in the browser at SiteUrl
- [ ] Home page loads, impact counters show, language switch (English / සිංහල / தமிழ்) works
- [ ] Browse lists seeded items; filters (type / district / category / search) work
- [ ] Sign in as `customer@...`, reserve 2 units -> **Reservations** shows a pickup code; stock drops by 2
- [ ] Sign in as `shop@...` -> Dashboard shows the reservation; **Verify a pickup** with the code -> "Hand over..." message; home counters rise
- [ ] Sign in as `charity@...`: can reserve the donation; the customer account cannot ("verified charities only")
- [ ] New listing with a **photo upload** works and the image appears (served through CloudFront `/images/*`)
- [ ] Register a brand-new account via the UI (email code from Cognito) - this is the least-tested path
- [ ] Open the **Step Functions console -> foodloop state machine -> Executions**: one execution per listing, in "Running" (waiting)

### Step 6 - Rehearse and record the 3-minute demo (60-90 min) - see `docs/DEMO_SCRIPT.md`
Use the **⚡ Demo timings** button on the New Listing form (2 / 3 / 6 minutes) so the whole
discount -> check stock -> convert -> expire cycle happens on camera. Keep the Step Functions console graph view open in a second tab.

### Step 7 - Screenshots and architecture diagram (20 min)
Capture: landing page, browse page (mobile + desktop), dashboard, Step Functions graph mid-run and after conversion,
DynamoDB item before/after conversion. The Mermaid diagram in `docs/ARCHITECTURE.md` can be rendered for the article.

### Step 8 - Real-world hardening before showing the project to real stores (after the challenge if short on time)
- Redeploy with `AUTO_APPROVE_ORGS=false` and approve organisations in the Admin page (verify charities by registration number).
- Review the checklist in `docs/ROLLOUT_SRI_LANKA.md` (food-safety terms, privacy, native-speaker review of Sinhala/Tamil).
- Set AWS Budgets alerts; consider a CloudFront custom domain + ACM certificate and Cognito SES email sender.

### Step 9 - Write and publish the article, then submit (60 min, finish with margin before 2:30 AM LKT)
1. Start from `docs/ARTICLE_DRAFT.md`; fill every `[bracket]` (live URL, repo URL, video, screenshots). Reconcile section
   names/title/tag with the **official** challenge page.
2. Make sure the GitHub repo is **public** and the README renders.
3. Publish on AWS Builder Center before the deadline. Submit early - not in the last 30 minutes.
4. Do not imply that Cargills, Keells or any real company is a partner. Demo stores are fictional.

## 3. Architecture in one screen

```
Browser ──> CloudFront ──> S3 (React app)   and   /images/* ──> S3 (food photos, private, OAC)
   │
   ├─ Cognito (sign-up/sign-in, JWT) ─────────────────────────────┐
   └─ API Gateway (HTTP API, JWT authorizer) ──> Lambda (Python) ──> DynamoDB
                                                        │
                                                        └─ start_execution ──> Step Functions (Standard)
                                                                   ├─ Wait until saleDeadline
                                                                   ├─ Lambda CheckInventory
                                                                   ├─ Lambda ConvertToDonation  (if opted in & eligible)
                                                                   ├─ Wait until final collection deadline
                                                                   └─ Lambda ExpireListing
```
Diagrams and the data model: `docs/ARCHITECTURE.md`. Infrastructure is entirely in `template.yaml`.

### Roles
`CUSTOMER` (reserve Smart Deals) · `BUSINESS` (publish listings, verify pickups) · `CHARITY` (reserve free donations; may also reserve deals) · `admin` (Cognito group; approves organisations).
Role/status live in the **Profiles** table and are decided server-side - never from request bodies. Businesses and charities are `APPROVED`
automatically only when the stack parameter `AutoApproveOrgs=true`.

### API (HTTP API; public = no sign-in)
| Method & path | Who | Lambda |
|---|---|---|
| GET `/listings`, GET `/listings/{id}`, GET `/stats` | public | list_listings, get_listing, stats |
| GET/PUT `/me` | signed-in | profile |
| POST `/listings/{id}/reserve`, GET `/me/reservations`, POST `/reservations/{id}/cancel` | customer / charity | reserve_listing, my_reservations, cancel_reservation |
| POST `/uploads/presign`, POST `/listings`, GET `/org/listings`, GET `/org/listings/{id}/reservations`, POST `/pickup/verify` | approved business | presign_upload, create_listing, org_listings, verify_pickup |
| GET `/admin/profiles`, POST `/admin/profiles/{userId}/decision` | Cognito group `admin` | admin |
| *(called only by Step Functions)* | - | check_inventory, convert_to_donation, expire_listing |

### Tables
`Listings` (GSIs `ByStatus`, `ByOwner`) · `Reservations` (GSIs `ByUser`, `ByListing`, `ByPickupCode`) · `Profiles` · `Impact` (one counter item).

### Listing lifecycle (the heart of the project)
1. `POST /listings` writes the listing, then starts **one Step Functions execution named after the listing id**
   (if starting fails, the listing is deleted - no listing ever lacks a lifecycle).
2. DISCOUNTED: wait until `saleDeadline` -> `CheckInventory` -> if stock left **and** `autoDonateRemaining` **and** the donation
   deadline is valid and not after `bestBeforeDate` -> `ConvertToDonation` (listing becomes `DONATION`, price 0, `collectionDeadline`
   := `donationDeadline`) -> wait until that deadline -> `ExpireListing`. Otherwise wait for `collectionDeadline` -> `ExpireListing`.
3. DONATION: wait until `collectionDeadline` -> `ExpireListing`.
4. `ExpireListing` sets `EXPIRED`, records `unclaimedQuantity`, marks uncollected reservations `NO_SHOW`.
5. Safety net: the public API hides anything past its reserve deadline even if a workflow is late.

## 4. Invariants - do not break these when changing code

1. **No oversell.** Reserving is one DynamoDB `TransactWriteItems`: decrement `availableQuantity` with condition
   `>= :q AND status = ACTIVE AND deadline not passed`, plus put the reservation. Cancel and pickup are also transactions.
2. **Identity comes only from the verified JWT** (`Request.user_id`). Never trust ids/roles in request bodies.
3. **Timestamps are UTC strings `YYYY-MM-DDTHH:MM:SSZ`** (`util.ISO_FMT`). Step Functions `Wait` and lexicographic comparisons depend on it.
4. **Call `util.now_utc()` / `util.now_iso()` through the module** so tests can freeze time. Never use `datetime.now()` directly.
5. **Workflow Lambdas must be idempotent** (Step Functions retries). They use conditional updates.
6. **Food-safety guard:** no collection or donation deadline may be after `bestBeforeDate`.
7. **Reservation snapshots `pickupBy`** at reserve time; later phases never shorten a customer's window.
8. **Serverless only, no pipeline.** Do not add EC2/ECS/containers/CodePipeline/GitHub Actions deploys. Deploy = `./scripts/deploy.sh`.
9. **Least privilege:** each Lambda gets only the SAM policies it needs in `template.yaml`.
10. DynamoDB TTL must never be used to close listings (it is asynchronous and can take days).

## 5. Repository map
```
template.yaml                     all AWS infrastructure (SAM)
workflows/listing_lifecycle.asl.json   the Step Functions state machine
backend/common/                   util (time/errors), http (API wrapper), db, domain (validation + rules)
backend/handlers/                 one module per Lambda (handler = handlers.<module>.handler)
tests/                            pytest; conftest builds DynamoDB tables FROM template.yaml (no drift)
frontend/                         React + Vite + Tailwind (HashRouter; Cognito via fetch; en/si/ta)
scripts/                          deploy.sh, seed.py, make-admin.sh, teardown.sh
docs/                             ARCHITECTURE, DEMO_SCRIPT, ARTICLE_DRAFT, ROLLOUT_SRI_LANKA
```

## 6. Command cheat sheet
```bash
pytest -q                                   # backend tests
sam validate --lint && sam build            # infra check + package
./scripts/deploy.sh                         # deploy everything
STACK=foodloop-dev AWS_REGION=ap-south-1 ./scripts/deploy.sh
cd frontend && npm run dev                  # local UI (copy .env.example -> .env.local with real stack outputs)
sam logs -n ReserveListingFunction --stack-name foodloop --tail
aws stepfunctions list-executions --state-machine-arn <StateMachineArn output>
./scripts/teardown.sh                       # delete everything (stops all cost)
```

## 7. Troubleshooting
- **Deploy fails on CloudFront/OAC:** read the failing event; delete a half-created stack (`./scripts/teardown.sh` or console) and redeploy.
- **Sign-up email never arrives:** Cognito's default sender is limited (small daily quota). Use the seeded accounts for judges/demo.
- **CORS error in browser:** the API only allows the CloudFront origin and `http://localhost:5173`. Use the SiteUrl or the Vite dev server.
- **Image upload fails:** check the browser network tab for the S3 POST response; the policy allows only JPG/PNG/WebP up to 3 MB.
- **401 on every call:** the app sends the Cognito **ID token**; the authorizer audience is the app client id from the stack outputs.
- **Workflow never converts:** the listing needs `autoDonateRemaining` true, stock left, and `donationDeadline` after the sale and before best-before. Look at the execution's `CheckInventory` output `reason`.
- **Windows (Git Bash):** `deploy.sh` sets `MSYS_NO_PATHCONV=1` so CloudFront paths like `/index.html` are not rewritten. Run the seed script with `python scripts/seed.py ...` after `pip install boto3`.
- **Admin page missing:** run `./scripts/make-admin.sh <email>`, then sign out and in (the group is in the token).

## 8. Known limitations (be upfront about these in the article)
- No online payments: customers pay at the store (Smart Deals) - deliberate MVP choice. Donations are free.
- `ByStatus` GSI + in-memory filtering is fine for a pilot; at national scale shard by district/date.
- Admin listing uses a table scan (tiny table). Reservation no-shows are not re-released to other customers.
- English-first UI; Sinhala/Tamil cover customer-facing screens only and need native review. No SMS/push (WhatsApp deep links instead).
- Single region, default CloudFront domain, no WAF.

## 9. Submission checklist
- [ ] Live URL works from a private/incognito window and from a phone
- [ ] Repo is public; README has architecture + run instructions; no secrets committed (`.env*` are git-ignored)
- [ ] 3-minute video recorded (see `docs/DEMO_SCRIPT.md`) and uploaded/linked
- [ ] Article published on Builder Center with the **official** title prefix/tag and 500+ words
- [ ] Judging narrative covered: technical innovation (auto discount-to-donation via Step Functions), craft (no-oversell transactions, tests),
      impact (Sri Lanka food waste + affordability), storytelling (end-to-end demo)
- [ ] Submitted with margin **before Nov 17, 2:30 AM Sri Lanka time**
