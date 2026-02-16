# Borrow Tracking & Returns - Feature Requirements (v1.2)

**Version History**:
- v1.0 - Initial specification (2025-01-10)
- v1.1 - Iteration 1 clarifications (2025-01-12) - Added due time specificity, timezone handling, tool unavailability during borrows, return confirmation workflow details, extension limits, overdue threshold definitions, transaction history inclusion rules, and dashboard active borrow filtering
- v1.2 - Iteration 2 clarifications (2025-01-14) - Added damage dispute handling, photo upload requirements, extension request timeout rules, auto-confirmation behavior, late return consequences, data retention policy, notification delivery redundancy, and reminder timing specifications

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
- As a borrower, I want to add my perspective if an owner reports damage I disagree with so that my side of the story is documented
- As a tool owner, I want to see who currently has each of my tools and when they're due back so that I can manage my inventory
- As a tool owner, I want to confirm returns and inspect condition so that any damage is documented at the right time
- As a tool owner, I want to report issues with returned tools so that problems are recorded in the transaction history
- As any user, I want to see my complete borrowing history so that I can reference past transactions
- As any user, I want the system to automatically flag overdue items so that late returns are visible and actionable
- As any user, I want to receive notifications through multiple channels so that I don't miss critical reminders due to email delivery issues

---

## Acceptance Criteria

- Dashboard displays all active borrows with tool name, other party's name, start date, due date, and days remaining
- Borrowers receive automated notifications (email + in-app) at 9:00 AM owner-timezone 1 day before due date and on the due date
- Borrowers can mark a tool as "Returned" which triggers an immediate notification to the owner
- Owners confirm returns by selecting "Good condition" or "Has issues"
- "Has issues" reports require issue description (max 1000 characters), allow up to 5 photos documenting damage, and checkbox indicating if usability is affected
- Photos only uploadable when reporting issues, not for "Good condition" confirmations
- Borrowers can add rebuttal notes (max 500 characters) to damage reports they disagree with
- Overdue items are visually flagged: yellow indicator at 1-2 days overdue, red indicator at 3+ days overdue
- Borrowers can request extensions with requested new due date and reason (max 500 characters)
- Extension requests expire after 72 hours with no owner response, automatically marked as "Timed Out"
- If owner doesn't confirm return within 7 days of borrower marking it returned, system auto-confirms as "Good condition" with visible "(Auto-confirmed)" label in history
- Transaction history shows all past borrows (completed and cancelled) with: tool name, other party, dates, final status, ratings, and any reported issues
- Late returns affect user reputation but do not trigger automatic restrictions or suspensions in v1
- History is filterable by date range and searchable by tool name or username
- All transaction state changes (approved → active → returned → confirmed) are timestamped and logged
- All reminders and critical notifications sent via both email and in-app notification center for redundancy
- Transaction history retained permanently (no automatic deletion)

---

## Functional Requirements

### Active Borrow Dashboard

**What**: A centralized view showing all currently active borrows for the logged-in user, displayed differently based on whether they are the borrower or owner.

**Why**: Users need a single source of truth for what tools they currently have borrowed or have lent out. Without this, users must dig through notifications or remember details, leading to confusion and late returns.

**Behavior**:
- Dashboard has two tabs: "I'm Borrowing" and "I'm Lending"
- Each tab shows a list of active borrows sorted by due date (soonest first)
- Each list item displays:
  - Tool name (linked to tool detail page)
  - Other party's name (linked to their profile) and neighborhood
  - Start date (when pickup occurred)
  - Due date (prominently displayed, including time: "Due Jan 15 at 6:00 PM")
  - Days remaining calculation (e.g., "Due in 3 days", "Due today", "1 day overdue")
  - Tool photo thumbnail
  - Status indicator (see Overdue Flagging section)
