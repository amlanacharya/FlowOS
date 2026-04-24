# FlowOS for Gyms — Separate Backend and Frontend BRD + PRD

## Document Status

* **Product:** FlowOS for Gyms
* **Focus:** Traditional gym with memberships, classes, and future multi-branch readiness
* **Current delivery target:** Single-branch POC
* **Prepared from the perspective of:** Senior Product Manager + Senior Business Analyst
* **Version:** 1.0

---

# Part A — Backend BRD

## 1. Backend Business Objective

Build a Python-based backend that acts as the single source of truth for gym operations and serves both the web application and Android application through secure, reusable APIs.

The backend must support the core business workflows of a traditional gym:

* lead capture and trial management
* member lifecycle and subscriptions
* class and attendance operations
* staff and trainer access
* payment tracking and dues visibility
* reporting and dashboard data
* single branch first, with schema and permissions ready for 2–3 branches later

## 2. Business Problem the Backend Solves

Gyms typically run operations across multiple disconnected tools:

* spreadsheets for member records and fees
* WhatsApp for follow-up and renewals
* manual attendance registers
* ad-hoc class schedules
* inconsistent staff data entry
* fragmented revenue visibility

Without a central backend, the product cannot enforce:

* data consistency
* role-based control
* membership validity rules
* class capacity rules
* branch-aware design
* consistent behavior across web and Android

## 3. Backend Stakeholders

### Primary internal stakeholders

* Backend engineers
* Mobile engineers
* Web engineers
* Product manager
* QA team

### Business stakeholders indirectly served

* gym owner
* branch manager
* front desk staff
* trainer
* member

## 4. Backend Success Criteria

The backend will be considered successful if it enables:

* a single API layer for both web and Android
* clean CRUD and workflow APIs for leads, members, payments, classes, attendance, and staff
* secure role-based access control
* consistent business rules across clients
* branch-aware data model
* scalable evolution from single branch to multi-branch without re-architecture

## 5. Backend Scope Summary

### In scope

* authentication and authorization
* branch-ready data model
* lead management APIs
* member management APIs
* membership plan and subscription APIs
* payment tracking APIs
* class and attendance APIs
* dashboard/reporting APIs
* notification trigger/logging support
* export-friendly endpoints for reporting and accounting workflows

### Out of scope for POC

* advanced workflow builder
* payroll engine
* AI recommendations
* deep accounting package integrations
* automated WhatsApp provider integration if needed can be mocked initially
* franchise hierarchy UI logic beyond branch-ready backend design

## 6. Backend Assumptions

* Web app and Android app will consume the same API contracts.
* The first deployment is for a single branch but all operational records will carry `branch_id` where appropriate.
* Payments can be manually recorded in the first release.
* Notification delivery may start with a simple service/logging layer and integrate with external providers later.

---

# Part B — Backend PRD

## 1. Backend Product Goal

Create a robust, maintainable, API-first Python backend that powers gym operations for both web and Android clients.

## 2. Recommended Technology Direction

* **Language:** Python
* **Framework:** FastAPI
* **Database:** PostgreSQL
* **ORM / modeling:** SQLAlchemy or SQLModel
* **Migrations:** Alembic
* **Auth:** JWT-based session/auth model
* **API style:** REST-first

## 3. Backend Functional Scope

## 3.1 Authentication and Authorization

### Requirements

* Staff users shall be able to log in securely.
* Role-based access shall be enforced.
* Roles shall include at minimum:

  * owner
  * branch_manager
  * front_desk
  * trainer
  * member (optional for POC if self-service included later)
* The system shall support branch-scoped access control.

### APIs

* login
* refresh session/token
* logout
* current user/profile

## 3.2 Branch and Organizational Model

### Requirements

* The system shall support an organization with one or more branches.
* The POC shall use one active branch operationally.
* All key records shall be branch-aware where applicable.

### Core entities

* organization
* branch

## 3.3 Lead Management

### Requirements

* Staff shall be able to create and update leads.
* Leads shall support pipeline stages.
* Trial scheduling shall be supported.
* Lead conversion to member shall be supported.

### Lead statuses

* new
* contacted
* trial_scheduled
* trial_attended
* converted
* lost

### APIs

* create lead
* list leads
* filter leads
* update lead
* schedule trial
* mark trial attended
* convert lead to member

## 3.4 Member Management

### Requirements

* Staff shall be able to create and manage member profiles.
* A member shall belong to a branch.
* Member status shall be trackable.
* Trainer assignment shall be optionally supported.

### Member statuses

* active
* expired
* paused
* inactive

### APIs

* create member
* list members
* member detail
* update member
* pause/freeze member
* assign trainer

## 3.5 Membership Plans and Subscriptions

### Requirements

* Plans shall be configurable per branch.
* Staff shall be able to assign a plan to a member.
* Renewals shall create a new subscription record or approved renewal record.
* Subscription validity dates and dues shall be tracked.

### Core entities

* membership_plan
* member_subscription

### APIs

* create plan
* list plans
* update plan
* assign subscription
* renew subscription
* list expiring subscriptions

## 3.6 Payment and Ledger Operations

### Requirements

