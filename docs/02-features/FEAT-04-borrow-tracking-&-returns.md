# Borrow Tracking & Returns - Feature Requirements

**Version**: 1.0  
**Date**: 2025-01-10  
**Status**: Initial - Awaiting Tech Lead Review

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

## Acceptance Criteria

- Dashboard displays all active borrows with tool name, other party's name, start date, due date, and days remaining
- Borrowers receive automated email reminders 1 day before due date and on the due date
- Borrowers can mark a tool as "Returned" which triggers an immediate notification to the owner
- Owners confirm returns by selecting "Good condition" or "Has issues" with optional photos (up to 5) and description (max 1000 characters)
- Overdue items are visually flagged: yellow indicator at 1 day overdue, red indicator at 3+ days overdue
- Borrowers can request extensions before or on the due date, requiring owner approval
- Extension requests include requested new due date and reason (max 500 characters)
- Transaction history shows all past borrows with: tool name, other party, dates, final status, ratings, and any reported issues
- History is filterable by date range and searchable by tool name or username
- All transaction state changes (approved → active → returned → confirmed) are timestamped and logged

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
  - Due date (prominently displayed)
  - Days remaining calculation (e.g., "Due in 3 days", "Due today", "1 day overdue")
  - Tool photo thumbnail
  - Status indicator (see Overdue Flagging section)
- "I'm Borrowing" tab includes "Mark as Returned" button for each item
- "I'm Lending" tab includes "View Details" button that shows borrower info and messaging option
- Empty state messaging: "You're not currently borrowing any tools" with link to browse available tools
- Count badges on tabs showing number of active items (e.g., "I'm Borrowing (3)")

---

### Return Initiation (Borrower Side)

**What**: The borrower marks a tool as returned after physically returning it to the owner.

**Why**: Provides a clear signal to the owner that the tool has been returned and shifts responsibility to the owner to confirm and close the transaction.

**Behavior**:
- "Mark as Returned" button available on each active borrow in dashboard
- Clicking shows confirmation modal: "Confirm you've returned [Tool Name] to [Owner Name]? They will be notified to confirm the return."
- Upon confirmation:
  - Borrow status changes to "Pending Return Confirmation"
  - Owner receives immediate notification (email + in-app): "[Borrower] has marked [Tool Name] as returned. Please confirm the return and check the tool's condition."
  - Borrower's dashboard updates to show "Awaiting owner confirmation" status
  - Item remains in "I'm Borrowing" list until owner confirms
- Borrowers can add optional return notes (max 300 characters) visible to owner: "Left it on your porch" or "Cleaned and ready to go"

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
     - Clicking confirms and closes the transaction
  2. **"Has issues"**: Tool has damage, missing parts, or other problems
     - Required: Description of issue (max 1000 characters)
     - Optional: Upload photos showing damage (up to 5 photos)
     - Checkbox: "Issue affects tool's usability" (marks tool as needing repair)
     - Clicking confirms and closes transaction with issue flagged
- Upon confirmation (either condition):
  - Borrow status changes to "Completed"
  - Both parties receive notification that transaction is closed
  - Both parties prompted to rate each other (separate flow, not blocking)
  - Tool returns to "Available" status (unless marked as needing repair)
  - Transaction moves to history for both users
- If tool marked "Has issues", owner's tool listing includes flag: "Recently reported issue - being repaired" until owner manually clears it

---

### Overdue Flagging

**What**: Automatic visual indicators when a borrow passes its due date, escalating in urgency.

**Why**: Makes late returns immediately visible to both parties and the broader community, creating social accountability. Helps owners know when to follow up and helps borrowers avoid accidentally damaging their reputation.

**Behavior**:
- **On due date (day 0 overdue)**:
  - Item shows yellow "Due Today" badge
  - Both parties receive notification
- **1-2 days overdue**:
  - Item shows yellow "1 Day Overdue" badge (or "2 Days Overdue")
  - Visual styling: yellow-orange background on dashboard item
  - Borrower receives additional reminder notification
- **3+ days overdue**:
  - Item shows red "X Days Overdue" badge
  - Visual styling: red background on dashboard item
  - In-app messaging becomes more prominent: "Please return [Tool] to [Owner] immediately"
- **7+ days overdue**:
  - System flags transaction for potential intervention
  - Both parties receive escalation notification: "This borrow is significantly overdue. Please communicate to resolve."
  - (Note: No automatic penalties in v1, but this data feeds reputation system)
