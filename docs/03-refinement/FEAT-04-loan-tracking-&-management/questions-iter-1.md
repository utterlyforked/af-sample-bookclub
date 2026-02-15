# Loan Tracking & Management - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: December 19, 2024

---

## Summary

After reviewing the specification, I've identified 8 areas that need clarification before implementation can begin. These questions address:
- Core loan lifecycle timing and behavior
- Notification system specifics
- Return confirmation workflow details
- Extension request constraints
- Data integrity and edge case handling

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What exactly triggers a loan to become "Active"?

**Context**: The PRD mentions loans become "Active" when "user accepts borrowing request" but doesn't specify the complete handoff process. This affects:
- When notifications start being scheduled
- When tools show as "unavailable" in listings
- Whether there's a pickup confirmation step

**Options**:
- **Option A: Active immediately on request acceptance**
  - Impact: Simple state transition, reminders start immediately based on agreed due date
  - Trade-offs: No confirmation that physical handoff occurred
  
- **Option B: Active only after both parties confirm pickup**
  - Impact: Need "Pickup Confirmation" step before loan becomes truly active
  - Trade-offs: More complex but ensures tool actually changed hands
  - Database: Additional PickupConfirmation entity needed

**Recommendation for MVP**: Option A (immediate activation). Simpler implementation, matches typical informal lending. Can add pickup confirmation in v2 if disputes arise.

---

### Q2: How specific are loan due dates and times?

**Context**: The PRD mentions due dates but not whether these include specific times. This affects:
- When "overdue" notifications trigger
- Database field types (date vs datetime)
- Time zone handling complexity
- User input forms

**Options**:
- **Option A: Date only (due "sometime on March 15th")**
  - Impact: Store as date field, overdue triggers at end of due date
  - Trade-offs: Simpler UX, less precision
  - Database: DATE column type
  
- **Option B: Date + specific time (due "March 15th at 6:00 PM")**
  - Impact: Store as datetime, overdue triggers at exact time
  - Trade-offs: More precise but complex time zone handling
  - Database: TIMESTAMP column type

- **Option C: Date + default end-of-day time**
  - Impact: Users see date, system treats as 11:59 PM on due date
  - Trade-offs: Best of both - simple UX, precise system behavior

**Recommendation for MVP**: Option C (date with default end-of-day). Users think in dates for tool loans, but system needs precise timing for notifications.

---

### Q3: What happens if return confirmation is never completed?

**Context**: PRD says "If not confirmed within 48 hours, both parties get reminder" but doesn't specify what happens after that. This affects:
- Whether loans can get stuck in limbo
- Data cleanup processes
- Dispute resolution workflows

**Options**:
- **Option A: Loan stays in "Pending Return Confirmation" indefinitely**
  - Impact: Need admin tools to resolve stuck loans
  - Trade-offs: No automatic assumptions, but requires manual intervention
  
- **Option B: Auto-complete return after 7 days with system note**
  - Impact: Automatic cleanup prevents stuck states
  - Trade-offs: Assumes return happened, might mask actual problems
  
- **Option C: Escalate to "Disputed Return" status after 7 days**
  - Impact: Flag for community moderator attention
  - Trade-offs: Acknowledges problem without assuming resolution

**Recommendation for MVP**: Option C (disputed status). Acknowledges that lack of confirmation might indicate a real problem rather than just ignoring it.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q4: Can multiple extension requests be made for the same loan?

**Context**: PRD describes extension request workflow but doesn't specify if borrowers can request multiple extensions or only one per loan.

**Options**:
- **Option A: Only one extension request per loan**
  - Impact: Simple validation, prevents endless extensions
  - Trade-offs: Inflexible if circumstances change again
  - Database: Simple boolean "extension_requested" flag
  
- **Option B: Multiple extensions allowed**
  - Impact: Need to track multiple ExtensionRequest records
  - Trade-offs: More flexible but could enable abuse
  - Database: Full ExtensionRequest entity with status tracking

- **Option C: Maximum 2 extensions per loan**
  - Impact: Middle ground with reasonable limit
  - Trade-offs: Some flexibility while preventing abuse

**Recommendation for MVP**: Option C (max 2 extensions). Handles legitimate needs (original extension + emergency) while preventing endless requests.

---

### Q5: Who can initiate the return confirmation process?

**Context**: PRD says "Either party can initiate return process" but this could create confusion about who should normally start it.

**Options**:
- **Option A: Either party, first one wins**
  - Impact: Simple rule, prevents duplicate processes
  - Trade-offs: Might confuse users about whose responsibility it is
  
- **Option B: Borrower must initiate, lender confirms**
  - Impact: Clear responsibility - borrower says "I returned it", owner confirms
  - Trade-offs: More intuitive workflow, matches real-world lending
  
- **Option C: Either party, but UI suggests borrower should initiate**
  - Impact: Flexible but guided UX
  - Trade-offs: Best of both worlds

**Recommendation for MVP**: Option B (borrower initiates). Matches natural expectation that borrower announces return, owner acknowledges receipt.

---

### Q6: What's the exact notification schedule for overdue loans?

**Context**: PRD mentions "1 day overdue" and "3 days overdue" notifications but doesn't specify the complete schedule or if there are further escalations.

**Options**:
- **Option A: Only the two mentioned (1 day + 3 days overdue)**
  - Impact: Simple schedule, limited notification spam
  - Trade-offs: Might not be enough for very late returns
  
- **Option B: Escalating schedule (1, 3, 7, 14 days overdue)**
  - Impact: More persistent follow-up for problem loans
  - Trade-offs: Could feel spammy, more complex to implement
  
- **Option C: 1, 3 days, then weekly until resolved**
  - Impact: Persistent but not overwhelming
  - Trade-offs: Ensures ongoing visibility without daily spam

**Recommendation for MVP**: Option A (just 1 and 3 days). Simple and sufficient for MVP, can add weekly reminders in v2 if needed.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q7: Should loan history show cancelled/failed loans?

**Context**: PRD mentions loan history but doesn't specify whether it includes loans that were cancelled before completion or failed to complete properly.

**Options**:
- **Option A: Only show completed loans in history**
  - Impact: Clean history focused on successful transactions
  - Trade-offs: Loses visibility into problem patterns
  
- **Option B: Show all loans with clear status indicators**
  - Impact: Complete audit trail including problems
  - Trade-offs: More complex UI but better transparency

**Recommendation**: Option B (show all with status). Better for building trust and identifying patterns, though can filter by status if needed.

---

### Q8: How are loan limits enforced across concurrent requests?

**Context**: PRD mentions "maximum 5 active borrowed loans and 10 active lent loans" but doesn't specify when this check happens - at request time or loan activation time.

**Options**:
- **Option A: Check limits when borrowing request is made**
  - Impact: Prevents requests that would exceed limits
  - Trade-offs: Simpler but might block valid requests if other loans end soon
  
- **Option B: Check limits when loan would become active**
  - Impact: Allow requests but prevent activation if limits exceeded
  - Trade-offs: More flexible but could create confusing pending states

**Recommendation**: Option A (check at request time). Clearer user experience - if you can't borrow more, the request is blocked immediately with clear explanation.

---

## Notes for Product

- These questions focus on behavior and business logic - once answered, the technical implementation using EF Core, PostgreSQL, and Hangfire for notifications is straightforward
- The notification system will integrate cleanly with your existing user communication infrastructure
- Database schema can support any of these options efficiently with proper indexing on loan status and dates
- Happy to do another iteration if these answers raise new questions about the workflows