- "I'm Borrowing" tab includes "Mark as Returned" button for each item
- "I'm Lending" tab includes "View Details" button that shows borrower info and messaging option
- Empty state messaging: "You're not currently borrowing any tools" with link to browse available tools
- Count badges on tabs showing number of active items (e.g., "I'm Borrowing (3)")
- **Active definition**: Borrows with Status = Active OR PendingReturnConfirmation (not yet Completed or Cancelled)
- Notification bell icon in header shows unread notification count, links to notification center

---

### Return Initiation (Borrower Side)

**What**: The borrower marks a tool as returned after physically returning it to the owner.

**Why**: Provides a clear signal to the owner that the tool has been returned and shifts responsibility to the owner to confirm and close the transaction.

**Behavior**:
- "Mark as Returned" button available on each active borrow in dashboard
- Clicking shows confirmation modal: "Confirm you've returned [Tool Name] to [Owner Name]? They will be notified to confirm the return."
- Upon confirmation:
  - Borrow status changes to "Pending Return Confirmation"
  - Owner receives immediate notification via **both email and in-app notification**
  - Email subject: "[Borrower] has returned your [Tool Name]"
  - Email body: Includes borrower's name, tool name, link to confirm return
  - In-app notification: Shows in notification center with red badge count
  - Borrower's dashboard updates to show "Awaiting owner confirmation" status
  - Item remains in "I'm Borrowing" list until owner confirms
  - Tool status remains "Borrowed" (not available for new requests) until owner confirms
- Borrowers can add optional return notes (max 300 characters) visible to owner: "Left it on your porch" or "Cleaned and ready to go"
- Return can be marked even if borrow is overdue (no blocking)

---

### Return Confirmation (Owner Side)

**What**: The owner inspects the returned tool and confirms the return, documenting condition.

**Why**: Creates accountability and a clear end to the transaction. Allows owners to document damage immediately when discovered, rather than only finding out later when they try to lend it again.

**Behavior**:
- When a borrow is marked as returned, owner sees notification and the item appears in "Pending Confirmation" section of "I'm Lending" tab
- Owner clicks "Confirm Return" button
- Confirmation modal presents two options:
  1. **"Good condition"**: Tool returned as expected
     - Optional: Add positive note (max 300 characters)
     - **No photo upload available** for good condition
     - Clicking confirms and closes the transaction
  2. **"Has issues"**: Tool has damage, missing parts, or other problems
     - **Required**: Description of issue (max 1000 characters)
     - **Optional**: Upload photos showing damage (up to 5 photos, max 10MB each, JPEG/PNG only)
     - **Photos only appear when "Has issues" is selected** - UI dynamically shows/hides upload area
     - Checkbox: "Issue affects tool's usability" (marks tool as needing repair)
     - Clicking confirms and closes transaction with issue flagged
- Upon confirmation (either condition):
  - Borrow status changes to "Completed"
  - Both parties receive notification (email + in-app) that transaction is closed
  - Both parties prompted to rate each other (separate flow, not blocking)
  - Tool returns to "Available" status (unless marked as needing repair)
  - Transaction moves to history for both users
  - `ReturnConfirmation` record created with `ConfirmedBy = OwnerId`
- If tool marked "Has issues", owner's tool listing includes flag: "Recently reported issue - being repaired" until owner manually clears it
- **7-day auto-confirmation rule**: If owner doesn't confirm within 7 days (168 hours) of borrower marking returned:
  - System automatically creates `ReturnConfirmation` with:
    - Condition = "Good"
    - OwnerNotes = null
    - `ConfirmedBy = System` (special system user ID)
    - `AutoConfirmed = true` (boolean flag)
  - Borrow status changes to "Completed"
  - Both parties notified: "Return auto-confirmed after 7 days with no response"
  - Tool returns to "Available" status
  - Transaction history shows: "Returned - Good condition (Auto-confirmed)"
  - **Trust score calculation treats auto-confirmed same as owner-confirmed** - borrower not penalized
  - Background job runs daily at 2:00 AM UTC, finds borrows where `Status = PendingReturnConfirmation AND ReturnMarkedDate < UtcNow - 7 days`

