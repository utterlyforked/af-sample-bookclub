# Borrowing Request System - Feature Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: request state machine, data model separation, communication boundaries)

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

## Acceptance Criteria (UPDATED v1.1)

- Borrowers can request tools with proposed start/end dates, intended use, and pickup preferences
- Only non-overlapping date requests are allowed - system blocks conflicting date submissions
- Tool owners receive notifications and can approve, decline, or counter-propose dates
- Counter-proposals require borrower acceptance before creating final agreement
- Approved loans create a binding agreement with pickup location, expected return condition, and any deposits required
- Both parties can message each other through the app with image attachments (5MB limit)
- Request status is always clear with defined states: pending, approved, declined, expired, counter_proposed, awaiting_borrower_response
- Only one active request per borrower per tool at a time
- Requests expire after 48 hours if no owner response
- Maximum 100 messages per request thread with 1000 character limit per message

---

## Detailed Specifications (UPDATED v1.1)

**Request Approval Workflow**

**Decision**: Counter-proposals require borrower acceptance before creating final agreement

**Rationale**: Both parties must agree to final terms for a binding agreement. This prevents situations where owners make changes the borrower didn't approve, which could lead to disputes or no-shows.

**Examples**:
- Owner receives request for "March 15-17" but counters with "March 16-18"
- System moves request to "counter_proposed" state and notifies borrower
- Borrower can accept (creates agreement) or decline (request becomes "declined")
- If borrower doesn't respond within 24 hours, counter-proposal expires

**Edge Cases**:
- Multiple counter-proposals: Only one active counter-proposal allowed - new one replaces previous
- Owner changes mind: Can decline their own counter-proposal before borrower responds

---

**Date Conflict Prevention**

**Decision**: Block overlapping requests at submission time

**Rationale**: Prevents user confusion and disappointment. Better to show "unavailable" immediately than let someone submit a request that will auto-decline. Creates clearer expectations for both parties.

**Examples**:
- Tool already requested for March 15-20
- New borrower tries to request March 17-22
- System shows "Tool unavailable for selected dates" with calendar showing conflicts
- Borrower can choose different dates or abandon request

**Edge Cases**:
- Existing request gets declined: Dates immediately become available for new requests
- Request expires: 5-minute grace period before dates become available (prevents race conditions)

---

**Request State Management**

**Decision**: Six distinct states with clear transitions between them

**Rationale**: Each state represents a specific point in the negotiation process where different actions are available. Clear state machine prevents impossible transitions and makes UI logic straightforward.

**State Definitions**:
- **pending**: Initial state, awaiting owner response
- **counter_proposed**: Owner suggested changes, awaiting borrower response
- **awaiting_borrower_response**: Generic state for any borrower action needed
- **approved**: Owner approved, creating loan agreement
- **declined**: Request rejected by either party
- **expired**: 48 hours passed without required response

**State Transitions**:
```
pending → counter_proposed (owner counters)
pending → approved (owner approves as-is)
pending → declined (owner declines)
pending → expired (48 hours, no response)

counter_proposed → approved (borrower accepts)
counter_proposed → declined (borrower rejects)
counter_proposed → expired (24 hours, no borrower response)
```

---

**Data Model Architecture**

**Decision**: Separate BorrowRequest and LoanAgreement entities

**Rationale**: Clean separation of concerns. BorrowRequest handles negotiation phase with multiple possible outcomes. LoanAgreement handles active loan tracking. This makes queries cleaner and allows different data retention policies.

**BorrowRequest Entity**:
- Handles negotiation lifecycle
- Contains all proposal/counter-proposal data
- Links to communication thread
- Archived after completion

**LoanAgreement Entity**:
- Created only when request approved
- Contains finalized terms and conditions
- Links to loan tracking system
- Permanent record for dispute resolution

**Relationship**:
- One-to-zero-or-one (request may not result in agreement)
- Foreign key from LoanAgreement to BorrowRequest

---

**Required Request Fields**

**Decision**: Minimal required fields - start_date, end_date, intended_use only

**Rationale**: Reduces friction for request submission while capturing essential information. Optional fields can be added based on user feedback. Most important data for owner decision-making is what the tool will be used for.

