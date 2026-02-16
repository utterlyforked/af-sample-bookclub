# Borrowing Request & Communication System — Engineering Spec

**Type**: feature
**Component**: borrowing-request-communication
**Dependencies**: foundation-spec
**Status**: Ready for Implementation

---

## Overview

This component enables users to request tools from other users and communicate about those requests. It owns the BorrowRequest and Message entities, managing the complete lifecycle from request submission through approval/denial to eventual return. Users can send messages associated with specific borrow requests. This component reads from foundation entities (User, Tool, ToolAvailability) but does not modify them.

---

## Data Model

### BorrowRequest

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| toolId | UUID | FK Tool(id), not null | Tool being requested |
| borrowerId | UUID | FK User(id), not null | User requesting to borrow |
| ownerId | UUID | FK User(id), not null | Tool owner (denormalized from Tool) |
| status | string(20) | not null, check constraint | One of: pending, approved, rejected, cancelled, active, returned, completed |
| requestedStartDate | date | not null | Cannot be in the past at creation |
| requestedEndDate | date | not null | Must be >= requestedStartDate |
| approvedAt | datetime | nullable | UTC timestamp when status changed to approved |
| rejectedAt | datetime | nullable | UTC timestamp when status changed to rejected |
| rejectionReason | string(500) | nullable | Required when status is rejected |
| cancelledAt | datetime | nullable | UTC timestamp when status changed to cancelled |
| cancellationReason | string(500) | nullable | Required when status is cancelled |
| pickedUpAt | datetime | nullable | UTC timestamp when borrower confirmed pickup (status becomes active) |
| returnedAt | datetime | nullable | UTC timestamp when owner confirmed return |
| createdAt | datetime | not null | UTC timestamp |
| updatedAt | datetime | not null | UTC timestamp, auto-updated on change |

**Indexes**:
- `(toolId, status)` for owner's request list filtering
- `(borrowerId, status)` for borrower's request list filtering
- `(ownerId, status)` for owner's incoming requests
- `(status, requestedStartDate)` for date-based queries

**Relationships**:
- Belongs to `Tool` via `toolId`
- Belongs to `User` (borrower) via `borrowerId`
- Belongs to `User` (owner) via `ownerId`
- Has many `Message` (cascade delete)

**Check Constraints**:
- `status IN ('pending', 'approved', 'rejected', 'cancelled', 'active', 'returned', 'completed')`
- `requestedEndDate >= requestedStartDate`
- `(status = 'rejected' AND rejectionReason IS NOT NULL) OR status != 'rejected'`
- `(status = 'cancelled' AND cancellationReason IS NOT NULL) OR status != 'cancelled'`

### Message

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| borrowRequestId | UUID | FK BorrowRequest(id), not null | Request this message belongs to |
| senderId | UUID | FK User(id), not null | User who sent the message |
| content | string(2000) | not null | Message text |
| isRead | boolean | not null, default false | Whether recipient has read the message |
| readAt | datetime | nullable | UTC timestamp when marked as read |
| createdAt | datetime | not null | UTC timestamp |

**Indexes**:
- `(borrowRequestId, createdAt)` for chronological message retrieval
- `(borrowRequestId, isRead)` for unread message counts

**Relationships**:
- Belongs to `BorrowRequest` via `borrowRequestId`
- Belongs to `User` via `senderId`

> **Note**: This spec owns only the entities listed above. Entities defined in the Foundation Spec (User, Tool, ToolAvailability, Location, Category) are referenced by name, not redefined.

---

## API Endpoints

### POST /api/v1/borrow-requests

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated (user cannot request their own tools)

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| toolId | UUID | yes | Must exist, must not be owned by requester, tool must be available |
| requestedStartDate | ISO 8601 date | yes | Cannot be in the past, max 365 days in future |
| requestedEndDate | ISO 8601 date | yes | Must be >= requestedStartDate, max 90 days duration |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| toolId | UUID | |
| borrowerId | UUID | |
| ownerId | UUID | |
| status | string | Always "pending" on creation |
| requestedStartDate | ISO 8601 date | |
| requestedEndDate | ISO 8601 date | |
| createdAt | ISO 8601 datetime | UTC |
| updatedAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure — returns field-level errors |
| 401 | Not authenticated |
| 403 | User attempting to request their own tool |
| 404 | Tool not found |
| 409 | Tool not available for requested dates (overlaps with approved/active request or maintenance) |
| 422 | Borrower has open pending request for this tool already |