- Overdue status persists even after tool is marked returned until owner confirms
- Overdue days calculated based on due date, not accounting for extension requests that weren't approved

---

### Extension Requests

**What**: Borrowers can request to extend the due date if they need the tool longer than originally planned.

**Why**: Projects run long, circumstances change. Providing a formal extension mechanism encourages communication and prevents borrowers from just keeping tools without asking (which damages trust).

**Behavior**:
- "Request Extension" button available on active borrows until due date passes
- Extension request form includes:
  - Current due date (display only)
  - Requested new due date (date picker, must be after current due date, max 14 days from request date)
  - Reason for extension (required, max 500 characters)
- Upon submission:
  - Request sent to owner immediately (email + in-app notification)
  - Borrower sees "Extension Requested" status on dashboard item
  - Original due date remains active until/unless owner approves
- Owner receives notification with borrower's reason and requested new date
- Owner can:
  - **Approve**: Due date updates to new date, both parties notified, overdue flags cleared if applicable
  - **Deny**: Due date remains unchanged, borrower notified with owner's message (required, max 500 characters)
  - **Counter-offer**: Propose different date (owner enters date and reason)
- Extension request times out after 24 hours with no response (treated as denied, borrower notified)
- Borrowers can request extension even if item is 1-2 days overdue (not available if 3+ days overdue)
- Only one pending extension request allowed at a time; must wait for response before requesting again
- Extension history tracked in transaction details (visible to both parties)

---

### Automated Reminders

**What**: System-generated email notifications sent at specific times before and during a borrow period.

**Why**: Reduces accidental late returns by proactively reminding borrowers. Keeps transactions on track without requiring constant manual checking.

**Behavior**:
- **Reminder Schedule**:
  - 1 day before due date: "Reminder: [Tool Name] due back tomorrow"
  - On due date: "Reminder: [Tool Name] due back today"
  - 1 day overdue: "Please return [Tool Name] to [Owner]"
  - 3 days overdue: "Urgent: [Tool Name] is now 3 days overdue"
- **Reminder Content**:
  - Tool name and photo
  - Owner's name and neighborhood
  - Original due date
  - Current status (on-time vs. overdue)
  - Quick actions: "Mark as Returned" link, "Request Extension" link (if eligible)
  - Owner's contact button for in-app messaging
- **Suppression Rules**:
  - No reminders sent after borrower marks as returned
  - No reminder sent if extension was approved and new due date is in future
  - Reminders pause if extension request is pending (resume if denied)
- **Owner Notifications** (parallel to borrower reminders):
  - Owner notified when their tool becomes overdue: "Your [Tool Name] lent to [Borrower] is now overdue"
  - Includes borrower's contact info and suggestion to reach out
- All reminders delivered via email with copy stored in in-app notification center

---

### Transaction History

**What**: A permanent, searchable record of all past borrow transactions for a user, viewable by that user only (not public).

**Why**: Users need to reference past borrows for disputes, tax records (if applicable later), or simply to remember what they've borrowed/lent. History contributes to trust signals on user profiles.

**Behavior**:
- Accessible via "History" tab on user's dashboard
- Shows completed transactions sorted by completion date (most recent first)
- Each history entry displays:
  - Tool name (linked to current tool listing if still exists)
  - Other party's name (linked to profile) and neighborhood
  - Role in transaction: "You borrowed" or "You lent"
  - Start date and end date (when return was confirmed)
  - Duration in days
  - Final status: "Returned - Good condition" or "Returned - Issues reported"
  - Ratings exchanged (if completed)
  - "View Details" link to see full transaction record
- **Detail view** includes:
  - All dates: requested, approved, started, due (original), due (if extended), returned, confirmed
  - Extension history if applicable (requests, approvals, denials)
  - Return notes from borrower
  - Return confirmation from owner (condition, photos, descriptions)
  - Issue reports if filed
  - All messages exchanged through in-app messaging system
  - Ratings and reviews from both parties
- **Search & Filter**:
  - Search by tool name or other party's username
  - Filter by date range (last 30 days, last 6 months, last year, all time)
  - Filter by role (borrowed vs. lent)
  - Filter by outcome (good condition vs. issues reported)
  - Filter by rating given/received
