# Borrowing Requests — Engineering Spec

**Type**: feature
**Component**: borrowing-requests
**Dependencies**: foundation-spec (User, Tool, Notification entities)
**Status**: Ready for Implementation

---

## Overview

The Borrowing Requests feature enables borrowers to request tools from owners and provides owners with controls to approve or decline requests. This component owns the `BorrowRequest` and `RequestMessage` entities, managing the complete lifecycle from initial request through approval/decline, pickup coordination, and completion. It reads from foundation entities (User, Tool) but does not own them. The feature enforces double-booking prevention via database-level exclusion constraints and implements progressive information disclosure (general location visible before request, exact address after approval).

---

## Data Model

### BorrowRequest

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| toolId | UUID | FK to Tool, not null | Tool being requested |
| borrowerUserId | UUID | FK to User, not null | User requesting the tool |
| ownerUserId | UUID | FK to User, not null | Tool owner (denormalized from Tool for query efficiency) |
| requestedStartDate | date | not null | Start date of borrow period |
| requestedEndDate | date | not null | End date of borrow period |
| projectDescription | string(500) | not null | Borrower's explanation, 50-500 chars |
| status | enum | not null, indexed | BorrowRequestStatus enum |
| createdAt | timestamp | not null, default NOW() | When request was submitted |
| respondedAt | timestamp | nullable | When owner approved/declined |
| pickedUpAt | timestamp | nullable | When borrower confirmed pickup |
| returnedAt | timestamp | nullable | When owner confirmed return |
| ownerMessage | string(500) | nullable | Optional message on approval, max 500 chars |
| declineReason | string(500) | nullable | Required on decline (20-500 chars) or system-generated |
| withdrawReason | string(500) | nullable | Required if owner withdraws approval (20-500 chars) |

**Indexes**:
- `(toolId, status)` - for querying pending/approved requests per tool
- `(borrowerUserId, status)` - for borrower's request history
- `(ownerUserId, status)` - for owner's incoming requests
- `(status, createdAt DESC)` - for chronological sorting by status
- GiST exclusion constraint on `(toolId, daterange(requestedStartDate, requestedEndDate))` WHERE status = 'Approved'

**Constraints**:
- `requestedEndDate >= requestedStartDate`
- `requestedEndDate <= requestedStartDate + 14 days`
- `respondedAt IS NULL` when `status = 'Pending'`
- `respondedAt IS NOT NULL` when `status IN ('Approved', 'Declined')`
- `declineReason IS NOT NULL` when `status = 'Declined'`
- `withdrawReason IS NOT NULL` when `status = 'Withdrawn'`
- `pickedUpAt IS NOT NULL` when `status IN ('PickedUp', 'Returned', 'Completed')`
- `returnedAt IS NOT NULL` when `status IN ('Returned', 'Completed')`
- Exclusion constraint: `EXCLUDE USING GIST (toolId WITH =, daterange(requestedStartDate, requestedEndDate, '[]') WITH &&) WHERE (status = 'Approved')`

**Relationships**:
- Belongs to `Tool` via `toolId`
- Belongs to `User` (borrower) via `borrowerUserId`
- Belongs to `User` (owner) via `ownerUserId`
- Has many `RequestMessage` (cascade delete)

**Status Enum** (BorrowRequestStatus):
- `Pending` - Initial state, awaiting owner response
- `Approved` - Owner approved, awaiting pickup
- `Declined` - Owner declined or system auto-declined
- `Cancelled` - Borrower cancelled before pickup
- `Withdrawn` - Owner withdrew approval before pickup
- `PickedUp` - Borrower confirmed pickup (active borrow)
- `Returned` - Owner confirmed return
- `Completed` - Both parties confirmed, can rate each other

**Valid State Transitions**:
- `Pending` → `Approved`, `Declined`, `Cancelled`
- `Approved` → `Withdrawn`, `Cancelled`, `PickedUp`
- `PickedUp` → `Returned`
- `Returned` → `Completed`

