# Borrowing Request & Communication System - Technical Questions (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: December 19, 2024

---

## Summary

After reviewing the v1.1 specification and the comprehensive Q&A from Iteration 1, this feature specification is sufficiently detailed to proceed with implementation. All critical questions have been answered clearly, and the product requirements provide unambiguous guidance for engineering decisions.

## What's Clear

### Data Model
- **BorrowingRequest** entity with status enum (Pending, Approved, Declined, Active, PendingReturn, Returned)
- **Message** entity for threaded communication within requests
- **RequestStatus** enumeration with specific state transitions
- Clear relationships: User→BorrowingRequest (borrower/lender), Tool→BorrowingRequest, BorrowingRequest→Message
- Specific constraints: max 10 pending requests per user, one pending request per tool per user
- Required fields: project description, start/end dates, pickup preferences, return timestamps

### Business Logic
- **Request Limits**: Exactly 10 pending requests maximum per user (Pending + Approved status)
- **Conflict Prevention**: System blocks new requests that overlap with existing approved loans
- **Auto-decline**: Fixed 48-hour timeout from request creation, timer resets on owner messages
- **Return Process**: Borrower initiates → Owner has 24 hours to confirm → Auto-confirms if no response
- **Status Transitions**: Clear workflow from Pending → Approved/Declined → Active → PendingReturn → Returned

### Authorization
- Only request participants (borrower + tool owner) can view message history
- Borrowers can cancel their own pending requests
- Tool owners can approve/decline requests for their tools
- Both parties can mark pickup/return events
- Admin receives reports but participants remain anonymous to each other

### UI/UX Specifications
- **Request Form**: Project description, date picker with conflict validation, pickup preferences
- **Owner Dashboard**: Request notifications with borrower profile preview
- **Messaging Interface**: Threaded conversation with immediate email notifications (user can disable)
- **Status Tracking**: Clear visual indicators for request progression
- **Conflict Prevention**: Show "Next available: June 6+" when dates conflict
- **Request Limits**: Display "Pending requests: 7/10" counter in user dashboard

### Edge Cases Addressed
- Same-day return/pickup allowed (no gap required)
- Partial responses (messages without approval) reset auto-decline timer  
- Double-booking prevention through date conflict validation
- Non-responsive owners handled via auto-confirmation
- Request spam prevented through 10-request limit
- Message abuse handled through admin reporting system

## Implementation Notes

**Database Schema**:
- BorrowingRequest table with foreign keys to Users (borrower_id, lender_id) and Tools (tool_id)
- Unique constraint on (tool_id, borrower_id) for pending requests only
- Message table with foreign key to BorrowingRequest (request_id)
- Status enum: Pending, Approved, Declined, Active, PendingReturn, Returned
- Timestamps: created_at, auto_decline_at (computed), return_initiated_at, confirmed_at

**Authorization Rules**:
- Request visibility: borrower + tool owner only
- Request creation: authenticated users with <10 pending requests
- Request approval/decline: tool owners only
- Message access: request participants only
- Return confirmation: borrower initiates, owner confirms

**Validation Rules**:
- Project description: required, max 2000 characters
- Date range: start_date < end_date, start_date >= today
- Pickup preferences: optional text field, max 500 characters
- Conflict validation: no overlap with approved loans for same tool
- Request limit: count pending + approved requests < 10

**Key Business Rules**:
- One pending request per tool per user (must cancel to resubmit)
- 48-hour auto-decline from request creation
- 24-hour return confirmation window with auto-confirm fallback
- Immediate email notifications for all messages (user setting to disable)
- Date conflicts block request submission with available date display

**Notification System**:
- Email triggers: new request, approval/decline, new message, return requests
- User preference: email_notifications_enabled (default: true)
- Admin reporting: simple email alert with message content and context

## Recommended Next Steps

1. Create detailed engineering specification with:
   - Entity Framework models and configurations
   - API endpoint specifications with request/response models  
   - Background job setup for auto-decline and auto-confirm
   - Email notification templates and delivery system

2. Set up initial database migrations with proper indexes for:
   - Date range conflict queries
   - Pending request count queries
   - Message threading and ordering

---

**This feature is ready for detailed engineering specification.**

The v1.1 iteration successfully addressed all ambiguities from the initial review. The product requirements now provide clear, implementable guidance for data models, business logic, user workflows, and edge case handling. The comprehensive Q&A section eliminates any remaining uncertainty about expected behavior.