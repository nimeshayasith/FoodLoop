# Smoke test report - live deployment

- **Site:** https://de9dfsc26bz0s.cloudfront.net (stack `foodloop`, region `ap-south-1`)
- **Run:** Mon 16 Nov 2026, about 15:00-15:30 Sri Lanka time
- **How:** scripted headless Chrome (private contexts, one per role) plus `curl` against the API. Screenshots are in [`screenshots/`](screenshots/).
- **Backend tests on the same day:** `pytest -q` -> **37 passed**.

## Results

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Home page loads, counters show | PASS | `01-home-en.png` |
| 2 | Browse lists seeded items; search / type filter work | PASS | `02-browse-en.png`, `07-browse-search-bread.png`, `07b-browse-free-donations.png` |
| 3 | Language switch English / Sinhala / Tamil | PASS (UI text switches; see note 4) | `03-browse-sinhala.png`, `04-browse-tamil.png` |
| 4 | Mobile layout (390 px) | PASS | `05-browse-mobile.png` |
| 5 | Customer signs in, reserves 2 bread packets | PASS - stock **100 -> 98**, pickup code `FL-V45YK` shown | `08`, `09`, `10`, `11` |
| 6 | Shop dashboard shows the reservation | PASS - "Saman Fernando (customer) - 2, RESERVED" | `13`, `14` |
| 7 | Shop verifies the pickup code | PASS - "Hand over 2 x Fresh bread packets to Saman Fernando" | `15` |
| 8 | Same code verified a second time | PASS (correctly refused) - HTTP 409 "Already collected" | `15b` |
| 9 | Customer on a free-donation listing | PASS - "Donations are only for verified charities and community groups" | `12` |
| 10 | Same rule enforced by the API, not just the UI | PASS - customer token: reserve donation **403**, create listing **403**, verify pickup **403**, admin **403**; no token **401** | curl output |
| 11 | Charity reserves free fruit & vegetable boxes | PASS - code issued | `21` |
| 12 | Shop creates a listing with a photo | PASS - image uploaded to S3 and served at `/images/...` through CloudFront (image decoded in the page) | `16`, `17`, `18` |
| 13 | Step Functions runs one execution per listing | PASS - 11 executions listed, one per listing | `aws stepfunctions list-executions` (take a console screenshot too) |
| 14 | 2-minute demo listing converts to a donation by itself | PASS - see timeline below | `19` |
| 15 | Charity reserves the converted donation | PASS - 8 of 20 | `19`, `20` |
| 16 | New account sign-up (UI -> Cognito) | PARTIAL - see note 1 | `23`, `24`, `25`, `26` |
| 17 | Home impact counters rise after a pickup | PASS - items rescued 2, saved LKR 200 | `22` |

### Step Functions timeline (listing `LSTF2BCB082E0`, "Smoke-test buns (demo)")
Times are Sri Lanka time (UTC+5:30), from `aws stepfunctions get-execution-history`.

| Time | Event |
|---|---|
| 15:19:57 | Execution starts when the shop publishes; enters *Wait until saleDeadline* |
| 15:21:01 | Sale deadline reached; `CheckInventory` runs (1.1 s) |
| 15:21:02 | Stock left and opt-in true -> `ConvertToDonation` runs (1.3 s) |
| 15:21:03 | Listing is now `DONATION`, price 0, `convertedFromDiscount = true`; enters *Wait until donationDeadline* |
| 15:25:01 | `ExpireListing` runs; execution **SUCCEEDED** (total 5 min 4 s) |

Final DynamoDB item: `status = EXPIRED`, `listingType = DONATION`, `availableQuantity = 12`, `unclaimedQuantity = 12`
(20 listed, 8 reserved by the charity, 12 left over).

## Notes and findings

1. **Sign-up was not fully tested.** I did not use your personal email. I signed up a throwaway address
   (`smoketest-...@foodloop.example`) through the real UI, which showed "We emailed you a 6-digit code", then confirmed the user with
   `aws cognito-idp admin-confirm-sign-up`, signed in and saved a profile. **Still to do by you:** one sign-up with a real inbox to prove the
   email code arrives (Cognito's default sender has a small daily quota). The throwaway user (see `smoketest-1794822844@foodloop.example`) should be deleted from the user
   pool; the delete command was blocked by a safety check in my session, so please run
   `aws cognito-idp admin-delete-user --user-pool-id ap-south-1_z8UPioORR --username smoketest-1794822844@foodloop.example --region ap-south-1`.
   Its profile row (name "Smoke Tester") can also be removed from the Profiles table.
2. **Clock skew affects the "Demo timings" button.** The button computes deadlines from the *browser's* clock. This PC was about **103 seconds behind AWS**, so a "2-minute"
   sale would really last about 15 seconds. For my test I shifted the browser clock to AWS time. Before recording the video, check the PC clock (Windows -> Settings -> Time -> Sync now)
   or the demo will look rushed. A durable fix is to compute the demo times from the server `Date` header.
3. **Duplicate seed data.** Each demo product appears three times in Browse because the seed script ran several times (three copies of rice, bread and fruit boxes, plus 3 executions each).
   Harmless, but it looks untidy in screenshots and the video. Optionally clean the table and re-run `seed.py --demo-only` once.
4. **Sinhala / Tamil:** menu, filters and labels switch language, but product names, store names and the countdown text ("1h 24m") stay in English. Native-speaker review is still pending (as in `CLAUDE.md`).
5. **"Items donated to charities" stays at 0** until a charity's pickup is verified by the shop; reserving alone does not count. This is by design but may confuse a viewer of the video, so verify one charity pickup on camera.
6. **Slow connection on the test PC.** Some calls took 2-12 seconds from this PC (a TLS handshake once took 10 s); server-side Lambda calls were fast. Judges on a slow link will see a "Loading..." state for a few seconds; the app handled it without errors.

## Not covered (needs you)
- **AWS Console screenshots** (Step Functions graph, DynamoDB items, CloudFormation resources): see [`AWS_CONSOLE_SCREENSHOTS.md`](AWS_CONSOLE_SCREENSHOTS.md).
- Real-email sign-up (note 1), a test on a real phone, and the admin approval screen (the stack runs with `AutoApproveOrgs=true`).
