# Taking FoodLoop to the real world in Sri Lanka

This is a practical plan, not legal advice. Items marked **(confirm)** must be checked with a lawyer or the relevant authority before launch.

## 1. Start with a tiny, honest pilot
- 2-3 independent bakeries or restaurants in **one** district (Colombo/Gampaha or Kandy) + 1-2 community kitchens or charities you can visit in person.
- Fictional demo stores stay fictional. Approach real businesses (including large retailers) only with their permission and never claim a partnership you do not have.
- Run it for 4-6 weeks. Track: items listed, items collected, items converted to donations, no-show rate, rupees saved, charity pickups, time to list (should be under a minute).

## 2. Verification and trust
- Deploy with `AUTO_APPROVE_ORGS=false`. Verify businesses (business registration, visit or call) and charities (registration number, a referee) in the Admin page.
- Keep an audit trail: approvals store the reviewer and time. Consider a "report a problem" link and a way to suspend an organisation.

## 3. Food safety and liability **(confirm)**
- Check obligations under Sri Lanka's Food Act (No. 26 of 1980) and guidance from the Ministry of Health / public health inspectors for selling and donating surplus food.
- The app already blocks deadlines after the best-before / use-by time, but stores remain responsible for storage, labelling and allergen information.
- Write simple Terms: stores are responsible for food safety; charities responsible for redistribution; customers collect at their own discretion. Ask a lawyer about donor liability and consumer-protection rules (Consumer Affairs Authority).

## 4. Privacy **(confirm)**
- FoodLoop stores names, phone numbers and emails. Review the Personal Data Protection Act (No. 9 of 2022) requirements: privacy notice, purpose limitation, retention, and data-subject requests.
- Store staff only see customer names/phones for their own listings; pickup codes are never listed to stores.

## 5. Language and access
- Have native speakers review the Sinhala and Tamil strings; extend translation to the business and charity screens.
- Keep the app light: it is a small static bundle and works on low-bandwidth mobile connections. Add a simple PWA install prompt later.
- WhatsApp links already work without an SMS gateway; add pickup reminders by SMS/WhatsApp when volume justifies the cost.

## 6. Payments
- Pilot with pay-at-store (no payment integration). Later evaluate Sri Lankan payment options (e.g. local card gateways and LankaQR) **(confirm availability and fees)**.

## 7. Operations and cost
- Set an AWS Budget alert. A pilot should sit in the Free Tier; check the Billing console weekly.
- Add a custom domain + ACM certificate on CloudFront, a Cognito email sender via SES, CloudWatch alarms on Lambda errors, and a log retention policy.
- Back-ups: DynamoDB point-in-time recovery is already enabled on the core tables.

## 8. Roadmap ideas
1. Notify nearby verified charities the moment a donation appears.
2. Map view and "near me" distance sorting.
3. Recycle no-show reservations back into stock automatically.
4. Store-side analytics (waste avoided per week) to help retailers report on sustainability.
5. Multi-region disaster recovery only if the pilot scales.