- History entries are never deleted; transactions are permanent record
- Users can add private notes to history entries (max 500 characters, not visible to other party)

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
  - OriginalDueDate
  - CurrentDueDate (may differ from original if extended)
  - Status (Active, PendingReturnConfirmation, Completed, Cancelled)
  - ReturnMarkedDate (when borrower clicked "Mark as Returned")
  - ReturnConfirmedDate (when owner confirmed return)
  - ReturnCondition (enum: GoodCondition, HasIssues, NotYetConfirmed)
  - CreatedAt, UpdatedAt timestamps

- **ExtensionRequest**: Tracks requests to extend due dates
  - ExtensionRequestId (primary key)
  - BorrowId (foreign key)
  - RequestedDate
  - RequestedNewDueDate
  - Reason (text, max 500 chars)
  - Status (Pending, Approved, Denied, TimedOut)
  - ResponseDate
  - ResponseMessage (from owner)
  - RespondedByUserId (foreign key to User - should be owner)

- **ReturnConfirmation**: Details about the return process
  - ReturnConfirmationId (primary key)
  - BorrowId (foreign key, one-to-one)
  - Condition (enum: Good, HasIssues)
  - OwnerNotes (text, max 1000 chars)
  - IssueDescription (text, max 1000 chars, nullable)
  - AffectsUsability (boolean)
  - ConfirmedDate
  - Photos (collection of photo URLs)

- **BorrowNote**: Private notes users add to their history
  - BorrowNoteId (primary key)
  - BorrowId (foreign key)
  - UserId (foreign key - who created the note)
  - NoteText (max 500 chars)
  - CreatedAt

- **ReminderLog**: Track which reminders have been sent to avoid duplicates
  - ReminderLogId (primary key)
  - BorrowId (foreign key)
  - ReminderType (enum: OneDayBefore, DueDate, OneDayOverdue, ThreeDaysOverdue)
  - SentDate
  - RecipientUserId (foreign key to User)

**Key Relationships**:
- Borrow has one ExtensionRequest (active) but many in history
- Borrow has one ReturnConfirmation when completed
- Borrow has many BorrowNotes (from either party)
- Borrow has many ReminderLogs
- Borrow references the original BorrowRequest (from Feature 2)
- Borrow references Tool and User entities (from Features 1 & 3)

---

## User Experience Flow

**Happy Path: Complete Borrow Cycle**

1. **Borrow begins**: Owner approves a borrow request, system creates Borrow entity with Status=Active, StartDate=now, OriginalDueDate and CurrentDueDate from request
2. **Borrower views active borrows**: Logs in, sees dashboard with tool listed under "I'm Borrowing", shows due date is 5 days away
3. **Reminder sent**: One day before due date, borrower receives email reminder with tool details and quick action links
4. **Project takes longer**: Borrower realizes they need one more day, clicks "Request Extension" on dashboard
5. **Extension requested**: Borrower selects new date (1 day later), enters reason "Need to finish staining the deck", submits
6. **Owner approves**: Owner receives notification, reviews request, approves extension
7. **Due date updated**: System updates CurrentDueDate, notifies borrower, resets reminder schedule
8. **Borrower returns tool**: On new due date, borrower returns tool to owner's house, clicks "Mark as Returned" in dashboard, adds note "Left it in your garage, thanks!"
9. **Owner confirms**: Owner receives notification, finds tool in garage, inspects condition, clicks "Confirm Return" → "Good condition", adds note "Thanks for cleaning it!"
10. **Transaction completes**: System sets Status=Completed, ReturnConfirmedDate=now, moves borrow to history for both users
11. **Rating prompt**: Both users see prompt to rate each other (separate workflow)

**Alternate Path: Overdue Handling**

1. Borrower doesn't return tool on due date
2. System marks borrow as overdue, sends reminder to borrower and notification to owner
3. Dashboard shows yellow "1 Day Overdue" badge
4. Three days pass with no return
5. System shows red "3 Days Overdue" badge, sends urgent reminder
6. Owner messages borrower through in-app messaging: "Hey, can you return my saw soon?"
7. Borrower apologizes, returns tool next day (4 days overdue)
8. Borrower marks as returned
9. Owner confirms return but notes "Good condition but would appreciate more communication about delays"
10. Transaction completes with late return documented in history

**Alternate Path: Tool Damaged**

