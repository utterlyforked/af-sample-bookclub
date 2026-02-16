# Borrowing Requests - Product Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification (2025-01-10)
- v1.1 - Iteration 1 clarifications (2025-01-10): Added race condition handling, lifecycle state management, notification policies, data model integration, and edge case behaviors

---

## Feature Overview

The Borrowing Requests feature is the core transaction mechanism of ToolShare - it enables borrowers to request tools from owners and provides owners with the information and controls needed to make informed lending decisions.

This feature transforms the awkward social interaction of asking to borrow something into a structured, asynchronous workflow. Borrowers can clearly communicate what they need, when they need it, and what they'll use it for. Owners can review requests on their own schedule, see relevant context about the borrower, and approve or decline with clear communication.

The feature prioritizes trust-building and safety by revealing information progressively: borrowers see general location before requesting, owners see borrower history before approving, and exact pickup addresses are only revealed after approval. This graduated disclosure protects privacy while enabling informed decisions.

By creating a paper trail of requests, approvals, and terms, this feature also reduces conflicts and misunderstandings that could damage both tools and community relationships.

---

## User Stories

[Original user stories - unchanged]

- As a borrower, I want to request a tool with specific dates and a project description so that the owner understands my need and timeline
- As a borrower, I want to see the status of my pending requests so that I know whether I can plan to use the tool or need to find alternatives
- As a tool owner, I want to receive notifications when someone requests my tool so that I can respond promptly
- As a tool owner, I want to review a borrower's profile and history before approving so that I can make an informed lending decision
- As a tool owner, I want to approve or decline requests with optional messages so that I can communicate terms, concerns, or alternative suggestions
- As a tool owner, I want to see all pending requests in one place so that I can manage multiple requests efficiently
- As both parties, I want to receive notifications about request status changes so that I stay informed without constantly checking the app
- As both parties, I want to message each other about an active request so that we can coordinate pickup details or ask questions

---

## Acceptance Criteria (UPDATED v1.1)

- Borrowers can only request tools that are marked as "Available" (not currently borrowed or temporarily unavailable)
- Borrowers must specify a start date (today or future), end date (max 14 days from start), and project description (50-500 characters)
- **System prevents double-booking via database constraint**: If a tool is already approved for overlapping dates, subsequent approval attempts fail with constraint violation and the second request is automatically declined
- **Borrowers can request multiple tools for overlapping dates** - no cross-tool validation prevents this
- Owners receive both email and in-app notification when a request is made (within 5 minutes)
- Owner can view borrower's profile including: full name, neighborhood, member since date, number of successful borrows completed, average rating, and any reviews from previous lenders
- Owner can approve a request with optional message (max 500 characters) or decline with required reason (max 500 characters)
- **Owners can withdraw approval before pickup occurs** with required reason (min 20 characters)
- Upon approval, borrower receives notification containing: approval confirmation, owner's full address, owner's phone number (if provided), and pickup instructions message
- Upon decline, borrower receives notification with owner's reason
- **Auto-declined requests show conflicting date range** to help borrower choose alternative dates
- **When tool is marked unavailable by owner, all pending requests are automatically declined** with system notification
- Both parties can send messages about an active request through in-app messaging (no external email/phone required for basic coordination)
- **Message notifications are batched**: 2 hours after first unread message, user receives one email digest with all unread messages in that thread
- **Borrowers can cancel approved requests until pickup is confirmed**, freeing the tool for other borrowers
- Request status progresses through clear states: Pending → Approved/Declined/Cancelled → (if approved and picked up) Active → Completed
- Users can view history of all their requests (sent and received) with status and dates
- **Message threads are retained permanently** for dispute resolution and record-keeping

---

## Detailed Specifications (UPDATED v1.1)

### Double-Booking Prevention & Race Conditions

**Decision**: Use optimistic locking with database-level unique constraint on (ToolId, DateRange).

**Rationale**: Database is the single source of truth for data integrity. By enforcing uniqueness at the schema level, we guarantee that no two approved requests can overlap for the same tool, even under high concurrency. This is simpler than application-level locking and leverages PostgreSQL's proven transaction handling.