---

### Damage Dispute & Rebuttal

**What**: When an owner reports issues with a returned tool, the borrower can add their perspective if they disagree with the damage assessment.

**Why**: Preserves both sides of the story in disputes about tool condition. Provides fairness and transparency without requiring complex admin mediation. Allows future trust systems to consider disputed vs. undisputed damage reports differently.

**Behavior**:
- When owner confirms return with "Has issues", borrower receives notification (email + in-app):
  - Subject: "[Owner] reported an issue with returned [Tool Name]"
  - Body: Shows owner's issue description and photos
  - Call-to-action: "Add your perspective" link
- Borrower can click through to see full damage report
- Below owner's report, borrower sees: "Disagree with this assessment? Add your perspective."
- Clicking opens rebuttal form:
  - Text area: "Your response" (max 500 characters)
  - Examples shown: "The blade was already dull when I picked it up" or "The crack was present before I borrowed it"
  - Submit button: "Add Response"
- Upon submission:
  - `ReturnConfirmation.BorrowerRebuttal` field populated
  - `ReturnConfirmation.RebuttalAddedAt` timestamp set
  - Owner notified (email + in-app): "[Borrower] has responded to the damage report"
  - Both parties can view both perspectives in transaction history
- **Rebuttal rules**:
  - Only available if owner reported issues (not available for "Good condition")
  - Can only be added once (no editing after submission)
  - Must be added within 30 days of return confirmation
  - Optional - borrower can choose not to respond
- **Display in transaction history**:
  - Shows owner's damage report prominently
  - Below it, shows borrower's rebuttal in distinct styling (e.g., lighter background)
  - Label: "Borrower's Response (Added [Date])"
  - Both visible to future potential borrowers viewing owner's tool history (trust transparency)
- **Trust score implications**:
  - v1: Late returns documented in history but no automatic restrictions
  - v2 enhancement: Disputed damage (has rebuttal) may be weighted differently than undisputed damage in reputation calculations
  - Pattern detection: Multiple disputed damage claims from same owner might flag owner as overly critical

---

### Overdue Flagging

**What**: Automatic visual indicators when a borrow passes its due date, escalating in urgency.

**Why**: Makes late returns immediately visible to both parties and the broader community, creating social accountability. Helps owners know when to follow up and helps borrowers avoid accidentally damaging their reputation.

**Behavior**:
- **Due time**: All borrows due at 6:00 PM (18:00) in owner's local timezone on the due date
- **On due date (day 0 overdue)**:
  - Before 6:00 PM: Item shows yellow "Due Today" badge
  - After 6:00 PM: Item shows yellow "1 Day Overdue" badge (grace period ends)
  - Both parties receive notification at 9:00 AM owner-timezone
- **1-2 days overdue**:
  - Item shows yellow "X Day(s) Overdue" badge (1 or 2)
  - Visual styling: yellow-orange background on dashboard item
  - Borrower receives additional reminder notification at 9:00 AM each day
- **3+ days overdue**:
  - Item shows red "X Days Overdue" badge
  - Visual styling: red background on dashboard item
  - In-app messaging becomes more prominent: "Please return [Tool] to [Owner] immediately"
  - Daily reminder notifications continue
- **7+ days overdue**:
  - System flags transaction for potential review (logged, not acted upon in v1)
  - Both parties receive escalation notification: "This borrow is significantly overdue. Please communicate to resolve."
  - (Note: No automatic penalties in v1 - trust system future enhancement)
- **Overdue calculation**:
  - Based on calendar days, not business days
  - Uses owner's timezone for consistency
  - Due time is 6:00 PM (18:00) local time
  - Overdue threshold = `UtcNow > CurrentDueDate.ToOwnerTimezone().AddHours(18)`
  - Days overdue = `(UtcNow.Date - DueDate.Date).Days`
