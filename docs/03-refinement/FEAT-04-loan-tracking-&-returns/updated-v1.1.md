# Loan Tracking & Returns - Feature Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification  
- v1.1 - Iteration 1 clarifications (added: loan lifecycle definition, photo requirements, confirmation workflow, notification delivery, status states, lost tool process, photo retention, extension workflow)

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

## Acceptance Criteria (UPDATED v1.1)

- Dashboard shows all active loans with days remaining, borrower info, and expected return date
- Automated reminders sent to borrowers 2 days and 1 day before return date via email
- Exactly 3 condition photos required at both pickup and return, with side-by-side comparison
- Late return notifications sent to both parties, with escalation options for significantly overdue items
- Tool owner must confirm return within app, with 7-day auto-closure if no response
- Both parties must confirm tool return before loan status changes to "completed"
- Loan history preserved with all photos, dates, and condition notes for 1 year after completion
- Overdue tools are clearly flagged in owner's inventory dashboard
- Email notifications for all time-sensitive communications (no push notifications in v1)
- Tool owners can mark tools as "lost" after 7 days overdue, automatic "lost" marking after 30 days
- Borrowers can request loan extensions through formal approval workflow

---

## Detailed Specifications (UPDATED v1.1)

**Loan Lifecycle Definition**

**Decision**: Loans are created when borrower confirms physical pickup with condition photos

**Rationale**: Clean separation between approved borrowing requests and actual active loans. Ensures condition photos are always available for return comparison. Handles no-show situations cleanly without creating phantom loans.

**Examples**:
- Borrowing request gets approved → status remains "approved request" 
- Borrower picks up tool, takes 3 photos → loan record created with status "Active"
- If borrower never picks up → request expires after 48 hours, no loan created

**Edge Cases**:
- Pickup photos are mandatory - cannot create loan without them
- If borrower attempts pickup but photos fail to upload, retry mechanism provided
- Loan creation timestamp used for all subsequent due date calculations

---

**Photo Documentation Requirements**

**Decision**: Exactly 3 photos required at pickup and return, flexible content but minimum quality enforced

**Rationale**: Ensures adequate documentation without overcomplicating workflow. Three photos provide sufficient coverage (overall view, detail shots, identifying features) while being manageable for users. Flexible content prevents rigid categorization that might not fit all tools.

**Examples**:
- Good pickup photos: overall tool view, close-up of any existing wear, serial number/brand label
- Good return photos: same angles as pickup photos for comparison
- App suggests photo types but doesn't enforce specific categories

**Edge Cases**:
- Photos must meet minimum quality standards (lighting, focus) or retaking is required
- If return photos are significantly different angles than pickup, warning shown but not blocked
- Photo upload failures trigger retry mechanism with offline capability

---

**Return Confirmation Process**

**Decision**: Owner must actively confirm return via app, with 7-day auto-closure if no response

**Rationale**: Encourages owner engagement while preventing indefinite pending states. Seven days is reasonable for owners to inspect tools and respond, but not so long that borrowers feel uncertain about loan closure.

**Examples**:
- Borrower marks returned → owner gets notification "Please confirm return of [tool]"
- Owner has 7 days to either "accept return" or "dispute condition"
- Day 7: if no owner response → loan auto-closes as "completed"
- If owner disputes → loan stays in "return disputed" until resolved via messaging

**Edge Cases**:
- Owner dispute after auto-closure: can still file dispute, reopens loan for resolution
- Owner on vacation: can pre-approve returns or designate trusted neighbor for confirmation
- Borrower return photos obviously show damage: owner gets prominent warning to review carefully

---

**Notification Delivery System**

**Decision**: Email notifications only for v1, no push notifications

**Rationale**: Reliable delivery without complex push notification infrastructure. Email works for all users regardless of device/app installation. Can add push notifications in v2 once core workflows are proven.

**Examples**:
- 48-hour reminder: "Your circular saw is due back to John on March 15th at 123 Oak St"
- Day-of reminder: "TODAY: Return circular saw to John by 6 PM"
- Overdue notification: "Your borrowed circular saw was due yesterday. Please coordinate return with John immediately"

