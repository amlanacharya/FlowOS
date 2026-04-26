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

9. Member addition workflow defaults:
- Member addition must include membership plan selection
- New member should be created with default status `active`
- Invoice must be auto-created during member addition flow
- Member, plan, and status details remain editable after creation

10. Pause/Resume operational requirements:
- Pause action must capture `pause_date`
- Resume action must capture `resume_date`
- Pause/resume events must be recorded in membership tracking history via FK linkage
- Total paused days must be calculated from history
- During renewal flow, paused-days impact must be visible in a popup with selected plan details

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

5. Member onboarding transaction:
- Add-member flow is transactional: create member (active), create subscription, create invoice
- If any step fails, the operation should rollback and return a clear validation/business error

6. Reminder operational UX:
- Priority queue ordered as: T+1, T, T-1, T-2, T-3
- Keep checklist and action logs (called, message sent, no response, paid)

7. Compliance and risk:
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

6. New SubscriptionPauseHistory model (required):
- `id`, `member_id`, `subscription_id`, `branch_id`
- `pause_date` (required), `resume_date` (nullable until resumed)
- `pause_days` (derived on resume and stored for reporting consistency)
- `reason`, `created_by_staff_id`, timestamps
- FK to `member_subscriptions.id` to maintain a complete pause timeline per subscription

7. MemberSubscription enhancements:
- `total_pause_days` (aggregate of related pause history)
- optional `last_pause_date`, `last_resume_date` (denormalized convenience fields)

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

6. `subscription_service.py` pause/resume expansion:
- pause API requires explicit `pause_date`
- resume API requires explicit `resume_date`
- creates/updates `subscription_pause_history` records
- recalculates and persists `member_subscriptions.total_pause_days`
- adjusts effective subscription end-date policy as defined by business rules

### API/router changes

Update:
- `app/routers/members.py`
- `app/routers/subscriptions.py`
- `app/routers/payments.py`

Add:
- `app/routers/invoices.py`
- `app/routers/membership_tracking.py`
- `app/routers/reminders.py`

Pause/Resume route contract updates:
- `POST /api/v1/subscriptions/{sub_id}/pause` accepts `pause_date` and reason
- `POST /api/v1/subscriptions/{sub_id}/resume` accepts `resume_date`
- add list endpoint for pause history under membership tracking for timeline view

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
- add component: `PauseResumeModal` (date inputs + history preview)
- add component: `RenewalImpactPopup` (selected plan + paused-days summary + payable calculation)

## Implementation phases

Phase 1: Data contracts and migrations
- enums, models, schemas, Alembic migration
- add `subscription_pause_history` table + FK constraints
- add `total_pause_days` to `member_subscriptions`

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
3. Member creation requires plan selection and defaults member status to `active`.
4. Front desk can find member by phone/name and settle an outstanding invoice.
5. Reminder queue correctly lists T-3, T-2, T-1, T, T+1 members.
6. Pause/resume and day adjustments are available from membership tracking page.
7. Blacklisted/terminated members are visible with controlled actions.
8. Pause requires pause date, resume requires resume date, and both are captured in pause history.
9. Renewal popup shows selected plan and pause-history impact before final renewal action.

## Notes

- This spec captures product planning decisions from owner feedback session on 2026-04-25.
- WhatsApp/SMS delivery is intentionally deferred; reminder data model and API are prepared first.

## Implementation status on `prem-dev-25thApr`

Implemented in current branch:
- Member onboarding now requires plan selection, defaults status to `active`, and creates subscription + invoice.
- New invoice model, listing API, and payment-to-invoice reconciliation flow.
- Membership tracking page with:
- pause (pause date + reason), resume (resume date), pause history timeline
- renewal popup with selectable plan and renewal invoice creation
- reminder checklist panel for T-3, T-2, T-1, T, T+1
- manual day adjustments (`+/- days`) with adjustment history
- Pause history is persisted in `subscription_pause_history` and total pause days are tracked on subscription.

Pending / next-phase:
- Reminder action logging states (called/message sent/no response/paid).
- Automated WhatsApp/SMS reminder delivery integration.
- Additional reporting widgets for adjustment trends and renewal pipeline conversion.