- Overdue status persists even after tool is marked returned until owner confirms
- Overdue days calculated based on `CurrentDueDate` (reflects extensions)
- Extension approval resets overdue flags and recalculates based on new due date
- **Late return consequences (v1)**:
  - No automatic restrictions or suspensions
  - No monetary penalties or fines
  - Late returns visible in transaction history
  - Overdue days documented: "Returned 3 days late"
  - Data collected for future reputation system
  - Owners can see pattern of late returns when reviewing borrow requests

---

### Extension Requests

**What**: Borrowers can request to extend the due date if they need the tool longer than originally planned.

**Why**: Projects run long, circumstances change. Providing a formal extension mechanism encourages communication and prevents borrowers from just keeping tools without asking (which damages trust).

**Behavior**:
- "Request Extension" button available on active borrows until due date passes
- **Not available if 3+ days overdue** - message: "This tool is significantly overdue. Please return it or contact the owner directly to discuss."
- **Available if 1-2 days overdue** - allows late borrowers to formalize new arrangement
- Extension request form includes:
  - Current due date (display only, shows original or currently extended date)
  - Requested new due date (date picker, must be after current due date, max 14 days from request date)
  - Reason for extension (required, max 500 characters)
- Upon submission:
  - Request sent to owner immediately via **email and in-app notification**
  - Email subject: "[Borrower] requests extension for [Tool Name]"
  - Email body: Shows current due date, requested new date, borrower's reason, approve/deny links
  - Borrower sees "Extension Requested" status on dashboard item
  - Original due date remains active until/unless owner approves
  - Request status = "Pending"
- **72-hour timeout rule**:
  - Extension requests expire 72 hours (3 days) after submission if owner doesn't respond
  - Background job runs daily at 2:00 AM UTC, finds requests where `RequestedDate + 72h < UtcNow AND Status = Pending`
  - Expired requests marked as Status = "TimedOut"
  - Borrower notified: "Your extension request expired - owner didn't respond within 72 hours. Please return the tool on the original due date or contact the owner directly."
  - UI shows countdown timer: "Extension request expires in 2 days, 5 hours"
- Owner receives notification with borrower's reason and requested new date
- Owner can:
  - **Approve**: 
    - `CurrentDueDate` updates to new date
    - Both parties notified
    - Overdue flags cleared if applicable
    - Reminder schedule resets based on new due date
    - Request status = "Approved"
  - **Deny**: 
    - Due date remains unchanged
    - Borrower notified with owner's message (required, max 500 characters)
    - Request status = "Denied"
  - **Counter-offer**: 
    - Owner enters different date and reason
    - Borrower receives counter-offer notification
    - Borrower can accept (updates due date) or decline (due date unchanged)
    - Creates new ExtensionRequest with Type = "CounterOffer"
- Only one pending extension request allowed at a time
- Must wait for response (approved/denied/timed out) before requesting again
- **Extension limits**:
  - No limit on total number of requests over borrow lifecycle
  - Each individual extension max 14 days from request date
  - Cumulative borrow duration max 28 days total (original + all extensions)
  - System blocks extension if new date would exceed 28-day total: "Maximum borrow duration is 28 days. This extension would exceed that limit."
- Extension history tracked in transaction details (visible to both parties)
- Extension requests count toward trust signals (frequent extenders noted in reputation)

---

### Automated Reminders & Notifications

**What**: System-generated notifications sent at specific times before and during a borrow period, delivered through multiple channels for reliability.

**Why**: Reduces accidental late returns by proactively reminding borrowers. Keeps transactions on track without requiring constant manual checking. Redundant delivery ensures users receive critical information even if email fails.

**Behavior**:
- **Dual-channel delivery**: All reminders sent via **both email and in-app notification**
  - Email: Standard HTML email with tool photo, details, and action links
  - In-app: Notification appears in notification center, increments unread badge count
  - Frontend polls notification API every 60 seconds or uses WebSocket for real-time updates
  - Users can mark in-app notifications as read individually or bulk "Mark all as read"