* Staff shall be able to record payments manually.
* The system shall track dues and outstanding balances.
* Payment mode shall be recorded.
* Summary and export-friendly reporting shall be available.

### Supported modes for POC

* cash
* card
* UPI
* bank transfer

### APIs

* record payment
* list payments
* member payment history
* outstanding dues list
* collections summary
* export collections report

## 3.7 Class and Program Operations

### Requirements

* Staff shall be able to create class types and class sessions.
* Trainers shall be assignable to sessions.
* Capacity shall be stored and enforced where booking is used.
* Class attendance shall be trackable.

### Core entities

* class_type
* class_session
* class_enrollment / booking

### APIs

* create class type
* list class types
* create class session
* list sessions
* enroll member in class (optional if enabled)
* class attendance mark
* trainer session view

## 3.8 Attendance

### Requirements

* The system shall support member attendance.
* Attendance shall support gym check-ins and class attendance.
* Attendance shall support trial attendance.

### Attendance types

* gym_checkin
* class_attendance
* trial_attendance

### APIs

* mark gym check-in
* mark class attendance
* mark trial attendance
* attendance history

## 3.9 Staff and Trainer Management

### Requirements

* Staff and trainer records shall be maintained.
* Roles and access levels shall be configurable within defined constraints.
* Trainers shall have class/session visibility.

### APIs

* create staff user
* list staff
* assign role
* update staff
* list trainer schedule

## 3.10 Dashboard and Reporting APIs

### Requirements

* Backend shall expose dashboard aggregates for owner and staff use.
* Dashboard data shall include operational, revenue, and lifecycle signals.

### Minimum dashboard outputs

* active members
* new leads
* trials scheduled
* trials converted
* renewals due in 7/15/30 days
* today’s collections
* outstanding dues
* classes scheduled today
* class fill rate
* inactive members

### APIs

* owner dashboard summary
* staff dashboard summary
* renewal report
* dues report
* attendance report
* class utilization report

## 3.11 Notification Support Layer

### Requirements

* Backend shall support notification event triggering.
* Backend shall maintain notification logs even if provider integration is mocked initially.

### Initial triggers

* trial reminder
* renewal reminder
* due payment reminder
* class reminder

### APIs / services

* trigger notification event
* list notification logs

## 3.12 Data Model — Minimum Core Entities

* organization
* branch
* user
* staff
* lead
* member
* membership_plan
* member_subscription
* payment
* class_type
* class_session
* class_enrollment
* attendance
* notification_log

## 3.13 Non-Functional Requirements

* API-first design
* clear validation and error handling
* auditability for critical operations
* branch-aware design
* secure authentication and authorization
* maintainable modular service structure
* scalable enough for POC and next-stage branch expansion

## 3.14 Backend Release Boundary for POC

### Must-have

* auth
* leads
* members
* plans/subscriptions
* payments
* classes
* attendance
* dashboard summaries
* staff roles

### Nice-to-have

* notification integration beyond logs/triggers
* member self-service APIs
* advanced search and analytics

---

# Part C — Frontend BRD

## 1. Frontend Business Objective

Build a user-facing product layer that allows gym staff, managers, owners, and later members to use FlowOS easily in day-to-day operations.

The frontend must turn backend workflows into simple operational experiences for:

* front desk execution
* owner visibility
* trainer coordination
* member-related interactions where included

## 2. Business Problem the Frontend Solves

Even the best backend fails if gym staff cannot use it quickly. Traditional gym staff need simple, fast workflows for:

* lead entry
* trial scheduling
* member lookup
* payment entry
* attendance marking
* class handling
* renewals and due follow-up

Owners need dashboards and reports, not raw database views.
Trainers need schedule and attendance clarity, not administrative clutter.

## 3. Frontend Stakeholders

### Primary users

* owner
* branch manager
* front desk staff
* trainer
* member (future/limited for POC)

### Internal stakeholders

* frontend engineers
* mobile engineers
* product manager
* designer
* QA team

## 4. Frontend Success Criteria

The frontend will be considered successful if it enables:

* fast day-to-day staff operations with minimal training
* clear role-based screens and actions
* easy navigation for operational tasks
* useful dashboards for decision-making
* responsive access on web and practical usage on Android

## 5. Frontend Scope Summary

### In scope

* web admin/staff application
* Android staff application
* role-based views
* operational workflows for leads, members, payments, classes, attendance, and dashboards

### Out of scope for POC

* fully polished member consumer app
* advanced marketing website
* complex white-label flows
* deeply customized branch theming

---

# Part D — Frontend PRD

## 1. Frontend Product Goal

Create a clean, role-aware web and Android user experience for a traditional gym, enabling operations staff and managers to run the gym efficiently from one system.

## 2. Frontend Platform Scope

## 2.1 Web Application Scope

The web app will be the primary control center for the POC.

### Primary users

* owner
* branch manager
* front desk staff
* trainer (limited operational view)

### Core web sections

* login
* dashboard
* leads
* members
* plans/subscriptions
* payments
* classes
* attendance
* staff management
* reports

## 2.2 Android Application Scope

The Android app will be the operational utility app for staff and trainers.

