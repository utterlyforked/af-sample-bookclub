# Borrowing Request & Communication System - Product Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: request limits, conflict resolution, confirmation flows, notification preferences)

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

## Acceptance Criteria (UPDATED v1.1)

- Users can send borrowing requests specifying dates needed, project description, and pickup preferences
- Users are limited to 10 pending requests maximum to prevent abuse
- System prevents double-booking by blocking requests that overlap with approved loans
- Tool owners receive notifications of new requests and can approve/decline with optional messages
- Auto-decline triggers exactly 48 hours after request creation if owner hasn't responded
- Built-in messaging system allows coordination of pickup/return details with immediate email notifications
- Request status tracking (pending, approved, declined, active loan, returned)
- Return confirmation requires borrower to initiate, owner to confirm within 24 hours (auto-confirms if no response)
- Borrowers can include experience level and project details in requests
- Owners can ask follow-up questions before approving requests
- All communication history is preserved for participants only (not public)
- Basic message reporting sends alerts to admin email for manual review
- Email notifications are sent for new requests, responses, and status changes

---

## Detailed Specifications (UPDATED v1.1)

**Request Limits & Abuse Prevention**

**Decision**: Maximum 10 pending requests per user

**Rationale**: Allows legitimate users to request multiple tools for different projects while preventing spam that would overwhelm tool owners. Pending requests are those with status "Pending" or "Approved" (not yet picked up).

**Examples**:
- User can have 8 pending requests and submit 2 more
- User tries to submit 11th request → error message: "You have reached the maximum of 10 pending requests. Please wait for responses or cancel existing requests."
- Declined and completed requests don't count toward the limit

**Edge Cases**:
- When request moves from Pending to Declined/Returned, limit decreases immediately
- System shows current count: "Pending requests: 7/10" in user dashboard

---

**Date Conflict Resolution**

**Decision**: Block new requests that overlap with existing approved loans

**Rationale**: Prevents tool owners from accidentally double-booking their equipment and ensures borrowers only see actually available dates. Owner maintains control without complex conflict management.

**Examples**:
- Tool approved for June 1-5
- New request for June 3-7 → blocked with message: "Tool not available June 3-5. Available again starting June 6."
- New request for May 25-30 → allowed (no overlap)

**Edge Cases**:
- Same-day return/pickup allowed (June 5 return, June 5 new pickup)
- System shows available date ranges when viewing tool: "Next available: June 6+"

---

**Auto-Decline Timing**

**Decision**: Fixed 48-hour timeout from request creation

**Rationale**: Simple and predictable for all users. Borrowers know exactly how long to wait, owners have reasonable time to respond including weekends. Consistent experience across the platform.

**Examples**:
- Request created Monday 2 PM → auto-decline Wednesday 2 PM if no response
- Email sent to borrower: "Your request for [Tool] was automatically declined due to no response. You can submit a new request."
- Status changes from "Pending" to "Declined" with reason "No response within 48 hours"

**Edge Cases**:
- Partial responses (messages without approval/decline) reset the 48-hour timer
- Owner can still approve/decline manually even after auto-decline

---

**Return Confirmation Process**

**Decision**: Borrower initiates return, owner confirms within 24 hours (auto-confirms if no response)

**Rationale**: Borrower knows when they actually returned the tool, owner gets chance to verify condition, automatic completion prevents loans from staying open indefinitely due to non-responsive owners.

**Examples**:
- Borrower clicks "Mark as Returned" → tool status becomes "Pending Return Confirmation"
- Owner gets notification: "[User] says they returned your [Tool]. Please confirm condition and return."
- Owner confirms → status becomes "Returned"
- No owner response after 24 hours → auto-confirms with note: "Return confirmed automatically"

**Edge Cases**:
- If owner disputes return, they can message borrower and keep status as "Active" until resolved
- Both parties can rate each other only after "Returned" status is reached

---

**Message Notification Settings**

**Decision**: Immediate email notifications for all messages, with user setting to disable

**Rationale**: Fast coordination is crucial for tool exchanges. Users who find it overwhelming can disable in their settings. Better to start with high engagement and let users dial it down.

**Examples**:
- New message → immediate email: "New message about your [Tool] request from [User]"
- User settings: Toggle "Email me for new messages" (default: ON)
- In-app notifications always shown regardless of email preference

**Edge Cases**:
- No rate limiting in v1 - trust community behavior and address abuse reactively
- Emails include message preview but require login to respond

---

**Communication Privacy**

**Decision**: Message history visible only to request participants (borrower and lender)

**Rationale**: Encourages honest communication about concerns, experience level, and logistics without worrying about public judgment. Users can communicate freely about pickup addresses and personal schedules.

**Examples**:
- Only Alice (borrower) and Bob (tool owner) can see their message thread
- Future borrowers cannot see how Bob typically communicates
- No aggregated metrics like "responds within 2 hours typically" in v1

**Future**: Consider adding anonymized response time stats in v2 if users request it.

---

**Message Reporting Mechanism**

**Decision**: Simple "Report Message" button sends admin email with context

**Rationale**: Minimal implementation that covers the safety need. Manual review appropriate for expected low volume. Can enhance based on actual abuse patterns.

**Examples**:
- "Report" link next to each message
- Clicking sends email to admin with: reporter, reported user, message content, request context
- Admin email: "Message reported in request #123 between [UserA] and [UserB]: [message content]"

