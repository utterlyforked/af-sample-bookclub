# Borrowing Requests - Feature Requirements

**Version**: 1.0  
**Date**: 2025-01-10  
**Status**: Initial - Awaiting Tech Lead Review

---

## Feature Overview

The Borrowing Requests feature is the core transaction mechanism of ToolShare - it enables borrowers to request tools from owners and provides owners with the information and controls needed to make informed lending decisions.

This feature transforms the awkward social interaction of asking to borrow something into a structured, asynchronous workflow. Borrowers can clearly communicate what they need, when they need it, and what they'll use it for. Owners can review requests on their own schedule, see relevant context about the borrower, and approve or decline with clear communication.

The feature prioritizes trust-building and safety by revealing information progressively: borrowers see general location before requesting, owners see borrower history before approving, and exact pickup addresses are only revealed after approval. This graduated disclosure protects privacy while enabling informed decisions.

By creating a paper trail of requests, approvals, and terms, this feature also reduces conflicts and misunderstandings that could damage both tools and community relationships.

---

## User Stories

- As a borrower, I want to request a tool with specific dates and a project description so that the owner understands my need and timeline
- As a borrower, I want to see the status of my pending requests so that I know whether I can plan to use the tool or need to find alternatives
- As a tool owner, I want to receive notifications when someone requests my tool so that I can respond promptly
- As a tool owner, I want to review a borrower's profile and history before approving so that I can make an informed lending decision
- As a tool owner, I want to approve or decline requests with optional messages so that I can communicate terms, concerns, or alternative suggestions
- As a tool owner, I want to see all pending requests in one place so that I can manage multiple requests efficiently
- As both parties, I want to receive notifications about request status changes so that I stay informed without constantly checking the app
- As both parties, I want to message each other about an active request so that we can coordinate pickup details or ask questions

---

## Acceptance Criteria

- Borrowers can only request tools that are marked as "Available" (not currently borrowed or temporarily unavailable)
- Borrowers must specify a start date (today or future), end date (max 14 days from start), and project description (50-500 characters)
- System prevents double-booking: if a tool is already requested for overlapping dates, subsequent requests are automatically declined or blocked
- Owners receive both email and in-app notification when a request is made (within 5 minutes)
- Owner can view borrower's profile including: full name, neighborhood, member since date, number of successful borrows completed, average rating, and any reviews from previous lenders
- Owner can approve a request with optional message (max 500 characters) or decline with required reason (max 500 characters)
- Upon approval, borrower receives notification containing: approval confirmation, owner's full address, owner's phone number (if provided), and pickup instructions message
- Upon decline, borrower receives notification with owner's reason
- Both parties can send messages about an active request through in-app messaging (no external email/phone required for basic coordination)
- Request status progresses through clear states: Pending → Approved/Declined → (if approved) Active Borrow → Completed
- Users can view history of all their requests (sent and received) with status and dates

---

## Functional Requirements

### Request Creation

**What**: Borrowers initiate a request by selecting a tool and providing essential details about their intended use.

**Why**: Gives tool owners the context they need to feel comfortable lending and helps set clear expectations about the borrow period.

**Behavior**:
- Request form appears when borrower clicks "Request This Tool" on a tool detail page
- Form fields:
  - **Start Date**: Date picker, default to today, cannot be in the past
  - **End Date**: Date picker, must be after start date, maximum 14 days from start date
  - **Project Description**: Text area, 50-500 characters, required
  - Character counter shows remaining characters
- Validation prevents submission if:
  - Dates are invalid (end before start, start in past, duration > 14 days)
  - Description is too short (<50 chars) or too long (>500 chars)
  - User already has a pending request for the same tool
- Upon submission:
  - Request is created with status "Pending"
  - Owner receives notification immediately
  - Borrower sees confirmation: "Request sent! [Owner name] will be notified and can review your request."
  - Borrower is redirected to "My Requests" page showing pending status

### Double-Booking Prevention

**What**: System ensures a tool cannot be borrowed by multiple people for overlapping date ranges.

