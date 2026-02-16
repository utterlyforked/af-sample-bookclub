# Loan Tracking & Management — Engineering Spec

**Type**: feature
**Component**: loan-tracking-management
**Dependencies**: foundation-spec (User, Group, GroupMember, authentication, authorization)
**Status**: Ready for Implementation

---

## Overview

The Loan Tracking & Management component enables users to record loans between group members, track repayment status, and manage loan lifecycle. This component owns the Loan and LoanRepayment entities and provides API endpoints for creating, viewing, updating, and deleting loans. It reads from foundation entities (User, Group, GroupMember) but does not modify them. All loan operations are scoped to authenticated users with appropriate group membership.

---

## Data Model

### Loan

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| group_id | UUID | FK, not null, indexed | References Group.id |
| lender_id | UUID | FK, not null, indexed | References User.id |
| borrower_id | UUID | FK, not null, indexed | References User.id |
| principal_amount | decimal(19,4) | not null, > 0 | Original loan amount |
| currency_code | string(3) | not null | ISO 4217 code (e.g., USD, EUR) |
| interest_rate | decimal(5,2) | null, >= 0, <= 100 | Annual percentage rate; null means 0% |
| start_date | date | not null | Date loan was issued |
| due_date | date | null | Date full repayment is due; null means open-ended |
| status | string(20) | not null, enum | One of: Active, PaidOff, Defaulted, Cancelled |
| outstanding_balance | decimal(19,4) | not null, >= 0 | Computed: principal + interest - repayments |
| description | string(500) | null | Optional loan purpose/notes |
| created_at | datetime | not null | UTC timestamp |
| updated_at | datetime | not null | UTC timestamp, updated on any change |
| created_by | UUID | FK, not null | References User.id |

**Indexes**:
- `(group_id, status)` — for filtering active/paid loans by group
- `(lender_id)` — for "loans I gave" queries
- `(borrower_id)` — for "loans I owe" queries
- `(due_date)` — for overdue loan queries

**Relationships**:
- Belongs to `Group` via `group_id`
- Belongs to `User` via `lender_id` (lender)
- Belongs to `User` via `borrower_id` (borrower)
- Belongs to `User` via `created_by` (creator)
- Has many `LoanRepayment` (cascade delete)

**Constraints**:
- `lender_id` and `borrower_id` must be different
- `lender_id` and `borrower_id` must both be members of `group_id`
- `due_date` must be >= `start_date` (if not null)
- `outstanding_balance` recalculated on every repayment insert/update/delete

---

### LoanRepayment

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| loan_id | UUID | FK, not null, indexed | References Loan.id |
| amount | decimal(19,4) | not null, > 0 | Repayment amount |
| currency_code | string(3) | not null | Must match Loan.currency_code |
| payment_date | date | not null | Date payment was made |
| payment_method | string(50) | null | Optional: Cash, Bank Transfer, etc. |
| notes | string(500) | null | Optional repayment notes |
| created_at | datetime | not null | UTC timestamp |
| created_by | UUID | FK, not null | References User.id |

**Indexes**:
- `(loan_id, payment_date)` — for chronological repayment history

**Relationships**:
- Belongs to `Loan` via `loan_id`
- Belongs to `User` via `created_by`

**Constraints**:
- `currency_code` must match parent Loan's `currency_code`
- Cannot create repayment if Loan.status is `Cancelled`
- Repayment total cannot exceed Loan.principal_amount + accrued interest

---

> **Note**: This spec owns only Loan and LoanRepayment entities. Entities defined in the Foundation Spec (User, Group, GroupMember) are referenced by name, not redefined.

---

## API Endpoints

### POST /api/v1/loans

**Auth**: Required (Bearer JWT)
**Authorization**: GroupMember (must be member of specified group)

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| group_id | UUID | yes | Valid UUID, user must be member |
| lender_id | UUID | yes | Valid UUID, must be group member, not same as borrower_id |
| borrower_id | UUID | yes | Valid UUID, must be group member, not same as lender_id |
| principal_amount | decimal | yes | > 0, max 19 digits with 4 decimal places |
| currency_code | string | yes | Valid ISO 4217 code, max 3 chars |
| interest_rate | decimal | no | >= 0, <= 100, max 5 digits with 2 decimal places |
| start_date | ISO 8601 date | yes | Valid date, not more than 1 year in past |
| due_date | ISO 8601 date | no | Valid date, >= start_date |
| description | string | no | Max 500 chars |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| group_id | UUID | |
| lender_id | UUID | |
| borrower_id | UUID | |
| principal_amount | decimal | |
| currency_code | string | |
| interest_rate | decimal | null if not provided |
| start_date | ISO 8601 date | |
| due_date | ISO 8601 date | null if not provided |
| status | string | Always "Active" on creation |
| outstanding_balance | decimal | Equals principal_amount on creation |
| description | string | null if not provided |
| created_at | ISO 8601 datetime | UTC |
| updated_at | ISO 8601 datetime | UTC |
| created_by | UUID | Current user ID |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure — returns field-level errors |
| 401 | Not authenticated |
| 403 | Not a member of specified group |
| 404 | Group not found, or lender/borrower not found |
| 409 | Lender and borrower are the same user |