- **Notification center UI**:
  - Bell icon in header shows unread count badge
  - Clicking opens dropdown with recent notifications (last 10)
  - Link to full notification center page showing all notifications
  - Notifications grouped by type and sorted by date
  - Filterable: "Unread", "All", "Reminders", "Returns", "Extensions"
- **Reminder timing**: All reminders sent at **9:00 AM in owner's local timezone**
  - Background job runs hourly (every hour on the hour)
  - Each run queries borrows due tomorrow/today in timezones where it's currently 9:00 AM
  - Marks reminder sent in `BorrowReminder` tracking table to prevent duplicates
- **Reminder Schedule**:
  - **1 day before due date** (9:00 AM day before):
    - Subject: "Reminder: [Tool Name] due back tomorrow"
    - Content: Tool photo, owner name, due date/time, return instructions
    - Actions: "Mark as Returned" button, "Request Extension" link
  - **On due date** (9:00 AM same day):
    - Subject: "Reminder: [Tool Name] due back today at 6:00 PM"
    - Content: Emphasizes due time, return process
    - Actions: "Mark as Returned" button, "Contact Owner" link
  - **1 day overdue** (9:00 AM next day):
    - Subject: "Please return [Tool Name] to [Owner]"
    - Content: Notes item is now late, encourages immediate return or communication
    - Actions: "Mark as Returned" button, "Request Extension" link (if eligible)
  - **3 days overdue** (9:00 AM):
    - Subject: "Urgent: [Tool Name] is now 3 days overdue"
    - Content: More urgent tone, suggests contacting owner if unable to return
    - Actions: "Mark as Returned" button, "Message Owner" link
  - **Daily reminders continue** every morning at 9:00 AM while overdue
- **Suppression Rules**:
  - No reminders sent after borrower marks tool as returned (status = PendingReturnConfirmation)
  - No reminders sent if extension approved and new due date is in future
  - Reminders pause if extension request is pending (resume if denied or timed out)
  - Reminders stop when borrow status = Completed
- **Owner Notifications** (parallel to borrower reminders):
  - Owner notified at 9:00 AM when their tool becomes overdue: "Your [Tool Name] lent to [Borrower] is now overdue"
  - Includes borrower's contact info and "Send Message" link
  - Owner notified daily while tool remains overdue
- **Email delivery failure handling**:
  - If email bounces (SMTP error), log to `EmailDeliveryLog` table with failure reason
  - No automatic retry for bounced emails (user still has in-app notification)
  - Dashboard for admins shows users with persistent email delivery issues
  - Users can update email address if delivery failing
- **Database tables**:
  - `BorrowReminder`: Tracks which reminders sent (BorrowId, ReminderType, SentAt, DeliveredVia)
  - `Notification`: In-app notifications (UserId, Type, Content, Read, CreatedAt)
  - `EmailDeliveryLog`: Email send attempts (NotificationId, Status, BouncedAt, ErrorMessage)

---

### Transaction History

**What**: A permanent, searchable record of all past borrow transactions for a user, viewable by that user only (not public).

**Why**: Users need to reference past borrows for disputes, tax records (if applicable later), or simply to remember what they've borrowed/lent. History contributes to trust signals on user profiles.

**Behavior**:
- Accessible via "History" tab on user's dashboard
- Shows **completed AND cancelled** transactions sorted by completion date (most recent first)
- Each history entry displays:
  - Tool name (linked to current tool listing if still exists)
  - Other party's name (linked to profile) and neighborhood
  - Role in transaction: "You borrowed" or "You lent"
  - Start date and end date (when return was confirmed, or when cancelled)
  - Duration in days (for completed borrows)
  - Final status: 
    - "Returned - Good condition"
    - "Returned - Good condition (Auto-confirmed)" if owner didn't confirm within 7 days
    - "Returned - Issues reported" (with borrower rebuttal indicator if present)
    - "Cancelled before pickup"
  - Lateness indicator if returned late: "Returned 3 days late" in orange text
  - Ratings exchanged (if completed): Stars shown for both parties
  - "View Details" link to see full transaction record
