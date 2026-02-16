# Borrowing Requests - Technical Review (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: 2025-01-10

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. The v1.1 iteration has comprehensively addressed all critical questions from the previous review, providing clear technical guidance on race conditions, data modeling, state management, and edge case handling.

The specification now includes:
- Explicit database-level constraints for double-booking prevention
- Complete state machine for request lifecycle
- Detailed notification policies with batching rules
- Clear integration points with other features
- Well-defined edge case behaviors

All critical ambiguities have been resolved with concrete implementation decisions.

---

## What's Clear

### Data Model

**BorrowRequest Entity** (single-table design):
- Complete schema provided with all fields typed (`Guid`, `DateOnly`, `DateTime`, `string`)
- Character limits specified: ProjectDescription (50-500), OwnerMessage (max 500), DeclineReason (20-500), WithdrawReason (min 20)
- Nullable fields clearly marked (`OwnerMessage?`, `DeclineReason?`, `WithdrawReason?`)
- Timestamp fields for lifecycle tracking: `CreatedAt`, `RespondedAt`, `PickedUpAt`, `ReturnedAt`
- Navigation properties to `Tool`, `User` (Borrower), `User` (Owner), `RequestMessage` collection

**Status Enum**:
- 8 states defined: `Pending`, `Approved`, `Declined`, `Cancelled`, `Withdrawn`, `PickedUp`, `Returned`, `Completed`
- Valid transitions explicitly documented (e.g., `Pending → Approved/Declined/Cancelled`, `Approved → Withdrawn/Cancelled/PickedUp`)
- Terminal states clear: `Declined`, `Cancelled`, `Withdrawn`, `Completed`

**Database Constraints**:
- PostgreSQL exclusion constraint using GiST index:
  ```sql
  EXCLUDE USING GIST (
    ToolId WITH =, 
    daterange(RequestedStartDate, RequestedEndDate, '[]') WITH &&
  ) WHERE (Status = 'Approved')
  ```
- Ensures no overlapping approved borrows for same tool at schema level
- Foreign keys: `ToolId → Tools`, `BorrowerUserId → Users`, `OwnerUserId → Users`

### Business Logic

**Request Submission**:
- Available tools only (status check before allowing request)
- Start date: today or future
- End date: maximum 14 days from start
- ProjectDescription: required, 50-500 characters
- No cross-tool validation (users can request multiple tools for overlapping dates)
- Soft rate limiting: warning after 5 requests in 1 hour, but submission proceeds

**Double-Booking Prevention**:
- Optimistic locking with database exclusion constraint
- Race condition handling: constraint violation caught, second request auto-declined
- Owner who lost the race sees error: "Someone else was just approved for these dates"
- Auto-declined borrower sees: "Tool is already borrowed [date range]. Try different dates."

**Owner Review**:
- Can view borrower profile: full name, neighborhood, member since, borrow count, average rating, reviews
- Approve with optional message (max 500 chars) OR decline with required reason (max 500 chars)
- Can withdraw approval before pickup with required reason (min 20 chars)

**Cancellation Rules**:
- Borrower can cancel approved request any time before pickup (even after start date passes)
- Owner can withdraw approval before pickup
- Both actions release tool's calendar dates immediately
- Both actions require notification to other party

**Tool Unavailability Impact**:
- When tool marked unavailable, all pending requests auto-declined
- System notification sent: "Owner has temporarily marked this tool as unavailable"
- Already-approved requests NOT affected (owner must manually withdraw)

**Message Threading**:
- In-app messaging for coordination
- 2-hour digest batching: if message unread after 2 hours, send one email with all unread messages in thread
- Threads retained permanently (no deletion)
- Threads become read-only after completion

### API Design

**Request Submission Endpoint**:
- `POST /api/v1/borrow-requests`
- Body: `{ toolId, requestedStartDate, requestedEndDate, projectDescription }`
- Validations: tool availability, date range (max 14 days), description length (50-500)
- Returns: `201 Created` with `BorrowRequest` DTO
- Triggers: notification to owner (email + in-app)

