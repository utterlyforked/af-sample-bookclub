# Loan Tracking & Management - Feature Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: loan activation triggers, due date handling, return confirmation workflow, extension limits, notification schedules)

---

## Feature Overview

The Loan Tracking & Management feature provides a comprehensive system for managing active tool loans throughout their lifecycle. It serves as the operational backbone that keeps borrowers and lenders informed about loan status, due dates, and return logistics.

This feature transforms what could be chaotic informal lending into an organized, reliable system. It ensures tool owners always know where their equipment is and when it's due back, while helping borrowers be responsible community members through proactive reminders and easy return processes. The feature builds trust by creating accountability and reducing the anxiety tool owners might feel about lending valuable equipment.

---

## User Stories

- As a tool owner, I want to track which tools are currently lent out and when they're due back so that I can manage my inventory
- As a borrower, I want reminders about return dates so that I can be a reliable community member  
- As both parties, I want to confirm when tools are returned so that loans are properly closed out
- As a tool owner, I want to know how to contact my borrower if my tool becomes overdue so that I can follow up appropriately
- As a borrower, I want to request an extension if I need the tool longer so that I can communicate changes rather than just being late

---

## Acceptance Criteria (UPDATED v1.1)

- Dashboard showing active loans with due dates, borrower/lender info, and contact options
- Automated email/notification reminders 1 day before due date and on due date
- Simple return confirmation process initiated by borrower, confirmed by tool owner
- Overdue loan notifications sent 1 day and 3 days after due date
- Users can see complete loan history for all tools they've borrowed or lent (including cancelled/failed loans)
- Extension requests limited to maximum 2 per loan, can be sent and approved/declined by tool owners
- Loan status is clearly indicated on tool listings (shows "Currently on loan, returns [date]")
- Loans become active immediately when borrowing request is accepted
- Due dates include date only with system treating as end-of-day (11:59 PM)
- Borrowing limits enforced: maximum 5 active borrowed loans, 10 active lent loans (checked at request time)

---

## Detailed Specifications (UPDATED v1.1)

### Loan Activation and Lifecycle

**Decision**: Loans become "Active" immediately when the tool owner accepts a borrowing request

**Rationale**: Matches typical informal lending behavior where agreement equals commitment. Eliminates need for complex pickup confirmation workflows in MVP while keeping the feature simple and intuitive.

**Examples**:
- Alice requests Bob's drill for March 10-15
- Bob clicks "Accept Request" → Loan status becomes "Active" immediately
- Drill listing shows "Currently on loan, returns March 15"
- Reminder notifications are scheduled based on March 15 due date

**Edge Cases**:
- Tool shows as unavailable in search results as soon as loan is active
- If borrower never picks up tool, owner can mark loan as "Cancelled" with reason

---

### Due Date Precision and Time Zones

**Decision**: Due dates are date-only from user perspective, but system treats as 11:59 PM on due date in user's local timezone

**Rationale**: Users naturally think "I'll return it Tuesday" rather than specific times. System needs precise timing for automated notifications and overdue detection. This gives best user experience while enabling reliable system behavior.

**Examples**:
- User interface shows "Due: March 15, 2024"
- Database stores as "2024-03-15 23:59:59" in user's timezone
- Overdue notifications trigger at midnight on March 16
- "Due today" reminders sent at 9 AM on March 15

**Technical Implementation**:
- Store due_date as TIMESTAMPTZ in PostgreSQL
- Convert user's date input to end-of-day timestamp in their timezone
- All comparisons use UTC for consistency

---

### Return Confirmation Workflow

**Decision**: Only borrowers can initiate return confirmation process. Tool owners confirm receipt.

**Rationale**: Matches natural lending expectations - borrower announces "I returned your tool" and owner acknowledges receipt. Creates clear responsibility and reduces confusion about workflow.

**Examples**:
- Sarah borrows Tom's ladder, returns it to his garage
- Sarah logs in, clicks "Mark as Returned" on loan dashboard
- Sarah adds optional note: "Left in garage as requested, good condition"
- Tom gets notification: "Sarah says she returned your ladder. Confirm receipt?"
- Tom confirms → Loan status becomes "Completed"

**Exception Handling**:
- If Tom doesn't confirm within 48 hours, both parties get reminder
- If still no confirmation after 7 days, loan status becomes "Disputed Return"
- Disputed returns flagged for community moderator review

---

### Extension Request Limits

**Decision**: Maximum 2 extension requests per loan (regardless of approval/denial)

**Rationale**: Handles legitimate scenarios (original extension + emergency situation) while preventing abuse. Most tool loans that need more than 2 extensions indicate poor planning or changed project scope that requires new negotiation.

**Examples**:
- Extension 1: "Project taking longer, need 3 extra days" → Approved
- Extension 2: "Weather delayed work, need 2 more days" → Approved  
- Extension 3 attempt: System blocks with message "Maximum extensions reached. Please contact lender directly to discuss."

**Technical Behavior**:
- Extension counter resets only when loan completes
- Denied extensions count toward limit (prevents spam requests)
- UI shows "1 of 2 extensions used" to set expectations

---

### Overdue Notification Schedule

**Decision**: Exactly two overdue notifications - 1 day and 3 days after due date. No further automated messages.