**Edge Cases**:
- Email delivery failures logged and retried up to 3 times
- Users can update email preferences but cannot disable critical notifications (overdue, disputes)
- Spam filter issues: include platform name and clear subject lines to improve delivery

---

**Loan Status State Machine**

**Decision**: Seven explicit states - Active, DueSoon, Overdue, ReturnPending, ReturnDisputed, Completed, Lost

**Rationale**: Covers all scenarios mentioned in requirements explicitly. Makes business logic clear in data model and enables precise querying for dashboards and notifications.

**Status Definitions**:
- **Active**: Normal loan period, return date >3 days away
- **DueSoon**: Return date within 3 days, triggers increased reminder frequency
- **Overdue**: Past return date, escalating notification sequence begins
- **ReturnPending**: Borrower marked returned, awaiting owner confirmation
- **ReturnDisputed**: Owner disputed condition, requires resolution via messaging
- **Completed**: Both parties confirmed, loan successfully closed
- **Lost**: Tool marked as lost by owner or automatically after 30 days overdue

**State Transitions**:
- Active → DueSoon (automated, 3 days before due)
- DueSoon → Overdue (automated, day after due date)
- Overdue → ReturnPending (borrower action)
- ReturnPending → Completed (owner confirmation or 7-day auto)
- ReturnPending → ReturnDisputed (owner disputes condition)
- Any → Lost (owner action after 7 days overdue, or automatic after 30 days)

---

**Lost Tool Process**

**Decision**: Owner can mark as lost after 7 days overdue, automatic marking after 30 days overdue

**Rationale**: Gives owners control over escalation while ensuring enforcement doesn't depend entirely on owner engagement. Seven days allows for communication and resolution attempts. Thirty-day automatic ensures platform maintains standards even with inactive owners.

**Examples**:
- Day 7 overdue: Owner dashboard shows "Mark as Lost" option
- Day 30 overdue: System automatically marks as lost, sends notification to both parties
- Lost status affects borrower's reputation score and may restrict future borrowing

**Edge Cases**:
- Owner marks lost then tool is returned: can reverse to "completed" with owner confirmation
- Borrower disputes "lost" marking: goes to platform mediation process
- Automatic lost marking happens even if owner is inactive on platform

---

**Photo Retention Policy**

**Decision**: Delete loan photos 1 year after loan completion

**Rationale**: Balances dispute resolution needs with storage costs and privacy concerns. One year is sufficient time for any disputes to surface and be resolved. Automatic cleanup prevents indefinite storage growth.

**Implementation**:
- Completion date + 365 days = deletion date
- Background job runs weekly to clean up expired photos
- Loan metadata (dates, status, notes) preserved indefinitely
- Users notified 30 days before photo deletion if loan had dispute history

**Edge Cases**:
- Active disputes prevent photo deletion until resolution
- User account deletion triggers immediate photo cleanup for privacy
- Platform backup retention follows same 1-year policy

---

**Loan Extension Workflow**

**Decision**: Borrower requests extension, owner approves/denies via notification, clear approval trail maintained

**Rationale**: Matches user expectation from requirements ("extend loan if owner approves"). Creates formal process that both parties understand. Maintains clear record of all date changes for accountability.

**Examples**:
- Borrower clicks "Request Extension" → selects new return date → adds reason
- Owner gets notification: "Sarah wants to keep your drill saw until March 20th (3 extra days). Reason: Project taking longer than expected"
- Owner approves → return date updated, overdue notifications cancelled, both parties notified
- Owner denies → original date remains, borrower must return on time

**Edge Cases**:
- Extension request while already overdue: allowed but clearly marked as "late extension"
- Multiple extension requests: each tracked separately, owner can see pattern
- Extension request after borrower already marked returned: not allowed, must go through return process

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
- At pickup: Borrower takes exactly 3 photos (app suggests: overall tool, any existing damage, serial number/distinctive features)
- At return: Borrower takes matching photos from same angles
- App displays pickup vs return photos side-by-side for comparison
- Both parties mark condition as "Same as pickup", "Minor wear", or "Damaged" with required explanation for damage
- Condition assessment affects borrower's reputation score
- Photos stored for 1 year after loan completion

### Late Return Management

**What**: Escalating notifications and tools for handling overdue loans