---

### GET /api/v1/loans/{id}

**Auth**: Required (Bearer JWT)
**Authorization**: GroupMember (must be member of loan's group)

**Path parameters**:
| Parameter | Type | Notes |
|-----------|------|-------|
| id | UUID | Loan ID |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| group_id | UUID | |
| lender_id | UUID | |
| borrower_id | UUID | |
| principal_amount | decimal | |
| currency_code | string | |
| interest_rate | decimal | |
| start_date | ISO 8601 date | |
| due_date | ISO 8601 date | |
| status | string | |
| outstanding_balance | decimal | |
| description | string | |
| created_at | ISO 8601 datetime | UTC |
| updated_at | ISO 8601 datetime | UTC |
| created_by | UUID | |
| repayments | array | Array of LoanRepayment objects (see below) |

**LoanRepayment object structure**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| amount | decimal | |
| currency_code | string | |
| payment_date | ISO 8601 date | |
| payment_method | string | |
| notes | string | |
| created_at | ISO 8601 datetime | UTC |
| created_by | UUID | |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | Not a member of loan's group |
| 404 | Loan not found |

---

### GET /api/v1/groups/{group_id}/loans

**Auth**: Required (Bearer JWT)
**Authorization**: GroupMember (must be member of specified group)

**Path parameters**:
| Parameter | Type | Notes |
|-----------|------|-------|
| group_id | UUID | Group ID |

**Query parameters**:
| Parameter | Type | Required | Validation | Default |
|-----------|------|----------|-----------|---------|
| status | string | no | One of: Active, PaidOff, Defaulted, Cancelled, All | Active |
| lender_id | UUID | no | Valid UUID | null (no filter) |
| borrower_id | UUID | no | Valid UUID | null (no filter) |
| page | integer | no | >= 1 | 1 |
| page_size | integer | no | >= 1, <= 100 | 20 |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| loans | array | Array of Loan objects (same structure as GET /loans/{id}, excluding repayments array) |
| total_count | integer | Total matching loans |
| page | integer | Current page |
| page_size | integer | Items per page |
| has_next_page | boolean | True if more pages available |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid query parameters |
| 401 | Not authenticated |
| 403 | Not a member of specified group |
| 404 | Group not found |

---

### PATCH /api/v1/loans/{id}

**Auth**: Required (Bearer JWT)
**Authorization**: GroupMember + LoanParticipant (must be lender, borrower, or loan creator)

**Path parameters**:
| Parameter | Type | Notes |
|-----------|------|-------|
| id | UUID | Loan ID |

**Request body** (all fields optional):
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| interest_rate | decimal | no | >= 0, <= 100 |
| due_date | ISO 8601 date | no | >= loan's start_date, or null to remove |
| status | string | no | One of: Active, PaidOff, Defaulted, Cancelled |
| description | string | no | Max 500 chars |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| (Same as GET /api/v1/loans/{id}) | | Updated loan object |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure |
| 401 | Not authenticated |
| 403 | Not a member of loan's group, or not lender/borrower/creator |
| 404 | Loan not found |
| 409 | Cannot change status from PaidOff or Cancelled to Active |

---

### DELETE /api/v1/loans/{id}

**Auth**: Required (Bearer JWT)
**Authorization**: GroupMember + LoanCreator (must be the user who created the loan)

**Path parameters**:
| Parameter | Type | Notes |
|-----------|------|-------|
| id | UUID | Loan ID |

**Success response** `204 No Content`:
(Empty body)

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | Not the loan creator |
| 404 | Loan not found |
| 409 | Cannot delete loan with status PaidOff or with existing repayments |

---

### POST /api/v1/loans/{loan_id}/repayments

**Auth**: Required (Bearer JWT)
**Authorization**: GroupMember + LoanParticipant (must be lender, borrower, or loan creator)

**Path parameters**:
| Parameter | Type | Notes |
|-----------|------|-------|
| loan_id | UUID | Loan ID |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| amount | decimal | yes | > 0, max 19 digits with 4 decimal places |
| currency_code | string | yes | Must match loan's currency_code |
| payment_date | ISO 8601 date | yes | Valid date, not in future |
| payment_method | string | no | Max 50 chars |
| notes | string | no | Max 500 chars |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| loan_id | UUID | |
| amount | decimal | |
| currency_code | string | |
| payment_date | ISO 8601 date | |
| payment_method | string | |
| notes | string | |
| created_at | ISO 8601 datetime | UTC |
| created_by | UUID | Current user ID |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure, or currency mismatch |
| 401 | Not authenticated |
| 403 | Not a member of loan's group, or not lender/borrower/creator |
| 404 | Loan not found |
| 409 | Loan status is Cancelled, or repayment exceeds outstanding balance |

---

### DELETE /api/v1/repayments/{id}

**Auth**: Required (Bearer JWT)
**Authorization**: GroupMember + RepaymentCreator (must be the user who created the repayment)

**Path parameters**:
| Parameter | Type | Notes |
|-----------|------|-------|
| id | UUID | Repayment ID |

**Success response** `204 No Content`:
(Empty body)

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | Not the repayment creator |
| 404 | Repayment not found |
| 409 | Cannot delete repayment if loan status is PaidOff or Cancelled |

---

## Business Rules

1. A loan's lender and borrower must be different users.
2. Both lender and borrower must be active members of the loan's group at the time of loan creation.
3. A loan's `outstanding_balance` is computed as: `principal_amount + accrued_interest - sum(repayments.amount)`.
4. Interest accrues daily based on the annual `interest_rate` (if provided) from `start_date` to current date, compounded daily using formula: `principal * (1 + rate/365)^days - principal`.
5. If a repayment causes `outstanding_balance` to reach zero, the loan's status is automatically updated to `PaidOff`.
6. A loan with status `Cancelled` cannot accept new repayments.
7. A loan's status cannot transition from `PaidOff` or `Cancelled` back to `Active`.
8. Repayment `payment_date` cannot be in the future.
9. The sum of all repayments for a loan cannot exceed `principal_amount + accrued_interest`.
10. Users may only view, edit, or delete loans for groups they are members of.
11. Only the loan creator may delete a loan, and only if it has no repayments and is not `PaidOff`.
12. Only the repayment creator may delete a repayment, and only if the loan is not `PaidOff` or `Cancelled`.
13. Currency code must be a valid ISO 4217 three-letter code (validated against a whitelist: USD, EUR, GBP, JPY, INR, NGN).
14. `start_date` cannot be more than 1 year in the past.

---

## Validation Rules

| Field | Rule | Error message |
|-------|------|---------------|
| group_id | Required, valid UUID, user must be member | "Group ID is required" / "Invalid group ID" / "You are not a member of this group" |
| lender_id | Required, valid UUID, must be group member, not equal to borrower_id | "Lender ID is required" / "Invalid lender ID" / "Lender must be a group member" / "Lender and borrower cannot be the same" |
| borrower_id | Required, valid UUID, must be group member, not equal to lender_id | "Borrower ID is required" / "Invalid borrower ID" / "Borrower must be a group member" / "Lender and borrower cannot be the same" |
| principal_amount | Required, > 0, max 19 digits with 4 decimal places | "Principal amount is required" / "Principal amount must be greater than zero" / "Principal amount is too large" |
| currency_code | Required, valid ISO 4217 code (whitelist: USD, EUR, GBP, JPY, INR, NGN), max 3 chars | "Currency code is required" / "Invalid currency code" |
| interest_rate | Optional, >= 0, <= 100, max 5 digits with 2 decimal places | "Interest rate must be between 0 and 100" / "Interest rate format is invalid" |
| start_date | Required, valid date, not more than 1 year in past | "Start date is required" / "Invalid start date" / "Start date cannot be more than 1 year in the past" |
| due_date | Optional, valid date, >= start_date | "Invalid due date" / "Due date must be on or after start date" |
| description | Optional, max 500 chars | "Description is too long (max 500 characters)" |
| status | Required, one of: Active, PaidOff, Defaulted, Cancelled | "Status is required" / "Invalid status value" |
| amount (repayment) | Required, > 0, max 19 digits with 4 decimal places | "Amount is required" / "Amount must be greater than zero" / "Amount is too large" |
| currency_code (repayment) | Required, must match loan's currency_code | "Currency code is required" / "Currency code must match loan currency" |
| payment_date | Required, valid date, not in future | "Payment date is required" / "Invalid payment date" / "Payment date cannot be in the future" |
| payment_method | Optional, max 50 chars | "Payment method is too long (max 50 characters)" |
| notes (repayment) | Optional, max 500 chars | "Notes are too long (max 500 characters)" |

---

## Authorization

| Action | Required policy | Notes |
|--------|----------------|-------|
| Create loan | Authenticated + GroupMember | User must be member of specified group |
| View loan | Authenticated + GroupMember | User must be member of loan's group |
| List loans in group | Authenticated + GroupMember | User must be member of specified group |
| Update loan | Authenticated + GroupMember + LoanParticipant | User must be lender, borrower, or creator |
| Delete loan | Authenticated + GroupMember + LoanCreator | User must be loan creator, loan must have no repayments |
| Create repayment | Authenticated + GroupMember + LoanParticipant | User must be lender, borrower, or loan creator |
| Delete repayment | Authenticated + GroupMember + RepaymentCreator | User must be repayment creator |

**Policy definitions**:
- **GroupMember**: User's ID appears in `GroupMember` table for the relevant `group_id` with `status = Active`
- **LoanParticipant**: User's ID matches `lender_id`, `borrower_id`, or `created_by` on the Loan
- **LoanCreator**: User's ID matches `created_by` on the Loan
- **RepaymentCreator**: User's ID matches `created_by` on the LoanRepayment

---

## Acceptance Criteria

- [ ] User can create a loan with valid lender, borrower, principal, currency, and start date
- [ ] System prevents creating a loan where lender and borrower are the same user
- [ ] System prevents creating a loan if lender or borrower is not a member of the specified group
- [ ] Newly created loan has status "Active" and outstanding_balance equal to principal_amount
- [ ] User can retrieve a loan by ID if they are a member of the loan's group
- [ ] User can list all loans in a group they are a member of, with pagination
- [ ] User can filter loans by status (Active, PaidOff, Defaulted, Cancelled, All)
- [ ] User can filter loans by lender_id or borrower_id
- [ ] User can update a loan's interest_rate, due_date, status, or description if they are a loan participant
- [ ] System prevents updating a loan's status from PaidOff or Cancelled back to Active
- [ ] User can delete a loan they created, only if it has no repayments and is not PaidOff
- [ ] User can record a repayment on a loan if they are a loan participant
- [ ] System validates repayment currency_code matches loan's currency_code
- [ ] System prevents repayment if payment_date is in the future
- [ ] System prevents repayment if loan status is Cancelled
- [ ] System automatically updates outstanding_balance after each repayment
- [ ] System automatically updates loan status to PaidOff when outstanding_balance reaches zero
- [ ] System prevents total repayments from exceeding principal_amount plus accrued interest
- [ ] User can delete a repayment they created, only if loan is not PaidOff or Cancelled
- [ ] Outstanding balance calculation includes daily compounded interest based on annual interest_rate
- [ ] System returns 403 for loan operations if user is not a member of the loan's group
- [ ] System returns 403 for update/delete operations if user is not a loan participant or creator
- [ ] System returns 404 if loan or repayment ID does not exist
- [ ] System returns 400 with field-level errors for validation failures
- [ ] System enforces currency_code whitelist (USD, EUR, GBP, JPY, INR, NGN)
- [ ] System prevents start_date more than 1 year in the past

---

## Security Requirements

**From AppSec Review:**

- All API endpoints require Bearer JWT authentication (except none specified here).
- Authorization policies (GroupMember, LoanParticipant, LoanCreator, RepaymentCreator) must be enforced server-side on every request.
- User IDs and Group IDs in requests must be validated against the authenticated user's JWT claims.
- SQL injection: Use parameterized queries (ORM by default); never concatenate user input into raw SQL.
- Mass assignment: Only allow modification of explicitly listed fields (interest_rate, due_date, status, description) in PATCH /loans/{id}.
- Decimal precision: Enforce 19 digits with 4 decimal places for all monetary amounts to prevent rounding exploits.
- Rate limiting: Max 100 loan creation requests per user per hour, max 200 repayment creation requests per user per hour.
- Audit logging: Log all loan and repayment creation, update, and deletion events with user ID, timestamp, and affected entity ID.
- Input sanitization: Validate and sanitize description, notes, and payment_method fields to prevent XSS in case values are rendered without escaping.
- Prevent time-based enumeration: Return same error message for "loan not found" and "not authorized to view loan" (403 only if authenticated).
- Currency code validation: Whitelist only supported codes (USD, EUR, GBP, JPY, INR, NGN); reject all others.
- Outstanding balance recalculation must be atomic (database transaction) to prevent race conditions during concurrent repayment creation.

**Additional:**

- Repayment deletions must trigger immediate recalculation of outstanding_balance within the same transaction.
- Interest calculation must use a consistent timestamp (e.g., UTC midnight) to avoid drift across time zones.

---

## Out of Scope

- Email or push notifications for overdue loans (future feature)
- Multi-currency conversion or exchange rates (each loan is single-currency)
- Loan amortization schedules or payment reminders (future feature)
- Loan approval workflows or multi-stage status (Active/Pending/Approved) (future feature)
- Integration with external payment processors (future feature)
- Historical audit trail UI for loan edits (logging only)
- Test plans and test case definitions (owned by QA spec)
- Implementation code, database migrations, or ORM configuration (engineer's responsibility)
- UI mockups or frontend component specifications (frontend engineer's responsibility)