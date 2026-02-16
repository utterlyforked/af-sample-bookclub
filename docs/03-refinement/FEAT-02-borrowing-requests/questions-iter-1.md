# Borrowing Requests - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: 2025-01-10

---

## Summary

After reviewing the specification, I've identified **12** areas that need clarification before implementation can begin. These questions address:
- Data integrity and race conditions in double-booking prevention
- Request lifecycle state management and edge cases
- Notification delivery guarantees and failure handling
- Message threading and data retention policies
- Authorization boundaries and multi-user scenarios

The feature is well-structured overall with clear user stories and acceptance criteria. However, several critical implementation details need product decisions to ensure we build the right behavior.

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: How should we handle race conditions in double-booking prevention?

**Context**: The PRD mentions "rapid approvals" and says "first approval wins" but doesn't specify the mechanism. When two owners approve overlapping requests for the same tool within milliseconds of each other, we need database-level protection. This affects:
- Database transaction isolation level
- Whether we use optimistic or pessimistic locking
- Error messages shown to the "losing" owner
- Whether the losing owner's approval attempt is silent or requires retry

**Options**:

- **Option A: Optimistic locking with unique constraint**
  - Impact: Add unique constraint on (ToolId, DateRange) in database. Second approval fails with constraint violation, caught by application layer.
  - Trade-offs: Simple, database handles integrity. Owner sees error: "Someone else was just approved for these dates. This request has been auto-declined." Owner's approval attempt is lost.
  - Technical: Use EF Core's `DbUpdateException` handling, return 409 Conflict to frontend.
  
- **Option B: Pessimistic locking during approval**
  - Impact: Acquire row-level lock on Tool when owner clicks approve, hold until dates are validated and request is saved.
  - Trade-offs: Guarantees consistency, but second owner waits (potential timeout). More complex transaction management.
  - Technical: Use SQL `SELECT FOR UPDATE`, wrap approval in explicit transaction with serializable isolation.

- **Option C: Accept race condition, auto-decline loser**
  - Impact: Both approvals succeed briefly, background job detects conflict within 60 seconds and auto-declines the second one (by created timestamp).
  - Trade-offs: Eventually consistent. Brief period where tool appears double-booked. Requires compensation logic.
  - Technical: Scheduled job checks for overlaps, sends apology notification to second borrower.

**Recommendation for MVP**: **Option A** (optimistic locking). Database constraint prevents bad data at the source. Error case is rare enough that asking owner to refresh and see the request is already declined is acceptable UX. Clean, no complex locking logic.

---

### Q2: What happens when a borrower submits a request for dates that overlap with their own pending/approved request for a DIFFERENT tool?

**Context**: PRD says "Cannot have multiple pending requests for the same tool" but doesn't address this scenario:
- User requests Tool A for Jan 10-15
- While that's pending, user requests Tool B for Jan 12-17
- Both tools are approved - user now has overlapping borrows

This affects:
- Whether we validate across all user's active borrows
- Whether users can "over-commit" themselves
- Tool availability calendar logic

**Options**:

- **Option A: Allow overlapping borrows**
  - Impact: No validation. User can borrow 10 tools for the same dates if approved.
  - Trade-offs: Flexible but user might over-commit and fail to pick up tools. Owners might be frustrated if borrower doesn't show.
  - Logic: No cross-tool validation needed.

- **Option B: Warn but allow**
  - Impact: Show warning when submitting overlapping request: "You already have a borrow during these dates. Are you sure you can handle multiple tools?"
  - Trade-offs: User freedom with safety check. Still allows over-commitment.
  - Logic: Check user's approved/active borrows before submission, show modal confirmation.

- **Option C: Block overlapping borrows**
  - Impact: Validation prevents submitting request if user has any approved/active borrow with overlapping dates.
  - Trade-offs: Protective but restrictive. User can't borrow drill and ladder for same weekend project.
  - Logic: Query user's BorrowRequests where status = Approved/Active, check date overlap.

