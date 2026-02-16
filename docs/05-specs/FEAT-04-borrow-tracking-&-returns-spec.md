# Borrow Tracking & Returns — Engineering Spec

**Type**: feature
**Component**: borrow-tracking-returns
**Dependencies**: foundation-spec, FEAT-01-tool-listing, FEAT-02-borrow-requests, FEAT-03-user-profiles
**Status**: Ready for Implementation

---

## Overview

This component manages the complete lifecycle of approved borrow transactions from pickup through return confirmation. It tracks active borrows, manages due dates and extensions, facilitates return workflows with condition reporting and dispute rebuttals, sends automated reminders via dual-channel delivery (email + in-app), flags overdue items with escalating visual indicators, and maintains permanent transaction history. The component owns the Borrow, ExtensionRequest, ReturnConfirmation, BorrowNote, BorrowReminder, Notification, and EmailDeliveryLog entities. It reads User, Tool, and BorrowRequest entities from foundation and other features but does not modify them.

---

## Data Model

### Borrow

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| borrowId | UUID | PK, not null | Generated on insert |
| borrowRequestId | UUID | FK to BorrowRequest, not null, unique | Links to approved request from FEAT-02 |
| toolId | UUID | FK to Tool, not null | Reference only, owned by FEAT-01 |
| borrowerId | UUID | FK to User, not null | Reference only, owned by foundation |
| ownerId | UUID | FK to User, not null | Reference only, owned by foundation |
| startDate | datetime | not null | UTC, set when request approved |
| originalDueDate | datetime | not null | UTC, immutable after creation |
| currentDueDate | datetime | not null | UTC, updated by extension approvals |
| status | string(50) | not null, enum | Values: Active, PendingReturnConfirmation, Completed, Cancelled |
| returnMarkedDate | datetime | nullable | UTC, set when borrower marks as returned |
| returnConfirmedDate | datetime | nullable | UTC, set when owner confirms or auto-confirms |
| returnCondition | string(50) | nullable, enum | Values: GoodCondition, HasIssues, NotYetConfirmed |
| ownerTimezone | string(100) | not null | IANA timezone ID (e.g., "America/Los_Angeles") |
| createdAt | datetime | not null | UTC |
| updatedAt | datetime | not null | UTC, auto-updated on modification |

**Indexes**:
- `(borrowerId, status, returnConfirmedDate DESC)` - for user history queries
- `(ownerId, status, returnConfirmedDate DESC)` - for owner history queries
- `(status, currentDueDate)` - for overdue flagging queries
- `(borrowRequestId)` unique - one borrow per approved request
- `(toolId, status)` - for checking tool availability

**Relationships**:
- Belongs to BorrowRequest via borrowRequestId (read-only reference)
- Belongs to Tool via toolId (read-only reference)
- Belongs to User via borrowerId (read-only reference)
- Belongs to User via ownerId (read-only reference)
- Has many ExtensionRequest (cascade delete)
- Has one ReturnConfirmation (cascade delete)
- Has many BorrowNote (cascade delete)
- Has many BorrowReminder (cascade delete)
- Has many Notification (cascade delete)

---

### ExtensionRequest

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| extensionRequestId | UUID | PK, not null | Generated on insert |
| borrowId | UUID | FK to Borrow, not null | |
| requestedDate | datetime | not null | UTC, when request submitted |
| requestedNewDueDate | datetime | not null | UTC, must be > currentDueDate |
| reason | string(500) | not null | Borrower's explanation |
| status | string(50) | not null, enum | Values: Pending, Approved, Denied, TimedOut |
| expiresAt | datetime | not null | UTC, calculated as requestedDate + 72 hours |
| responseDate | datetime | nullable | UTC, when owner responded or timeout occurred |
| responseMessage | string(500) | nullable | Owner's message if denied or counter-offer |
| respondedByUserId | UUID | FK to User, nullable | Should be ownerId or null |
| type | string(50) | not null, enum | Values: Initial, CounterOffer |
| createdAt | datetime | not null | UTC |
| updatedAt | datetime | not null | UTC |

