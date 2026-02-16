# Borrow Tracking & Returns - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: 2025-01-10

---

## Summary

After reviewing the specification, I've identified **17** areas that need clarification before implementation can begin. These questions address:
- Core data model and state transitions
- Extension request mechanics and limits
- Auto-confirmation behavior
- Overdue calculation and timing
- Return confirmation workflow details
- Photo upload constraints
- Notification timing and timezone handling
- Transaction history access patterns

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: Can borrowers mark a tool as returned before the due date?

**Context**: The spec shows "Mark as Returned" button on active borrows but doesn't explicitly state whether this is only available on/after due date or anytime during the borrow period. This affects UI logic and whether we need validation to prevent premature returns.

**Options**:
- **Option A: Allow return anytime after start date**
  - Impact: Borrower can mark returned even day 1 of a 14-day borrow
  - Trade-offs: Maximum flexibility, handles early returns naturally, simpler logic
  - Database: No additional validation needed
  
- **Option B: Only allow on or after due date**
  - Impact: Button disabled until due date arrives
  - Trade-offs: Enforces minimum borrow period, but borrower might return early and forget to mark it
  - Database: Need validation check against due date

**Recommendation for MVP**: Option A (allow anytime). Users returning early is good behavior and shouldn't be blocked. Early returns show good faith and responsibility.

---

### Q2: What happens if borrower requests extension while tool is already marked "returned" but not confirmed?

**Context**: Spec says extensions can be requested "until due date passes" but doesn't address the "Pending Return Confirmation" state. Can borrower request extension if they marked it returned but owner hasn't confirmed yet?

**Options**:
- **Option A: No extensions in "Pending Return Confirmation" state**
  - Impact: Extension button disappears once marked returned
  - Trade-offs: Simple logic, but if owner takes days to confirm, borrower locked out
  - UI: Clear state transition
  
- **Option B: Allow extension until owner confirms**
  - Impact: Borrower could mark returned, then request extension (contradictory)
  - Trade-offs: Confusing UX, creates weird state
  
- **Option C: Marking returned cancels any pending extension requests**
  - Impact: If extension pending and borrower marks returned, extension auto-denied
  - Trade-offs: Clean state management, prevents contradictions

**Recommendation for MVP**: Option A + C combined. Once marked returned, no new extensions allowed. Any pending extension auto-denied when marked returned. Clearest logic.

---

### Q3: Can borrower "un-mark" a return before owner confirms?

**Context**: Spec shows borrower marks returned, then owner confirms. But what if borrower accidentally clicked button, or marked returned but owner says "I don't have it yet"?

**Options**:
- **Option A: No undo - return marking is permanent**
  - Impact: Once marked, borrower can't reverse it
  - Trade-offs: Simpler state machine, but frustrating if mistake made
  - Database: Status change is one-way
  
- **Option B: Allow borrower to cancel return before owner confirms**
  - Impact: "Cancel Return" button in "Pending Confirmation" state
  - Trade-offs: More flexible, handles mistakes, but adds complexity
  - Database: Need reverse transition logic
  
- **Option C: Only allow undo within X minutes (grace period)**
  - Impact: 15-minute window to cancel, then locked
  - Trade-offs: Catches immediate mistakes, bounded complexity

**Recommendation for MVP**: Option A (no undo). Borrower should contact owner directly if mistake made. Can add grace period in v2 if users request it. Keeps state machine simple.

---

### Q4: What's the exact timing for the 7-day auto-confirm?

**Context**: Spec says "if owner doesn't respond within 7 days, system auto-confirms as 'Good condition'". Need precise definition of when this 7-day clock starts.

**Options**:
- **Option A: 7 days from when borrower marks returned (ReturnMarkedDate)**
  - Impact: Clock starts immediately when borrower clicks button
  - Trade-offs: Clear trigger, but owner might not see notification for a day
  
- **Option B: 7 days from due date, if marked returned**
  - Impact: Different timing based on when returned
  - Trade-offs: More complex, accounts for early returns differently than on-time
  
- **Option C: 168 hours (exact) from ReturnMarkedDate**
  - Impact: Precise to the hour vs. "7 calendar days"
  - Trade-offs: More predictable, easier to test