---

### GET /api/v1/borrow-requests

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated

**Query parameters**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| role | string | no | One of: borrower, owner. Default: both |
| status | string | no | Comma-separated statuses to filter. Default: all |
| page | integer | no | Min 1, default 1 |
| pageSize | integer | no | Min 1, max 100, default 20 |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| items | array | Array of borrow request objects (same structure as POST response, plus tool/user details) |
| totalCount | integer | Total matching records |
| page | integer | Current page |
| pageSize | integer | Items per page |

Each item in `items` includes:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| toolId | UUID | |
| tool | object | { id, name, imageUrl } |
| borrowerId | UUID | |
| borrower | object | { id, name, avatarUrl } |
| ownerId | UUID | |
| owner | object | { id, name, avatarUrl } |
| status | string | |
| requestedStartDate | ISO 8601 date | |
| requestedEndDate | ISO 8601 date | |
| approvedAt | ISO 8601 datetime | nullable |
| rejectedAt | ISO 8601 datetime | nullable |
| rejectionReason | string | nullable |
| cancelledAt | ISO 8601 datetime | nullable |
| cancellationReason | string | nullable |
| pickedUpAt | ISO 8601 datetime | nullable |
| returnedAt | ISO 8601 datetime | nullable |
| unreadMessageCount | integer | Unread messages for current user in this request |
| createdAt | ISO 8601 datetime | UTC |
| updatedAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid query parameters |
| 401 | Not authenticated |

---

### GET /api/v1/borrow-requests/{id}

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower or owner of the request

**Success response** `200 OK`:
Same structure as individual item from GET /api/v1/borrow-requests

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is neither borrower nor owner |
| 404 | Request not found |

---

### PATCH /api/v1/borrow-requests/{id}/approve

**Auth**: Required (Bearer JWT)
**Authorization**: Must be owner of the tool, request must be in pending status

**Request body**: Empty

**Success response** `200 OK`:
Same structure as GET /api/v1/borrow-requests/{id}

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is not the owner |
| 404 | Request not found |
| 409 | Request is not in pending status |
| 422 | Tool availability conflict (another request was approved after this one was created) |

---

### PATCH /api/v1/borrow-requests/{id}/reject

**Auth**: Required (Bearer JWT)
**Authorization**: Must be owner of the tool, request must be in pending status

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| reason | string | yes | Non-empty, max 500 chars |

**Success response** `200 OK`:
Same structure as GET /api/v1/borrow-requests/{id}

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure on reason |
| 401 | Not authenticated |
| 403 | User is not the owner |
| 404 | Request not found |
| 409 | Request is not in pending status |

---

### PATCH /api/v1/borrow-requests/{id}/cancel

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower, request must be in pending or approved status

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| reason | string | yes | Non-empty, max 500 chars |

**Success response** `200 OK`:
Same structure as GET /api/v1/borrow-requests/{id}

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure on reason |
| 401 | Not authenticated |
| 403 | User is not the borrower |
| 404 | Request not found |
| 409 | Request is not in pending or approved status |

---

### PATCH /api/v1/borrow-requests/{id}/confirm-pickup

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower, request must be in approved status

**Request body**: Empty

**Success response** `200 OK`:
Same structure as GET /api/v1/borrow-requests/{id}

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is not the borrower |
| 404 | Request not found |
| 409 | Request is not in approved status |

---

### PATCH /api/v1/borrow-requests/{id}/confirm-return

**Auth**: Required (Bearer JWT)
**Authorization**: Must be owner of the tool, request must be in active status

**Request body**: Empty

**Success response** `200 OK`:
Same structure as GET /api/v1/borrow-requests/{id}

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is not the owner |
| 404 | Request not found |
| 409 | Request is not in active status |

---

