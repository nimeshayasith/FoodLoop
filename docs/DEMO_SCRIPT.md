# 3-minute demo script

Goal: tell a story, not a tour of services. Record in segments and edit; the 2-3 minute waits for the workflow are cut with a jump-cut
(show the countdown, cut, show the result). Rehearse once end-to-end first.

## Before recording (10 min)
1. Deployed + seeded (`./scripts/seed.py --demo`). Have four browser profiles/windows: store, customer, charity, and the **Step Functions console** (state machine -> Executions).
2. Language set to English; browser zoom 110%; hide bookmarks; use a phone-width window for one shot to show mobile.
3. A fresh short-timer listing is the star: create it on camera with **⚡ Demo timings (2 / 3 / 6 min)**.

## Script
| Time | Scene | Say / show |
|---|---|---|
| 0:00-0:25 | **Problem** | Photo or shot of a bakery counter at closing time. "Every evening, good food is thrown away while families struggle with food prices and charities wait for donations." Show the FoodLoop landing page and tagline. |
| 0:25-0:55 | **Store publishes** | Store dashboard -> New listing: "Bread packets", 100 units, LKR 200 -> LKR 100, upload a photo, tick **Donate unsold items automatically**, click **Demo timings**, publish. Show it appear on the dashboard. |
| 0:55-1:25 | **Customer reserves** | Customer window (mobile width): browse, filter by Colombo, open the deal, reserve 60 (or 8 for a short demo) -> big pickup code. Back on the store dashboard, remaining stock dropped. Mention "DynamoDB transaction: it can never oversell". |
| 1:25-2:10 | **Step Functions** | Console -> Executions -> the running execution graph, paused on *Wait for sale deadline*. Jump-cut to the deadline: graph highlights CheckInventory -> ConvertToDonation. Open the DynamoDB item (or dashboard) and show `listingType: DONATION`, price 0, "converted" badge. |
| 2:10-2:35 | **Charity reserves** | Charity window: Browse -> Free donation tab shows the converted listing -> reserve all leftover. Then store verifies a pickup code on the dashboard: "Hand over 8 x ..."; landing page impact counters tick up. |
| 2:35-3:00 | **Architecture + close** | Show the diagram: CloudFront/S3, API Gateway, Lambda, DynamoDB, Step Functions, Cognito, one SAM template, no servers, no pipeline. "FoodLoop turns a manual surplus-food process into an automated, event-driven workflow. Built for Sri Lanka, ready for a pilot." |

## Tips
- If a take fails, re-seed with `--demo` for a fresh 2-minute timer instead of waiting.
- Keep the narration to what the judges score: innovation (auto conversion), craft (no oversell, tests, IaC), impact (Sri Lanka), story (end-to-end).
- Do not name real companies as partners.