**Indexes**:
- `(borrowId, createdAt DESC)` - for extension history
- `(status, expiresAt)` - for timeout background job
- `(borrowId, status)` - for checking pending requests

**Relationships**:
- Belongs to Borrow via borrowId
- Belongs to User via respondedByUserId (nullable reference)

---

### ReturnConfirmation

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| returnConfirmationId | UUID | PK, not null | Generated on insert |
| borrowId | UUID | FK to Borrow, not null, unique | One-to-one relationship |
| condition | string(50) | not null, enum | Values: Good, HasIssues |
| ownerNotes | string(1000) | nullable | Optional positive note for Good condition |
| issueDescription | string(1000) | nullable | Required if condition = HasIssues |
| affectsUsability | boolean | not null, default false | Checkbox value from issue report |
| confirmedDate | datetime | not null | UTC |
| confirmedBy | UUID | FK to User, not null | OwnerId or system user ID for auto-confirm |
| autoConfirmed | boolean | not null, default false | True if 7-day auto-confirm triggered |
| photos | JSON | nullable | Array of photo URLs, max 5 items |
| borrowerRebuttal | string(500) | nullable | Borrower's response to damage report |
| rebuttalAddedAt | datetime | nullable | UTC, when rebuttal submitted |
| createdAt | datetime | not null | UTC |
| updatedAt | datetime | not null | UTC |

**Indexes**:
- `(borrowId)` unique
- `(condition, createdAt)` - for filtering by outcome

**Relationships**:
- Belongs to Borrow via borrowId (one-to-one)
- Belongs to User via confirmedBy

**Validation**:
- If condition = HasIssues, issueDescription must be non-null
- If condition = Good, issueDescription must be null
- photos array max 5 items
- borrowerRebuttal can only be added if condition = HasIssues
- rebuttalAddedAt must be within 30 days of confirmedDate

---

### BorrowNote

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| borrowNoteId | UUID | PK, not null | Generated on insert |
| borrowId | UUID | FK to Borrow, not null | |
| userId | UUID | FK to User, not null | Who created the note |
| noteText | string(500) | not null | Private note content |
| createdAt | datetime | not null | UTC |

**Indexes**:
- `(borrowId, userId)` - for user's private notes on borrow
- `(userId, createdAt DESC)` - for user's all notes

**Relationships**:
- Belongs to Borrow via borrowId
- Belongs to User via userId

---

### BorrowReminder

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| borrowReminderId | UUID | PK, not null | Generated on insert |
| borrowId | UUID | FK to Borrow, not null | |
| reminderType | string(50) | not null, enum | Values: OneDayBefore, DueDate, OneDayOverdue, ThreeDaysOverdue, SevenDaysOverdue, DailyOverdue |
| sentAt | datetime | not null | UTC |
| recipientUserId | UUID | FK to User, not null | Borrower for most, owner for overdue notifications |
| deliveredVia | string(50) | not null, enum | Values: Email, InApp, Both |
| createdAt | datetime | not null | UTC |

**Indexes**:
- `(borrowId, reminderType, recipientUserId)` unique - prevent duplicate reminders
- `(borrowId, sentAt DESC)` - for reminder history
- `(sentAt)` - for cleanup queries

**Relationships**:
- Belongs to Borrow via borrowId
- Belongs to User via recipientUserId

---

### Notification

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| notificationId | UUID | PK, not null | Generated on insert |
| userId | UUID | FK to User, not null | Recipient |
| type | string(50) | not null, enum | Values: Reminder_DueSoon, Reminder_DueToday, Reminder_Overdue, Return_Marked, Return_Confirmed, Extension_Requested, Extension_Approved, Extension_Denied, Damage_Reported, Rebuttal_Added |
| title | string(200) | not null | Notification headline |
| content | string(1000) | not null | Notification body text |
| actionUrl | string(500) | nullable | Link to relevant page |
| read | boolean | not null, default false | Read status |
| createdAt | datetime | not null | UTC |
| readAt | datetime | nullable | UTC, when marked as read |

