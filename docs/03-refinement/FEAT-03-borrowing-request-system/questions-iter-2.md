# Borrowing Request System - Technical Review (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: February 15, 2025

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. All critical questions from the first iteration have been answered clearly, and the updated v1.1 specification provides concrete guidance on data models, business logic, state management, and edge case handling.

## What's Clear

### Data Model
- **BorrowRequest** entity with fields: start_date, end_date, intended_use (required), pickup_time_preference, special_requests (optional)
- **LoanAgreement** entity (separate from BorrowRequest) created only when approved
- **Message** entity linked to BorrowRequest with 1000 char limit, image attachments
- One-to-zero-or-one relationship: BorrowRequest → LoanAgreement
- Foreign key constraints and request-scoped access for images

### Business Logic
- **State Machine**: Six states (pending, counter_proposed, awaiting_borrower_response, approved, declined, expired) with defined transitions
- **Date Conflict Prevention**: Block overlapping requests at submission time with immediate feedback
- **Counter-Proposal Flow**: Owner changes require borrower acceptance before creating agreement
- **Expiration Rules**: 48 hours for initial owner response, 24 hours for borrower response to counter-proposals
- **Request Limits**: One active request per borrower per tool

### API Design
- Date validation: start_date must be future, end_date after start_date, within max_loan_duration
- Request blocking for overlapping dates with calendar conflict display
- State transition endpoints following defined state machine
- Image upload with format restrictions (JPG, PNG, WebP) and 5MB limit
- Message threading with 100 message limit per request

### Authorization
- Tool owners can approve, decline, or counter-propose on their tools
- Borrowers can accept/decline counter-proposals
- Both parties can message within request thread
- Request-scoped image access (only parties involved can view)

### Edge Cases
- **Multiple Counter-Proposals**: New counter-proposal replaces previous (only one active)
- **Owner Mind Changes**: Can decline own counter-proposal before borrower responds
- **Request Expiration**: 5-minute grace period before dates become available (prevents race conditions)
- **Concurrent Requests**: System blocks at submission time, not approval time

## Implementation Notes

**Database**:
- BorrowRequest table with status enum, foreign key to Tool and User
- LoanAgreement table with foreign key to BorrowRequest (nullable initially)
- Message table with foreign key to BorrowRequest, image URLs stored
- Unique constraint preventing multiple pending requests per (borrower_id, tool_id)

**Authorization**:
- Tool owners control all approval/decline/counter-proposal actions
- Borrowers control counter-proposal acceptance/rejection
- Both parties have equal messaging rights within request scope

**Validation**:
- intended_use: 50-500 characters with profanity filter
- special_requests: max 200 characters
- Date ranges cannot exceed tool's max_loan_duration setting
- Image validation: file type, size (5MB), 3 per message maximum

**Key Decisions**:
- No automatic approval in MVP (owner must actively approve each request)
- Image-only attachments (no arbitrary file uploads)
- Counter-proposals require explicit borrower acceptance
- Separate entities for negotiation (BorrowRequest) vs active loans (LoanAgreement)

## Recommended Next Steps

1. Create engineering specification with detailed API endpoints and database schema
2. Set up blob storage configuration for image attachments
3. Design notification system for request state changes
4. Plan integration points with existing Tool and User entities

---

**This feature is ready for detailed engineering specification.**