# Borrow Tracking & Returns - Feature Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: return timing rules, extension request limits, auto-confirmation behavior, state transition logic, timezone handling, history filtering)

---

## Feature Overview

The Borrow Tracking & Returns feature provides a complete lifecycle management system for tool borrowing transactions. Once a borrow request is approved, this feature tracks the active borrow from pickup through return, manages due dates and extensions, facilitates the return confirmation process, and maintains a permanent transaction history.

This feature is critical for building trust in the platform. Tool owners need confidence that they'll get their tools back in good condition and on time. Borrowers need a clear system to track what they have, when it's due, and how to properly return items. Without robust tracking, the platform risks becoming unreliable, leading to disputes, lost tools, and eroded community trust.

The feature balances accountability (clear due dates, overdue flags, return confirmations) with flexibility (extension requests, issue reporting) while maintaining a transaction history that contributes to user reputation and trust signals.

---

## User Stories

- As a borrower, I want to see all my currently borrowed tools with their due dates in one place so that I can manage my returns and avoid being late
- As a borrower, I want to receive reminders before tools are due so that I don't accidentally keep something too long
- As a borrower, I want to easily mark a tool as returned so that the owner knows I've brought it back
- As a borrower, I want to request an extension if my project runs long so that I can communicate proactively with the owner
- As a tool owner, I want to see who currently has each of my tools and when they're due back so that I can manage my inventory
- As a tool owner, I want to confirm returns and inspect condition so that any damage is documented at the right time
- As a tool owner, I want to report issues with returned tools so that problems are recorded in the transaction history
- As any user, I want to see my complete borrowing history so that I can reference past transactions
- As any user, I want the system to automatically flag overdue items so that late returns are visible and actionable

---

## Acceptance Criteria (UPDATED v1.1)

- Dashboard displays all active borrows with tool name, other party's name, start date, due date, and days remaining
- Borrowers receive automated email reminders 1 day before due date and on the due date
- **Borrowers can mark a tool as "Returned" at any time after the borrow starts (even before due date)**
- **Owners can confirm returns either after borrower marks returned OR proactively from Active state if they physically receive the tool**
- Owners confirm returns by selecting "Good condition" or "Has issues" with optional photos (up to 5) and description (max 1000 characters)
- Overdue items are visually flagged: yellow indicator at 1 day overdue, red indicator at 3+ days overdue
- **Borrowers can request extensions only BEFORE the due date passes (no extensions once overdue)**
- Extension requests include requested new due date and reason (max 500 characters)
- **Maximum 3 extension requests allowed per borrow (regardless of outcome)**
- **Pending extension requests are automatically cancelled if borrower marks tool as returned**
- **If owner doesn't confirm return within 168 hours (7 days) of borrower marking returned, system auto-confirms as "Good condition"**
- Transaction history shows completed AND cancelled borrows with: tool name, other party, dates, final status, ratings, and any reported issues
- History is filterable by date range, searchable by tool name or username, and filterable by return condition (Good/Issues)
- All transaction state changes are timestamped and logged
- **Due times are 6:00 PM in the owner's timezone (displayed clearly as "Due by 6:00 PM on [date]")**

---

## Detailed Specifications (UPDATED v1.1)

### Return Timing & Flexibility

**Decision**: Borrowers can mark tools as returned at ANY time after the borrow starts, including same-day returns or returns before the due date.

**Rationale**: Early returns demonstrate responsible behavior and good faith. There's no legitimate reason to prevent someone from returning a tool they're done using. Same-day turnaround (borrowing in morning, returning in evening) is perfectly valid and should be celebrated, not blocked. Restricting this would create artificial friction and poor user experience.

**Examples**:
- User borrows drill on Monday for 7-day period ending next Monday
- User finishes project Wednesday evening
- User returns drill to owner Thursday morning (4 days early)
- User marks as returned Thursday 9 AM
- Owner confirms that afternoon
- Transaction shows as completed with 4-day actual duration
- History displays: "Borrowed less than 1 day" if same-day, or "Borrowed 3 days" if multi-day but early