### RequestMessage

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| borrowRequestId | UUID | FK to BorrowRequest, not null | Associated request |
| senderUserId | UUID | FK to User, not null | User who sent the message |
| recipientUserId | UUID | FK to User, not null | User who receives the message |
| messageText | string(1000) | not null | Message content, 1-1000 chars |
| sentAt | timestamp | not null, default NOW() | When message was sent |
| readAt | timestamp | nullable | When recipient read the message |
| emailDigestSentAt | timestamp | nullable | When 2-hour digest email was sent (if applicable) |

**Indexes**:
- `(borrowRequestId, sentAt ASC)` - for chronological message threads
- `(recipientUserId, readAt)` WHERE `readAt IS NULL` - for unread message queries
- `(borrowRequestId, sentAt)` WHERE `emailDigestSentAt IS NULL AND readAt IS NULL` - for pending digest job

**Constraints**:
- `senderUserId != recipientUserId`
- `senderUserId IN (borrowRequest.borrowerUserId, borrowRequest.ownerUserId)`
- `recipientUserId IN (borrowRequest.borrowerUserId, borrowRequest.ownerUserId)`

**Relationships**:
- Belongs to `BorrowRequest` via `borrowRequestId`
- Belongs to `User` (sender) via `senderUserId`
- Belongs to `User` (recipient) via `recipientUserId`

> **Note**: This spec owns only the entities listed above. Entities defined in the Foundation Spec (User, Tool, Notification) are referenced by name, not redefined.

---

## API Endpoints

### POST /api/v1/borrow-requests

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| toolId | UUID | yes | Must reference existing Tool with status = 'Available' |
| requestedStartDate | ISO 8601 date | yes | Must be >= today, <= 90 days in future |
| requestedEndDate | ISO 8601 date | yes | Must be >= requestedStartDate, <= requestedStartDate + 14 days |
| projectDescription | string | yes | 50-500 characters, non-empty |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| toolId | UUID | |
| borrowerUserId | UUID | |
| ownerUserId | UUID | |
| requestedStartDate | ISO 8601 date | |
| requestedEndDate | ISO 8601 date | |
| projectDescription | string | |
| status | string | Always "Pending" on creation |
| createdAt | ISO 8601 datetime | UTC |
| tool | object | Embedded Tool summary (id, name, imageUrl, ownerName, ownerNeighborhood) |
| rateLimitWarning | boolean | True if user submitted 5+ requests in past hour |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure — projectDescription too short/long, dates invalid, end date > 14 days from start |
| 401 | Not authenticated |
| 403 | Borrower is same as tool owner (cannot borrow own tool) |
| 404 | Tool not found |
| 409 | Tool status is not 'Available' (already borrowed, withdrawn, or unavailable) |
| 429 | User exceeded hard rate limit (>20 requests in 1 hour) |

**Side effects**:
- Creates `BorrowRequest` record with status = 'Pending'
- Creates `Notification` for owner (type: 'BorrowRequestReceived')
- Sends email to owner (if email notifications enabled): "You have a new borrow request for [Tool name] from [Borrower name]"
- If user submitted 5+ requests in past hour, returns `rateLimitWarning: true` in response

---

### GET /api/v1/borrow-requests

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated

**Query parameters**:
| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| role | enum | no | Filter by 'borrower' or 'owner'. Default: both |
| status | enum | no | Filter by BorrowRequestStatus. Multiple allowed (comma-separated) |
| toolId | UUID | no | Filter by specific tool |
| page | integer | no | Page number (1-indexed), default: 1 |
| pageSize | integer | no | Results per page (1-50), default: 20 |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| items | array | Array of BorrowRequest objects (see GET by id response) |
| totalCount | integer | Total matching requests across all pages |
| page | integer | Current page |
| pageSize | integer | Results per page |
| hasNextPage | boolean | True if more pages available |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid query parameters (e.g., pageSize > 50, invalid status enum) |
| 401 | Not authenticated |

---