**Edge Cases**:
- No automatic actions taken - purely for admin awareness
- Reporter remains anonymous to reported user
- Can report multiple messages in same conversation

---

## Q&A History

### Iteration 1 - December 19, 2024

**Q1: Can users have multiple pending requests for the same tool?**  
**A**: No. Users can have only one pending request per tool. They must cancel and resubmit if they want different dates. This prevents request spam and keeps owner inboxes manageable.

**Q2: What happens when request dates conflict with existing approved loans?**  
**A**: System blocks new requests that overlap with approved loans. Users see available dates and cannot submit conflicting requests. Prevents double-booking and owner confusion.

**Q3: When exactly does auto-decline trigger and can it be customized?**  
**A**: Fixed 48-hour timeout from request creation. Simple and predictable for all users. No customization in v1 to keep complexity low.

**Q4: What constitutes "confirmation from both parties" for returned status?**  
**A**: Borrower initiates return, owner has 24 hours to confirm. Auto-confirms if owner doesn't respond. This prevents loans from getting stuck due to non-responsive owners while giving owners chance to verify condition.

**Q5: What's the maximum number of simultaneous borrowing requests per user?**  
**A**: 10 pending requests maximum per user. Covers legitimate multi-tool needs while preventing abuse and notification overwhelm for tool owners.

**Q6: How should we handle message notifications for active conversations?**  
**A**: Immediate email for every message, with user setting to disable. Fast coordination is crucial for tool logistics. Users can turn off if it becomes overwhelming.

**Q7: Should we show request/message history to future potential borrowers?**  
**A**: No. Message history visible only to participants for privacy. Encourages honest communication without public judgment concerns.

**Q8: What basic reporting mechanism do we need for inappropriate messages?**  
**A**: "Report Message" button sends admin email with full context. Manual review for expected low volume. Simple implementation that covers safety needs.

---

## Product Rationale

**Why limit to 10 pending requests?**  
Balances user flexibility with community health. Users working on multiple projects need several tools, but unlimited requests would spam tool owners. 10 is generous for legitimate use while preventing abuse.

**Why block date conflicts instead of queuing?**  
Simplicity for MVP. Queuing creates complex notification chains and user expectations about priority. Better to show clear availability and let users make informed requests.

**Why borrower-initiated returns?**  
Borrower knows exactly when they returned the tool. Owner confirmation protects against disputes while auto-confirmation prevents stuck loans. Clear workflow with minimal friction.

**Why immediate message notifications?**  
Tool coordination often needs quick responses for pickup timing. Unlike social media, these are actionable messages with time constraints. Users can disable if needed, but default should optimize for successful exchanges.

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:
- BorrowingRequest: Core request entity with dates, status, project details
- Message: Individual messages within a request thread  
- RequestStatus: Enumeration (Pending, Approved, Declined, Active, PendingReturn, Returned)
- Notification: User notifications and email preferences

**Key Relationships**:
- User (borrower) → BorrowingRequest (one-to-many)
- User (lender) → BorrowingRequest (one-to-many)  
- Tool → BorrowingRequest (one-to-many)
- BorrowingRequest → Message (one-to-many)
- BorrowingRequest → Notification (one-to-many)

**Additional Fields Needed**:
- BorrowingRequest.return_initiated_at (timestamp for return confirmation flow)
- User.email_notifications_enabled (boolean for message notification preference)
- BorrowingRequest.auto_decline_at (computed field for 48-hour timeout)

---

## User Experience Flow

### Happy Path - Successful Request

1. Borrower finds tool and clicks "Request to Borrow"
2. System checks: user has <10 pending requests, dates don't conflict with approved loans
3. Fills out request form with project details, dates, and preferences
4. Submits request - owner gets immediate email notification
5. Owner reviews request and borrower's profile
6. Owner approves with message about pickup logistics
7. Both parties coordinate pickup details via messaging (immediate email notifications)
8. Owner marks tool as "picked up" when borrower collects it (status: Active)
9. System reminds borrower about return date
10. Borrower clicks "Mark as Returned" (status: PendingReturn)
11. Owner confirms return within 24 hours (status: Returned)
12. Both parties can rate the experience

### Alternative Path - Questions Before Approval

1-4. Same as above
5. Owner clicks "Ask Questions" and sends message about experience level
6. Borrower responds with more details (48-hour auto-decline timer resets)
7. Owner feels comfortable and approves request
8-12. Continue as happy path

---

## Edge Cases & Constraints

- **Multiple requests for same tool**: Only one pending request per tool per user - must cancel to submit new dates
- **Request date conflicts**: System prevents overlapping requests with approved loans, shows next available date
- **No response from owner**: Auto-decline after exactly 48 hours from request creation
- **Inappropriate messages**: "Report Message" button sends admin email for manual review
- **Request modifications**: No editing after submission - must cancel and resubmit  
- **Emergency contact**: No emergency features in v1 - standard contact methods only
- **Non-responsive owner for return**: Auto-confirms return after 24 hours to prevent stuck loans
- **Request spam prevention**: 10 pending request limit per user, no rate limiting on messages in v1

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
- Real-time messaging (async is sufficient for v1)
- Customizable auto-decline timeouts
- Request queuing for conflicting dates

---

## Dependencies

**Depends On**: 
- User Profiles & Community Verification (need user ratings and trust scores)
- Tool Listing & Discovery (need tools to request)

**Enables**: 
- Loan Tracking & Management (approved requests become tracked loans)
- Rating/review system (completed loans enable mutual rating)