**Edge Cases**:
- **Minimum duration**: No minimum enforced. Zero friction for responsible behavior.
- **Days remaining calculation**: If returned early, days remaining becomes "Returned X days early" in history view
- **Reminder suppression**: Once marked returned, all future reminders cancelled immediately

---

### State Transitions & Return Confirmation

**Decision**: Both borrowers and owners can initiate the return closure process. The state machine supports two paths:
1. **Borrower-initiated**: Active → Pending Return Confirmation → Completed
2. **Owner-initiated**: Active → Completed (owner confirms receipt directly)

**Rationale**: In the physical world, tools can be returned without the borrower using the app (left on porch, handed off in person, etc.). If the borrower forgets to mark it returned in the system but the owner physically has the tool, the owner shouldn't be blocked from closing the transaction. This maintains system accuracy even when users don't follow the ideal workflow.

**Examples**:

*Borrower-initiated path (happy path):*
1. Borrower clicks "Mark as Returned"
2. Status: Active → Pending Return Confirmation
3. Owner receives notification with photos/notes from borrower
4. Owner clicks "Confirm Return" → selects condition
5. Status: Pending Return Confirmation → Completed
6. Both parties can now rate each other

*Owner-initiated path (borrower forgot):*
1. Tool is overdue, borrower returned it physically but didn't mark in app
2. Owner has tool, inspects it
3. Owner clicks "Confirm Receipt" from dashboard (available on Active borrows)
4. Status: Active → Completed (skips Pending state)
5. System records: ConfirmedBy = Owner, ReturnMarkedDate = null
6. Borrower receives notification: "Owner confirmed they received [Tool]. Thank you!"

**Database Impact**:
- `Borrow.Status` enum includes: Active, PendingReturnConfirmation, Completed, Cancelled
- `ReturnConfirmation.ConfirmedBy` tracks who initiated closure: Borrower | Owner
- `Borrow.ReturnMarkedDate` is nullable (null if owner-initiated path)

**UI Considerations**:
- Borrowers see "Mark as Returned" on Active borrows
- Owners see "Confirm Receipt" on Active borrows (separate from "Confirm Return" button shown in Pending state)
- Both buttons lead to same confirmation flow, just different entry points

---

### Undo & Correction After Marking Returned

**Decision**: Once a borrower marks a tool as returned, they CANNOT undo or cancel that action. The return marking is permanent.

**Rationale**: Keeping the state machine simple and unidirectional prevents confusion and ambiguous states. If a borrower clicks "Mark as Returned" by mistake, the impact is minimal—they can contact the owner directly to explain. The owner's confirmation step catches any actual issues. Adding undo functionality complicates the state machine, requires additional notification logic, and creates potential for gaming (marking returned to stop overdue flags, then unmarking).

**Examples**:
- Borrower accidentally clicks "Mark as Returned" on wrong tool
- System moves to Pending Return Confirmation
- Borrower contacts owner via in-app messaging: "Sorry, marked wrong tool as returned. Still have your drill!"
- Owner sees the pending confirmation but knows not to confirm yet
- When actual return happens, owner confirms normally
- Edge case is handled through human communication, not technical undo

**Alternative Handling**:
- If a borrower genuinely returned wrong tool to wrong owner (unlikely but possible), the actual owner can use "Confirm Receipt" to close their own borrow
- Admin intervention available for data correction if needed (out of scope for v1 but possible later)

**Trade-off Accepted**: 
We accept that accidental clicks require human communication to resolve. This is preferable to maintaining complex undo logic that adds little value for the common case. Users learn to be careful with the "Mark as Returned" button, similar to other permanent actions in apps.

---

### Extension Requests & Overdue Status