### GET /api/v1/borrow-requests/{id}

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower or owner of the request

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| toolId | UUID | |
| borrowerUserId | UUID | |
| ownerUserId | UUID | |
| requestedStartDate | ISO 8601 date | |
| requestedEndDate | ISO 8601 date | |
| projectDescription | string | |
| status | string | BorrowRequestStatus enum value |
| createdAt | ISO 8601 datetime | UTC |
| respondedAt | ISO 8601 datetime | UTC, nullable |
| pickedUpAt | ISO 8601 datetime | UTC, nullable |
| returnedAt | ISO 8601 datetime | UTC, nullable |
| ownerMessage | string | nullable |
| declineReason | string | nullable |
| withdrawReason | string | nullable |
| tool | object | Embedded Tool summary (id, name, description, imageUrl, category) |
| borrower | object | Embedded User summary (id, fullName, neighborhood, memberSince, profileImageUrl) |
| owner | object | Embedded User summary (id, fullName, neighborhood, memberSince, profileImageUrl, phone if status = 'Approved', fullAddress if status = 'Approved') |
| borrowerStats | object | Visible to owner only: { completedBorrowsCount, averageRating, onTimeReturnRate } |
| messages | array | Array of RequestMessage objects (see message response schema) |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is neither borrower nor owner of this request |
| 404 | Request not found |

---

### POST /api/v1/borrow-requests/{id}/approve

**Auth**: Required (Bearer JWT)
**Authorization**: Must be owner of the tool

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| message | string | no | Optional message to borrower, max 500 chars |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Request id |
| status | string | "Approved" |
| respondedAt | ISO 8601 datetime | UTC |
| ownerMessage | string | nullable |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Request is not in 'Pending' status |
| 401 | Not authenticated |
| 403 | User is not the tool owner |
| 404 | Request not found |
| 409 | Exclusion constraint violation (another request was approved for overlapping dates) |

**Side effects**:
- Updates `BorrowRequest` status to 'Approved', sets `respondedAt` to NOW()
- Creates `Notification` for borrower (type: 'BorrowRequestApproved')
- Sends email to borrower with owner's full address, phone, and pickup instructions
- If constraint violation occurs (409):
  - Automatically declines the request (status = 'Declined', declineReason = system-generated)
  - Creates `Notification` for owner: "Another request was approved for these dates. This request has been automatically declined."
  - Returns error to owner with message: "Someone else was just approved for these dates. This request has been automatically declined. Please review other pending requests."
- Queries for other pending requests with overlapping dates and auto-declines them:
  - Sets status = 'Declined', declineReason = "This tool was approved for another borrower during overlapping dates ([conflicting start] - [conflicting end]). Please request again with different dates if you still need it."
  - Creates `Notification` for each affected borrower
  - Sends email to each affected borrower with suggested alternative dates

---

### POST /api/v1/borrow-requests/{id}/decline

**Auth**: Required (Bearer JWT)
**Authorization**: Must be owner of the tool

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| reason | string | yes | 20-500 characters, non-empty |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Request id |
| status | string | "Declined" |
| respondedAt | ISO 8601 datetime | UTC |
| declineReason | string | |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure (reason too short/long) OR request is not in 'Pending' status |
| 401 | Not authenticated |
| 403 | User is not the tool owner |
| 404 | Request not found |

**Side effects**:
- Updates `BorrowRequest` status to 'Declined', sets `respondedAt` to NOW(), stores `declineReason`
- Creates `Notification` for borrower (type: 'BorrowRequestDeclined')
- Sends email to borrower with owner's decline reason

---

### POST /api/v1/borrow-requests/{id}/cancel

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower of the request

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Request id |
| status | string | "Cancelled" |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Request status is not 'Pending' or 'Approved' (already picked up or completed) |
| 401 | Not authenticated |
| 403 | User is not the borrower |
| 404 | Request not found |

**Side effects**:
- Updates `BorrowRequest` status to 'Cancelled'
- If previous status was 'Approved', releases date range (other users can now request those dates)
- Creates `Notification` for owner (type: 'BorrowRequestCancelled')
- Sends email to owner: "[Borrower name] cancelled their borrow of [Tool name] for [dates]. Your tool is now available again."

---

### POST /api/v1/borrow-requests/{id}/withdraw

**Auth**: Required (Bearer JWT)
**Authorization**: Must be owner of the tool

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| reason | string | yes | 20-500 characters, non-empty |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Request id |
| status | string | "Withdrawn" |
| withdrawReason | string | |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure (reason too short/long) OR request is not in 'Approved' status |
| 401 | Not authenticated |
| 403 | User is not the tool owner |
| 404 | Request not found |

