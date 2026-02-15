# Borrowing Request & Communication System - Feature Requirements

**Version**: 1.0  
**Date**: December 19, 2024  
**Status**: Initial - Awaiting Tech Lead Review

---

## Feature Overview

The Borrowing Request & Communication System is the core interaction mechanism that enables safe, organized communication between tool borrowers and lenders to arrange exchanges. This feature transforms casual "can I borrow your drill?" conversations into a structured, trackable process that builds trust and accountability within the community.

Users can send detailed borrowing requests that include project context, timeframes, and logistics preferences. Tool owners can review these requests with full information to make informed decisions about lending their equipment. The built-in messaging system then facilitates coordination of pickup/return logistics while maintaining a record of all interactions.

This feature is essential because it moves tool sharing from informal social networks (where you need to know someone personally) to an organized community system where strangers can safely transact based on profiles, ratings, and clear communication protocols.

---

## User Stories

- As someone needing a tool, I want to send borrowing requests with my project details and timeframe so that owners can make informed lending decisions
- As a tool owner, I want to review borrowing requests and approve/decline them so that I maintain control over my equipment
- As both parties, I want to communicate about pickup/return logistics so that we can coordinate the exchange smoothly
- As a borrower, I want to explain what I'm using the tool for so that owners feel comfortable lending expensive equipment
- As a tool owner, I want to ask questions about the borrower's experience level so that I can provide appropriate usage guidance
- As any user, I want a record of our communication so that I can reference pickup times and return agreements

---

## Acceptance Criteria

- Users can send borrowing requests specifying dates needed, project description, and pickup preferences
- Tool owners receive notifications of new requests and can approve/decline with optional messages
- Built-in messaging system allows coordination of pickup/return details
- Request status tracking (pending, approved, declined, active loan, returned)
- Borrowers can include experience level and project details in requests
- Owners can ask follow-up questions before approving requests
- All communication history is preserved for both parties
- Email notifications are sent for new requests, responses, and status changes

---

## Functional Requirements

### Request Creation

**What**: Borrowers can create detailed requests to borrow specific tools

**Why**: Detailed requests help owners make informed decisions and reduce back-and-forth communication

**Behavior**:
- Request form includes: dates needed (start/return), project description (required), experience level with tool type, preferred pickup times, contact preferences
- System validates that return date is after start date
- Character limits: project description (500 chars), additional notes (200 chars)
- Requests are immediately sent to tool owner with email notification
- Borrower can cancel pending requests but not approved ones

### Request Review & Response

**What**: Tool owners can review incoming requests and approve/decline with messaging

**Why**: Owners need control over their equipment and ability to communicate requirements or concerns

**Behavior**:
- Owners see request details including borrower's profile summary and rating
- Approve/decline buttons with optional message field (300 char limit)
- "Ask Questions" option sends request to pending status with message thread
- Auto-decline after 48 hours if no response (configurable per user)
- Owners can view borrower's previous borrowing history summary

### In-App Messaging System

**What**: Structured messaging between borrower and lender for each request

**Why**: Keeps all coordination in one place and maintains records for accountability

**Behavior**:
- Message threads are tied to specific tool requests
- Messages limited to 500 characters each
- No photo sharing in v1 (text only)
- Message timestamps and read receipts
- Email notifications for new messages (can be disabled in settings)
- Message history preserved even after loan completion

### Request Status Management

**What**: Clear status tracking throughout the borrowing lifecycle

**Why**: Both parties need visibility into where things stand and what actions are needed

**Behavior**:
- Status flow: Pending → Approved/Declined → Active Loan → Returned
- Status changes trigger notifications to both parties
- "Active Loan" status is set when owner marks tool as picked up
- "Returned" status requires confirmation from both parties
- Declined requests show decline reason if provided

### Notification System

**What**: Email and in-app notifications for key events

**Why**: Users need timely updates to coordinate effectively and maintain engagement

**Behavior**:
- New request: immediate email to tool owner
- Request response: immediate email to borrower
- New message: email notification (unless disabled)
- Status changes: notification to both parties
- Pickup reminders: 24 hours before agreed pickup time
- Return reminders: 24 hours before due date

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:
- BorrowingRequest: Core request entity with dates, status, project details
- Message: Individual messages within a request thread
- RequestStatus: Enumeration (Pending, Approved, Declined, Active, Returned)
- Notification: User notifications and email preferences

**Key Relationships**:
- User (borrower) → BorrowingRequest (one-to-many)
- User (lender) → BorrowingRequest (one-to-many)
- Tool → BorrowingRequest (one-to-many)
- BorrowingRequest → Message (one-to-many)
- BorrowingRequest → Notification (one-to-many)

[Note: This is preliminary - Tech Lead will ask questions to clarify]

---

## User Experience Flow

### Happy Path - Successful Request

1. Borrower finds tool and clicks "Request to Borrow"
2. Fills out request form with project details, dates, and preferences
3. Submits request - owner gets email notification
4. Owner reviews request and borrower's profile
5. Owner approves with message about pickup logistics
6. Both parties coordinate pickup details via messaging
7. Owner marks tool as "picked up" when borrower collects it
8. System reminds borrower about return date
9. Borrower returns tool, both parties confirm return
10. Request closes and both can rate the experience

### Alternative Path - Questions Before Approval

1-4. Same as above
5. Owner clicks "Ask Questions" and sends message about experience level
6. Borrower responds with more details
7. Owner feels comfortable and approves request
8-10. Continue as happy path

---

## Edge Cases & Constraints

- **Multiple requests for same tool**: First-come-first-served for approval, but owner can approve future dates
- **Request date conflicts**: System prevents double-booking by showing tool availability when requesting
- **No response from owner**: Auto-decline after 48 hours with notification to borrower
- **Inappropriate messages**: Basic reporting mechanism, but no automated moderation in v1
- **Request modifications**: No editing after submission - must cancel and resubmit
- **Emergency contact**: No emergency features in v1 - standard contact methods only

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- Payment processing or security deposits
- Advanced scheduling/calendar integration
- Photo sharing in messages
- Video chat or voice calls
- Automated damage assessment
- Insurance or liability management
- Integration with external calendar apps
- Bulk messaging or broadcast features
- Message translation services

---

## Open Questions for Tech Lead

- Should we implement real-time messaging or is async sufficient for v1?
- What's the appropriate rate limiting for messages to prevent spam?
- How should we handle timezone differences in pickup scheduling?
- Should request status changes be reversible (e.g., moving from "Active" back to "Approved")?

---

## Dependencies

**Depends On**: 
- User Profiles & Community Verification (need user ratings and trust scores)
- Tool Listing & Discovery (need tools to request)

**Enables**: 
- Loan Tracking & Management (approved requests become tracked loans)
- Rating/review system (completed loans enable mutual rating)