- **Detail view** includes:
  - **Timeline**:
    - All dates: requested, approved, started, due (original), due (if extended), returned, confirmed
    - Extension history if applicable (requests, approvals, denials, counter-offers)
    - Overdue period if late: "Overdue from Jan 10 to Jan 13 (3 days)"
  - **Return documentation**:
    - Return notes from borrower (if provided)
    - Return confirmation from owner (condition, photos, descriptions)
    - **Issue report with borrower rebuttal** (if applicable):
      - Owner's damage description and photos shown first
      - Below: "Borrower's Response" section with rebuttal text
      - Timestamp showing when rebuttal was added
      - Both perspectives preserved permanently
  - **Communication**:
    - All messages exchanged through in-app messaging system (read-only archive)
    - Extension request conversations
  - **Ratings**:
    - Ratings and reviews from both parties
    - Date ratings were submitted
- **Search & Filter**:
  - Search by tool name or other party's username (case-insensitive, partial match)
  - Filter by date range (last 30 days, last 6 months, last year, all time, custom range)
  - Filter by role (borrowed vs. lent)
  - Filter by outcome (good condition vs. issues reported vs. cancelled)
  - Filter by rating given/received (5 stars, 4+ stars, 3 or fewer)
  - Filter by late returns: "Show only late returns"
- **Data retention**: 
  - Transaction history **retained permanently** - no automatic deletion
  - Includes both completed and cancelled transactions
  - Soft-delete not implemented in v1 - can add in v2 if legal/compliance requires
  - Users cannot delete their own history (data integrity for disputes)
- Users can add **private notes** to history entries:
  - Max 500 characters
  - Not visible to other party
  - Use cases: Personal reminders, context about transaction, notes for future
  - Example: "Borrowed this for kitchen remodel - worked great"
- **Performance considerations**:
  - Index on `(UserId, Status, ReturnConfirmedDate DESC)` for fast history queries
  - Pagination: 20 transactions per page
  - Consider partitioning by year if table grows very large (future optimization)

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:

- **Borrow**: Represents a single borrowing transaction
  - BorrowId (primary key)
  - BorrowRequestId (foreign key to request that was approved)
  - ToolId (foreign key)
  - BorrowerId (foreign key to User)
  - OwnerId (foreign key to User)
  - StartDate (when pickup occurred / request approved)
  - OriginalDueDate (DateTime with timezone)
  - CurrentDueDate (DateTime with timezone, may differ from original if extended)
  - Status (enum: Active, PendingReturnConfirmation, Completed, Cancelled)
  - ReturnMarkedDate (DateTime, when borrower clicked "Mark as Returned")
  - ReturnConfirmedDate (DateTime, when owner confirmed return or auto-confirmed)
  - ReturnCondition (enum: GoodCondition, HasIssues, NotYetConfirmed)
  - OwnerTimezone (string, IANA timezone ID, e.g. "America/Los_Angeles")
  - CreatedAt, UpdatedAt timestamps

- **ExtensionRequest**: Tracks requests to extend due dates
  - ExtensionRequestId (primary key)
  - BorrowId (foreign key)
  - RequestedDate (DateTime UTC)
  - RequestedNewDueDate (DateTime)
  - Reason (text, max 500 chars)
  - Status (enum: Pending, Approved, Denied, TimedOut)
  - ExpiresAt (DateTime UTC, calculated as RequestedDate + 72 hours)
  - ResponseDate (DateTime UTC, nullable)
  - ResponseMessage (text, max 500 chars, from owner)
  - RespondedByUserId (foreign key to User - should be owner)
  - Type (enum: Initial, CounterOffer - for tracking counter-offers)

