<!--
DRAFT for the AWS Builder Center article. Before publishing:
1. Reconcile the TITLE prefix, TAG and required sections with the OFFICIAL challenge page (not confirmed when this was written).
2. Replace every [bracket]. Add real screenshots, the demo video and the live URL. Do not publish unverified claims.
3. Keep it honest: describe what you actually deployed and tested.
-->

# Weekend Challenge: No Pipeline, No Problem: FoodLoop - Buy Smart. Share Surplus. Waste Less.

**Live app:** [CloudFront URL] · **Code:** https://github.com/nimeshayasith/FoodLoop · **Demo video:** [link]

## Vision & what the app does
In Sri Lanka, rising food prices sit side by side with perfectly good food that bakeries, supermarkets and restaurants cannot sell
before closing time. Charities and community kitchens, meanwhile, rely on irregular donations. FoodLoop connects the two problems
through one serverless platform.

Stores publish surplus in two ways:
- **Smart Deals** - discounted food with a sale deadline (for example 100 bread packets at LKR 100 instead of LKR 200). Shoppers reserve online and pay at the store.
- **Free Donations** - food offered to verified charities and community groups.

The feature I am proudest of is **automatic discount-to-donation conversion**. A store can opt in when it publishes a deal.
When the sale deadline passes, FoodLoop checks what is left and, if the food is still safe to collect, converts the remaining stock
into a free donation that charities can reserve - without anyone watching a clock.

## How I built it
Everything is serverless and defined in a single AWS SAM template, deployed by hand with the SAM CLI - no CI/CD pipeline.

| Service | Role in FoodLoop |
|---|---|
| Amazon S3 + CloudFront | React web app and private food photos served over CloudFront |
| Amazon API Gateway (HTTP API) | REST API with a Cognito JWT authorizer and throttling |
| AWS Lambda (Python) | Listings, reservations, pickup verification, admin approvals and the workflow steps |
| Amazon DynamoDB | Listings, reservations, profiles and impact counters |
| AWS Step Functions | One workflow per listing that waits for deadlines, checks stock, converts and expires |
| Amazon Cognito | Sign-up, sign-in and an `admin` group |

[Insert architecture diagram - see docs/ARCHITECTURE.md]

**The lifecycle workflow.** When a store creates a listing, a Lambda writes it to DynamoDB and starts a Step Functions Standard
execution named after the listing. The workflow waits until the sale deadline, calls a Lambda to check the remaining quantity,
and - if the store opted in and the stock is still eligible - calls another Lambda to convert the leftovers into a donation, waits for the final
collection deadline, and closes the listing. No server polls anything, and a Lambda never sits idle waiting for a timestamp.

[Insert screenshot of the Step Functions execution graph]

## Key decisions & challenges
- **No overselling.** Two shoppers can tap "reserve" for the last packets at the same moment. A reservation is a DynamoDB transaction that
  decrements stock only if enough is left and the listing is still open, and creates the reservation in the same atomic step.
  I tested the guarantee by simulating a stale read - the pre-check passes, and the transaction condition still blocks the sale.
- **Don't close listings with DynamoDB TTL.** TTL deletes are asynchronous and can lag, so the workflow owns the business state and TTL is not used for correctness.
- **Food safety first.** Every collection and donation deadline must be before the item's best-before time, and conversion is re-checked at run time.
- **Trust.** Businesses and charities are verified by an admin before they can publish or reserve donations (the challenge demo auto-approves so judges can test freely).
- **Direct uploads.** Photos go from the browser straight to S3 using a presigned POST policy that fixes the key, type and size, so large files never pass through Lambda.
- **Cost-aware.** Pay-per-request DynamoDB, arm64 Lambda and a static frontend keep a pilot well inside the AWS Free Tier. [Add real cost numbers if you measured them]
- [Add one real problem you hit while deploying and how you fixed it.]

## Built for Sri Lanka
Prices are in LKR, shoppers filter by the 25 districts, times are shown in Sri Lanka time, the UI can switch between English, Sinhala and Tamil,
and stores and customers reach each other through WhatsApp links - no SMS gateway needed for the first pilot. Payment happens at the store, which avoids a payment
integration for the first version. The demo stores are fictional; FoodLoop is not affiliated with any retailer.

## What I tested
The backend has 37 automated tests covering validation, role rules, pickup codes, the no-oversell guarantee and the full discount-to-donation lifecycle; the
state machine definition was validated, and the template passes `sam validate --lint`. [Add what you verified on the live deployment.]

## What's next
A pilot with a few independent bakeries and one community kitchen, native-speaker review of the Sinhala and Tamil text, local payment options,
reminders for pickups, and a better matching algorithm that notifies nearby charities the moment a donation appears.

**Try it:** [URL] - demo logins are listed in the README. **Code:** https://github.com/nimeshayasith/FoodLoop