### POST /api/v1/borrow-requests/{borrowRequestId}/messages

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower or owner of the request

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| content | string | yes | Non-empty, max 2000 chars |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| borrowRequestId | UUID | |
| senderId | UUID | |
| sender | object | { id, name, avatarUrl } |
| content | string | |
| isRead | boolean | Always false on creation |
| readAt | ISO 8601 datetime | Always null on creation |
| createdAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure on content |
| 401 | Not authenticated |
| 403 | User is neither borrower nor owner |
| 404 | Borrow request not found |

---

### GET /api/v1/borrow-requests/{borrowRequestId}/messages

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower or owner of the request

**Query parameters**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| page | integer | no | Min 1, default 1 |
| pageSize | integer | no | Min 1, max 100, default 50 |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| items | array | Array of message objects (same structure as POST response) |
| totalCount | integer | Total messages in this request |
| page | integer | Current page |
| pageSize | integer | Items per page |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid query parameters |
| 401 | Not authenticated |
| 403 | User is neither borrower nor owner |
| 404 | Borrow request not found |

---

### PATCH /api/v1/messages/{id}/mark-read

**Auth**: Required (Bearer JWT)
**Authorization**: Must be the recipient (not the sender) of the message

**Request body**: Empty

**Success response** `200 OK`:
Same structure as POST /api/v1/borrow-requests/{borrowRequestId}/messages response

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is the sender (cannot mark own message as read) or not participant in request |
| 404 | Message not found |
| 409 | Message already marked as read |

---

## Business Rules

1. A user cannot create a borrow request for a tool they own.
2. A user can have at most one pending borrow request per tool at any time.
3. A tool can have at most one approved or active borrow request at any given time.
4. Requested start date cannot be more than 365 days in the future at time of creation.
5. Maximum borrow duration is 90 days (requestedEndDate - requestedStartDate ≤ 90).
6. Only the tool owner can approve or reject a pending request.
7. Only the borrower can cancel a pending or approved request.
8. Approval checks for date conflicts with existing approved/active requests and tool maintenance periods from ToolAvailability.
9. Status transitions are enforced: pending → (approved | rejected | cancelled), approved → (active | cancelled), active → returned → completed.
10. Once a request reaches rejected, cancelled, or completed status, it cannot change status again.
11. The ownerId field is denormalized from Tool at request creation time and does not update if tool ownership changes.
12. Messages can only be sent by the borrower or owner of the associated borrow request.
13. A message can only be marked as read by the recipient (the user who did not send it).
14. Marking a message as read is idempotent (no error if already read, but returns 409 for clarity).
15. When a request status changes to active, the corresponding ToolAvailability period (if one exists) should be referenced but not modified by this component.

---

## Validation Rules

| Field | Rule | Error message |
|-------|------|---------------|
| toolId (request) | Required, valid UUID, tool must exist, must not be owned by requester | "Tool ID is required" / "Invalid tool ID" / "Tool not found" / "Cannot request your own tool" |
| requestedStartDate | Required, valid ISO 8601 date, cannot be in past, max 365 days future | "Start date is required" / "Invalid date format" / "Start date cannot be in the past" / "Start date too far in future" |
| requestedEndDate | Required, valid ISO 8601 date, must be >= requestedStartDate, max 90 days from start | "End date is required" / "Invalid date format" / "End date must be on or after start date" / "Borrow duration cannot exceed 90 days" |
| reason (reject) | Required, non-empty after trim, max 500 chars | "Reason is required" / "Reason cannot be empty" / "Reason too long (max 500 characters)" |
| reason (cancel) | Required, non-empty after trim, max 500 chars | "Reason is required" / "Reason cannot be empty" / "Reason too long (max 500 characters)" |
| content (message) | Required, non-empty after trim, max 2000 chars | "Message content is required" / "Message cannot be empty" / "Message too long (max 2000 characters)" |
| role (query param) | If provided, must be "borrower" or "owner" | "Invalid role parameter" |
| status (query param) | If provided, comma-separated valid statuses | "Invalid status value" |
| page (query param) | Min 1 | "Page must be at least 1" |
| pageSize (query param) | Min 1, max 100 | "Page size must be between 1 and 100" |

---

## Authorization