**Side effects**:
- Updates `BorrowRequest` status to 'Withdrawn', stores `withdrawReason`
- Releases date range (other users can now request those dates)
- Creates `Notification` for borrower (type: 'BorrowRequestWithdrawn')
- Sends email to borrower with owner's withdrawal reason and encouragement to request again or find alternatives
- Increments owner's `withdrawnRequestsCount` (internal tracking, not publicly visible)

---

### GET /api/v1/borrow-requests/{id}/messages

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower or owner of the request

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| messages | array | Array of message objects, sorted by sentAt ASC |

**Message object**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| senderUserId | UUID | |
| recipientUserId | UUID | |
| messageText | string | |
| sentAt | ISO 8601 datetime | UTC |
| readAt | ISO 8601 datetime | UTC, nullable |
| sender | object | { id, fullName, profileImageUrl } |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is neither borrower nor owner |
| 404 | Request not found |

---

### POST /api/v1/borrow-requests/{id}/messages

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower or owner of the request

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| messageText | string | yes | 1-1000 characters, non-empty |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Message id |
| senderUserId | UUID | |
| recipientUserId | UUID | |
| messageText | string | |
| sentAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure (message too short/long) OR request is in terminal state ('Completed' and >7 days old) |
| 401 | Not authenticated |
| 403 | User is neither borrower nor owner |
| 404 | Request not found |

**Side effects**:
- Creates `RequestMessage` record
- Creates in-app `Notification` for recipient (type: 'RequestMessageReceived')
- Schedules background job to run at `sentAt + 2 hours`:
  - If recipient has unread messages in this thread, send one email digest with all unread messages
  - Email subject: "[Sender name] sent you messages about [Tool name]"
  - Email body: List of unread messages with timestamps, "View Conversation" CTA
  - Marks `emailDigestSentAt` for all included messages
  - If recipient read messages before 2-hour window, cancel job (no email sent)

---

### PUT /api/v1/borrow-requests/{id}/messages/{messageId}/read

**Auth**: Required (Bearer JWT)
**Authorization**: Must be recipient of the message

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Message id |
| readAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is not the recipient |
| 404 | Message not found |

**Side effects**:
- Updates `RequestMessage.readAt` to NOW()
- Cancels pending email digest job if this was the last unread message in thread

---

## Business Rules

1. Email addresses are normalized to lowercase before storage and lookup (inherited from Foundation).
2. Borrowers may not request their own tools (constraint: `borrowerUserId != tool.ownerUserId`).
3. Tools must have status 'Available' to be requested; requests to 'Borrowed', 'Unavailable', or 'Withdrawn' tools are rejected with HTTP 409.
4. Requested end date must be >= start date and <= start date + 14 days (maximum borrow period).
5. Requested start date must be >= today and <= 90 days in future (prevent stale requests, encourage near-term planning).
6. Only one approved request may exist for a tool during overlapping dates (enforced by PostgreSQL exclusion constraint).
7. When a request is approved, all other pending requests with overlapping dates for the same tool are automatically declined with system-generated reason showing conflicting date range.
8. When a tool's status changes to 'Unavailable', all pending requests for that tool are automatically declined with system notification.
9. Borrowers may have multiple approved/active borrows for different tools with overlapping dates (no cross-tool validation).
10. Borrowers may cancel requests with status 'Pending' or 'Approved' (before pickup); cancellation releases the date range for other users.
11. Owners may withdraw approval (status 'Approved' → 'Withdrawn') before pickup occurs; withdrawal releases the date range and requires a reason (20-500 chars).
12. Owners may not approve requests once the tool status is not 'Available' (must return to 'Available' first).
13. Message threads are retained permanently (no automated deletion) for dispute resolution and audit trail.
14. After a user submits 5 requests within 1 hour, subsequent requests return a `rateLimitWarning` flag (soft limit, not enforced).
15. Users submitting >20 requests within 1 hour are rejected with HTTP 429 (hard rate limit).
16. Owner's full address and phone number are only revealed to borrower after request is approved.
17. When a message is sent, recipient receives in-app notification immediately; if unread after 2 hours, recipient receives one email digest with all unread messages in that thread.
18. State transitions are restricted: 'Pending' may only transition to 'Approved', 'Declined', or 'Cancelled'; 'Approved' may only transition to 'Withdrawn', 'Cancelled', or 'PickedUp'; no transitions back to 'Pending'.