**Why**: Protects tool owners' property while maintaining community relationships

**Behavior**:
- Day 1 overdue: Automatic notification to both parties "Tool was due yesterday. Please coordinate return ASAP."
- Day 3 overdue: Escalation email to borrower with CC to tool owner: "This tool is significantly overdue. Please return immediately or explain delay."
- Day 7 overdue: Platform enables owner to "mark as lost" which affects borrower's reputation and may restrict future borrowing
- Day 30 overdue: Platform automatically marks as lost
- Tool owners can approve extension requests to stop overdue notifications
- Chronically late borrowers (3+ late returns) receive warning and possible borrowing restrictions

### Return Confirmation Process

**What**: Two-step verification that ensures both parties agree the loan is complete

**Why**: Closes the loop definitively and prevents future disputes about whether return occurred

**Behavior**:
- Borrower initiates return: takes 3 condition photos, confirms return location/time, marks "returned"
- Tool owner has 7 days to: review condition photos, physically inspect tool, mark "return accepted" or "dispute condition"
- If owner confirms: loan status changes to "completed", both parties prompted to rate each other
- If owner disputes: loan remains "return disputed" until resolved via messaging or platform mediation
- If owner doesn't respond within 7 days: loan auto-closes as "completed"

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:
- **Loan**: Status (Active/DueSoon/Overdue/ReturnPending/ReturnDisputed/Completed/Lost), pickup_date, expected_return_date, actual_return_date, owner_id, borrower_id, tool_id
- **LoanPhoto**: Photo_url, photo_type (pickup_condition, return_condition), timestamp, loan_id, photo_order (1,2,3)
- **LoanStatusHistory**: Previous_status, new_status, timestamp, changed_by_user_id, notes
- **LoanExtension**: Requested_date, approved_date, old_return_date, new_return_date, reason, status (pending/approved/denied)
- **Reminder**: Reminder_type (48hr/24hr/day_of/overdue), scheduled_time, sent_time, loan_id

**Key Relationships**:
- Loan belongs to one User (owner) and one User (borrower) and one Tool
- LoanPhoto belongs to one Loan, exactly 3 photos per pickup/return session
- LoanExtension belongs to one Loan, multiple extensions possible per loan
- Reminders belong to one Loan, multiple reminders per loan lifecycle

---

## User Experience Flow

### Happy Path - On-Time Return

1. **Day 2 Before Due**: Borrower receives email reminder with return details
2. **Day 1 Before Due**: Borrower receives final email reminder, reviews return location and time
3. **Return Day**: Borrower arrives at return location, opens app, selects active loan
4. **Condition Photos**: Borrower takes exactly 3 photos of tool condition, app shows side-by-side with pickup photos
5. **Return Submission**: Borrower confirms tool is returned, app emails notification to owner
6. **Owner Confirmation**: Owner has 7 days to inspect tool, review photos, mark "return accepted"
7. **Completion**: Loan auto-closes to "completed" (or earlier if owner confirms), both parties emailed to rate each other

### Extension Request Flow

1. **Borrower Request**: Borrower clicks "Request Extension", selects new date (up to 7 days later), adds reason
2. **Owner Notification**: Owner receives email "Extension request for [tool]" with details and approve/deny buttons
3. **Owner Response**: Owner approves or denies with optional message to borrower
4. **Update**: If approved, return date updated and both parties notified; if denied, original date remains

### Overdue Path

1. **Day After Due**: Both parties receive "overdue" email notification
2. **Day 3 Overdue**: Escalation warning emailed to borrower with CC to owner
3. **Day 7 Overdue**: Owner dashboard shows "Mark as Lost" option
4. **Day 30 Overdue**: System automatically marks as lost, both parties notified
5. **Resolution**: Either tool returned late (affects borrower rating) or remains lost (serious penalty)

---

## Edge Cases & Constraints