### Primary Android use cases

* quick lead entry
* lead follow-up
* member search
* attendance marking
* payment entry
* class list and attendance
* trainer schedule view

### Android POC principle

Android should prioritize speed and action-oriented tasks rather than full administrative coverage.

## 3. Role-Based Frontend Experience

## 3.1 Owner / Manager

### Needs

* business health at a glance
* revenue visibility
* renewals due
* lead conversion visibility
* branch performance readiness

### Key screens

* dashboard
* collections report
* renewal report
* active vs inactive members
* class performance
* staff view

## 3.2 Front Desk

### Needs

* create lead quickly
* schedule trials
* convert leads to members
* collect payments
* mark attendance
* handle renewals
* manage class bookings/attendance

### Key screens

* lead list and creation
* member lookup
* renewal due list
* payment entry
* attendance screen
* class roster screen

## 3.3 Trainer

### Needs

* view class schedule
* mark attendance
* see assigned members/classes

### Key screens

* trainer schedule
* class roster
* attendance marking
* assigned member list (optional)

## 3.4 Member (limited / future)

### Needs

* see membership status
* see upcoming classes
* see payment history
* receive reminders

For the initial POC, this can remain minimal or deferred.

## 4. Web Functional Requirements

### FR-W1 Dashboard

* The system shall show a role-based dashboard after login.
* The owner/manager dashboard shall show key gym KPIs.
* Front desk dashboard shall surface operational tasks.

### FR-W2 Lead Management Screens

* Users shall be able to create, edit, and filter leads.
* Users shall be able to schedule trials and update lead status.
* Users shall be able to convert leads to members.

### FR-W3 Member Management Screens

* Users shall be able to create and update members.
* Users shall be able to view membership status and subscription details.
* Users shall be able to pause/freeze or renew member subscriptions.

### FR-W4 Payment Screens

* Users shall be able to record payments.
* Users shall be able to view dues and payment history.
* Users shall be able to access collection summaries and exports.

### FR-W5 Class and Attendance Screens

* Users shall be able to create class types and sessions.
* Users shall be able to view class calendars/lists.
* Users shall be able to mark class attendance.
* Users shall be able to mark gym check-in attendance.

### FR-W6 Staff and Role Screens

* Authorized users shall be able to view and manage staff roles.
* Authorized users shall be able to view trainer schedules.

### FR-W7 Reports

* Users shall be able to access reports for renewals, dues, attendance, and collections.

## 5. Android Functional Requirements

### FR-A1 Login and Dashboard

* Staff shall be able to log in on Android.
* Dashboard shall prioritize quick operational actions.

### FR-A2 Lead Quick Capture

* Staff shall be able to create a lead rapidly from mobile.
* Staff shall be able to update lead status and trial schedule.

### FR-A3 Member Quick Access

* Staff shall be able to search and view members.
* Staff shall be able to record payments and check subscription status.

### FR-A4 Attendance Actions

* Staff and trainers shall be able to mark attendance from mobile.
* Trainers shall be able to mark class attendance.

### FR-A5 Trainer Utility

* Trainers shall be able to view their sessions.
* Trainers shall be able to access class rosters.

## 6. Frontend UX Principles

* Fast, low-friction workflows for high-frequency tasks
* Minimal training required for front desk staff
* Clear role-based separation
* Mobile-friendly and touch-friendly interactions
* Dashboard-first for managers
* Form design optimized for operational speed

## 7. Screen Scope — Web

### Web POC screen list

* Login
* Dashboard
* Leads list
* Lead create/edit
* Trial schedule
* Members list
* Member detail
* Plans list
* Subscription create/renew
* Payments list/entry
* Dues view
* Class types
* Class sessions/calendar
* Attendance
* Staff list
* Reports

## 8. Screen Scope — Android

### Android POC screen list

* Login
* Quick dashboard
* Add lead
* Leads follow-up list
* Member lookup
* Payment entry
* Attendance mark screen
* Class list
* Class roster and attendance
* Trainer schedule

## 9. Non-Functional Frontend Requirements

* Responsive web layout
* Good performance on standard business internet/mobile conditions
* Clear error states and validation messages
* Consistent API error handling
* Session handling and secure logout
* Simple navigation hierarchy

## 10. Frontend Release Boundary for POC

### Must-have web

* dashboard
* leads
* members
* subscriptions
* payments
* classes
* attendance
* reports

### Must-have Android

* login
* dashboard summary
* add lead
* member lookup
* payment entry
* attendance
* trainer schedule

### Defer

* full member portal
* advanced notifications center
* marketing pages
* deep customization controls

---

# Part E — Summary of Separation of Responsibilities

## Backend owns

* business logic
* data model
* validation
* security
* workflows
* role enforcement
* shared API contracts
* reporting aggregates

## Frontend owns

* user experience
* role-based navigation
* operational screens
* forms and workflows
* dashboard presentation
* mobile action flows

---

# Part F — Recommended Next Deliverables

1. Backend module breakdown by service/folder
2. Database schema draft
3. API contract draft
4. Web screen wireframe list
5. Android screen flow map
6. POC milestone plan