**Indexes**:
- `(userId, read, createdAt DESC)` - for unread notifications
- `(userId, createdAt DESC)` - for notification center
- `(userId, type, createdAt DESC)` - for filtering by type

**Relationships**:
- Belongs to User via userId
- Has one EmailDeliveryLog (optional)

---

### EmailDeliveryLog

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| emailDeliveryLogId | UUID | PK, not null | Generated on insert |
| notificationId | UUID | FK to Notification, nullable | Null for emails not linked to notifications |
| recipientUserId | UUID | FK to User, not null | |
| emailAddress | string(256) | not null | Email sent to |
| subject | string(200) | not null | Email subject line |
| status | string(50) | not null, enum | Values: Sent, Bounced, Failed |
| sentAt | datetime | not null | UTC |
| bouncedAt | datetime | nullable | UTC, when bounce detected |
| errorMessage | string(2000) | nullable | SMTP error details |
| createdAt | datetime | not null | UTC |

**Indexes**:
- `(notificationId)` - one-to-one lookup
- `(recipientUserId, status, sentAt DESC)` - for user email delivery history
- `(status, sentAt)` - for admin monitoring

**Relationships**:
- Belongs to Notification via notificationId (nullable)
- Belongs to User via recipientUserId

---

> **Note**: This spec owns only the entities listed above. Entities defined in the Foundation Spec (User, Group, GroupMember) and other feature specs (Tool, BorrowRequest) are referenced by name and foreign key, not redefined.

---

## API Endpoints

### GET /api/v1/borrows/active

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated user

**Query parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| role | string | no | Values: borrower, lender. Default: both |

**Success response** `200 OK`:
```json
{
  "borrowing": [
    {
      "borrowId": "uuid",
      "tool": {
        "toolId": "uuid",
        "name": "string",
        "photoUrl": "string"
      },
      "owner": {
        "userId": "uuid",
        "name": "string",
        "neighborhood": "string"
      },
      "startDate": "2025-01-10T14:30:00Z",
      "originalDueDate": "2025-01-17T18:00:00-08:00",
      "currentDueDate": "2025-01-17T18:00:00-08:00",
      "status": "Active",
      "daysRemaining": 3,
      "overdueStatus": null,
      "hasExtensionPending": false
    }
  ],
  "lending": [
    {
      "borrowId": "uuid",
      "tool": {
        "toolId": "uuid",
        "name": "string",
        "photoUrl": "string"
      },
      "borrower": {
        "userId": "uuid",
        "name": "string",
        "neighborhood": "string"
      },
      "startDate": "2025-01-10T14:30:00Z",
      "currentDueDate": "2025-01-17T18:00:00-08:00",
      "status": "PendingReturnConfirmation",
      "daysOverdue": 2,
      "overdueStatus": "yellow",
      "returnMarkedDate": "2025-01-19T10:00:00Z"
    }
  ]
}
```

**Field notes**:
- daysRemaining: positive if future, 0 if today before due time, negative if overdue
- daysOverdue: null if not overdue, else number of days past due date
- overdueStatus: null, "yellow" (1-2 days), "red" (3+ days)
- Dates returned in ISO 8601 format with timezone
- currentDueDate shown in owner's timezone
- hasExtensionPending: true if extension request exists with status=Pending

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |

---

### POST /api/v1/borrows/{borrowId}/mark-returned

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower of this borrow

**Path parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| borrowId | UUID | yes | Must exist and belong to authenticated user as borrower |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| returnNotes | string | no | Max 300 characters |