---

## Validation Rules

| Field | Rule | Error message |
|-------|------|---------------|
| toolId | Required, must exist in Tool table | "Tool not found" |
| requestedStartDate | Required, valid ISO 8601 date, >= today, <= 90 days from today | "Start date is required" / "Start date must be today or later" / "Start date must be within 90 days" |
| requestedEndDate | Required, valid ISO 8601 date, >= requestedStartDate, <= requestedStartDate + 14 days | "End date is required" / "End date must be after start date" / "Borrow period cannot exceed 14 days" |
| projectDescription | Required, 50-500 characters, non-empty after trim | "Project description is required" / "Project description must be at least 50 characters" / "Project description cannot exceed 500 characters" |
| ownerMessage | Optional, max 500 characters | "Owner message cannot exceed 500 characters" |
| declineReason | Required on decline, 20-500 characters | "Decline reason is required" / "Decline reason must be at least 20 characters" / "Decline reason cannot exceed 500 characters" |
| withdrawReason | Required on withdraw, 20-500 characters | "Withdrawal reason is required" / "Withdrawal reason must be at least 20 characters" / "Withdrawal reason cannot exceed 500 characters" |
| messageText | Required, 1-1000 characters, non-empty after trim | "Message is required" / "Message cannot be empty" / "Message cannot exceed 1000 characters" |

---

## Authorization

| Action | Required policy | Notes |
|--------|----------------|-------|
| Create request | Authenticated | Borrower must not be tool owner |
| View request | Authenticated | Must be borrower or owner |
| List requests | Authenticated | User sees only requests where they are borrower or owner |
| Approve request | Authenticated | Must be tool owner, request status must be 'Pending' |
| Decline request | Authenticated | Must be tool owner, request status must be 'Pending' |
| Cancel request | Authenticated | Must be borrower, request status must be 'Pending' or 'Approved' |
| Withdraw approval | Authenticated | Must be tool owner, request status must be 'Approved' |
| View messages | Authenticated | Must be borrower or owner |
| Send message | Authenticated | Must be borrower or owner, request not in terminal completed state |
| Mark message read | Authenticated | Must be recipient |

---

## Acceptance Criteria

- [ ] Borrower can submit request with valid dates (today to +14 days) and project description (50-500 chars)
- [ ] Request submission is rejected with 409 if tool status is not 'Available'
- [ ] Request submission is rejected with 403 if borrower is the tool owner
- [ ] Request submission is rejected with 400 if end date > start date + 14 days
- [ ] Request submission is rejected with 400 if start date > 90 days in future
- [ ] After submitting 5 requests in 1 hour, borrower sees warning modal before 6th submission (soft limit)
- [ ] After submitting 20 requests in 1 hour, borrower receives 429 error (hard limit)
- [ ] Owner receives in-app notification and email within 5 minutes of request submission
- [ ] Owner can view borrower's profile including: full name, neighborhood, member since, completed borrows count, average rating
- [ ] Owner can approve request with optional message (max 500 chars)
- [ ] On approval, borrower receives notification containing: approval confirmation, owner's full address, owner's phone, owner's message
- [ ] On approval, all other pending requests with overlapping dates are auto-declined with conflicting date range shown in reason
- [ ] If two owners approve overlapping requests simultaneously, second approval fails with 409 and request is auto-declined
- [ ] Owner can decline request with required reason (20-500 chars)
- [ ] On decline, borrower receives notification with owner's decline reason
- [ ] Borrower can cancel pending or approved request before pickup
- [ ] On cancellation, owner receives notification and tool's date range is released
- [ ] Owner can withdraw approval before pickup with required reason (20-500 chars)
- [ ] On withdrawal, borrower receives notification with owner's reason and tool's date range is released
- [ ] When tool status changes to 'Unavailable', all pending requests are auto-declined with system notification
- [ ] Borrower and owner can send messages (1-1000 chars) through request detail page
- [ ] Messages create in-app notification immediately for recipient
- [ ] If recipient doesn't read messages within 2 hours, recipient receives one email digest with all unread messages in thread
- [ ] If recipient reads messages before 2-hour window, no email digest is sent
- [ ] Message threads remain accessible indefinitely (no deletion) even after borrow completion
- [ ] Borrower can have multiple approved/active borrows for different tools with overlapping dates (no cross-tool blocking)
- [ ] Request list page allows filtering by role (borrower/owner), status, and toolId
- [ ] Request detail page shows status, dates, project description, messages, and user profiles
- [ ] Owner sees borrower stats (completed borrows, avg rating, on-time return rate) when reviewing request
- [ ] Borrower sees general location (neighborhood) before requesting, exact address only after approval
- [ ] Database exclusion constraint prevents overlapping approved borrows (verified via concurrent approval test)
- [ ] Valid state transitions enforced: Pending → Approved/Declined/Cancelled, Approved → Withdrawn/Cancelled/PickedUp (no backwards transitions)