**Why**: Prevents conflicts and ensures owners maintain control of their inventory. Avoids the awkward situation where an owner approves multiple requests and then must disappoint someone.

**Behavior**:
- When a request is submitted, system checks for approved requests with overlapping dates
- **Scenario 1 - No conflicts**: Request proceeds normally to "Pending" status
- **Scenario 2 - Conflict exists**: Request is automatically declined with system message:
  - "This tool is already borrowed during your requested dates. Try different dates or search for a similar tool nearby."
  - Borrower can immediately submit a new request with different dates
- When an owner approves a request:
  - System locks those dates for that tool
  - Any pending requests with overlapping dates are automatically declined with message: "Another borrower was approved for these dates. Please request again with different dates if you still need this tool."
- Edge case - rapid approvals: If owner somehow approves two overlapping requests simultaneously (race condition), first approval wins, second approval fails with error message to owner

### Owner Notification

**What**: Owners are promptly notified when someone requests their tool, through multiple channels.

**Why**: Quick notification enables timely responses, which improves borrower experience and increases successful transactions. Multi-channel approach ensures owners don't miss requests.

**Behavior**:
- **Email notification** sent within 5 minutes of request:
  - Subject: "[Borrower Name] wants to borrow your [Tool Name]"
  - Body includes: borrower's name and neighborhood, requested dates, project description, link to view full request and borrower profile
  - Clear call-to-action button: "Review Request"
- **In-app notification**:
  - Red badge appears on notifications icon in navigation bar
  - Notification entry shows: borrower's profile photo, name, tool name, "1 hour ago" timestamp
  - Clicking notification navigates to request review page
- **Notification consolidation**: If owner has multiple pending requests, single daily digest email after the first immediate notification (prevents email overload)
- Notifications are marked as "read" when owner views the request detail page

### Request Review Page

**What**: A dedicated page where owners can see all relevant information about a request and the borrower before making a decision.

**Why**: Informed lending decisions require context about both the borrower and the specific request. This page aggregates everything needed in one place.

**Behavior**:
- Page layout:
  - **Left column**: Request details
    - Tool name and photo
    - Requested dates prominently displayed
    - Project description in readable format
    - Days until start date (if future)
    - Request submitted timestamp
  - **Right column**: Borrower profile card
    - Profile photo, name, neighborhood
    - "Member since [date]" (e.g., "Member since Jan 2025")
    - Statistics:
      - "X successful borrows completed"
      - "Average rating: ★★★★★ (4.8)"
    - Link to view full profile and reviews
  - **Bottom section**: Action buttons and messaging
    - "Approve" button (green)
    - "Decline" button (red)
    - Text area for optional message (approve) or required reason (decline)
- If borrower has no completed borrows yet: Shows "New member - no borrows yet" with encouraging note
- If borrower has negative reviews or reports: Warning badge appears with "View concerns" link to problem reports

### Approval Flow

**What**: Owner approves the request and provides pickup information to the borrower.

**Why**: Approval signifies trust and commitment. Revealing the owner's full address only after approval protects privacy while enabling the transaction.

**Behavior**:
- Owner clicks "Approve" button
- Optional message field expands (if not already visible):
  - Placeholder: "Share pickup instructions, gate codes, or other details (optional)"
  - Max 500 characters
  - Suggestions appear: "Tell them where to find the tool, best times to pick up, or special usage instructions"
- Owner clicks "Confirm Approval"
- System immediately:
  - Changes request status from "Pending" to "Approved"
  - Creates an "Active Borrow" record (tracked in Borrow Tracking feature)
  - Locks the tool's calendar for those dates
  - Sends notification to borrower (email + in-app)
- Borrower notification includes:
  - "Good news! [Owner name] approved your request for [Tool name]"
  - Requested dates confirmed
  - **Owner's full address** (revealed for first time)
  - Owner's phone number (if owner provided one in their profile)
  - Owner's message (if provided)
  - Call-to-action: "Coordinate pickup with [Owner name]"
- Tool listing status changes to "Currently Borrowed" (visible to other users searching)

### Decline Flow