**Owner Response Endpoint**:
- `PATCH /api/v1/borrow-requests/{id}/approve` with optional `{ message }`
- `PATCH /api/v1/borrow-requests/{id}/decline` with required `{ reason }`
- Validations: only owner can respond, request must be Pending
- Returns: `200 OK` with updated `BorrowRequest`
- Triggers: notification to borrower, auto-decline conflicting requests on approval
- Error: `409 Conflict` if constraint violation (double-booking), request auto-declined

**Cancellation Endpoints**:
- `PATCH /api/v1/borrow-requests/{id}/cancel` (borrower only, while Approved/Pending)
- `PATCH /api/v1/borrow-requests/{id}/withdraw` (owner only, while Approved) with required `{ reason }`
- Validations: only requester/owner can cancel/withdraw, status must allow transition
- Returns: `200 OK`
- Triggers: notification to other party, calendar dates released

**Messaging Endpoint**:
- `POST /api/v1/borrow-requests/{id}/messages` with `{ content }`
- Authorization: only borrower or owner of request
- Returns: `201 Created` with `RequestMessage`
- Triggers: in-app notification immediately, schedule 2-hour email digest job

**Query Endpoints**:
- `GET /api/v1/borrow-requests/sent` (borrower's outgoing requests)
- `GET /api/v1/borrow-requests/received` (owner's incoming requests)
- Query params: `?status=Pending,Approved&page=1&pageSize=20`
- Returns: paginated list with tool details, user details, status

### Authorization

**Request Submission**:
- Any authenticated user can submit request (excluding owner of the tool)

**Request Response**:
- Only tool owner can approve/decline/withdraw
- Request must be in valid state for action (Pending for approve/decline, Approved for withdraw)

**Cancellation**:
- Only borrower can cancel own request
- Only while status is Pending or Approved (before pickup)

**Messaging**:
- Only borrower and owner can send messages on request thread
- Read-only access after status = Completed

**Profile Viewing**:
- Owner can view borrower's profile when reviewing request
- Borrower cannot view owner's profile until approved (privacy protection)

### UI/UX

**Request Submission Form**:
- Tool name + image shown at top
- Date pickers: "Start Date" (default today), "End Date" (default today + 1 day, max start + 14 days)
- Textarea: "What will you use this for?" (placeholder, 50-500 char counter)
- Submit button: "Send Request"
- Validation errors shown inline

**Borrower Dashboard - Sent Requests**:
- Tabs: "Pending" (default), "Approved", "Declined/Cancelled", "Active" (PickedUp), "Completed"
- Each request card shows: tool name, dates, status badge, owner name (if approved), project description
- Actions: "Cancel" (if Pending/Approved), "Message Owner" (if Approved), "Confirm Pickup" (if Approved, handled by Borrow Tracking feature)

**Owner Dashboard - Received Requests**:
- Tabs: "Pending" (default), "Approved", "Declined", "Active", "Completed"
- Each request card shows: tool name, dates, borrower name, project description, "View Profile" link
- Actions: "Approve", "Decline" (if Pending), "Withdraw" (if Approved), "Message Borrower"

**Borrower Profile Modal** (for owner review):
- Full name, neighborhood (not full address), member since
- Stats: "X successful borrows", "Y.Y average rating"
- Recent reviews from previous owners (if any)
- Close button

**Approval Modal**:
- Title: "Approve Request from [Borrower]"
- Body: "You're approving [Tool] for [dates]. [Borrower] will receive your address and phone number."
- Textarea: "Optional message (pickup instructions, rules, etc.)" - max 500 chars
- Buttons: "Cancel" (gray), "Approve & Share Address" (green)

**Decline Modal**:
- Title: "Decline Request from [Borrower]"
- Body: "Please let [Borrower] know why you can't lend your [Tool]. Be respectful - they might request again later."
- Textarea: "Reason for declining" - required, 20-500 chars, char counter
- Buttons: "Cancel" (gray), "Send Decline" (red)

**Withdraw Modal**:
- Title: "Withdraw Approval"
- Body: "This will notify [Borrower] that the borrow is cancelled. Please explain why:"
- Textarea: required, 20-500 chars
- Buttons: "Cancel" (gray), "Withdraw Approval" (red)

**Auto-Decline Notification** (in-app + email):
- Subject: "Your request for [Tool] couldn't be approved"
- Body: "This tool is already borrowed **Jan 12-15**. Try requesting dates before Jan 12 or after Jan 15."
- Button: "Request Again" (pre-fills tool in submission form)

**Rate Limit Warning Modal**:
- Title: "You've submitted several requests recently"
- Body: "You've requested 5 tools in the past hour. Consider waiting for responses before requesting more. Requesting many tools at once may reduce your approval rate."
- Buttons: "Go Back" (gray), "Submit Anyway" (yellow)

**Message Thread**:
- Chat-style interface (messages on left/right by sender)
- Input box at bottom: "Send message" button
- Timestamps on each message
- Read-only after status = Completed
- No delete button (permanent record)

### Edge Cases

**Constraint Violation Handling**:
- Database timeout (>30 sec): return `504 Gateway Timeout`, prompt owner to retry
- Simultaneous approvals: second fails, auto-declines, owner sees error
- Simultaneous declines: idempotent, both succeed
- Request deleted during approval: return `404 Not Found`

**Cancellation Race Conditions**:
- Borrower cancels while owner approving: whoever's transaction commits first wins
- Multiple cancellation clicks: idempotent, first succeeds, subsequent return 400 "already cancelled"

**Notification Failures**:
- Email bounce: log error, don't block request lifecycle, user still sees in-app notification
- In-app notification delivery: use persistent connection (SignalR/WebSockets) with fallback to polling

**Calendar Edge Cases**:
- Same-day requests: allowed even at 11:59 PM (no minimum notice)
- Past start dates with Pending status: allowed (request doesn't auto-expire in v1)
- Overlapping dates with borrower's other requests: allowed (no cross-tool validation)

**Tool Status Changes**:
- Tool marked unavailable: auto-decline all Pending requests, keep Approved requests
- Tool deleted: cascade soft-delete to requests (retain for history), show "Tool no longer available" in UI

**Message Batching Edge Cases**:
- User reads messages at 1:59 (before 2-hour window): email job finds no unread messages, doesn't send
- User never reads messages: emails keep sending every 2 hours per new message batch
- Multiple threads: independent timers, user might receive multiple digest emails

---

## Implementation Notes

### Database

**BorrowRequest Table**:
```sql
CREATE TABLE BorrowRequests (
    Id UUID PRIMARY KEY,
    ToolId UUID NOT NULL REFERENCES Tools(Id),
    BorrowerUserId UUID NOT NULL REFERENCES Users(Id),
    OwnerUserId UUID NOT NULL REFERENCES Users(Id),
    
    RequestedStartDate DATE NOT NULL,
    RequestedEndDate DATE NOT NULL,
    ProjectDescription VARCHAR(500) NOT NULL,
    
    Status VARCHAR(20) NOT NULL, -- enum
    CreatedAt TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    RespondedAt TIMESTAMPTZ,
    PickedUpAt TIMESTAMPTZ,
    ReturnedAt TIMESTAMPTZ,
    
    OwnerMessage VARCHAR(500),
    DeclineReason VARCHAR(500),
    WithdrawReason VARCHAR(500),
    
    CHECK (LENGTH(ProjectDescription) >= 50),
    CHECK (RequestedEndDate <= RequestedStartDate + INTERVAL '14 days'),
    CHECK (Status IN ('Pending', 'Approved', 'Declined', 'Cancelled', 'Withdrawn', 'PickedUp', 'Returned', 'Completed'))
);

-- Exclusion constraint for double-booking prevention
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE BorrowRequests 
ADD CONSTRAINT no_overlapping_approved_borrows 
EXCLUDE USING GIST (
    ToolId WITH =, 
    daterange(RequestedStartDate, RequestedEndDate, '[]') WITH &&
) WHERE (Status = 'Approved');

-- Indexes
CREATE INDEX idx_borrow_requests_borrower ON BorrowRequests(BorrowerUserId, Status, CreatedAt DESC);
CREATE INDEX idx_borrow_requests_owner ON BorrowRequests(OwnerUserId, Status, CreatedAt DESC);
CREATE INDEX idx_borrow_requests_tool ON BorrowRequests(ToolId, Status, RequestedStartDate);
```

**RequestMessages Table** (referenced but not fully specified in PRD):
```sql
CREATE TABLE RequestMessages (
    Id UUID PRIMARY KEY,
    BorrowRequestId UUID NOT NULL REFERENCES BorrowRequests(Id),
    SenderUserId UUID NOT NULL REFERENCES Users(Id),
    RecipientUserId UUID NOT NULL REFERENCES Users(Id),
    Content TEXT NOT NULL,
    SentAt TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ReadAt TIMESTAMPTZ,
    EmailSentAt TIMESTAMPTZ
);

CREATE INDEX idx_request_messages_thread ON RequestMessages(BorrowRequestId, SentAt);
CREATE INDEX idx_request_messages_recipient_unread ON RequestMessages(RecipientUserId, ReadAt) WHERE ReadAt IS NULL;
```

### Authorization

**Policy-Based Authorization**:
- `CanReviewRequestPolicy`: User is tool owner AND request status is Pending
- `CanWithdrawApprovalPolicy`: User is tool owner AND request status is Approved AND pickup hasn't occurred
- `CanCancelRequestPolicy`: User is borrower AND request status is Pending/Approved AND pickup hasn't occurred
- `CanMessageRequestPolicy`: User is borrower OR owner AND request status is not Cancelled/Declined/Withdrawn

### Validation

**Request Submission**:
- Tool exists and Status = 'Available'
- Start date >= today
- End date <= start date + 14 days
- ProjectDescription: 50-500 characters
- User is not tool owner
- Tool not marked as unavailable

**Owner Response**:
- Approve: optional OwnerMessage max 500 characters
- Decline: required DeclineReason 20-500 characters
- Only while status = Pending

**Withdrawal**:
- Required WithdrawReason min 20 characters
- Only while status = Approved
- Cannot withdraw after pickup (status = PickedUp)

**Messages**:
- Content required, max 2000 characters (reasonable for coordination)
- Recipient must be other party (borrower if sender is owner, vice versa)

### Key Decisions

**Single-Table Design**:
- `BorrowRequest` tracks entire lifecycle (no separate "ActiveBorrow" entity)
- Simplifies queries: "show my active borrows" = `WHERE status IN (Approved, PickedUp)`
- State transitions managed through status enum

**Database-Level Concurrency Control**:
- Exclusion constraint prevents race conditions at source of truth
- Application catches `ConstraintViolationException`, auto-declines conflicting request
- No application-level locks needed (simpler, more reliable)

**Notification Batching**:
- Background job scheduled at `messageTime + 2 hours`
- Query unread messages, send digest if any exist
- Mark `EmailSentAt` to prevent duplicates

**No Cross-Tool Validation**:
- Users can have overlapping borrows of different tools
- Social reputation (reviews) corrects over-commitment behavior
- Owner sees borrower's other active borrows in profile for context

**Same-Day Requests Allowed**:
- No minimum notice period
- Owner responsibility to respond or decline if timing doesn't work
- Aligns with real-world spontaneous tool needs

**Permanent Message Retention**:
- Text storage is cheap (~1KB per message)
- Complete audit trail protects both parties
- No deletion functionality (prevents evidence tampering)

---

## Recommended Next Steps

1. **Create engineering specification** with:
   - API endpoint definitions (request/response schemas)
   - Service layer architecture (request lifecycle manager, notification service)
   - Background job implementation (message digest scheduler)
   - Error handling patterns (constraint violations, timeouts)

2. **Set up database migrations**:
   - BorrowRequests table with exclusion constraint
   - RequestMessages table
   - Indexes for query performance

3. **Implement notification infrastructure**:
   - Email service integration (SendGrid/Azure)
   - In-app notification system (SignalR or polling)
   - Background job scheduler (Hangfire)

4. **Create React components**:
   - Request submission form with validation
   - Request list/cards for borrower and owner dashboards
   - Approval/decline/withdraw modals
   - Message thread UI
   - Borrower profile modal

5. **Write integration tests**:
   - Double-booking race condition scenarios
   - State transition validation
   - Notification delivery
   - Authorization enforcement

---

**This feature is ready for detailed engineering specification.**