---

## Security Requirements

### Authentication & Authorization
- All endpoints except public tool browsing require JWT authentication via Bearer token.
- JWT tokens expire after 24 hours (inherited from Foundation Auth).
- User can only view/modify requests where they are borrower or owner (row-level authorization).
- Attempt to approve own tool returns 403 with error: "You cannot approve requests for your own tools."

### Data Protection
- Owner's full address and phone number are excluded from API responses unless request status is 'Approved' and requester is the borrower.
- Borrower's profile visible to owner includes only: full name, neighborhood (not full address), member since date, aggregate stats (completed borrows count, average rating).
- Message content is visible only to borrower and owner of the request (no public access).
- Soft-deleted users' requests remain in database for audit but API returns 404 for any requests involving deleted users.

### Rate Limiting
- Soft limit: 5 request submissions per user per hour (warning returned, submission allowed).
- Hard limit: 20 request submissions per user per hour (HTTP 429, submission blocked).
- Rate limit counters reset on rolling 1-hour window (not fixed hourly boundaries).
- Rate limits apply per-user (identified by JWT sub claim), not per IP (to prevent shared IP issues).

### Input Validation
- All text inputs sanitized for XSS: HTML tags stripped, special chars escaped.
- Project description, owner message, decline reason, withdraw reason, and message text limited to printable UTF-8 characters (no control characters except newline/tab).
- Date inputs validated server-side to prevent time-based injection attacks (e.g., negative date ranges, year 9999 values).

### Audit Trail
- All state transitions (Pending → Approved, etc.) logged with timestamp, actor userId, and IP address.
- Message send/read events logged for dispute resolution.
- Approval attempts that fail due to exclusion constraint logged with conflicting request ID.
- Withdrawal and cancellation events logged with reason text (full audit trail retained permanently).

### Database Security
- Exclusion constraint enforced at database level (not application level) to prevent race conditions.
- All queries use parameterized statements (no string concatenation for SQL injection prevention).
- Foreign key constraints prevent orphaned requests (tool deletion cascades to requests).
- Database user account has minimal privileges (SELECT, INSERT, UPDATE on relevant tables only; no DROP, ALTER, or admin privileges).

---

## Out of Scope

- Implementation code (C#, TypeScript, SQL migrations, EF Core configurations) - engineer's responsibility.
- Test plans (unit tests, integration tests, E2E scenarios) - owned by QA spec.
- UI mockups and component designs - owned by design system.
- Pickup confirmation flow (status 'Approved' → 'PickedUp') - owned by Borrow Tracking feature (FEAT-03).
- Return confirmation flow (status 'PickedUp' → 'Returned') - owned by Borrow Tracking feature (FEAT-03).
- Rating and review submission after completion - owned by Ratings & Reviews feature (FEAT-04).
- User reputation scoring algorithm - owned by Trust & Safety feature (future).
- Dispute resolution workflow - owned by Support & Moderation feature (future).
- Push notifications (mobile app) - owned by Mobile Notifications feature (future).
- In-app chat UI/UX (message threads displayed in frontend) - owned by frontend implementation, not spec.
- Email template HTML/CSS design - owned by email service configuration, spec defines content only.
- Performance benchmarks and load testing - owned by QA spec and infrastructure team.