**What**: Owner declines the request and must provide a reason to help the borrower understand.

**Why**: Required reasons prevent silent rejections, reduce borrower frustration, and help borrowers improve future requests. They also create accountability for owners to decline thoughtfully.

**Behavior**:
- Owner clicks "Decline" button
- Required reason field expands:
  - Placeholder: "Let them know why (required)"
  - Max 500 characters
  - Must have at least 20 characters to submit
  - Common reasons appear as quick-select chips:
    - "Tool is in use during those dates"
    - "Tool needs maintenance first"
    - "Prefer to lend to people I know"
    - "Project seems outside tool's intended use"
- Owner writes reason and clicks "Confirm Decline"
- System immediately:
  - Changes request status from "Pending" to "Declined"
  - Records reason (visible to borrower, not public)
  - Sends notification to borrower (email + in-app)
- Borrower notification includes:
  - "[Owner name] declined your request for [Tool name]"
  - Owner's reason
  - Encouragement: "Don't be discouraged! Try requesting a similar tool from another neighbor or adjusting your dates."
  - Link to search for similar tools
- Borrower can submit a new request for the same tool with different dates (no cooldown period)

### In-App Messaging

**What**: Borrowers and owners can exchange messages about a specific request without leaving the platform or sharing personal contact information.

**Why**: Enables coordination ("What time should I pick up?") and questions ("Does this come with a charger?") while maintaining platform-mediated communication for safety and record-keeping.

**Behavior**:
- Message thread is associated with each request
- Accessible from request detail page for both parties
- Simple threaded conversation interface:
  - Messages show sender name, timestamp, and text
  - Sorted chronologically (oldest first)
  - New messages are bold until read
- Message composition:
  - Text area with 1000 character limit
  - "Send" button
  - No attachments in v1 (can share photos by adding to tool listing)
- Notifications for new messages:
  - In-app notification badge
  - Email notification if user hasn't read message within 2 hours
  - Email includes message preview and link to thread
- Message thread remains accessible:
  - During "Pending" state
  - After approval, throughout "Active Borrow"
  - After completion, in transaction history (read-only)