- **ReturnConfirmation**: Details about the return process
  - ReturnConfirmationId (primary key)
  - BorrowId (foreign key, one-to-one)
  - Condition (enum: Good, HasIssues)
  - OwnerNotes (text, max 1000 chars, nullable)
  - IssueDescription (text, max 1000 chars, nullable - required if Condition = HasIssues)
  - AffectsUsability (boolean, default false)
  - ConfirmedDate (DateTime UTC)
  - ConfirmedBy (foreign key to User - OwnerId or System for auto-confirm)
  - AutoConfirmed (boolean, default false - true if 7-day auto-confirm triggered)
  - Photos (JSON array of photo URLs, max 5, nullable)
  - BorrowerRebuttal (text, max 500 chars, nullable - added if borrower disputes damage)
  - RebuttalAddedAt (DateTime UTC, nullable)

- **BorrowNote**: Private notes users add to their history
  - BorrowNoteId (primary key)
  - BorrowId (foreign key)
  - UserId (foreign key - who created the note)
  - NoteText (text, max 500 chars)
  - CreatedAt (DateTime UTC)

- **BorrowReminder**: Track which reminders have been sent to avoid duplicates
  - BorrowReminderId (primary key)
  - BorrowId (foreign key)
  - ReminderType (enum: OneDayBefore, DueDate, OneDayOverdue, ThreeDaysOverdue, SevenDaysOverdue)
  - SentAt (DateTime UTC)
  - RecipientUserId (foreign key to User)
  - DeliveredVia (enum: Email, InApp, Both)

- **Notification**: In-app notification center messages
  - NotificationId (primary key)
  - UserId (foreign key - recipient)
  - Type (enum: Reminder_DueSoon, Reminder_DueToday, Reminder_Overdue, Return_Marked, Return_Confirmed, Extension_Requested, Extension_Approved, Extension_Denied, Damage_Reported, Rebuttal_Added)
  - Title (string, max 200 chars)
  - Content (text, max 1000 chars)
  - ActionUrl (string, nullable - link to relevant page)
  - Read (boolean, default false)
  - CreatedAt (DateTime UTC)
  - ReadAt (DateTime UTC, nullable)

- **EmailDeliveryLog**: Track email delivery success/failures
  - EmailDeliveryLogId (primary key)
  - NotificationId (foreign key, nullable - not all emails linked to notifications)
  - RecipientUserId (foreign key to User)
  - EmailAddress (string, email sent to)
  - Subject (string, max 200 chars)
  - Status (enum: Sent, Bounced, Failed)
  - SentAt (DateTime UTC)
  - BouncedAt (DateTime UTC, nullable)
  - ErrorMessage (text, nullable)

**Key Relationships**:
- Borrow has many ExtensionRequests (history of all extension attempts)
- Borrow has one ReturnConfirmation when completed
- Borrow has many BorrowNotes (from either party, private to each)
- Borrow has many BorrowReminders (tracks all reminders sent)
- Borrow references the original BorrowRequest (from Feature 2)
- Borrow references Tool and User entities (from Features 1 & 3)
- ReturnConfirmation optionally has BorrowerRebuttal (embedded field, not separate table)
- Notification has optional EmailDeliveryLog (if notification sent via email)

---

## User Experience Flow

**Happy Path: Complete Borrow Cycle**

1. **Borrow begins**: Owner approves a borrow request, system creates Borrow entity with Status=Active, StartDate=now, OriginalDueDate and CurrentDueDate from request, OwnerTimezone from owner's profile
2. **Borrower views active borrows**: Logs in, sees dashboard with tool listed under "I'm Borrowing", shows due date is 5 days away (displayed in owner's timezone)
3. **Reminder sent**: One day before due date at 9:00 AM owner-timezone, borrower receives email + in-app notification with tool details and quick action links, notification badge shows "1" unread
4. **Project takes longer**: Borrower realizes they need one more day, clicks "Request Extension