1. Borrower returns tool on time, marks as returned
2. Owner inspects and discovers damage
3. Owner clicks "Confirm Return" → "Has issues"
4. Owner uploads photos of damage, describes: "Blade is dull and guard is cracked"
5. Owner checks "Issue affects tool's usability"
6. System documents issue in ReturnConfirmation, flags tool as needing repair
7. Tool listing automatically marked as "Temporarily Unavailable" until owner fixes it
8. Transaction completes but issue report visible in both users' history
9. Issue affects borrower's reputation (future enhancement - not blocking v1)

---

## Edge Cases & Constraints

- **Extension requested after already overdue**: Allow if only 1-2 days overdue, deny if 3+ days overdue (message: "Please return the tool or contact the owner directly")
- **Owner never confirms return**: After borrower marks returned, if owner doesn't respond within 7 days, system auto-confirms as "Good condition" and notifies both parties
- **Multiple extension requests**: Borrowers can request multiple extensions over the life of a borrow, but only one pending request at a time
- **Maximum total borrow duration**: Original due date max 14 days from start; extensions can add up to 14 more days; absolute maximum 28 days total
- **Borrower deletes account with active borrows**: Not allowed; must return all tools and have returns confirmed before account deletion
- **Owner deletes account with tools lent out**: Not allowed; must wait for all tools to be returned and confirmed before account deletion
- **Tool deleted while borrowed**: Not allowed; tools cannot be deleted from system if Status != Available
- **Photos in issue reports**: Max 5 photos, max 10MB each, accepted formats: JPEG, PNG
- **Overdue calculations**: Based on calendar days, not business days; due time is end of day (11:59 PM) in owner's timezone
- **Timezone handling**: All dates stored in UTC, displayed in user's local timezone as set in their profile

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- **Monetary penalties for late returns**: No automatic fines or deposits charged for overdue items (may be added in v2 with payment system)
- **Automatic dispute resolution**: If borrower and owner disagree about condition or return, they must resolve themselves; no automated mediation or admin intervention in v1
- **Damage cost estimation**: No feature to estimate repair costs or request reimbursement (future enhancement requires payment integration)
- **Insurance claims integration**: Issue reports are for record-keeping only, not for filing insurance claims
- **Automatic reputation penalties**: Late returns and issues are documented but don't automatically block future borrows or lower profile score (reputation system is future enhancement)
- **Pickup/drop-off scheduling**: No calendar integration or scheduling tool for coordinating return logistics
- **Multi-tool returns**: Borrow tracking is per-tool; if user borrows 3 tools from same owner, they're tracked as 3 separate borrows with independent due dates
- **Partial returns**: Cannot mark a tool as "partially returned" or "returned but missing accessories" - return is binary (returned or not)
- **Tool maintenance tracking**: Issue reports document problems at return time but don't feed into maintenance history or service schedule tracking

---

## Open Questions for Tech Lead

1. **Background Job Architecture**: Reminder emails are time-sensitive. Should we use Hangfire for scheduled reminders, or is there a preferred approach for time-based notifications in our stack?

2. **Photo Storage**: Return confirmation can include up to 5 photos of damage. Should these go to Azure Blob Storage / S3, or handle differently than tool listing photos?

3. **Overdue Calculation Logic**: Should overdue calculations happen at query time (computed property) or via background job that updates a flag field? Trade-off between accuracy and performance.

4. **Extension Request Timeout**: 24-hour timeout for extension requests requires detecting when requests have expired. Background job or query-time check?

5. **Auto-confirm After 7 Days**: If owner doesn't confirm return after borrower marks it returned, we auto-confirm after 7 days. Background job to find and auto-confirm these?

6. **Notification Delivery Reliability**: If email delivery fails for a critical reminder (due date, overdue), should we retry? Log and surface in admin dashboard? What's our general approach to notification reliability?

---

## Dependencies

**Depends On**: 
- Feature 2 (Borrowing Requests) - borrows are created when requests are approved
- Feature 1 (Tool Listings) - tracks what tool is borrowed, updates tool availability status
- Feature 3 (User Profiles) - ratings/reviews generated after returns feed into user reputation

**Enables**: 
- Feature 3 (User Profiles & Trust System) - transaction history and ratings data feed user trust scores and profile statistics
- Future payment/insurance features - issue reports and return confirmations provide audit trail for disputes