- Thread is closed (read-only) when:
  - Request is declined (borrower can read owner's decline reason, cannot reply)
  - Borrow is completed and return is confirmed
  - Either party can report problematic messages to moderation (future feature)

### Request Status Tracking

**What**: Both borrowers and owners can see the current state and history of all their requests.

**Why**: Transparency reduces anxiety and follow-up messages. Users know where things stand without having to ask.

**Behavior**:
- **"My Requests" page** (borrower view):
  - Tabs: "Pending" (default), "Approved", "Declined", "Completed"
  - Each request card shows:
    - Tool name and photo thumbnail
    - Owner's name and neighborhood
    - Requested dates
    - Status with visual indicator (yellow dot = pending, green = approved, red = declined)
    - Request submitted date
    - Action buttons based on status:
      - Pending: "View Details", "Cancel Request"
      - Approved: "View Pickup Info", "Message Owner"
      - Declined: "View Reason", "Request Again"
  - Sorted by request date (most recent first)
- **"Requests for My Tools" page** (owner view):
  - Tabs: "Pending" (default), "Approved", "Declined"
  - Each request card shows:
    - Borrower's profile photo, name, and rating
    - Tool requested and dates
    - Project description preview (first 100 chars)
    - Status
    - Action buttons:
      - Pending: "Review & Decide"
      - Approved: "View Details", "Message Borrower"
      - Declined: "View Details"
  - Badge on "Pending" tab shows count of pending requests
- Status badge colors:
  - Yellow: Pending
  - Green: Approved
  - Red: Declined
  - Blue: Active (pickup occurred, return pending - tracked in Borrow Tracking feature)
  - Gray: Completed

### Request Cancellation

**What**: Borrowers can cancel pending requests if their plans change.

**Why**: Gives borrowers flexibility and prevents owners from spending time reviewing requests that are no longer needed.

**Behavior**:
- "Cancel Request" button available on pending requests
- Confirmation modal: "Are you sure you want to cancel this request? This cannot be undone."
- Upon confirmation:
  - Request status changes to "Cancelled" (distinct from "Declined")
  - Owner receives notification: "[Borrower name] cancelled their request for [Tool name]"
  - Request moves to borrower's "Declined" tab (grouped with declined requests for simplicity)
  - Borrower can submit a new request immediately if desired
- Cannot cancel after approval (must coordinate return through Borrow Tracking feature instead)

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:

- **BorrowRequest**: Core entity representing a request to borrow a tool
  - Properties: id, toolId, borrowerUserId, ownerUserId, requestedStartDate, requestedEndDate, projectDescription, status (enum: Pending, Approved, Declined, Cancelled), createdAt, respondedAt, ownerMessage, declineReason
  
- **RequestMessage**: Messages exchanged about a specific request
  - Properties: id, requestId, senderUserId, messageText, sentAt, readAt

- **Notification**: Alerts sent to users about request activity
  - Properties: id, userId, requestId, notificationType, sentAt, readAt, emailSent, inAppDelivered

**Key Relationships**:
- BorrowRequest belongs to Tool (one-to-many: tool has many requests)
- BorrowRequest belongs to User (as borrower) and User (as owner) (many-to-one relationships)
- BorrowRequest has many RequestMessages
- RequestMessage belongs to User (sender)
- Notification belongs to User and references BorrowRequest

**Status Transitions**:
- Valid state machine: Pending → [Approved | Declined | Cancelled]
- No transitions back to Pending
- Approved requests later transition to Active Borrow (managed by Borrow Tracking feature)

**Constraints**:
- Cannot request a tool you own
- Cannot have multiple pending requests for the same tool
- End date must be after start date
- Maximum borrow period: 14 days
- No overlapping approved borrows for the same tool

---

## User Experience Flow

### Happy Path - Borrower Perspective

1. User searches for "lawn mower" and finds one 2 miles away marked "Available"
2. User clicks "Request This Tool" button on tool detail page
3. Form appears:
   - Start date: User selects "Tomorrow" (Jan 11)
   - End date: User selects "Jan 13" (2 days later)
   - Project description: User types "Need to mow front and back lawn after vacation. Should take a few hours."
4. User clicks "Send Request"
5. Confirmation appears: "Request sent! Mike Johnson will be notified and can review your request."
6. User is redirected to "My Requests" page, sees request with "Pending" status
7. (2 hours later) User receives email: "Mike Johnson approved your request!"
8. User opens app, clicks notification, sees approval message with Mike's address: "123 Oak Street" and message: "Tool is in the garage, door code is 1234. Make sure to use the safety guard!"
9. User clicks "Message Mike" and sends: "Thanks! I'll pick it up tomorrow morning around 9am if that works?"
10. (Next day) User picks up mower, and the borrow becomes active (Borrow Tracking feature takes over)

### Happy Path - Owner Perspective

1. Mike receives email: "Sarah Chen wants to borrow your Lawn Mower - Electric"
2. Mike clicks "Review Request" in email
3. Mike sees request page:
   - Left side: Lawn mower photo, dates Jan 11-13, project: "Need to mow front and back lawn..."
   - Right side: Sarah's profile - Member since Dec 2024, 3 successful borrows, 5.0 star rating
4. Mike clicks "View Profile" to see Sarah's reviews: All positive, previous lenders commented "Returned on time", "Tool came back clean"
5. Mike feels confident and clicks "Approve"
6. Optional message field appears, Mike types: "Tool is in the garage, door code is 1234. Make sure to use the safety guard!"
7. Mike clicks "Confirm Approval"
8. Mike sees confirmation: "Approved! Sarah will receive your contact info and pickup instructions."
9. (Later) Mike receives message from Sarah: "Thanks! I'll pick it up tomorrow morning around 9am if that works?"
10. Mike replies: "Perfect, I'll be home. See you then!"

---

## Edge Cases & Constraints

- **Borrower has no history**: Display "New member - no borrows yet" instead of statistics. Owners can still approve based on profile information and project description. Note in future iterations: Consider requiring email/phone verification for first-time borrowers.

- **Owner doesn't respond**: Request remains in "Pending" state indefinitely in v1. No automatic expiration or reminder escalation. Note for v2: Consider auto-declining requests after 7 days with notification to borrower.

- **Dates become invalid after approval**: If owner approves a request for future dates, then someone else borrows the tool for overlapping dates, this is prevented by the double-booking check. Once approved, those dates are locked.

- **Tool is deleted while request is pending**: Request is automatically declined with system message: "This tool is no longer available." Borrower is notified.

- **User is deleted/banned while request is pending**: All their pending requests (sent or received) are automatically cancelled with system message. Other party is notified.

- **Borrower requests many tools simultaneously**: No limit on number of pending requests in v1. Possible future consideration: Flag users who request >10 tools in 24 hours as potential spam.

- **Owner has many pending requests**: All shown in "Pending" tab sorted by request date. No prioritization or batch-action features in v1. Owner must review each individually.

- **Project description contains inappropriate content**: No automated content filtering in v1. Owners can decline and should report abusive requests through user reporting feature (future). Note for v2: Consider basic profanity filter.

- **Pickup never happens after approval**: Request stays in "Approved" state until borrower or owner marks pickup as occurred (handled in Borrow Tracking feature). No automatic transition based on start date.

- **Same-day requests**: Allowed. Borrower can select today as start date. Owner might respond immediately or not - no guaranteed response time.

- **Long project descriptions**: Hard limit of 500 characters enforced in UI and backend. Truncated with ellipsis in card views, full text shown in detail view.

- **Timezone handling**: All dates are date-only (no times) in v1. System uses user's local timezone for display. Start date means "anytime on that day" - specific pickup times coordinated through messaging.

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- **Calendar integration**: No sync with Google Calendar or Apple Calendar. Users manually track dates.
- **Automated reminders about upcoming pickups**: No notifications like "Your borrow starts tomorrow!" in v1. (Future: Borrow Tracking feature might add this)
- **Request templates**: No saved project descriptions or quick-request presets.
- **Batch approval/decline**: Owner must handle requests one at a time. No "approve all from this user" feature.
- **Request editing**: Once submitted, borrower cannot edit dates or description. Must cancel and resubmit.
- **Conditional approval**: Owner cannot approve with modified dates (e.g., "Yes but only Jan 11-12 not 13"). Must decline with explanation or approve as-is and coordinate changes through messaging.
- **Request expiration**: Pending requests don't auto-decline after a time period.
- **Priority/urgent requests**: All requests are equal priority. No "I need this ASAP" flag or expedited review.
- **Favorite/preferred borrowers**: No owner setting like "auto-approve requests from users I've lent to before."
- **Request history visible to others**: Only the borrower and owner see the request. Other users don't see that a tool has pending requests.
- **Waitlist for unavailable dates**: If dates are taken, borrower must manually try again later. No "notify me if this becomes available" feature.
- **Scheduling pickup appointments**: Specific pickup day/time coordinated through messaging. No calendar picker for pickup appointment.
- **Request analytics**: No data like "This tool has been requested X times" visible to owners.

---

## Open Questions for Tech Lead

1. **Message notification timing**: Email after 2 hours if unread - is this too long/short? Should we have a user preference for notification frequency?

2. **Date range validation**: Should we prevent requests that start more than 30 days in the future? Or allow any future date?

3. **Concurrent request limits**: Should we limit how many pending requests a borrower can have at once (e.g., max 5) to prevent spam?

4. **Request history retention**: How long should we keep declined/cancelled request records? Forever for audit trail, or purge after 1 year?

5. **Phone number requirement**: Should owners be required to provide a phone number to list tools, or remain optional? (Impacts pickup coordination)

---

## Dependencies

**Depends On**: 
- Feature 1 (Tool Listings) - must have tools to request
- Feature 3 (User Profiles & Trust System) - must display borrower history and ratings during review

**Enables**: 
- Feature 4 (Borrow Tracking & Returns) - approved requests transition to active borrows