**Recommendation for MVP**: Option A + C combined. Start clock at ReturnMarkedDate timestamp, auto-confirm exactly 168 hours later. Clear, testable, fair to both parties.

---

### Q5: Can owner confirm return if borrower hasn't marked it returned yet?

**Context**: Spec describes borrower marking → owner confirming flow. But in physical world, tool might be returned and owner has it, but borrower forgot to mark in system. Can owner confirm proactively?

**Options**:
- **Option A: No - borrower must mark first**
  - Impact: Owner sees overdue item, has the tool, but can't close transaction
  - Trade-offs: Enforces process but frustrating if borrower unresponsive
  - Database: Strict state machine: Active → PendingReturnConfirmation → Completed
  
- **Option B: Yes - owner can confirm from Active state**
  - Impact: Owner sees "I received the tool back" button even if borrower hasn't marked
  - Trade-offs: More flexible, but might create confusion about whose responsibility
  - Database: Allow Active → Completed transition directly
  
- **Option C: Owner can "report received" which prompts borrower to confirm**
  - Impact: Reverse flow - owner says "I have it" → borrower must confirm
  - Trade-offs: Collaborative, but adds another state

**Recommendation for MVP**: Option B (owner can confirm directly). If borrower forgets to mark returned, owner shouldn't be blocked. Both parties can initiate close. Add flag "ConfirmedBy" to track who initiated.

---

### Q6: What happens to pending extension requests when borrow is marked returned?

**Context**: Extension requests can be pending for up to 24 hours. Borrower might request extension, then return tool before owner responds.

**Options**:
- **Option A: Auto-deny all pending extensions when marked returned**
  - Impact: Return action automatically closes any pending extension requests
  - Trade-offs: Clean state, but no notification to owner that request is moot
  
- **Option B: Leave extension request open until timeout**
  - Impact: Owner still sees extension request even though tool returned
  - Trade-offs: Confusing, owner might approve extension after tool already back
  
- **Option C: Cancel extension with notification to owner**
  - Impact: "Extension request cancelled - borrower returned tool"
  - Trade-offs: Clear communication, extra notification

**Recommendation for MVP**: Option C (cancel with notification). Keeps owner informed, prevents confusion. Extension request table gets Status="Cancelled" with reason.

---

### Q7: How do we handle same-day turnaround (start and return on same day)?

**Context**: User borrows tool in morning, returns it same evening. Due date might be 7 days out. Days remaining calculation could be confusing.

**Options**:
- **Option A: Allow it - perfectly valid**
  - Impact: Transaction can complete in hours
  - Trade-offs: Simple logic, no artificial restrictions
  - Display: Show "Borrowed less than 1 day" in history
  
- **Option B: Enforce minimum borrow duration (24 hours)**
  - Impact: Can't mark returned until 24 hours after start
  - Trade-offs: Prevents gaming system, but restricts legitimate quick returns
  
- **Option C: Flag same-day returns for review**
  - Impact: Allow but track for analytics
  - Trade-offs: Data for future decision, no user impact

**Recommendation for MVP**: Option A (allow it). Quick returns are good behavior. No minimum duration needed for v1.

---

### Q8: Maximum number of pending extension requests per borrow?

**Context**: Spec says "only one pending request at a time" but doesn't specify total limit over lifetime of borrow. Borrower could request, wait for timeout, request again, repeat.

**Options**:
- **Option A: Unlimited total, one pending at a time**
  - Impact: Borrower can request extension 5+ times if each times out
  - Trade-offs: Maximum flexibility, but could annoy owners
  
- **Option B: Maximum 3 extension requests per borrow**
  - Impact: After 3 attempts (approved or denied), no more allowed
  - Trade-offs: Reasonable limit, prevents abuse
  
- **Option C: Maximum 2 approved extensions per borrow**
  - Impact: Can request unlimited times, but only 2 can be approved
  - Trade-offs: Flexible on requests, strict on approvals

**Recommendation for MVP**: Option B (max 3 total requests). Prevents extension request spam. After 3 requests, borrower must return tool or contact owner outside system.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q9: Should extension requests be allowed after tool is overdue?