| Action | Required policy | Notes |
|--------|----------------|-------|
| Create borrow request | Authenticated | Must not own the tool being requested |
| List borrow requests | Authenticated | User sees only requests where they are borrower or owner |
| View borrow request | Authenticated | Must be borrower or owner of the request |
| Approve request | Authenticated, must be owner | Request must be in pending status |
| Reject request | Authenticated, must be owner | Request must be in pending status |
| Cancel request | Authenticated, must be borrower | Request must be in pending or approved status |
| Confirm pickup | Authenticated, must be borrower | Request must be in approved status |
| Confirm return | Authenticated, must be owner | Request must be in active status |
| Send message | Authenticated | Must be borrower or owner of the request |
| List messages | Authenticated | Must be borrower or owner of the request |
| Mark message as read | Authenticated | Must be recipient (not sender) of the message |

---

## Acceptance Criteria

- [ ] Authenticated user can create a borrow request for a tool they do not own with valid dates
- [ ] Creating a request with start date in the past returns 400
- [ ] Creating a request with duration exceeding 90 days returns 400
- [ ] Creating a request with start date more than 365 days in future returns 400
- [ ] User cannot create a borrow request for their own tool (returns 403)
- [ ] User cannot create multiple pending requests for the same tool (returns 422)
- [ ] Tool owner can approve a pending request
- [ ] Tool owner can reject a pending request with a reason
- [ ] Borrower can cancel a pending or approved request with a reason
- [ ] Approving a request when tool has conflicting approved/active request returns 422
- [ ] Approving a request when tool has overlapping maintenance period returns 422
- [ ] User who is neither borrower nor owner cannot view request details (returns 403)
- [ ] User can list borrow requests filtered by role (borrower, owner, or both)
- [ ] User can list borrow requests filtered by status
- [ ] Borrower can confirm pickup of an approved request, changing status to active
- [ ] Owner can confirm return of an active request, changing status to returned
- [ ] Attempting status transitions out of order returns 409
- [ ] Attempting to change status of completed/rejected/cancelled request returns 409
- [ ] Borrower or owner can send a message on a borrow request
- [ ] User who is neither borrower nor owner cannot send message (returns 403)
- [ ] Messages are returned in chronological order
- [ ] Recipient can mark a message as read
- [ ] Sender cannot mark their own message as read (returns 403)
- [ ] Marking already-read message as read returns 409
- [ ] Unread message count is accurate in borrow request list and detail responses
- [ ] Pagination works correctly for borrow requests list
- [ ] Pagination works correctly for messages list
- [ ] Deleting a borrow request cascades to delete all associated messages
- [ ] All timestamps are stored and returned in UTC
- [ ] Email notifications are not sent by this component (handled by separate notification system reading events)

---

## Security Requirements

- All endpoints require authentication via Bearer JWT token (except none explicitly marked public).
- Authorization checks must occur before any business logic or database queries that reveal resource existence.
- Ensure borrowRequestId and messageId lookups verify the authenticated user has access (borrower or owner) before returning data or errors that confirm existence.
- Rejection reason and cancellation reason fields are visible to both borrower and owner — no sensitive data should be entered.
- Messages are visible to both borrower and owner of the request — treat as semi-public within that context.
- Input validation must prevent injection attacks: all string inputs are parameterized in database queries, max lengths enforced.
- Rate limiting (defined at API gateway level, not in this spec): max 100 requests per user per minute for borrow request creation.
- Rate limiting for message sending: max 50 messages per user per borrow request per hour to prevent spam.
- Audit logging (handled by foundation middleware) must capture all status changes and message sends with user ID and timestamp.

---

## Out of Scope

- Email or push notifications when request status changes (handled by separate notification system)
- Real-time message delivery via WebSockets (future enhancement, messages are polled via API)
- Ratings or reviews of borrowers/owners (separate feature)
- Payment or deposit handling (separate feature if required)
- Image attachments in messages (future enhancement)
- Editing or deleting messages after send (intentionally excluded for audit trail)
- Tool owner delegate permissions (only tool owner can approve/reject)
- Automated approval based on owner preferences (future enhancement)
- In-app notifications UI (frontend responsibility)
- Test plans (owned by QA spec)
- Implementation code (engineer's responsibility)
- Database migration scripts (engineer's responsibility)
- Specific EF Core configuration or DbContext setup (engineer's responsibility)