- **Lost/Stolen Tool**: Owner can mark tool as "lost" after 7+ days overdue, automatically marked after 30 days, triggering borrower penalties and potential requirement for replacement cost
- **Damaged During Use**: Condition photos allow assessment of damage; minor wear expected but major damage may require repair/replacement discussion
- **Weather Delays**: Return process includes "request extension" option for borrowers to communicate delays with owner approval required
- **Photo Quality Issues**: App requires minimum photo quality/lighting and allows retaking if images are too dark/blurry
- **Timezone Handling**: All dates/times stored in UTC, displayed in user's local timezone, email reminders sent based on return location timezone
- **Email Delivery**: Failed emails retried up to 3 times, delivery issues logged for platform monitoring

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- Insurance or damage liability coverage (handled outside platform)
- Monetary deposit processing (payments not in V1)
- Push notification delivery (email only in V1)
- Automatic tool replacement ordering or repair service recommendations
- GPS tracking of tool location during loan period
- Integration with tool manufacturer warranties or support
- Bulk actions for tool owners with many simultaneous loans

---

## Q&A History

### Iteration 1 - February 15, 2025

**Q1: What defines a "loan" and when is it created?**  
**A**: Loans are created when borrower confirms physical pickup with condition photos. This provides clean separation between approved requests and actual active loans, ensuring condition photos are always available for return comparison.

**Q2: How are condition photos structured and what's required?**  
**A**: Exactly 3 photos required at both pickup and return, with flexible content but minimum quality enforced. App suggests photo types (overall view, details, identifying features) but doesn't enforce rigid categories.

**Q3: What constitutes "owner confirmation" for returns?**  
**A**: Owner must actively confirm return via app within 7 days, or loan auto-closes as completed. This encourages owner engagement while preventing indefinite pending states.

**Q4: How do reminder notifications work technically?**  
**A**: Email notifications only for v1. Reminders sent at 48 hours, 24 hours, and day-of return date. Failed emails retried up to 3 times with delivery monitoring.

**Q5: What are the exact loan status values and transitions?**  
**A**: Seven states - Active, DueSoon, Overdue, ReturnPending, ReturnDisputed, Completed, Lost. States transition automatically based on dates and user actions, with clear business logic encoded in the state machine.

**Q6: Who can mark a tool as "lost" and what happens?**  
**A**: Owner can mark as lost after 7 days overdue. System automatically marks as lost after 30 days. Both trigger borrower reputation penalties and potential borrowing restrictions.

**Q7: How long should loan photos be retained?**  
**A**: Photos deleted 1 year after loan completion. Balances dispute resolution needs with storage costs and privacy. Loan metadata preserved indefinitely.

**Q8: Can loan return dates be extended, and how?**  
**A**: Borrower requests extension with reason, owner approves/denies via email notification. Clear approval trail maintained, multiple extensions allowed but tracked for pattern analysis.

---

## Product Rationale

**Why loan creation at pickup?**  
Clean data model that only tracks actual loans, not requests. Ensures condition documentation is always available. Handles no-shows cleanly without phantom records.

**Why exactly 3 photos?**  
Ensures adequate documentation without workflow complexity. Three photos provide sufficient coverage while being manageable for users. Flexible content prevents rigid categorization.

**Why 7-day owner confirmation window?**  
Reasonable time for owners to inspect and respond, but not so long that borrowers feel uncertain. Auto-closure prevents indefinite pending states that harm user experience.

**Why email-only notifications for v1?**  
Reliable delivery without complex infrastructure investment. Email works universally and can be enhanced with push notifications in v2 once core workflows are proven.

**Why detailed status states vs simple flags?**  
Makes business logic explicit in the data model. Enables precise querying for dashboards and automated workflows. Matches the complexity described in requirements.

**Why both 7-day owner and 30-day automatic lost marking?**  
Gives owners control over their property while ensuring platform standards are maintained even with inactive owners. Balances owner autonomy with community protection.

---

## Dependencies

**Depends On**: 
- User authentication system (to identify owners/borrowers)
- Tool Inventory Management (loan status updates tool availability)
- Borrowing Request System (creates the approved requests that become loans)
- Email delivery infrastructure (SendGrid, AWS SES, or similar)
- Photo upload and storage system (AWS S3, Azure Blob, or similar)
- Background job processing (for automated status transitions and reminders)

**Enables**: 
- User reputation/rating system (uses loan completion and condition data)
- Community analytics and reporting (loan patterns, return rates, etc.)
- Tool owner confidence in platform (reliable returns increase lending willingness)