**Implementation**:
- PostgreSQL exclusion constraint using `daterange` type and GiST index:
  ```sql
  ALTER TABLE BorrowRequests 
  ADD CONSTRAINT no_overlapping_approved_borrows 
  EXCLUDE USING GIST (
    ToolId WITH =, 
    daterange(RequestedStartDate, RequestedEndDate, '[]') WITH &&
  ) 
  WHERE (Status = 'Approved');
  ```
- When owner clicks "Approve", backend wraps operation in transaction
- If constraint violation occurs (HTTP 409 Conflict):
  - Request is automatically declined with system message
  - Owner sees error: "Someone else was just approved for these dates. This request has been automatically declined."
  - Frontend refreshes request list to show declined status
  - Owner can immediately review other pending requests

**Examples**:
- **Scenario 1 - Normal case**: Owner A approves request for Jan 10-15. Database accepts. Owner B tries to approve overlapping request (Jan 12-17) seconds later. Database rejects with constraint violation. Application catches exception, declines request, notifies Owner B.
- **Scenario 2 - Non-overlapping**: Owner A approves Jan 10-12. Owner B approves Jan 13-15. Both succeed - date ranges don't overlap.
- **Scenario 3 - Edge-touching dates**: Request A is Jan 10-12, Request B is Jan 12-14. These overlap (both include Jan 12). Second approval fails.

**Edge Cases**:
- **Database timeout**: If transaction takes >30 seconds (network issue), return 504 Gateway Timeout to owner with retry prompt
- **Simultaneous declines**: If owner tries to decline a request that's being auto-declined due to conflict, decline succeeds (idempotent operation)
- **Request deleted during approval**: If borrower cancels request in race with owner approval, foreign key constraint fails - return 404 "Request no longer exists"

---

### Cross-Tool Borrow Validation

**Decision**: Allow borrowers to have multiple approved/active borrows with overlapping dates. No validation prevents requesting multiple tools for the same date range.

**Rationale**: Users legitimately need multiple tools for single projects (e.g., borrowing a ladder and drill for home repair, or mower and edger for lawn work). Blocking overlapping borrows would create frustration and reduce platform utility. Users are adults capable of managing their commitments, and over-scheduling will naturally correct through social reputation (if someone no-shows repeatedly, owners will see poor ratings and decline).

**Behavior**:
- Borrower can submit request for Tool B even while having pending/approved request for Tool A with overlapping dates
- No warning shown during submission (keep UX simple)
- Owner reviewing request can see borrower's other active borrows in profile (transparency for lending decision)
- If borrower over-commits and fails to pick up tools, owners can leave negative reviews, reducing future approval rates

**Future Consideration**: In v2, if analytics show high no-show rates for users with 3+ simultaneous borrows, we can add soft warning: "You have 3 tools borrowed during these dates. Can you handle another?" But don't implement in v1 without data justifying it.

---

### Auto-Decline Notifications

**Decision**: When a request is auto-declined due to date conflicts (because owner approved a different request), the owner whose request was declined is NOT notified. Only the borrower receives notification.

**Rationale**: The owner took the action they wanted—approving someone. They don't need to know about requests they didn't actively decline. Pending requests are in a queue; owners aren't tracking every single one. Notifying owners would add noise without value ("why am I being told about a request I never reviewed?"). The declined request simply moves from their Pending tab to Declined tab if they check later.

**Behavior**:
- Owner A has 3 pending requests for their tool: Request 1 (Jan 10-15), Request 2 (Jan 12-17), Request 3 (Jan 20-25)
- Owner A approves Request 1
- System immediately:
  - Approves Request 1 (status: Approved)
  - Auto-declines Request 2 (status: Declined, reason: "This tool was approved for another borrower during overlapping dates (Jan 10-15). Please request again with different dates if you still need it.")
  - Leaves Request 3 untouched (no overlap)
- Borrower 2 receives notification about auto-decline
- **Owner A receives no notification about Request 2** - it just disappears from their Pending queue
- Owner A can later view Request 2 in their Declined tab if curious, showing system-generated reason

