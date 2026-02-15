# Loan Tracking & Returns - Feature Requirements

**Version**: 1.0  
**Date**: February 15, 2025  
**Status**: Initial - Awaiting Tech Lead Review

---

## Feature Overview

The Loan Tracking & Returns feature provides comprehensive monitoring and management of active tool loans from initial pickup through final return. This feature ensures tools are returned on time and in good condition while maintaining positive relationships between community members.

This feature acts as the operational backbone of the tool sharing platform - without reliable tracking and return processes, tool owners would lose confidence in lending their valuable equipment. It combines automated monitoring (reminders, notifications) with manual verification (condition checks, confirmation steps) to create accountability while remaining user-friendly.

The feature serves both tool owners (who need visibility into their loaned inventory) and borrowers (who need clear guidance on return expectations) while capturing the data needed to build trust and reputation within the community.

---

## User Stories

- As a tool owner, I want to see all my loaned-out tools and their expected return dates so I can track my inventory
- As a borrower, I want reminders about return dates and instructions so I can be a good neighbor  
- As both parties, I want to confirm tool condition at pickup and return so we agree on any damage
- As a tool owner, I want to be notified if my tool is returned late so I can follow up appropriately
- As a borrower, I want to easily mark a tool as returned and confirm its condition so the transaction closes properly
- As a community member, I want to see that the platform handles overdue items so I feel confident participating

---

## Acceptance Criteria

- Dashboard shows all active loans with days remaining, borrower info, and expected return date
- Automated reminders sent to borrowers 2 days and 1 day before return date
- Photo-based condition check required at both pickup and return, with side-by-side comparison
- Late return notifications sent to both parties, with escalation options for significantly overdue items
- Both parties must confirm tool return before loan status changes to "completed"
- Loan history preserved with all photos, dates, and condition notes for future reference
- Overdue tools are clearly flagged in owner's inventory dashboard
- Push notifications and email backups for all time-sensitive communications

---

## Functional Requirements

### Active Loan Dashboard

**What**: A centralized view showing all currently active loans for both owners and borrowers

**Why**: Users need visibility into their active commitments - owners to track their property, borrowers to manage their responsibilities

**Behavior**:
- Tool owners see: tool name/photo, borrower name/rating, pickup date, expected return date, days remaining (color-coded: green >3 days, yellow 1-3 days, red overdue)
- Borrowers see: tool name/photo, owner name, return date, return location, special instructions
- Quick actions available: message other party, extend loan (if owner approves), report issue
- Filters for overdue items, items due soon (next 3 days), and all active loans

### Automated Reminder System

**What**: Time-based notifications to ensure borrowers return tools on schedule

**Why**: Prevents most late returns by giving borrowers advance notice and clear instructions

**Behavior**:
- 48-hour reminder: "Your [tool name] is due back to [owner] on [date] at [location]. Any questions? Message them now."
- 24-hour reminder: "Don't forget: [tool name] is due back tomorrow by [time]. Return location: [address]."
- Day-of reminder: "Today is return day for [tool name]. Due by [time] at [location]."
- All reminders include owner's preferred contact method and any special return instructions
- Users can opt out of reminders but receive warning that this may affect their borrower rating

### Condition Documentation System

**What**: Photo-based verification of tool condition at pickup and return

**Why**: Prevents disputes about damage by establishing clear before/after documentation

**Behavior**:
- At pickup: Borrower takes 2-3 photos (overall tool, any existing damage, serial number/distinctive features)
- At return: Borrower takes matching photos from same angles
- App displays pickup vs return photos side-by-side for comparison
- Both parties mark condition as "Same as pickup", "Minor wear", or "Damaged" with required explanation for damage
- Condition assessment affects borrower's reputation score
- Photos stored permanently in loan history record

### Late Return Management

**What**: Escalating notifications and tools for handling overdue loans

**Why**: Protects tool owners' property while maintaining community relationships