**Recommendation for MVP**: **Option A** (allow overlapping). Users are adults and might legitimately need multiple tools for one project (e.g., ladder + drill for home repair). We can add warnings in v2 if we see abuse patterns. Keep it simple.

---

### Q3: When a request is auto-declined due to date conflicts, should we notify the owner?

**Context**: PRD says "Any pending requests with overlapping dates are automatically declined" when another request is approved. But should the owner of the now-declined request know this happened?

This affects:
- Whether owners are confused by "disappearing" requests
- Notification volume for owners
- Owner understanding of platform behavior

**Options**:

- **Option A: Notify owner**
  - Impact: Owner receives notification: "[Tool name] request from [Borrower] was auto-declined because you approved another borrower for overlapping dates."
  - Trade-offs: Full transparency, but extra notification noise. Owner didn't take action but gets notified.
  - Logic: Send notification to owner of declined request when auto-decline happens.

- **Option B: Silent auto-decline for owner**
  - Impact: Request simply disappears from owner's pending list. No notification.
  - Trade-offs: Less noise, but owner might wonder "where did that request go?" if they were considering it.
  - Logic: Only borrower is notified of auto-decline.

- **Option C: Summary notification**
  - Impact: If multiple requests are auto-declined, send one notification: "3 pending requests were auto-declined due to date conflicts."
  - Trade-offs: Balances awareness with noise reduction.
  - Logic: Batch auto-declines, send single summary.

**Recommendation for MVP**: **Option B** (silent for owner). The owner took the action they wanted (approving someone), and managing their pending queue is lower priority than reducing notification fatigue. The request just moves from Pending to their Declined tab if they want to review it later.

---

### Q4: What exactly is the "Active Borrow" record created on approval?

**Context**: The PRD says approval "Creates an 'Active Borrow' record (tracked in Borrow Tracking feature)" but this feature doc doesn't define that entity. This is a critical integration point.

This affects:
- Whether BorrowRequest and ActiveBorrow are the same entity or separate
- Data model relationships
- When exactly the status transitions happen

**Options**:

- **Option A: BorrowRequest IS the borrow record**
  - Impact: Single entity. Status flows: Pending → Approved → PickedUp → Returned → Completed.
  - Trade-offs: Simpler data model, single source of truth. All lifecycle in one table.
  - Schema: BorrowRequest has status enum with all states including pickup/return states.

- **Option B: Separate BorrowRequest and Borrow entities**
  - Impact: BorrowRequest (status: Pending/Approved/Declined), approved requests create separate Borrow entity (status: Active/Returned/Completed).
  - Trade-offs: Clear separation of concerns. BorrowRequest is pre-approval, Borrow is post-approval. More complex with two tables and foreign key.
  - Schema: Borrow table has borrowRequestId FK, tracks pickup/return details.

- **Option C: BorrowRequest transitions to Borrow (exclusive)**
  - Impact: When approved, BorrowRequest row is marked as "consumed" and Borrow row is created. Request cannot be re-opened.
  - Trade-offs: Clear lifecycle boundary, but orphans some request data if we want to query "all requests that became borrows."
  - Schema: BorrowRequest.consumedAt timestamp, Borrow.borrowRequestId FK.

**Recommendation for MVP**: Need Product to decide based on Borrow Tracking feature requirements, but **suggest Option A** (single entity) for simplicity unless there's a strong reason to separate. The "request" and "borrow" are the same transaction at different stages. Fewer joins, simpler queries.

---

### Q5: Can a borrower cancel a request after the start date has passed but before pickup occurs?

**Context**: PRD says "Cannot cancel after approval" but doesn't address this scenario:
- Request approved for Jan 10-15
- Start date (Jan 10) arrives
- Borrower never picked up tool
- Can borrower still cancel on Jan 11?

This affects:
- Whether expired-but-not-picked-up requests clutter the system
- How owners handle no-shows
- Status lifecycle logic

**Options**:

- **Option A: No cancellation after start date**
  - Impact: Once start date passes, request is locked. Borrower must coordinate with owner through messaging or owner reports as no-show.
  - Trade-offs: Forces accountability, but inflexible if borrower's plans changed last-minute.
  - Logic: Cancel button disabled if `today > requestedStartDate`.

- **Option B: Allow cancellation until pickup is marked**
  - Impact: Borrower can cancel anytime before pickup is confirmed (even days after start date).
  - Trade-offs: Flexible, but owner might be waiting for pickup that never happens.
  - Logic: Cancel button available while status = Approved (not PickedUp).

- **Option C: Grace period after start date**
  - Impact: Can cancel for 24 hours after start date, then locked.
  - Trade-offs: Balances flexibility with accountability.
  - Logic: Cancel button enabled if `today <= requestedStartDate + 1 day AND status = Approved`.

**Recommendation for MVP**: **Option B** (allow until pickup). If no pickup occurred, the borrow isn't really active yet. Let borrower cancel to clean up their queue and free the owner's tool. Owner can report chronic no-shows through reputation system (future feature).

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q6: Should owners be able to edit or withdraw approval after approving but before pickup?

**Context**: Scenario: Owner approves request, then realizes they need the tool themselves, or borrower sends concerning messages. Can owner "unapprove"?

The PRD doesn't address this. It affects:
- Power balance between borrower and owner
- Whether approval is a binding commitment
- Complexity of state transitions

**Options**:

- **Option A: Approval is binding**
  - Impact: No "unapprove" button. Owner must coordinate cancellation with borrower through messaging or contact support.
  - Trade-offs: Protects borrower expectations, but inflexible for owner emergencies.
  - Logic: No withdrawal action available.

- **Option B: Owner can withdraw with required reason**
  - Impact: "Withdraw Approval" button available until pickup. Borrower notified with owner's reason (similar to decline flow).
  - Trade-offs: Flexible for owners, potentially frustrating for borrowers who made plans.
  - Logic: Status transitions Approved → Withdrawn (new state), borrower can re-request with different dates.

- **Option C: Mutual cancellation only**
  - Impact: Owner can request cancellation, borrower must agree. Both must confirm.
  - Trade-offs: Fair but adds complexity and potential coordination failure.
  - Logic: Owner clicks "Request Cancellation" → borrower receives notification → must accept/decline.

**Recommendation for MVP**: **Option B** (owner can withdraw). Owners are lending personal property and need an escape hatch for emergencies (tool breaks, family needs it, safety concern about borrower). Require reason to discourage abuse. Track frequency to flag owners who withdraw often.

---

### Q7: What notifications should be sent for messages, and can users configure frequency?

**Context**: PRD says "Email notification if user hasn't read message within 2 hours" but doesn't specify:
- Does this apply to every message in a thread, or just the first unread?
- Can users opt out of email notifications entirely?
- What if 5 messages arrive in 2 hours?

This affects:
- Email notification volume
- User preference data model
- Notification job scheduling logic

**Options**:

- **Option A: Email per message after 2 hours**
  - Impact: Every unread message triggers separate email after 2-hour window.
  - Trade-offs: Ensures no message is missed, but could send many emails if conversation is active.
  - Logic: Scheduled job checks message.sentAt + 2 hours, sends email if still unread.

- **Option B: Digest of unread messages**
  - Impact: After 2 hours of first unread message, send one email with all unread messages in that thread.
  - Trade-offs: Reduces email volume, still timely. More complex to track "first unread."
  - Logic: Track firstUnreadAt per thread, send digest after 2 hours.

- **Option C: Configurable per user**
  - Impact: User settings: "Email me about new messages: immediately / after 2 hours / daily digest / never"
  - Trade-offs: Maximum flexibility, but adds complexity and most users won't configure.
  - Logic: User preference stored, respected by notification job.

**Recommendation for MVP**: **Option B** (digest). Balances responsiveness with noise reduction. We can add user preferences in v2 if requested. Default behavior works for most users.