**Edge Cases**:
- If owner manually declines Request 2 in race with auto-decline, manual decline wins (takes precedence, uses owner's custom reason instead of system message)
- If owner refreshes Pending page while auto-decline is processing, request may briefly flicker before disappearing (acceptable UX)

---

### Data Model: BorrowRequest Entity

**Decision**: Use single entity `BorrowRequest` to track both the request phase and the active borrow phase. No separate "Borrow" or "ActiveBorrow" table.

**Rationale**: Simplifies data model and eliminates confusion about which entity to query. The "request" and "borrow" are the same transaction at different lifecycle stages. Having one table with a status enum makes state transitions explicit and avoids foreign key complexity. Queries like "show me all my active borrows" are simply `WHERE status IN (Approved, PickedUp)`.

**Schema**:
```csharp
public class BorrowRequest
{
    public Guid Id { get; set; }
    public Guid ToolId { get; set; }
    public Guid BorrowerUserId { get; set; }
    public Guid OwnerUserId { get; set; }
    
    public DateOnly RequestedStartDate { get; set; }
    public DateOnly RequestedEndDate { get; set; }
    public string ProjectDescription { get; set; } // 50-500 chars
    
    public BorrowRequestStatus Status { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? RespondedAt { get; set; } // when owner approved/declined
    public DateTime? PickedUpAt { get; set; } // when borrower confirmed pickup
    public DateTime? ReturnedAt { get; set; } // when owner confirmed return
    
    public string? OwnerMessage { get; set; } // optional message on approval, max 500 chars
    public string? DeclineReason { get; set; } // required on decline, 20-500 chars
    public string? WithdrawReason { get; set; } // required if owner withdraws approval
    
    // Navigation properties
    public Tool Tool { get; set; }
    public User Borrower { get; set; }
    public User Owner { get; set; }
    public ICollection<RequestMessage> Messages { get; set; }
}

public enum BorrowRequestStatus
{
    Pending,      // Initial state, awaiting owner response
    Approved,     // Owner approved, awaiting pickup
    Declined,     // Owner declined or system auto-declined
    Cancelled,    // Borrower cancelled before pickup
    Withdrawn,    // Owner withdrew approval before pickup
    PickedUp,     // Borrower confirmed pickup (active borrow)
    Returned,     // Owner confirmed return
    Completed     // Both parties confirmed, can rate each other
}
```

**Status Transitions**:
- `Pending` → `Approved` (owner approves)
- `Pending` → `Declined` (owner declines OR system auto-declines due to conflict)
- `Pending` → `Cancelled` (borrower cancels)
- `Approved` → `Withdrawn` (owner withdraws approval before pickup)
- `Approved` → `Cancelled` (borrower cancels before pickup)
- `Approved` → `PickedUp` (borrower confirms pickup - handled by Borrow Tracking feature)
- `PickedUp` → `Returned` (owner confirms return - handled by Borrow Tracking feature)
- `Returned` → `Completed` (both parties confirm - handled by Borrow Tracking feature)

**Constraints**:
- `RespondedAt` is set when status changes from Pending to Approved/Declined
- `PickedUpAt` can only be set if status is Approved (validates before transition)
- `ReturnedAt` can only be set if status is PickedUp
- Cannot transition back to Pending from any other state
- `DeclineReason` is required if status = Declined and not system-generated
- `WithdrawReason` is required if status = Withdrawn

---

### Cancellation Rules After Approval

**Decision**: Borrowers can cancel approved requests any time before pickup occurs, even if the start date has passed.

**Rationale**: If no pickup happened, the borrow isn't truly active—it's just a reservation. Allowing cancellation keeps the system flexible and lets borrowers clean up their queue if plans change. It also frees the owner's tool for other borrowers. If a borrower chronically cancels after approval, owners will see this in their history and can decline future requests.

**Behavior**:
- "Cancel Request" button is visible on approved requests while `status = Approved` (not PickedUp)
- No date-based restrictions: borrower can cancel on Jan 15 even if start date was Jan 10
- Upon cancellation:
  - Status changes to `Cancelled`
  - Tool's calendar dates are released (available for other requests)
  - Owner receives notification: "[Borrower name] cancelled their borrow of [Tool name] for Jan 10-15. Your tool is now available again."
  - Request moves to borrower's "Cancelled" section (grouped with declined for simplicity)
- Borrower can immediately submit a new request for same tool with different dates

**Edge Cases**:
- **Cancel during pickup coordination**: If borrower cancels while owner is literally waiting for pickup, owner might be frustrated. This is acceptable—better than no-show without communication. Owner can leave negative review if appropriate.
- **Cancel after multiple reschedules**: No limit on cancellations in v1. If abuse emerges, we can track cancellation rate in v2 and warn owners about users with >50% cancellation rate.
- **Owner already en route**: Notification is instant (in-app + email), but owner might not see it. Risk accepted—better than locking borrower into pickup they can't make.

---

### Owner Approval Withdrawal

**Decision**: Owners can withdraw approval before pickup occurs, with required reason (minimum 20 characters).

**Rationale**: Owners are lending personal property and need an escape hatch for emergencies: tool breaks before pickup, family member needs it urgently, safety concern arises from borrower's messages, owner will be out of town, etc. Requiring a reason creates accountability and helps borrowers understand it's not personal. This is fair given that owners are taking the risk of lending.

**Behavior**:
- "Withdraw Approval" button appears on approved requests in owner's dashboard
- Button is hidden once `status = PickedUp` (too late, borrow is active)
- Clicking button shows modal:
  - Title: "Withdraw Approval"
  - Message: "This will notify [Borrower name] that the borrow is cancelled. Please explain why:"
  - Text area: required, 20-500 characters
  - Buttons: "Cancel" (gray), "Withdraw Approval" (red)
- Upon confirmation:
  - Status changes from `Approved` to `Withdrawn`
  - Tool's calendar dates are released
  - Borrower receives notification:
    - Subject: "[Owner name] withdrew approval for [Tool name]"
    - Body: Owner's reason
    - Encouragement: "You can request this tool again for different dates, or search for similar tools nearby."
  - Request appears in borrower's "Declined" tab (treated similarly to decline)

**Tracking & Accountability**:
- System tracks `withdrawnRequestsCount` per owner (not publicly visible)
- If owner withdraws >30% of approved requests, flag for review (future moderation feature)
- Borrower can report abusive withdrawal patterns through reporting system (future feature)

**Examples**:
- **Legitimate withdrawal**: "My drill's battery died and I need to replace it. Sorry for the inconvenience!"
- **Concerning withdrawal**: "I don't feel comfortable lending to you anymore." (vague, but allowed—better than silent cancellation)
- **Tool damage**: "Unfortunately the tool broke yesterday before you could pick it up. Marking it as unavailable while I repair it."

**Edge Cases**:
- **Withdraw during pickup window**: If owner withdraws on pickup day, borrower might already be driving over. Notification is instant but might not prevent wasted trip. Risk accepted—owner needs flexibility for emergencies.
- **Rapid approve-withdraw cycles**: If owner approves then withdraws within 5 minutes repeatedly, might indicate indecision or gaming. Not prevented in v1, but tracked for future moderation.

---

### Message Notification Batching

**Decision**: After a message is sent, if the recipient hasn't read it within 2 hours, send one email digest containing all unread messages in that thread. No per-message emails.

**Rationale**: Balances timely notification with email fatigue. Active conversations shouldn't generate 10 emails in 2 hours. Batching reduces noise while ensuring messages aren't ignored indefinitely. 2-hour window is long enough for users to check the app organically, but short enough to maintain momentum in coordination.

**Behavior**:
- When a message is sent:
  - Recipient receives in-app notification immediately (red badge)
  - System schedules "check for unread messages" job for this thread at `sentAt + 2 hours`
- 2 hours later, background job runs:
  - Query all messages in thread where `recipientUserId = user AND readAt IS NULL AND sentAt <= 2 hours ago`
  - If any unread messages exist, send one email:
    - Subject: "[Sender name] sent you messages about [Tool name]"
    - Body: "You have 3 unread messages from [Sender name] about your borrow request:"
    - List messages with timestamps
    - Call-to-action button: "View Conversation"
  - Mark email as sent (don't send duplicate if job runs again)
- If user reads messages before 2-hour window, cancel pending email job (no notification needed)

**Examples**:
- **Scenario 1 - Single message**: Borrower sends "What time should I pick up?" at 10:00 AM. Owner doesn't read it. At 12:00 PM, owner receives email digest with that one message.
- **Scenario 2 - Conversation**: Borrower sends 3 messages between 10:00-10:15 AM. Owner doesn't read. At 12:00 PM, owner receives one email with all 3 messages.
- **Scenario 3 - Owner replies**: Borrower sends message at 10:00 AM. Owner reads and replies at 10:30 AM. Borrower doesn't read reply. At 12:30 PM, borrower receives email with owner's reply (new 2-hour window started when owner sent message).

**Edge Cases**:
- **User checks app at 1:59**: If user reads messages 1 minute before email would send, job finds no unread messages and doesn't send email (desired behavior)
- **Multiple threads**: Each thread has independent 2-hour timer. User could receive multiple digest emails for different tools.
- **Email delivery failure**: Use SendGrid/Azure email service with retry logic. If email bounces, log error but don't block thread functionality. User can still see messages in-app.

---

### Message Retention Policy

**Decision**: Message threads are retained permanently. No automated deletion or archival.

**Rationale**: Text storage is extremely cheap (messages are <1KB each). Complete communication history protects both parties in disputes, provides audit trail for moderation, and eliminates risk of losing important context. Even if a user has 100 completed borrows with 10 messages each (1000 messages), that's only ~1MB of data. This is negligible compared to images or other media.

**Behavior**:
- Messages remain accessible indefinitely through request detail page
- Completed borrows show read-only message thread (no new messages, but can review history)
- Users can reference old messages years later if needed
- No "delete message" functionality (prevents covering up evidence in disputes)

**Future Optimization** (only if needed at scale):
- After 2 years, move messages for completed borrows to cold storage (cheaper S3 tier)
- Lazy-load old messages (require click to expand threads older than 1 year)
- Estimated timeline before optimization needed: 100K users with avg 10 borrows/year = 10M message threads over 5 years = still <10GB total

---

### Auto-Decline Communication for Borrowers

**Decision**: When a request is auto-declined due to date conflicts, show the conflicting date range to help borrower choose alternative dates.

**Rationale**: Generic "dates are taken" message forces borrower to guess-and-check, leading to frustration and repeated failed requests. Showing the conflicting range (e.g., "Tool is already borrowed Jan 12-15") lets borrower immediately adjust. Minor privacy trade-off (revealing another borrower's schedule) is acceptable because: (1) Tool listings already show general location, (2) dates without identity aren't sensitive, (3) user benefit outweighs privacy concern.

**Behavior**:
- When request is auto-declined, system queries the approved request that caused the conflict
- Borrower receives notification:
  - Subject: "Your request for [Tool name] couldn't be approved"
  - Body: "This tool is already borrowed **Jan 12-15**. Try requesting dates before Jan 12 or after Jan 15."
  - Call-to-action: "Request Again" button (pre-fills tool, borrower adjusts dates)
- In-app declined request shows same message in reason field

**Examples**:
- Borrower requests Jan 10-16
- Conflicting approval is Jan 12-14
- Message: "Tool is already borrowed Jan 12-14. Try dates before Jan 12 or after Jan 14."
- Borrower immediately requests Jan 8-11 (before conflict) or Jan 15-18 (after conflict)

**Privacy Consideration**:
- Message does NOT reveal:
  - Who the other borrower is
  - Why they're borrowing it
  - Their rating or history
- Message DOES reveal:
  - Dates tool is unavailable (already somewhat visible in tool listing status)
- This is acceptable: knowing "tool is borrowed Jan 12-14" is like knowing "tool owner is busy that week"—not sensitive personal information

---

### Tool Unavailability Impact on Pending Requests

**Decision**: When an owner marks a tool as "unavailable" (temporary status in Tool Listings feature), all pending requests for that tool are automatically declined with system notification.

**Rationale**: Clean state management. If the tool isn't available, pending requests can't be approved anyway. Auto-declining them immediately (1) notifies borrowers so they can find alternatives, (2) clears owner's pending queue, and (3) prevents confusion where borrowers are waiting for responses that will never come. If owner wants to approve specific requests first, they should do that before marking unavailable.

**Behavior**:
- Owner clicks "Mark as Unavailable" on tool (Tool Listings feature)
- System checks for pending requests on that tool
- If pending requests exist:
  - All are simultaneously declined (status: `Declined`)
  - Decline reason: "Owner has temporarily marked this tool as unavailable. You can request again once it's listed as available."
  - Each borrower receives notification (email + in-app)
- Owner receives confirmation: "Tool marked unavailable. 3 pending requests were automatically declined and borrowers were notified."
- Already-approved requests are NOT affected (if pickup hasn't occurred, owner must manually withdraw those)

**Examples**:
- Owner's mower breaks, needs repair. Owner marks tool unavailable. 2 pending requests are auto-declined. 1 approved request (pickup tomorrow) remains approved—owner manually withdraws that if needed.

**Edge Cases**:
- **Tool marked unavailable then available again**: If owner marks unavailable, auto-declines requests, then marks available 10 minutes later, those requests stay declined. Borrowers must submit new requests (prevents confusing state).
- **Pending request submitted during unavailable period**: Request creation is blocked by tool status check ("tool is unavailable, cannot request"). No request enters Pending state.

---

### Request Submission Rate Limiting

**Decision**: After submitting 5 requests within 1 hour, show warning modal to user. Allow submission to proceed, but encourage moderation.

**Rationale**: Soft guardrail discourages spray-and-pray behavior (requesting 20 tools hoping someone approves) without blocking legitimate use cases (user planning big project needs several tools). Warning nudges thoughtful behavior. Hard limit would frustrate serious users. We can tighten if abuse emerges.

**Behavior**:
- Before submitting request, backend counts user's requests where `createdAt > now - 1 hour`
- If count >= 5, return warning to frontend (HTTP 200 with `warning` flag, not error)
- Frontend shows modal:
  - Title: "You've submitted several requests recently"
  - Message: "You've requested 5 tools in the past hour. Consider waiting for responses before requesting more. Requesting many tools at once may reduce your approval rate."
  - Buttons: "Go Back" (gray), "Submit Anyway" (yellow)
- If user clicks "Submit Anyway", request proceeds normally
- No backend enforcement—this is purely a UX nudge

**Tracking**:
- Log users who submit >10 requests/day (not visible to user, for future analytics)
- If patterns emerge (e.g., users with high request volume have low approval rates), revisit in v2

**Examples**:
- User requests drill, ladder, saw in quick succession (normal behavior, no warning)
- User requests 5 different mowers in 10 minutes (warning appears, user can proceed but is encouraged to be selective)
- User ignores warning and submits 15 requests in 1 hour (allowed, but if approval rate is low, future owners see poor history)

---

### Same-Day Request Timing

**Decision**: No minimum notice period. Borrowers can request tools for "today" even at 11:59 PM. Owner's responsibility to respond in reasonable time or decline if timing doesn't work.

**Rationale**: PRD explicitly allows same-day requests ("default to today"). Adding minimum notice (e.g., 2-hour or 24-hour) contradicts this design decision. Real-world tool borrowing is often spontaneous: user realizes they need a tool today, checks if neighbor has it available. If owner can't respond quickly, they'll decline with explanation. Better to allow optimistic requests than block potentially successful same-day borrows.

**Behavior**:
- Start date picker includes "Today" as valid option
- No validation prevents selecting today even if current time is late (e.g., 11 PM)
- Owner receives immediate notification (if they're available, can approve; if not, can decline)
- If owner doesn't respond and start date passes, request stays Pending (no auto-expiration in v1)

**Examples**:
- User requests tool at 2 PM for same-day use. Owner is actively using app, sees request, approves. Pickup happens at 4 PM. (Success case)
- User requests tool at 11 PM for today. Owner sees notification next morning, declines: "Sorry, too late to coordinate pickup for yesterday. Request again for today if you still need it." (Failure case, but user learns to plan ahead)

**Future Consideration**: In v2, analytics might show same-day requests have <10% approval rate. At that point, consider adding soft warning: "Same-day requests are often declined. Requesting a day ahead increases approval chances." But don't block in v1 without data.

---

## Q&A History

### Iteration 1 - 2025-01-10

**Q1: How should we handle race conditions in double-booking prevention?**  
**A**: Use optimistic locking with PostgreSQL exclusion constraint on (ToolId, DateRange). Database prevents overlapping approved borrows at schema level. Second approval attempt fails with constraint violation, caught by application, and request is auto-declined. Owner sees error message explaining another borrower was just approved. This is simpler than pessimistic locking and leverages database integrity guarantees.

**Q2: What happens when a borrower submits a request for dates that overlap with their own pending/approved request for a DIFFERENT tool?**  
**A**: Allow it. No cross-tool validation. Users legitimately need multiple tools for single projects (e.g., ladder + drill). Blocking would frustrate legitimate use. If users over-commit and no-show, social reputation (reviews) will correct behavior. Owner can see borrower's other active borrows when reviewing request for context.

**Q3: When a request is auto-declined due to date conflicts, should we notify the owner?**  
**A**: No. Owner took the action they wanted (approving someone). Notifying them about requests they didn't review adds noise without value. Request simply moves from Pending to Declined tab if owner checks later. Only borrower is notified so they can request alternative dates.

**Q4: What exactly is the "Active Borrow" record created on approval?**  
**A**: There is no separate entity. `BorrowRequest` is the single entity tracking the entire lifecycle. Status enum progresses: Pending → Approved → PickedUp → Returned → Completed. When approved, the same row's status changes. No foreign key to separate "Borrow" table. This simplifies data model and queries.

**Q5: Can a borrower cancel a request after the start date has passed but before pickup occurs?**  
**A**: Yes. Cancellation is allowed any time while `status = Approved` (before pickup), even if start date passed. If no pickup occurred, the "borrow" isn't truly active—just a reservation. This keeps system flexible and frees owner's tool for others. Owner is notified immediately about cancellation.

**Q6: Should owners be able to edit or withdraw approval after approving but before pickup?**  
**A**: Yes. "Withdraw Approval" button is available until pickup. Owner must provide reason (min 20 characters). This gives owners an escape hatch for emergencies (tool breaks, safety concern, family needs it). Borrower is notified with owner's reason and can request again or find alternative. Withdrawal frequency is tracked for potential abuse detection in future.

**Q7: What notifications should be sent for messages, and can users configure frequency?**  
**A**: Digest notifications. If user hasn't read message within 2 hours of it being sent, send one email with all unread messages in that thread. No per-message emails. No user configuration in v1 (default behavior works for most users; can add preferences in v2 if requested). This balances timely notification with email fatigue.

**Q8: How long should message threads remain accessible after a borrow is completed?**  
**A**: Forever. Text storage is cheap and complete communication history protects both parties in disputes. Messages are <1KB each; even at scale, storage impact is negligible. Threads become read-only after completion but remain accessible in transaction history indefinitely.

**Q9: Should we show borrowers WHY their request was auto-declined due to date conflicts?**  
**A**: Yes, show the conflicting date range. Instead of generic "dates are taken", show: "Tool is already borrowed Jan 12-15. Try dates before Jan 12 or after Jan 15." This helps borrower immediately adjust request. Privacy trade-off is minimal (dates without identity aren't sensitive) and user benefit outweighs it.

**Q10: Should request submission be rate-limited per user?**  
**A**: Soft limit with warning. After 5 requests in 1 hour, show modal warning user that they're requesting many tools and might reduce approval rate. Allow them to proceed anyway. This nudges thoughtful behavior without blocking legitimate users who need multiple tools. No hard limit in v1.

**Q11: What happens to pending requests when a tool's status changes to "unavailable" by the owner?**  
**A**: Auto-decline all pending requests with system notification: "Owner has temporarily marked this tool as unavailable." Borrowers are notified so they can find alternatives. Already-approved requests (awaiting pickup) are NOT auto-declined—owner must manually withdraw those if needed. This keeps state clean and prevents borrowers from waiting indefinitely for responses that will never come.

**Q12: Should the system prevent requests for dates that start within the next X hours?**  
**A**: No minimum notice period. Borrow