**Required Fields**:
- start_date (must be future date)
- end_date (must be after start_date, within tool's max_loan_duration)
- intended_use (text, 50-500 characters)

**Optional Fields**:
- pickup_time_preference (morning/afternoon/evening)
- special_requests (text, up to 200 characters)

**Validation**:
- Date range cannot exceed tool owner's max_loan_duration setting
- intended_use must be family-friendly (profanity filter)
- Cannot have multiple pending requests for same tool

---

**Communication System**

**Decision**: Image attachments only, 5MB limit per image, stored in blob storage

**Rationale**: Covers primary use case (showing tool condition, project context) without security risks of arbitrary file uploads. 5MB allows high-quality photos while preventing abuse.

**Message Specifications**:
- Maximum 1000 characters per message
- Maximum 100 messages per request thread
- Image attachments: JPG, PNG, WebP only
- 5MB per image, 3 images per message
- Images automatically compressed and resized

**Storage**:
- Images stored in blob storage with request-scoped access
- Messages stored in database with foreign key to BorrowRequest
- 90-day retention after loan completion

---

**Automatic Approval**

**Decision**: No automatic approval in MVP

**Rationale**: Keeps initial implementation simple and focused. Tool lending involves trust and property protection - owners should actively approve each request initially. Can add auto-approval rules in v2 based on user feedback about repetitive approvals.

**Future Consideration**: 
V2 could include simple auto-approval checkbox: "Automatically approve requests from borrowers with 4+ star rating" with ability to set maximum loan duration for auto-approval.

---

## Q&A History

### Iteration 1 - February 15, 2025

**Q1: What exactly happens when a request is "approved with changes"?**  
**A**: Changes go back to borrower for acceptance/rejection. Request moves to "counter_proposed" state, borrower has 24 hours to accept or decline. This ensures both parties agree to final terms.

**Q2: Can multiple users request the same tool for overlapping dates?**  
**A**: No. System blocks overlapping requests at submission time, showing "Tool unavailable for selected dates" with calendar conflicts. Prevents user confusion and disappointment.

**Q3: What are the exact states a BorrowRequest can have?**  
**A**: Six states: pending, counter_proposed, awaiting_borrower_response, approved, declined, expired. Each state has specific transitions and available actions.

**Q4: Are BorrowRequest and LoanAgreement separate database entities?**  
**A**: Yes, separate entities. BorrowRequest handles negotiation, LoanAgreement created only when approved. Clean separation of concerns and different data retention needs.

**Q5: What specific data is required vs optional in a borrow request?**  
**A**: Required: start_date, end_date, intended_use. Optional: pickup_time_preference, special_requests. Minimal friction while capturing essential decision-making information.

**Q6: How should we handle message attachments and storage?**  
**A**: Image attachments only (JPG, PNG, WebP), 5MB limit, stored in blob storage. Covers main use case without security risks of arbitrary files.

**Q7: What's the maximum message length and conversation limits?**  
**A**: 1000 characters per message, 100 messages per request thread. Should handle legitimate conversations while preventing abuse.

**Q8: Should automatic approval rules be part of MVP?**  
**A**: No. Keep MVP simple, owners actively approve each request. Can add auto-approval rules in v2 based on usage patterns and user feedback.

---

## Product Rationale

**Why Counter-Proposals Require Acceptance?**  
Prevents disputes and ensures both parties are committed to the final terms. A borrower who didn't agree to changes is more likely to not show up or be dissatisfied with the arrangement.

**Why Block Overlapping Requests?**  
Better user experience to show unavailability immediately rather than accept requests that will be auto-declined. Creates clearer expectations and reduces disappointment.

**Why Separate Request and Agreement Entities?**  
Different lifecycles and data needs. Requests are negotiation tools that can be archived; agreements are permanent records for active loans and dispute resolution.

**Why Minimal Required Fields?**  
Reduces friction for request submission. The most important factor for owner decisions is understanding what the tool will be used for - other details can be discussed through messaging if needed.

**Why Image-Only Attachments?**  
Covers 90% of use cases (showing project context, tool condition) while avoiding security risks of arbitrary file uploads. Simpler implementation and storage management.

**Why No Auto-Approval in MVP?**  
Tool lending involves significant trust. Better to start with active owner involvement and add automation based on real usage patterns rather than assumptions about what owners want automated.