**Success response** `200 OK`:
```json
{
  "borrowId": "uuid",
  "status": "PendingReturnConfirmation",
  "returnMarkedDate": "2025-01-15T14:30:00Z",
  "message": "Return marked. Owner has been notified."
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Borrow already marked as returned or completed |
| 401 | Not authenticated |
| 403 | Not the borrower of this borrow |
| 404 | Borrow not found |

**Side effects**:
- Updates Borrow.status to PendingReturnConfirmation
- Sets Borrow.returnMarkedDate to current UTC time
- Creates Notification for owner with type Return_Marked
- Sends email to owner with subject "[Borrower] has returned your [Tool Name]"
- Creates EmailDeliveryLog entry

---

### POST /api/v1/borrows/{borrowId}/confirm-return

**Auth**: Required (Bearer JWT)
**Authorization**: Must be owner of this borrow

**Path parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| borrowId | UUID | yes | Must exist and belong to authenticated user as owner |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| condition | string | yes | Values: Good, HasIssues |
| ownerNotes | string | no | Max 1000 characters |
| issueDescription | string | conditional | Required if condition=HasIssues, max 1000 characters |
| affectsUsability | boolean | no | Default false, only relevant if condition=HasIssues |
| photos | array of strings | no | Max 5 items, each max 500 chars (URLs), only if condition=HasIssues |

**Success response** `201 Created`:
```json
{
  "returnConfirmationId": "uuid",
  "borrowId": "uuid",
  "condition": "Good",
  "confirmedDate": "2025-01-15T16:00:00Z",
  "autoConfirmed": false
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Borrow status not PendingReturnConfirmation |
| 400 | condition=HasIssues but issueDescription missing |
| 400 | condition=Good but issueDescription or photos provided |
| 400 | photos array exceeds 5 items |
| 401 | Not authenticated |
| 403 | Not the owner of this borrow |
| 404 | Borrow not found |

**Side effects**:
- Creates ReturnConfirmation entity with confirmedBy = ownerId, autoConfirmed = false
- Updates Borrow.status to Completed
- Updates Borrow.returnConfirmedDate to current UTC time
- Updates Borrow.returnCondition based on condition parameter
- If condition=HasIssues and affectsUsability=true, updates Tool.status to NeedsRepair
- Else updates Tool.status to Available
- Creates Notification for borrower with type Return_Confirmed or Damage_Reported
- Sends email to borrower
- Creates EmailDeliveryLog entry
- If condition=HasIssues, notification includes link for borrower to add rebuttal

---

### POST /api/v1/borrows/{borrowId}/extension-requests

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower of this borrow

**Path parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| borrowId | UUID | yes | Must exist and belong to authenticated user as borrower |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| requestedNewDueDate | datetime | yes | Must be > currentDueDate, max 14 days from today, total borrow duration max 28 days |
| reason | string | yes | Non-empty, max 500 characters |

**Success response** `201 Created`:
```json
{
  "extensionRequestId": "uuid",
  "borrowId": "uuid",
  "requestedNewDueDate": "2025-01-20T18:00:00-08:00",
  "reason": "string",
  "status": "Pending",
  "expiresAt": "2025-01-18T14:30:00Z",
  "requestedDate": "2025-01-15T14:30:00Z"
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Borrow is 3+ days overdue |
| 400 | Pending extension request already exists |
| 400 | requestedNewDueDate not after currentDueDate |
| 400 | Extension would exceed 28-day total duration |
| 400 | requestedNewDueDate more than 14 days from today |
| 400 | reason empty or exceeds 500 characters |
| 401 | Not authenticated |
| 403 | Not the borrower of this borrow |
| 404 | Borrow not found |

**Side effects**:
- Creates ExtensionRequest entity with status=Pending, expiresAt = requestedDate + 72h
- Creates Notification for owner with type Extension_Requested
- Sends email to owner with approve/deny links
- Creates EmailDeliveryLog entry

---

### POST /api/v1/extension-requests/{extensionRequestId}/respond

**Auth**: Required (Bearer JWT)
**Authorization**: Must be owner of the borrow

**Path parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| extensionRequestId | UUID | yes | Must exist and have status=Pending |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| action | string | yes | Values: approve, deny, counter |
| responseMessage | string | conditional | Required if action=deny, max 500 characters |
| counterOfferDate | datetime | conditional | Required if action=counter, must be > currentDueDate and <= requestedNewDueDate |

**Success response** `200 OK`:
```json
{
  "extensionRequestId": "uuid",
  "status": "Approved",
  "newDueDate": "2025-01-20T18:00:00-08:00",
  "responseDate": "2025-01-15T18:00:00Z"
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | ExtensionRequest status not Pending |
| 400 | action=deny but responseMessage missing |
| 400 | action=counter but counterOfferDate missing or invalid |
| 400 | ExtensionRequest has expired (past expiresAt) |
| 401 | Not authenticated |
| 403 | Not the owner of this borrow |
| 404 | ExtensionRequest not found |

**Side effects**:
- If action=approve:
  - Updates ExtensionRequest.status to Approved
  - Updates Borrow.currentDueDate to requestedNewDueDate
  - Clears overdue flags
  - Creates Notification for borrower with type Extension_Approved
  - Sends email to borrower
- If action=deny:
  - Updates ExtensionRequest.status to Denied
  - Stores responseMessage
  - Creates Notification for borrower with type Extension_Denied
  - Sends email to borrower with responseMessage
- If action=counter:
  - Updates ExtensionRequest.status to Denied
  - Creates new ExtensionRequest with type=CounterOffer, requestedNewDueDate=counterOfferDate
  - Creates Notification for borrower with type Extension_CounterOffer
  - Sends email to borrower
- All actions set ExtensionRequest.responseDate to current UTC time
- All actions set ExtensionRequest.respondedByUserId to authenticated user
- Creates EmailDeliveryLog entries

---

### GET /api/v1/borrows/{borrowId}

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower or owner of this borrow

**Path parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| borrowId | UUID | yes | Must exist |

**Success response** `200 OK`:
```json
{
  "borrowId": "uuid",
  "tool": {
    "toolId": "uuid",
    "name": "string",
    "photoUrl": "string"
  },
  "borrower": {
    "userId": "uuid",
    "name": "string",
    "neighborhood": "string"
  },
  "owner": {
    "userId": "uuid",
    "name": "string",
    "neighborhood": "string"
  },
  "startDate": "2025-01-10T14:30:00Z",
  "originalDueDate": "2025-01-17T18:00:00-08:00",
  "currentDueDate": "2025-01-17T18:00:00-08:00",
  "status": "Completed",
  "returnMarkedDate": "2025-01-17T10:00:00Z",
  "returnConfirmedDate": "2025-01-17T16:00:00Z",
  "daysLate": 0,
  "extensionHistory": [
    {
      "extensionRequestId": "uuid",
      "requestedDate": "2025-01-12T10:00:00Z",
      "requestedNewDueDate": "2025-01-20T18:00:00-08:00",
      "reason": "string",
      "status": "Approved",
      "responseDate": "2025-01-12T14:00:00Z",
      "responseMessage": null
    }
  ],
  "returnConfirmation": {
    "returnConfirmationId": "uuid",
    "condition": "HasIssues",
    "issueDescription": "string",
    "photos": ["url1", "url2"],
    "affectsUsability": true,
    "confirmedDate": "2025-01-17T16:00:00Z",
    "autoConfirmed": false,
    "borrowerRebuttal": "string",
    "rebuttalAddedAt": "2025-01-18T10:00:00Z"
  },
  "userNote": "string"
}
```

**Field notes**:
- daysLate: 0 if not late, else number of days between currentDueDate and returnConfirmedDate
- userNote: private note for authenticated user if exists
- extensionHistory: all extension requests, chronological
- returnConfirmation: null if not yet confirmed

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | Not borrower or owner of this borrow |
| 404 | Borrow not found |

---

### GET /api/v1/borrows/history

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated user

**Query parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| role | string | no | Values: borrower, lender. Default: both |
| startDate | datetime | no | ISO 8601 format |
| endDate | datetime | no | ISO 8601 format, must be >= startDate |
| search | string | no | Case-insensitive partial match on tool name or other party name |
| outcome | string | no | Values: good, issues, cancelled |
| page | integer | no | Default 1, min 1 |
| pageSize | integer | no | Default 20, min 1, max 100 |

**Success response** `200 OK`:
```json
{
  "items": [
    {
      "borrowId": "uuid",
      "tool": {
        "toolId": "uuid",
        "name": "string",
        "photoUrl": "string"
      },
      "otherParty": {
        "userId": "uuid",
        "name": "string",
        "neighborhood": "string"
      },
      "role": "borrower",
      "startDate": "2025-01-10T14:30:00Z",
      "endDate": "2025-01-17T16:00:00Z",
      "durationDays": 7,
      "daysLate": 0,
      "status": "Completed",
      "outcome": "Good",
      "autoConfirmed": false,
      "hasIssues": false,
      "hasRebuttal": false,
      "rating": {
        "given": 5,
        "received": 5
      }
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 45,
    "totalPages": 3
  }
}
```

**Field notes**:
- role: borrower or lender from authenticated user's perspective
- outcome: "Good", "HasIssues", or "Cancelled"
- endDate: returnConfirmedDate if Completed, cancellation date if Cancelled
- rating.given: rating authenticated user gave to other party (null if not rated)
- rating.received: rating other party gave to authenticated user (null if not rated)

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid query parameters |
| 401 | Not authenticated |

---

### POST /api/v1/borrows/{borrowId}/notes

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower or owner of this borrow

**Path parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| borrowId | UUID | yes | Must exist |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| noteText | string | yes | Non-empty, max 500 characters |

**Success response** `201 Created`:
```json
{
  "borrowNoteId": "uuid",
  "borrowId": "uuid",
  "noteText": "string",
  "createdAt": "2025-01-15T14:30:00Z"
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | noteText empty or exceeds 500 characters |
| 401 | Not authenticated |
| 403 | Not borrower or owner of this borrow |
| 404 | Borrow not found |

**Side effects**:
- Creates BorrowNote entity with userId = authenticated user

---

### POST /api/v1/return-confirmations/{returnConfirmationId}/rebuttal

**Auth**: Required (Bearer JWT)
**Authorization**: Must be borrower of this borrow

**Path parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| returnConfirmationId | UUID | yes | Must exist and have condition=HasIssues |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| rebuttalText | string | yes | Non-empty, max 500 characters |

**Success response** `201 Created`:
```json
{
  "returnConfirmationId": "uuid",
  "borrowerRebuttal": "string",
  "rebuttalAddedAt": "2025-01-18T10:00:00Z"
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | ReturnConfirmation.condition = Good (no issues to dispute) |
| 400 | Rebuttal already exists |
| 400 | More than 30 days since confirmedDate |
| 400 | rebuttalText empty or exceeds 500 characters |
| 401 | Not authenticated |
| 403 | Not the borrower of this borrow |
| 404 | ReturnConfirmation not found |

**Side effects**:
- Updates ReturnConfirmation.borrowerRebuttal with rebuttalText
- Sets ReturnConfirmation.rebuttalAddedAt to current UTC time
- Creates Notification for owner with type Rebuttal_Added
- Sends email to owner
- Creates EmailDeliveryLog entry

---

### GET /api/v1/notifications

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated user

**Query parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| unreadOnly | boolean | no | Default false |
| type | string | no | Notification type filter |
| page | integer | no | Default 1, min 1 |
| pageSize | integer | no | Default 20, min 1, max 100 |

**Success response** `200 OK`:
```json
{
  "items": [
    {
      "notificationId": "uuid",
      "type": "Reminder_DueSoon",
      "title": "string",
      "content": "string",
      "actionUrl": "/borrows/uuid",
      "read": false,
      "createdAt": "2025-01-15T14:30:00Z",
      "readAt": null
    }
  ],
  "unreadCount": 5,
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 45,
    "totalPages": 3
  }
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 