**Context**: Spec says "Borrowers can request extension even if item is 1-2 days overdue (not available if 3+ days overdue)" but this creates odd incentive structure. Why allow after already late?

**Options**:
- **Option A: No extensions once overdue at all**
  - Impact: Extension button disappears at 12:01 AM on overdue day
  - Trade-offs: Encourages requesting before due date, simpler rule
  
- **Option B: Allow up to 2 days overdue (as spec states)**
  - Impact: Small grace period for "I meant to request yesterday"
  - Trade-offs: More forgiving, but still has hard cutoff at 3 days
  
- **Option C: Always allow extensions, but owner sees overdue status**
  - Impact: Request UI shows "Tool is X days overdue - requesting extension"
  - Trade-offs: Most flexible, owner makes informed decision

**Recommendation for MVP**: Option A (no extensions once overdue). Cleaner incentive structure: request before due date or return tool. Being overdue means communicate directly with owner, not through extension system.

---

### Q10: What "due time" should we use for due date calculations?

**Context**: Spec mentions "end of day (11:59 PM) in owner's timezone" but this creates complexity. Need to decide exact cutoff time.

**Options**:
- **Option A: 11:59 PM in owner's timezone**
  - Impact: Due date is last minute of calendar day in owner's location
  - Trade-offs: Most generous, but timezone math complex
  - Example: Tool due Jan 10, owner in PST, borrower in EST → different times
  
- **Option B: 11:59 PM in borrower's timezone**
  - Impact: Due when borrower's day ends
  - Trade-offs: Borrower controls deadline, simpler for borrower
  
- **Option C: End of day UTC (11:59 PM UTC)**
  - Impact: Single global reference, no timezone confusion
  - Trade-offs: Could be middle of day for some users
  
- **Option D: 6:00 PM in owner's timezone**
  - Impact: "Business hours" cutoff, easier to coordinate returns
  - Trade-offs: More realistic return time, less generous than midnight