---

### Q8: How long should message threads remain accessible after a borrow is completed?

**Context**: PRD says threads are "read-only" after completion but doesn't specify retention. This affects:
- Storage costs (messages are text, low cost, but at scale matters)
- User expectations for record-keeping
- Dispute resolution if issues arise later

**Options**:

- **Option A: Keep forever**
  - Impact: Messages never deleted, always accessible in transaction history.
  - Trade-offs: Complete audit trail, no storage strategy needed. Low cost for text.
  - Storage: Minimal impact, messages are small.

- **Option B: Keep for 1 year**
  - Impact: Messages archived/deleted after borrow completion + 1 year.
  - Trade-offs: Balances record-keeping with storage hygiene. Most disputes surface within weeks.
  - Logic: Scheduled job purges messages older than 1 year from completed borrows.

- **Option C: Keep for 90 days**
  - Impact: Shorter retention, messages deleted 90 days after completion.
  - Trade-offs: Encourages users to resolve issues quickly, but might lose context for late-surfacing problems.
  - Logic: Same as B but shorter window.

**Recommendation for MVP**: **Option A** (keep forever). Text storage is cheap, and having a complete communication history protects both parties in disputes. We can add archival strategy later if storage becomes an issue (unlikely for years).

---

### Q9: Should we show borrowers WHY their request was auto-declined due to date conflicts?

**Context**: PRD says borrower receives "This tool is already borrowed during your requested dates" but doesn't show which specific dates conflict or when the tool becomes available again.

This affects:
- User frustration vs. re-engagement
- Whether users immediately retry with better dates
- UI complexity of conflict messaging

**Options**:

- **Option A: Generic message only**
  - Impact: "This tool is already borrowed during your requested dates. Try different dates."
  - Trade-offs: Simple, but borrower must guess which dates are free.
  - Logic: No additional data retrieval.

- **Option B: Show conflicting date range**
  - Impact: "This tool is already borrowed Jan 12-15. Try dates before Jan 12 or after Jan 15."
  - Trade-offs: More helpful, but reveals another borrower's schedule (minor privacy concern?).
  - Logic: Query approved borrows for tool, find overlap, return date range.

- **Option C: Show tool availability calendar**
  - Impact: Link to tool detail page with calendar overlay showing unavailable dates.
  - Trade-offs: Most helpful for user, but requires calendar UI component (future feature per PRD scope).
  - Logic: Build mini-calendar component showing available/unavailable dates.

**Recommendation for MVP**: **Option B** (show conflicting range). Strikes balance between helpful and simple. Privacy concern is minimal—tool listings already show approximate location, and knowing "tool is borrowed Jan 12-15" doesn't reveal who. Helps borrower adjust dates immediately.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q10: Should request submission be rate-limited per user?

**Context**: PRD mentions "Possible future consideration: Flag users who request >10 tools in 24 hours" but doesn't set any limit for v1.

This affects:
- Spam prevention
- Database load from malicious users
- Owner experience if flooded with fake requests

**Options**:

- **Option A: No rate limit in v1**
  - Impact: Users can submit unlimited requests.
  - Trade-offs: Simple implementation, but vulnerable to abuse/spam.
  - Logic: No validation.

- **Option B: Soft limit with warning**
  - Impact: After 5 requests in 1 hour, show warning: "You've submitted several requests. Consider waiting for responses before requesting more tools."
  - Trade-offs: Nudges behavior without blocking legitimate use (e.g., planning big project).
  - Logic: Count user's requests where createdAt > now - 1 hour, show modal if > 5.

- **Option C: Hard limit**
  - Impact: Max 10 requests per 24 hours, return 429 error if exceeded.
  - Trade-offs: Prevents spam, but might frustrate power users.
  - Logic: Count user's requests in last 24h, block if >= 10.

**Recommendation for MVP**: **Option B** (soft limit warning). Discourages spray-and-pray behavior without blocking legitimate users who are serious about borrowing multiple tools. Easy to adjust threshold based on real usage patterns.