**Rationale**: Balances persistent follow-up with avoiding spam. Two reminders catch honest mistakes while escalating tone appropriately. Beyond 3 days, human intervention more appropriate than automated nagging.

**Examples**:
- Tool due March 15, not returned by midnight
- March 16 at 9 AM: "Your borrowed [tool] was due yesterday. Please return or contact lender."
- March 18 at 9 AM: "Your borrowed [tool] is now 3 days overdue. This may affect your community rating. Please resolve immediately."
- No further automated messages after day 3

**Escalation Path**:
- After 7 days overdue, tool owner can mark loan as "Lost/Unreturned"
- Community moderators can see all loans overdue >7 days for intervention

---

### Loan History and Record Keeping

**Decision**: Show all loans in history regardless of completion status, with clear status indicators

**Rationale**: Complete transparency builds trust and helps identify patterns. Users can see their full lending/borrowing activity, community moderators can spot problem behaviors, and successful transactions are highlighted.

**Examples**:
- Loan History shows:
  - ✅ "Drill - Completed 3/15/24 - 5 days - Both rated ⭐⭐⭐⭐⭐"
  - ❌ "Saw - Cancelled 3/10/24 - Borrower never picked up"
  - ⚠️ "Ladder - Disputed Return 3/20/24 - Confirmation pending"
  - 🔄 "Sander - Active - Due 3/25/24"

**Filtering Options**:
- Default view: Completed loans only
- Show all: Includes cancelled, disputed, active loans
- Filter by: Status, date range, tool type, other party

---

### Borrowing Limits Enforcement

**Decision**: Check loan limits when borrowing request is submitted, not when loan activates

**Rationale**: Clearer user experience - immediate feedback prevents confusion. Users know right away if they've hit limits rather than having requests accepted then blocked later.

**Examples**:
- Mike has 5 active borrowed loans (at limit)
- Mike tries to request Sarah's drill
- System blocks immediately: "You have reached the maximum of 5 active borrowed loans. Return a tool before borrowing another."
- Clear call-to-action: "View your active loans →"

**Edge Cases**:
- Limit counts only "Active" loans, not "Pending" requests
- If user at limit but loan ends before new request accepted, new request proceeds
- Tool owners see borrower's current loan count when reviewing requests

---

## Q&A History

### Iteration 1 - December 19, 2024

**Q1: What exactly triggers a loan to become "Active"?**  
**A**: Loans become "Active" immediately when the tool owner accepts a borrowing request. No separate pickup confirmation needed for MVP - keeps workflow simple while matching informal lending expectations.

**Q2: How specific are loan due dates and times?**  
**A**: Date only from user perspective (due "March 15th") but system treats as 11:59 PM on due date in user's timezone. Gives simple UX while enabling precise overdue detection and notifications.

**Q3: What happens if return confirmation is never completed?**  
**A**: After 7 days without confirmation, loan status becomes "Disputed Return" and flags for community moderator attention. Acknowledges potential problem rather than assuming resolution.

**Q4: Can multiple extension requests be made for the same loan?**  
**A**: Maximum 2 extension requests per loan total (including denied requests). Handles legitimate needs while preventing abuse. Counter resets only when loan completes.

**Q5: Who can initiate the return confirmation process?**  
**A**: Only borrowers can initiate return confirmation. Tool owners confirm receipt. Matches natural expectation - borrower announces return, owner acknowledges.

**Q6: What's the exact notification schedule for overdue loans?**  
**A**: Exactly two notifications: 1 day overdue and 3 days overdue. No further automated messages. After day 3, human intervention more appropriate than continued automated reminders.

**Q7: Should loan history show cancelled/failed loans?**  
**A**: Yes, show all loans with clear status indicators. Complete transparency builds trust and helps identify patterns. Users can filter to "completed only" if desired.

**Q8: How are loan limits enforced across concurrent requests?**  
**A**: Check limits when borrowing request is submitted. Immediate feedback prevents user confusion. Limits check only "Active" loans, not pending requests.

---

## Product Rationale

**Why immediate loan activation?**  
Matches how informal lending actually works - when someone agrees to lend, both parties consider it committed. Adding pickup confirmation would create extra friction without significant benefit for MVP. Can add pickup workflows in v2 if disputes about handoffs become common.

**Why date-only due dates with end-of-day handling?**  
Users think naturally in dates for tool loans ("I'll return it Thursday") but system needs precise timing for notifications. This approach gives intuitive user experience while enabling reliable automated behavior.

**Why borrower-initiated returns?**  
Mirrors real-world etiquette - borrower has responsibility to announce return, lender acknowledges receipt. Creates clear workflow expectations and reduces confusion about whose turn it is to act.

**Why 2-extension limit?**  
Handles genuine scenarios (project runs long, weather delays work) while preventing endless extension requests that could indicate project scope has fundamentally changed. Forces real communication after 2 extensions.

**Why simple overdue schedule?**  
Two notifications strike balance between helpful reminders and avoiding spam. Beyond 3 days overdue, issue likely needs human discussion rather than more automated messages.

**Why enforce borrowing limits at request time?**  
Immediate feedback is better user experience than delayed rejection. If system says "request sent" but then blocks activation later, creates confusion and broken expectations.