# AWS Console screenshots to capture

I could not take these: they need your signed-in AWS Console session. Region for everything: **Asia Pacific (Mumbai) `ap-south-1`**.
Save each file in `docs/screenshots/` with the name below, and the article already points to them.
Tip: use the browser zoom at 90%, hide bookmarks, and crop out the account ID in the top-right corner if you do not want it public.

| File name | Where to click | What it proves |
|---|---|---|
| `aws-01-cloudformation-stack.png` | CloudFormation -> Stacks -> `foodloop` -> **Resources** tab | One SAM template created everything (state `CREATE_COMPLETE`) |
| `aws-02-stepfunctions-executions.png` | Step Functions -> State machines -> `ListingLifecycleStateMachine-...` -> **Executions** | One execution per listing, most are *Running* (waiting for a deadline) |
| `aws-03-stepfunctions-graph-waiting.png` | Open a **Running** execution (for example `LST04ECFC1659`) -> graph view | The workflow sleeping in *Wait until sale deadline*, with no server running |
| `aws-04-stepfunctions-graph-converted.png` | Open execution **`LSTF2BCB082E0`** (Succeeded) -> graph view | The finished path: Wait -> CheckInventory -> ConvertToDonation -> Wait -> ExpireListing, all green |
| `aws-05-stepfunctions-event-history.png` | Same execution -> **Event history** (timestamps visible) | Conversion happened about one second after the sale deadline |
| `aws-06-dynamodb-listing-item.png` | DynamoDB -> Tables -> `foodloop-ListingsTable-...` -> Explore items -> `LSTF2BCB082E0` | Item after conversion: `listingType = DONATION`, `convertedFromDiscount = true`, `status = EXPIRED`, `unclaimedQuantity = 12` |
| `aws-07-dynamodb-reservations.png` | DynamoDB -> `foodloop-ReservationsTable-...` -> Explore items | Reservation rows with pickup codes and `COLLECTED` / `RESERVED` status |
| `aws-08-lambda-functions.png` | Lambda -> Functions (search `foodloop`) | The 15 Python functions, runtime `python3.13`, architecture arm64 |
| `aws-09-apigateway-routes.png` | API Gateway -> the HTTP API -> **Routes** | Public vs JWT-protected routes |
| `aws-10-cognito-users.png` | Cognito -> User pools -> `ap-south-1_z8UPioORR` -> Users | The demo users and groups (hide real email addresses) |
| `aws-11-cloudfront-s3.png` | CloudFront -> distribution `E1TOQNV3ZYSY4E` -> Origins | Web app and `/images/*` served privately from S3 through CloudFront |

## Optional extras
- `aws-12-cloudwatch-lambda-logs.png`: CloudWatch -> Log groups -> the `ConvertToDonation` function log around 09:51 UTC (15:21 Sri Lanka time).
- `aws-13-billing-free-tier.png`: Billing -> Free Tier page, to back up any cost claim in the article.
- `aws-14-sam-deploy-terminal.png`: a screenshot of the terminal after `./scripts/deploy.sh` finishes.

## Before you capture the "waiting" graph
The old demo executions are stale. For a fresh graph, create a new listing with **Demo timings** (after syncing the PC clock - see
[`SMOKE_TEST_REPORT.md`](SMOKE_TEST_REPORT.md), note 2) and take `aws-03` straight away, then `aws-04` about 6 minutes later.