---

### Q11: What happens to pending requests when a tool's status changes to "unavailable" by the owner?

**Context**: Tool owners can mark tools as temporarily unavailable (from Tool Listings feature). PRD doesn't address impact on pending requests.

This affects:
- Whether pending requests are auto-declined
- Owner's responsibility to manually handle requests
- Borrower expectations

**Options**:

- **Option A: Auto-decline pending requests**
  - Impact: When tool marked unavailable, all pending requests auto-declined with message: "Owner has marked this tool as temporarily unavailable."
  - Trade-offs: Clean state, but owner loses option to approve specific requests before going unavailable.
  - Logic: When tool.status changes to Unavailable, update all pending requests to Declined.

- **Option B: Freeze pending requests**
  - Impact: Pending requests remain in limbo. Owner must manually approve/decline before marking unavailable, or system warns: "You have X pending requests. Handle these before marking unavailable."
  - Trade-offs: Forces owner to make decisions, but extra friction.
  - Logic: Validate pendingRequestCount = 0 before allowing status change.

- **Option C: Leave pending, allow approval**
  - Impact: Tool marked unavailable, but owner can still approve/decline existing pending requests. New requests are blocked.
  - Trade-offs: Flexible for owner, but borrower might be confused (tool shows unavailable but their request is approved?).
  - Logic: Block new request creation if tool.status = Unavailable, allow processing existing.

**Recommendation for MVP**: **Option A** (auto-decline). Clean and simple. If owner wants to approve certain requests, they should do so before marking unavailable. Prevents confusion where tool is "unavailable" but requests are still pending.

---

### Q12: Should the system prevent requests for dates that start within the next X hours?

**Context**: PRD allows same-day requests ("Borrower can select today as start date") but doesn't specify if there's a minimum notice period. 

This affects:
- Whether owners have reasonable time to respond
- Borrower expectations for immediate availability
- Practicality of same-hour pickups

**Options**:

- **Option A: No minimum notice**
  - Impact: Borrower can request tool for "today" at 11pm. Owner might not see it in time.
  - Trade-offs: Maximum flexibility, but low success rate for last-minute requests.
  - Logic: No validation beyond "not in the past."

- **Option B: Minimum 2-hour notice**
  - Impact: Borrower can request for today only if current time is before (start date + 2 hours).
  - Trade-offs: Prevents unrealistic last-minute requests, still allows same-day.
  - Logic: Validate requestedStartDate >= today AND (if same day) currentTime + 2 hours <= end of day.

- **Option C: Minimum 24-hour notice**
  - Impact: Requests must be for tomorrow or later.
  - Trade-offs: More realistic for owner response time, but removes same-day option.
  - Logic: Validate requestedStartDate > today.

**Recommendation for MVP**: **Option A** (no minimum). PRD explicitly says "default to today" is allowed. Let users be optimistic—owner can always decline if timing doesn't work. We can add minimum notice if data shows same-day requests have very low approval rates.

---

## Notes for Product

- **Integration with Feature 4** (Borrow Tracking): Q4 about Active Borrow record creation is critical and should be decided in coordination with that feature's spec. Suggest reviewing both PRDs together to ensure status transitions align.

- **Notification infrastructure**: Questions 6 and 7 about notification timing and batching might benefit from a broader notification strategy document if we plan more features with similar needs (e.g., reminders, announcements).

- **Privacy consideration**: Q9 mentions showing conflicting date ranges might reveal other borrowers' schedules. Want to confirm this is acceptable.

- **Default behavior preference**: For MEDIUM priority questions (Q10-Q12), I've recommended defaults that favor simplicity and user freedom. Happy to implement stricter controls if you anticipate abuse issues or have data from similar platforms.

- Once these questions are answered, I'm confident we can proceed to detailed technical spec. The core data model and workflows are well-defined in the PRD—these questions just clarify edge cases and product philosophy.