**Decision**: Extension requests are ONLY allowed BEFORE the due date passes. Once a borrow becomes overdue (after 6:00 PM on due date in owner's timezone), the "Request Extension" button is disabled. No grace period, no exceptions.

**Rationale**: The purpose of extension requests is proactive communication—borrowers signal they need more time BEFORE becoming late. Allowing extensions after already overdue creates misaligned incentives and undermines the due date concept. If a borrower is already late, they should communicate directly with the owner through messaging, not through the formal extension system. This creates clear behavior: request extensions early, or return the tool on time.

**Examples**:

*Proactive extension (desired behavior):*
- Tool due Friday at 6:00 PM
- Borrower realizes Thursday they need 2 more days
- Thursday 10 AM: Borrower requests extension to Sunday
- Owner approves Friday morning
- New due date: Sunday 6:00 PM
- No overdue flags ever appear

*Reactive attempt (blocked):*
- Tool due Friday at 6:00 PM
- Friday 6:01 PM: Tool now overdue
- "Request Extension" button disabled with tooltip: "Cannot request extension after due date. Please return the tool or contact owner directly."
- Borrower sees owner's contact info prominently displayed
- Borrower must message owner: "Sorry I'm late, can I keep until Sunday?"
- Owner can manually extend through messaging agreement, but no formal extension request

**Edge Cases**:
- **On the due date**: Extension allowed until 6:00 PM. At 6:01 PM, disabled.
- **Timezone edge**: Due date calculation uses owner's timezone. If borrower in different timezone, system displays both: "Due Friday 6:00 PM PST (9:00 PM EST)"
- **Already pending extension**: If borrower requested extension Tuesday for Friday due date, but Friday arrives with no response and request times out, extension button remains disabled once overdue

**Database Impact**:
- Extension request validation checks `CurrentDueDate` against `DateTime.UtcNow` converted to owner's timezone
- UI polls/checks due date status to disable button at transition moment

---

### Extension Request Limits

**Decision**: Maximum 3 extension requests per borrow, counting all requests regardless of outcome (approved, denied, timed out). After 3 requests, no more extensions allowed.

**Rationale**: Prevents extension request spam and establishes that borrows have bounded duration. Three requests is generous (allows asking multiple times if circumstances change) but prevents abuse. If a borrower truly needs the tool for an extended period after 3 requests, they should return it and request a new borrow, or the owner can manually extend through direct communication.

**Examples**:

*Reasonable use:*
- Request 1: Approved (+3 days)
- Request 2: Approved (+2 days)
- Tool returned on time with both extensions
- Total requests: 2 (under limit)

*Limit reached:*
- Request 1: Denied (owner needs tool back)
- Request 2: Approved (+5 days)
- Request 3: Timed out (owner didn't respond)
- "Request Extension" button now permanently disabled for this borrow
- Tooltip: "Extension limit reached (3 requests). Please return tool or contact owner directly."

*Mixed outcomes:*
- Request 1: Approved
- Request 2: Denied
- Request 3: Approved
- Cannot request 4th extension
- Borrower must work within approved timeline or return tool

**Database Impact**:
- `ExtensionRequest` table has all requests for a borrow
- Query counts: `SELECT COUNT(*) FROM ExtensionRequest WHERE BorrowId = X`
- If count >= 3, UI disables request button
- Validation on backend also checks count before creating new request

**Display**:
- Dashboard shows: "Extensions: 2/3 used" or similar indicator
- Transaction detail view shows history of all extension requests with outcomes

---

### Extension Requests & Return Interaction

**Decision**: When a borrower marks a tool as returned, any pending extension request is automatically cancelled. The extension request status changes to "Cancelled - Tool Returned" and the owner receives a notification.

**Rationale**: A pending extension request becomes moot once the tool is returned. Keeping the request open would confuse the owner (why approve an extension for a tool I have back?). Auto-cancellation maintains clean state and prevents the owner from wasting time reviewing an irrelevant request. Clear notification ensures the owner understands what happened.

**Examples**:

*Extension pending when returned:*
1. Monday: Borrower requests extension from Friday to Sunday
2. Extension status: Pending (owner hasn't responded yet)
3. Wednesday: Borrower finishes early, marks tool as returned
4. System immediately:
   - Changes extension status to "Cancelled"
   - Sets cancellation reason: "Tool returned before extension needed"
   - Sends notification to owner: "[Borrower] returned [Tool] early. Their extension request has been cancelled."
5. Owner sees returned tool pending confirmation, no action needed on extension

*Multiple extensions, last one pending:*
1. Extension 1: Approved (now at 2/3 limit)
2. Extension 2: Requested, pending
3. Borrower marks returned
4. Extension 2 cancelled automatically
5. Transaction history shows: 1 approved extension, 1 cancelled extension

**Notification Content**:
```
Subject: Extension request cancelled - tool returned

[Borrower Name] marked [Tool Name] as returned, so their pending 
extension request is no longer needed and has been cancelled.

Please confirm the return to complete this transaction.

[Confirm Return Button]
```

**Database Impact**:
- When `Borrow.Status` changes to `PendingReturnConfirmation`, trigger check for pending extensions
- Update `ExtensionRequest.Status = Cancelled` where `BorrowId = X AND Status = Pending`
- Set `ExtensionRequest.CancellationReason = "Tool returned"`
- This cancellation does NOT count against the 3-request limit for future borrows

**Edge Case - Owner Confirms Receipt Directly**:
- If owner uses owner-initiated path (confirms receipt from Active state)
- Same logic applies: any pending extensions cancelled
- Owner sees note in confirmation flow: "This will cancel the borrower's pending extension request"

---

### Auto-Confirmation After 7 Days

**Decision**: If a borrower marks a tool as returned and the owner does not confirm within exactly 168 hours (7 days), the system automatically confirms the return as "Good condition" with a system-generated note.

**Rationale**: Prevents borrows from remaining in limbo indefinitely if owners are unresponsive. Seven days is ample time for an owner to inspect a returned tool. Auto-confirmation defaults to "Good condition" (benefit of the doubt to borrower) and frees the borrower from responsibility. This protects borrowers from owner negligence while still giving owners a full week to report issues.

**Examples**:

*Owner responds in time:*
- Tuesday 2:00 PM: Borrower marks returned
- Friday 10:00 AM: Owner confirms good condition
- Auto-confirmation never triggers

*Owner doesn't respond:*
- Tuesday 2:00 PM: Borrower marks returned (`ReturnMarkedDate = 2025-01-14 14:00:00 UTC`)
- Next Tuesday 2:00 PM: 168 hours elapsed
- Background job triggers auto-confirmation:
  - Status: Pending Return Confirmation → Completed
  - ReturnCondition: Good
  - OwnerNotes: "Auto-confirmed after 7 days - no issues reported"
  - ReturnConfirmedDate: 2025-01-21 14:00:00 UTC
  - ConfirmedBy: System
- Both parties notified: "This return was automatically confirmed as no issues were reported within 7 days."

*Owner reports issue at day 6:*
- Day 1: Marked returned
- Day 6: Owner confirms with issue report
- Auto-confirmation job sees status is already Completed, skips

**Precise Timing**:
- Clock starts at `ReturnMarkedDate` timestamp (exact minute)
- Auto-confirmation triggers at `ReturnMarkedDate + 168 hours`
- Background job runs hourly, processes all borrows where:
  - `Status = PendingReturnConfirmation`
  - `ReturnMarkedDate <= UtcNow - 168 hours`
- Job is idempotent (safe to run multiple times)

**Database Impact**:
- `ReturnConfirmation` record created by system with:
  - `Condition = Good`
  - `OwnerNotes = "Auto-confirmed after 7 days - no issues reported"`
  - `ConfirmedBy = System`
- `Borrow.Status = Completed`
- `Borrow.ReturnConfirmedDate = UtcNow`

**Notifications**:
- Both borrower and owner receive email + in-app notification
- Message emphasizes: "No response within 7 days = assumed good condition"
- Owners reminded of this policy in initial notification when tool marked returned

---

### Due Date Timing & Timezone Handling

**Decision**: All tools are due at 6:00 PM (18:00) in the owner's timezone on the due date. This time is displayed prominently as "Due by 6:00 PM [Timezone] on [Date]".

**Rationale**: 6:00 PM is more realistic than midnight for physical tool returns. Most people don't coordinate returns at 11:59 PM. End of business/dinner time is when people are home and can realistically meet to return items. Using owner's timezone makes sense because the owner is the one receiving the tool—the return happens in their location. This is simpler than calculating midpoint timezones or using borrower's location.

**Examples**:

*Owner and borrower same timezone:*
- Owner in Seattle (PST)
- Borrower in Portland (PST)
- Due date: Friday, January 17, 2025
- Display: "Due by 6:00 PM PST on Friday, Jan 17"
- Overdue triggers at: 2025-01-17 18:00:01 PST (converted to UTC for calculation)

*Owner and borrower different timezones:*
- Owner in Los Angeles (PST)
- Borrower in New York (EST)
- Due date: Friday, January 17, 2025
- Borrower sees: "Due by 6:00 PM PST (9:00 PM EST) on Friday, Jan 17"
- System clarifies both timezones to prevent confusion
- Overdue calculation uses PST (owner's timezone)

*Edge case - borrower crosses timezone:*
- Borrower in Seattle (PST) when borrow starts
- Borrower travels to Chicago (CST) with tool
- Due date still calculated in owner's PST timezone
- App displays: "Due by 6:00 PM PST (8:00 PM CST) on Friday, Jan 17"
- Uses borrower's current device timezone to show local equivalent

**Database Storage**:
- All timestamps stored as UTC in database
- `Borrow.CurrentDueDate` stored as `2025-01-17 02:00:00 UTC` (6:00 PM PST)
- `User.Timezone` field stores owner's timezone (e.g., "America/Los_Angeles")
- Due time always calculated as 6:00 PM in that timezone, converted to UTC for storage

**Display Logic**:
```typescript
// Frontend displays both timezones if different
const ownerTime = "6:00 PM PST";
const borrowerTime = convertToTimezone(dueDate, borrower.timezone);
const display = borrower.timezone === owner.timezone 
  ? `Due by ${ownerTime} on ${date}`
  : `Due by ${ownerTime} (${borrowerTime}) on ${date}`;
```

**Reminder Timing**:
- "1 day before" reminder sent at 6:00 PM (owner's timezone) the day before
- "Due today" reminder sent at 9:00 AM (owner's timezone) on due date
- Gives borrower full day to coordinate return

**Days Remaining Calculation**:
- "Due today" if current time is before 6:00 PM on due date (owner's timezone)
- "Due today by 6:00 PM" if same day
- "Due in X days" if multiple days away
- "1 day overdue" if after 6:00 PM on due date

---

### Transaction History Visibility & Filtering

**Decision**: Transaction history shows ALL completed AND cancelled borrows by default, with a filterable "Status" that allows users to hide cancelled transactions if desired. History also includes a "Return Condition" filter with options: All / Good Condition / Has Issues.

**Rationale**: Complete audit trail is important for accountability and dispute resolution. Cancelled borrows provide context (e.g., "This person requested 5 times but cancelled every borrow" is useful pattern to see). However, most users primarily care about completed transactions, so we make the UI default to showing completed while allowing quick toggle to include cancelled. The condition filter is particularly valuable for owners who want to track which borrows resulted in damage.

**Examples**:

*Default view:*
- History tab loads showing completed borrows only
- Sorted by completion date descending (most recent first)
- Checkbox at top: "☐ Show cancelled borrows"
- Dropdown: "Return condition: All"

*Owner checking damage history:*
- Owner clicks history tab
- Selects "Return condition: Has Issues"
- Sees list of 3 borrows where tools were returned with problems
- Each entry shows: tool, borrower, issue description summary
- Can click details to see full issue report with photos

*User includes cancelled:*
- Checks "Show cancelled borrows"
- List now includes entries with status "Cancelled"
- Cancelled entries display differently:
  - Greyed out or with distinct badge
  - Shows cancellation reason: "Cancelled by borrower before pickup" or "Owner cancelled request"
  - No return condition (not applicable)

**Filter Options**:

1. **Status Filter**:
   - ☐ Show cancelled borrows (checkbox, unchecked by default)
   - When checked, includes `Borrow.Status = Cancelled` in results
   
2. **Return Condition Filter** (dropdown):
   - All (default)
   - Good condition (`ReturnCondition = Good`)
   - Has issues (`ReturnCondition = HasIssues`)
   - Only applies to completed borrows; cancelled borrows don't have return condition

3. **Date Range Filter**:
   - Last 30 days
   - Last 6 months
   - Last year
   - All time (default)
   - Custom range (date picker)

4. **Search**:
   - Text input searches: tool name, other party's username, neighborhood
   - Live filtering as user types

**Query Behavior**:
```sql
-- Default query (completed only, all conditions, all time)
SELECT * FROM Borrows 
WHERE (BorrowerId = @UserId OR OwnerId = @UserId)
  AND Status = 'Completed'
ORDER BY ReturnConfirmedDate DESC;

-- With "Show cancelled" checked
SELECT * FROM Borrows 
WHERE (BorrowerId = @UserId OR OwnerId = @UserId)
  AND Status IN ('Completed', 'Cancelled')
ORDER BY COALESCE(ReturnConfirmedDate, CancelledDate) DESC;

-- With "Has Issues" filter
SELECT * FROM Borrows 
WHERE (BorrowerId = @UserId OR OwnerId = @UserId)
  AND Status = 'Completed'
  AND ReturnCondition = 'HasIssues'
ORDER BY ReturnConfirmedDate DESC;
```

**Display Details**:

Each history entry shows:
- Tool photo thumbnail
- Tool name
- Other party: "[Name] ([Neighborhood])"
- Role indicator: "You borrowed" or "You lent"
- Date range: "Jan 5 - Jan 12, 2025 (7 days)"
- Status badge: "Returned - Good" or "Returned - Issues" or "Cancelled"
- If issues: Preview of issue description (first 100 chars) + "View details"
- Ratings exchanged (stars, clickable to see reviews)

**Empty States**:
- "No completed borrows yet" (with link to browse tools)
- "No borrows match these filters" (with button to clear filters)

---

### Borrower Return Notes

**Decision**: When marking a tool as returned, borrowers are presented with an optional text box for return notes (max 300 characters). The field is not required but includes helpful placeholder text encouraging communication: "Let the owner know where you left it or if there's anything they should know..."

**Rationale**: Requiring notes creates friction in the return flow and might feel like homework for users who handed the tool directly to the owner. However, we want to encourage communication, especially for porch drop-offs or situations where context helps. Optional with good prompting strikes the right balance—fast for users in a hurry, helpful for those who want to add context. We can analyze usage data and make it required for overdue returns in v2 if needed.

**Examples**:

*Quick return with note:*
- Borrower marks returned
- Sees text box with placeholder
- Types: "Left it on your back porch in the blue bin. Thanks!"
- Owner sees note immediately in notification and confirmation screen

*Return without note:*
- Borrower marks returned
- Leaves text box empty
- Clicks confirm
- No error, just proceeds
- Owner sees: "(No note provided)" or blank field

*Late return with explanation:*
- Borrower returning 2 days overdue
- Uses note field: "Sorry for delay, project took longer than expected. Tool is cleaned and ready."
- Proactive communication helps maintain relationship

**UI Presentation**:
```
Modal: "Mark [Tool Name] as Returned"

You're confirming you've returned this tool to [Owner Name].

Return notes (optional):
[Text box with placeholder: "Let the owner know where you 
left it or if there's anything they should know..."]

0 / 300 characters

[Cancel] [Confirm Return]
```

**Database Storage**:
- `Borrow.ReturnNotes` (nullable, varchar(300))
- Stored when borrower marks returned
- Visible to owner in notification and confirmation screen
- Becomes part of permanent transaction record

**Future Enhancement** (note for v2):
- Could make required if returning overdue: "Please explain the delay (required for late returns)"
- Could analyze: do notes correlate with better ratings? More "Good condition" confirmations?

---

### Display Format: Days Remaining on Due Date

**Decision**: On the due date itself, the dashboard displays "Due today by 6:00 PM [Timezone]" rather than "Due today" or "0 days remaining".

**Rationale**: Users need to know WHEN "today" ends. Simply saying "Due today" leaves ambiguity—does that mean midnight? End of business day? By including the specific time and timezone, we remove all confusion and help users plan their return. This is especially important for borrowers in different timezones than the owner.

**Examples**:

*Same timezone:*
- Current time: Friday, Jan 17, 2025 at 10:00 AM PST
- Due date: Friday, Jan 17, 2025 at 6:00 PM PST
- Display: "Due today by 6:00 PM PST"
- Color: Yellow/amber to indicate urgency

*Different timezone:*
- Current time: Friday, Jan 17, 2025 at 1:00 PM EST (10:00 AM PST)
- Due date: Friday, Jan 17, 2025 at 6:00 PM PST
- Display: "Due today by 6:00 PM PST (9:00 PM EST)"
- Shows both for clarity

*After due time passes:*
- Current time: Friday, Jan 17, 2025 at 6:05 PM PST
- Display changes to: "Overdue by <1 day"
- Color changes to red

**Complete Display Logic**:
```typescript
function getDaysRemainingDisplay(dueDate: DateTime, ownerTz: string, borrowerTz: string) {
  const now = DateTime.now();
  const dueTime = dueDate.setZone(ownerTz); // 6:00 PM in owner's timezone
  
  if (now > dueTime) {
    // Overdue
    const daysOverdue = Math.floor(now.diff(dueTime, 'days').days);
    return {
      text: daysOverdue < 1 ? "Overdue by <1 day" : `Overdue by ${daysOverdue} day(s)`,
      color: daysOverdue >= 3 ? "red" : "yellow-orange"
    };
  }
  
  const daysRemaining = Math.floor(dueTime.diff(now, 'days').days);
  
  if (daysRemaining === 0) {
    // Due today
    const ownerTimeStr = dueTime.toFormat('h:mm a ZZZZ'); // "6:00 PM PST"
    if (ownerTz === borrowerTz) {
      return {
        text: `Due today by ${ownerTimeStr}`,
        color: "amber"
      };
    } else {
      const borrowerTimeStr = dueTime.setZone(borrowerTz).toFormat('h:mm a ZZZZ');
      return {
        text: `Due today by ${ownerTimeStr} (${borrowerTimeStr})`,
        color: "amber"
      };
    }
  }
  
  if (daysRemaining === 1) {
    return {
      text: "Due tomorrow by 6:00 PM",
      color: "yellow"
    };
  }
  
  return {
    text: `Due in ${daysRemaining} days`,
    color: "normal"
  };
}
```

---

### Owner Dashboard View Details Interaction

**Decision**: The "View Details" button in the "I'm Lending" tab opens a modal overlay showing key information about the active borrow, including borrower contact info, borrow dates, and quick actions.

**Rationale**: Active borrows have a focused set of information—borrower identity, timeline, and communication options. A modal is sufficient for this content and keeps the user on their dashboard where they can see all their lending activity. A full page would require navigation away from the dashboard context. An accordion expansion would make the dashboard unwieldy with multiple tools lent out. Modal provides the right balance: quick access to details without losing context.

**Examples**:

*Owner clicks "View Details" on active borrow:*
- Modal opens over dashboard (dark overlay behind)
- Modal title: "[Tool Name] - Currently borrowed"
- Modal content:
  - Borrower info: photo, name, neighborhood, trust score
  - Timeline: Start date, due date, days remaining
  - Extension history (if any): "Extended once: Jan 5 → Jan 8"
  - Quick actions:
    - "Message [Borrower]" button (opens in-app messaging)
    - "Confirm Receipt" button (if want to proactively confirm return)
  - Borrow ID for reference
  - "View Full Tool Listing" link
- Close modal returns to dashboard with all lending items still visible

*Modal on mobile:*
- Full-screen modal on mobile (not tiny popup)
- Same content, optimized for vertical layout
- Swipe down to close

**Modal Content Structure**:
```
┌─────────────────────────────────────┐
│ [X] Power Drill - Currently borrowed│
├─────────────────────────────────────┤
│ Borrowed by:                        │
│ [Photo] John Smith                  │
│         Fremont · Trust Score: 4.8  │
│                                      │
│ Timeline:                           │
│ • Started: Jan 10, 2025             │
│ • Due: Jan 17, 2025 by 6:00 PM PST  │
│ • Status: Due in 3 days             │
│                                      │
│ Extension History:                  │
│ • Jan 12: Extended to Jan 17 ✓      │
│                                      