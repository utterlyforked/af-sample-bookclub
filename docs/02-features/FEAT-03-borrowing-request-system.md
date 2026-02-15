# Borrowing Request System - Feature Requirements

**Version**: 1.0  
**Date**: February 15, 2025  
**Status**: Initial - Awaiting Tech Lead Review

---

## Feature Overview

The Borrowing Request System is the core transaction mechanism that enables structured communication between borrowers and tool owners. This feature transforms casual "can I borrow this?" conversations into formal agreements with clear terms, dates, and expectations.

This system acts as the bridge between tool discovery and loan tracking, ensuring both parties understand exactly what's being borrowed, when, and under what conditions. It creates accountability while maintaining the neighborly spirit of community sharing by providing a paper trail that prevents misunderstandings and disputes.

The feature handles the entire request lifecycle from initial inquiry through final acceptance, including counter-offers, term negotiation, and the creation of binding loan agreements that feed into the loan tracking system.

---

## User Stories

- As a borrower, I want to request a tool for specific dates so the owner knows exactly when I need it
- As a tool owner, I want to approve or decline requests with the ability to suggest alternative dates so I maintain control over my property
- As both parties, I want all loan terms documented (pickup/return times, condition expectations, deposits) so there are no misunderstandings
- As a borrower, I want to explain what I'm using the tool for so the owner can assess if it's appropriate and provide relevant advice
- As a tool owner, I want to see the borrower's profile and previous borrowing history so I can make informed lending decisions
- As both parties, I want to communicate through the app during the request process so we can clarify details and build trust

---

## Acceptance Criteria

- Borrowers can request tools with proposed start/end dates, intended use, and pickup preferences
- Tool owners receive notifications and can approve, decline, or counter-propose dates
- Approved loans create a binding agreement with pickup location, expected return condition, and any deposits required
- Both parties can message each other through the app with conversation history preserved
- Request status is always clear to both parties (pending, approved, declined, expired)
- Only one active request per borrower per tool at a time
- Tool owners can set automatic approval rules for trusted borrowers

---

## Functional Requirements

### Request Creation

**What**: Borrowers can submit detailed requests for specific tools with all necessary context

**Why**: Clear, complete requests help owners make quick decisions and prevent back-and-forth clarification

**Behavior**:
- Request form includes: start date, end date, intended use description, pickup time preference, special requests
- System validates dates are in the future and end date is after start date
- Maximum loan duration enforced based on tool owner's settings (default: 7 days)
- Borrower must confirm they've read the tool's usage instructions and restrictions
- Request automatically expires after 48 hours if no response from owner

### Request Management

**What**: Tool owners can review, approve, decline, or modify incoming requests

**Why**: Owners need full control over their property while being able to accommodate borrowers when possible

**Behavior**:
- Owners see borrower's profile, rating, and request details in a single view
- Three response options: Approve as-is, Approve with changes, or Decline
- When approving with changes, owner can modify dates, pickup/return times, or add special conditions
- Decline requires selecting a reason (tool unavailable, dates don't work, borrower concerns, etc.)
- All responses must be submitted within 48 hours or request auto-expires

### Agreement Formation

**What**: Approved requests become binding loan agreements with clear terms

**Why**: Both parties need certainty about expectations to prevent disputes and ensure smooth transactions

**Behavior**:
- Agreement includes: exact pickup/return dates and times, pickup location, tool condition expectations, any deposit requirements
- Both parties must digitally acknowledge the agreement before pickup
- Agreement generates unique loan ID for tracking
- Changes after approval require mutual consent from both parties
- Agreements automatically include standard community terms of use

### Communication Thread

**What**: Built-in messaging system for each request with full conversation history

**Why**: Keeps all request-related communication in one place and provides context for future interactions

**Behavior**:
- Messages are threaded to specific requests and preserved even after completion
- Both parties can attach photos to messages (useful for showing tool condition or project context)
- System messages automatically log status changes (approved, declined, modified)
- Conversations remain accessible for 90 days after loan completion
- Profanity filter and reporting system for inappropriate messages

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:
- **BorrowRequest**: Core request with dates, status, terms
- **RequestMessage**: Individual messages within a request thread  
- **LoanAgreement**: Formalized agreement created from approved requests
- **RequestStatusHistory**: Audit trail of status changes

**Key Relationships**:
- BorrowRequest belongs to User (borrower) and Tool (being requested)
- RequestMessage belongs to BorrowRequest and User (sender)
- LoanAgreement is created from approved BorrowRequest
- Tool owner is derived through Tool → User relationship

[Note: This is preliminary - Tech Lead will ask questions to clarify]

---

## User Experience Flow

1. **Borrower finds tool** and clicks "Request to Borrow"
2. **System presents request form** with tool details and owner preferences pre-populated
3. **Borrower fills out dates, intended use, and pickup preferences** then submits
4. **Tool owner receives notification** (push + email) about new request
5. **Owner reviews request** seeing borrower profile, tool details, and request specifics
6. **Owner responds** with approve, decline, or counter-offer
7. **If counter-offer**, borrower gets notification and can accept or decline the changes
8. **If approved**, system generates loan agreement requiring acknowledgment from both parties
9. **Both parties acknowledge agreement** and loan moves to active tracking system

---

## Edge Cases & Constraints

- **Overlapping Requests**: If multiple people request same dates, first-come-first-served with others getting decline notice
- **Owner Non-Response**: Requests expire after 48 hours and borrower is notified
- **Date Conflicts**: System prevents requests during periods when tool is already loaned out
- **Rapid-Fire Requests**: Users can only have 3 pending outbound requests at once to prevent spam
- **Communication Abuse**: Profanity filter and user blocking capabilities required
- **Agreement Changes**: Post-approval changes require mutual consent and generate new agreement versions

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- Payment processing or security deposits (handled separately if needed)
- Calendar integration or advanced scheduling
- Automated delivery coordination (handled through messaging)
- Tool availability forecasting or smart date suggestions
- Integration with external messaging platforms
- Video calling or advanced communication features

---

## Dependencies

**Depends On**: 
- Tool Inventory Management (need tools to request)
- User authentication and profiles (need verified users)
- Basic notification system (email/push capability)

**Enables**: 
- Loan Tracking & Returns (creates active loans to track)
- Reputation/Rating System (provides transaction history to rate)
- Community analytics (provides usage data)

---

## Open Questions for Tech Lead

- Should we support recurring/repeated requests (same tool, same borrower, regular schedule)?
- What's the appropriate database indexing strategy for request searches (by user, by tool, by date range)?
- How should we handle timezone considerations for pickup/return times?
- What's the expected volume of concurrent requests to plan for (database locking considerations)?