**Recommendation for MVP**: Option D (6:00 PM owner's timezone). More realistic than midnight - people don't return tools at 11:59 PM. Simpler coordination. Display clearly: "Due by 6:00 PM on [date]".

---

### Q11: Should transaction history show cancelled/failed borrows?

**Context**: Spec describes history for "completed transactions" but doesn't address borrows that were approved but never started, or cancelled mid-borrow.

**Options**:
- **Option A: Only show completed borrows (status=Completed)**
  - Impact: History is only successful transactions
  - Trade-offs: Clean history, but missing context if disputes arise
  
- **Option B: Show completed + cancelled, with clear distinction**
  - Impact: History includes "Cancelled" transactions with reason
  - Trade-offs: Complete record, but more clutter
  
- **Option C: Separate tabs: "Completed" vs "Cancelled"**
  - Impact: Two views of historical data
  - Trade-offs: Clean separation, but more UI complexity

**Recommendation for MVP**: Option B (show completed + cancelled). Filter defaults to "Completed" but user can toggle "Show cancelled" checkbox. Complete audit trail matters for disputes.

---

### Q12: Can users filter history by "Has issues" vs "Good condition"?

**Context**: Spec mentions filtering by outcome but doesn't define exactly what filter options exist.

**Options**:
- **Option A: Yes - explicit "Condition" filter**
  - Impact: Filter dropdown includes "Good condition" / "Has issues" / "All"
  - Trade-offs: Useful for owners tracking damaged returns
  
- **Option B: No filter - only visible in detail view**
  - Impact: Must scan list or use search
  - Trade-offs: Simpler UI, less query complexity
  
- **Option C: Smart filter combining multiple factors**
  - Impact: "Problem returns" filter = issues reported OR late OR low rating
  - Trade-offs: More useful but requires definition of "problem"

**Recommendation for MVP**: Option A (simple condition filter). Owners need to track which borrows resulted in damage. Clean boolean filter on ReturnCondition field.

---

### Q13: Should reminder emails include photos of the tool?

**Context**: Spec says reminders include "tool name and photo" but doesn't specify if this is thumbnail, full image, or just link.

**Options**:
- **Option A: Inline thumbnail in email (50x50px)**
  - Impact: Small image embedded in email HTML
  - Trade-offs: Visual reminder, but increases email size slightly
  
- **Option B: Link to tool listing page**
  - Impact: Text only, click to see tool
  - Trade-offs: Smaller email, requires click
  
- **Option C: Responsive image (thumbnail on mobile, larger on desktop)**
  - Impact: Better UX but more complex email template
  - Trade-offs: Professional look, standard practice

**Recommendation for MVP**: Option A (simple thumbnail). Visual reminder helps borrower remember which tool. Small enough to not impact delivery. Standard practice for transactional emails.

---

### Q14: What's the character limit for owner's response message when denying extension?

**Context**: Spec says owner can deny extension with message but doesn't specify length limit.

**Options**:
- **Option A: Same as extension request reason (500 chars)**
  - Impact: Symmetric limits for both parties
  - Trade-offs: Consistent, enough for explanation
  
- **Option B: Shorter limit (200 chars)**
  - Impact: Brief explanation only
  - Trade-offs: Encourages concise communication
  
- **Option C: Optional message (not required)**
  - Impact: Owner can deny without explanation
  - Trade-offs: Faster for owner, but less informative

**Recommendation for MVP**: Option A (500 chars, required). Denying extension is impactful to borrower - owner should explain why. Same limit as request reason maintains symmetry.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q15: Should borrower's return notes be required or optional?

**Context**: Spec says "optional return notes (max 300 characters)" but doesn't specify if we should encourage them.

**Options**:
- **Option A: Truly optional - can submit without note**
  - Impact: Many users will skip it
  - Trade-offs: Faster workflow, but less communication
  
- **Option B: Optional but prompted with placeholder text**
  - Impact: Text box says "Let the owner know where you left it..."
  - Trade-offs: Encourages communication without forcing
  
- **Option C: Required for overdue returns**
  - Impact: If returning late, must explain
  - Trade-offs: Ensures communication when it matters most

**Recommendation for MVP**: Option B (optional with good prompt). Encourage good communication without blocking workflow. Could make required for overdue in v2.

---

### Q16: How do we display "days remaining" on the due date itself?

**Context**: Spec shows various "days remaining" messages but doesn't specify exact wording for due date.

**Options**:
- **Option A: "Due today"**
  - Impact: Clear, simple
  
- **Option B: "Due today by 6:00 PM"**
  - Impact: Includes specific time (if we chose Option D for Q10)
  
- **Option C: "0 days remaining"**
  - Impact: Consistent with calculation logic

**Recommendation for MVP**: Option B (include time). Users need to know when "today" ends. "Due today by 6:00 PM" is clearest.

---

### Q17: Should "View Details" button in owner's lending tab open a modal or navigate to new page?

**Context**: Spec mentions "View Details" button for owners to see borrower info and messaging option, but doesn't specify interaction pattern.

**Options**:
- **Option A: Modal overlay**
  - Impact: Lightweight view, stays on dashboard
  - Trade-offs: Quick access, but limited space for details
  
- **Option B: Navigate to dedicated borrow detail page**
  - Impact: Full page with all borrow information
  - Trade-offs: More space for info, but leaves dashboard
  
- **Option C: Expandable accordion within dashboard**
  - Impact: Inline expansion showing details
  - Trade-offs: Keeps context, but dashboard gets long

**Recommendation for MVP**: Option A (modal). Active borrows have limited info to show - tool details, borrower contact, message button. Modal is sufficient and maintains dashboard context.

---

## Notes for Product

- The spec is quite comprehensive! Most questions are about edge cases and exact behavior rather than missing core functionality.
- Extension request mechanics (Q2, Q6, Q8, Q9) form a cluster - these decisions interact with each other.
- Timezone handling (Q10) has downstream impacts on reminder timing and overdue calculations.
- Several questions about state transitions (Q2, Q3, Q5, Q6) - these need to be answered consistently to maintain clean state machine.
- Once these are answered, the data model and workflows are clear enough to proceed to implementation.
- Auto-confirmation timing (Q4) is critical for background job implementation.

---

**This feature will be ready for implementation once these questions are answered. Happy to do another iteration if answers raise new questions.**