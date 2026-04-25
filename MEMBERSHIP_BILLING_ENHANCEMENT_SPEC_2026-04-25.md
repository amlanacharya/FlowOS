# FlowOS Membership and Billing Enhancement Spec

Date: 2026-04-25
Branch: Prem-Dev-25thAPR
Owner context: Gym operations and front-desk workflow

## Scope from feedback

1. Member add flow needs richer details:
- Aadhaar number
- PAN number
- Membership plan at onboarding

2. Payment records need operational lookup:
- Member search by phone number or name
- Invoice number based reconciliation

3. Membership plans to support:
- Monthly
- Quarterly
- Half-yearly
- Annually
- Lifetime

4. Pricing rule:
- Registration charge INR 1000 only for new monthly member addition
- No registration charge for renewals

5. Dedicated membership tracking page:
- Renewal workflow
- Pause/Resume flow
- Add/Subtract extra days

6. Membership statuses:
- Active
- Inactive
- Terminated
- Blacklisted

7. Reminder flow:
- T-3, T-2, T-1, T, T+1
- Popup/list and checklist view for last-week memberships
- Future channels: WhatsApp, SMS

8. Invoice/payment behavior:
- On member + plan assignment: auto-create invoice
- On renewal: create renewal record + invoice
- Payment recording reconciles outstanding uncleared invoices (or from phone/member search)

## Current-state assessment

Existing foundation in codebase:
- Plans, subscriptions, renew, pause, resume APIs exist.
- Payments API exists with summary.
- Notifications framework exists (stub/webpush/whatsapp provider structure).
- Dashboard includes renewals-due metric.

Major gaps:
- No first-class invoice entity and invoice lifecycle.
- No reminder scheduler with checkpoint semantics (T-3...T+1).
- Member schema lacks Aadhaar/PAN fields.
- Member status enum does not currently include terminated/blacklisted.
- No dedicated membership tracking UI page with renewal checklist and day adjustments.

## Product and business design decisions

1. Add invoice domain model with status lifecycle:
- draft, issued, partial, paid, overdue, void

2. Add billing event types:
- new_join, renewal, addon, adjustment

3. Enforce pricing policy:
- Registration fee applies only when plan_type == monthly and membership is first-time join
- Registration fee excluded for all renewals

4. Renewal operations:
- Renewal always creates a new billable event and invoice
- Payment posting must reconcile against selected invoice or oldest outstanding by policy

5. Reminder operational UX:
- Priority queue ordered as: T+1, T, T-1, T-2, T-3
- Keep checklist and action logs (called, message sent, no response, paid)

6. Compliance and risk:
- Store Aadhaar/PAN securely (mask in UI, restrict role visibility)

## Proposed architecture changes

### Data model changes

1. Member:
- add `aadhaar_no` (nullable, unique optional)
- add `pan_no` (nullable, unique optional)
- extend status enum to include `terminated`, `blacklisted`

2. New Invoice model:
- `id`, `invoice_no`, `branch_id`, `member_id`, `subscription_id`
- `invoice_type` (new_join/renewal/addon/adjustment)
- `subtotal`, `registration_fee`, `discount`, `tax`, `total_amount`
- `due_date`, `status`
- `notes`, `created_by_staff_id`, timestamps

3. New MembershipAdjustment model:
- `id`, `member_id`, `subscription_id`, `days_delta` (+/-), `reason`
- `approved_by_staff_id`, timestamps

4. New ReminderTask (or ReminderLog) model:
- `id`, `member_id`, `subscription_id`
- `checkpoint_day` (-3,-2,-1,0,+1)
- `scheduled_for`, `status`, `channel`, `action_note`, timestamps

5. Payment linkage:
- add `invoice_id` reference for direct reconciliation

### Service layer changes

1. `invoice_service.py` (new):
- create invoice with policy rules
- list/search outstanding invoices
- apply payment and move status

2. `subscription_service.py`:
- on create/renew trigger invoice creation
- maintain renewal cycle consistency

3. `payment_service.py`:
- reconcile payment to invoice
- enforce outstanding balance updates

4. `reminder_service.py` (new):
- generate T-3..T+1 tasks
- list action checklist for membership last week
- later trigger WhatsApp/SMS providers

5. `member_service.py`:
- handle KYC fields
- blacklist/terminate flows

### API/router changes

Update:
- `app/routers/members.py`
- `app/routers/subscriptions.py`
- `app/routers/payments.py`

Add:
- `app/routers/invoices.py`
- `app/routers/membership_tracking.py`
- `app/routers/reminders.py`

### Frontend changes

Update:
- `web/src/pages/MembersPage.tsx` (enhanced member add + plan/invoice start)
- `web/src/pages/PaymentsPage.tsx` (phone/name lookup + invoice no + reconciliation)
- `web/src/types.ts`
- `web/src/api.ts`
- `web/src/components/Sidebar.tsx` (new nav entries)

Add:
- `web/src/pages/MembershipTrackingPage.tsx`
- optional components: `InvoiceDrawer`, `RenewalChecklist`, `MemberLookupInput`, `AdjustmentModal`

## Implementation phases

Phase 1: Data contracts and migrations
- enums, models, schemas, Alembic migration

Phase 2: Invoice and reconciliation backend
- invoice service/router, payment reconciliation

Phase 3: Renewal/reminder workflow backend
- reminder tasks, checklist APIs, renewal event completeness

Phase 4: Frontend operational screens
- membership tracking page + enhanced payments/member flow

Phase 5: KPI and reporting
- overdue and renewal pipeline widgets

## Acceptance criteria (high level)

1. Adding a new monthly member creates invoice including registration fee.
2. Renewal creates invoice with zero registration fee.
3. Front desk can find member by phone/name and settle an outstanding invoice.
4. Reminder queue correctly lists T-3, T-2, T-1, T, T+1 members.
5. Pause/resume and day adjustments are available from membership tracking page.
6. Blacklisted/terminated members are visible with controlled actions.

## Notes

- This spec captures product planning decisions from owner feedback session on 2026-04-25.
- WhatsApp/SMS delivery is intentionally deferred; reminder data model and API are prepared first.