**Behavior**:
- Day 1 overdue: Automatic notification to both parties "Tool was due yesterday. Please coordinate return ASAP."
- Day 3 overdue: Escalation email to borrower with CC to tool owner: "This tool is significantly overdue. Please return immediately or explain delay."
- Day 7 overdue: Platform flags account and suggests owner "mark as lost" which affects borrower's reputation and may restrict future borrowing
- Tool owners can mark tools as "extended with permission" to stop overdue notifications
- Chronically late borrowers (3+ late returns) receive warning and possible borrowing restrictions

### Return Confirmation Process

**What**: Two-step verification that ensures both parties agree the loan is complete

**Why**: Closes the loop definitively and prevents future disputes about whether return occurred

**Behavior**:
- Borrower initiates return: takes condition photos, confirms return location/time, marks "returned"
- Tool owner confirms: reviews condition photos, physically inspects tool, marks "return accepted"
- Only after both confirmations does loan status change to "completed"
- If owner disputes condition, loan remains "return disputed" until resolved via messaging or platform mediation
- Completed loans automatically generate prompts for both parties to rate each other

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:
- **Loan**: Status, pickup_date, expected_return_date, actual_return_date, owner_id, borrower_id, tool_id
- **LoanPhoto**: Photo_url, photo_type (pickup_condition, return_condition), timestamp, loan_id
- **LoanStatusHistory**: Previous_status, new_status, timestamp, changed_by_user_id, notes
- **Reminder**: Reminder_type, scheduled_time, sent_time, loan_id

**Key Relationships**:
- Loan belongs to one User (owner) and one User (borrower) and one Tool
- LoanPhoto belongs to one Loan, can have multiple per loan
- Reminders belong to one Loan, multiple reminders per loan lifecycle

[Note: This is preliminary - Tech Lead will ask questions to clarify]

---

## User Experience Flow

### Happy Path - On-Time Return

1. **Day 2 Before Due**: Borrower receives reminder notification with return details
2. **Day 1 Before Due**: Borrower receives final reminder, reviews return location and time
3. **Return Day**: Borrower arrives at return location, opens app, selects active loan
4. **Condition Photos**: Borrower takes 2-3 photos of tool condition, app shows side-by-side with pickup photos
5. **Return Submission**: Borrower confirms tool is returned, app notifies owner
6. **Owner Confirmation**: Owner inspects tool, reviews photos, marks "return accepted"
7. **Completion**: Both parties prompted to rate each other, loan marked completed

### Overdue Path

1. **Day After Due**: Both parties receive "overdue" notification
2. **Day 3 Overdue**: Escalation warning sent to borrower
3. **Owner Action**: Owner can either mark "extended with permission" or continue overdue process
4. **Resolution**: Either tool returned late (affects borrower rating) or marked lost (serious penalty)

---

## Edge Cases & Constraints

- **Lost/Stolen Tool**: Owner can mark tool as "lost" after 7+ days overdue, triggering borrower penalties and potential requirement for replacement cost
- **Damaged During Use**: Condition photos allow assessment of damage; minor wear expected but major damage may require repair/replacement discussion
- **Weather Delays**: Return process includes "report delay" option for borrowers to communicate issues (storms, illness, etc.)
- **Photo Quality Issues**: App requires minimum photo quality/lighting and allows retaking if images are too dark/blurry
- **Timezone Handling**: All dates/times stored in UTC, displayed in user's local timezone, reminders sent based on return location timezone

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- Insurance or damage liability coverage (handled outside platform)
- Monetary deposit processing (payments not in V1)
- Automatic tool replacement ordering or repair service recommendations
- GPS tracking of tool location during loan period
- Integration with tool manufacturer warranties or support
- Bulk actions for tool owners with many simultaneous loans

---

## Open Questions for Tech Lead

- How should we handle timezone differences when tools are borrowed/returned across timezone boundaries?
- What's the optimal photo storage strategy for condition documentation (compression levels, retention period)?
- Should overdue notifications have rate limiting to prevent spam if user repeatedly marks extensions?

---

## Dependencies

**Depends On**: 
- User authentication system (to identify owners/borrowers)
- Tool Inventory Management (loan status updates tool availability)
- Borrowing Request System (creates the loans that need tracking)
- Push notification infrastructure
- Photo upload and storage system

**Enables**: 
- User reputation/rating system (uses loan completion data)
- Community analytics and reporting
- Tool owner confidence in platform (reliable returns)