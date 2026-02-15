# Loan Tracking & Returns - Technical Review (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: February 15, 2025

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. All critical questions from the previous iteration have been answered clearly and comprehensively. The v1.1 update provides explicit guidance on data models, business logic, user workflows, and edge case handling.

## What's Clear

### Data Model
- **Loan Entity**: 7 explicit status states (Active, DueSoon, Overdue, ReturnPending, ReturnDisputed, Completed, Lost) with clear transition rules
- **Photo Requirements**: Exactly 3 photos at pickup and return, stored with loan_id and photo_order (1,2,3)
- **Extension Tracking**: Formal LoanExtension entity with approval workflow and audit trail
- **Status History**: Complete audit trail of all loan state changes with timestamps and user actions
- **Foreign Key Relationships**: Loan → User (owner), User (borrower), Tool with clear cardinality

### Business Logic
- **Loan Creation**: Triggered at physical pickup with condition photos (not at request approval)
- **Auto-transitions**: Active → DueSoon (3 days before due), DueSoon → Overdue (day after due)
- **Owner Confirmation**: 7-day window with auto-closure if no response
- **Lost Tool Process**: Owner can mark after 7 days overdue, automatic after 30 days
- **Extension Workflow**: Borrower requests → Owner approves/denies → Clear audit trail
- **Photo Retention**: Delete after 1 year, preserve metadata indefinitely

### API Design
- **Status Endpoints**: GET /api/v1/loans/{id}/status, PUT /api/v1/loans/{id}/status
- **Photo Upload**: POST /api/v1/loans/{id}/photos with multipart form data
- **Extension Requests**: POST /api/v1/loans/{id}/extensions, PUT /api/v1/extensions/{id}/approve
- **Dashboard Data**: GET /api/v1/loans/active (filtered by owner/borrower)
- **Return Process**: PUT /api/v1/loans/{id}/return (borrower), PUT /api/v1/loans/{id}/confirm-return (owner)

### UI/UX
- **Dashboard Views**: Owner sees tools loaned out, borrower sees tools borrowed, color-coded by days remaining
- **Photo Comparison**: Side-by-side pickup vs return photos during return process
- **Reminder Content**: Specific email templates with return location, contact info, and instructions
- **Extension UI**: Clear request form with reason field and approval/denial workflow
- **Status Indicators**: Visual distinction between all 7 loan states in user interface

### Edge Cases
- **Photo Quality**: Minimum standards enforced with retry mechanism
- **Email Delivery**: 3 retry attempts with failure logging
- **Timezone Handling**: UTC storage, local display, location-based reminder timing
- **No-Show Pickups**: Request expires after 48 hours without loan creation
- **Concurrent Operations**: State machine prevents invalid transitions
- **Account Deletion**: Immediate photo cleanup for privacy compliance

## Implementation Notes

**Database**:
- Loan table with status ENUM (Active, DueSoon, Overdue, ReturnPending, ReturnDisputed, Completed, Lost)
- LoanPhoto table with exactly 3 photos per pickup/return session
- LoanStatusHistory for complete audit trail
- LoanExtension for formal approval workflow
- Foreign keys: Loan → Users (owner_id, borrower_id), Loan → Tools (tool_id)

**Authorization**:
- Only loan owner can mark as lost or confirm returns
- Only borrower can initiate return or request extensions
- Both parties can view loan details and photo history
- Platform admins can override for dispute resolution

**Validation**:
- Exactly 3 photos required for pickup and return
- Photo quality minimums (lighting, focus) enforced
- Extension requests limited to 7 days maximum
- Status transitions follow state machine rules strictly

**Background Jobs**:
- Daily job for status transitions (Active → DueSoon → Overdue)
- Email reminder scheduling (48hr, 24hr, day-of)
- Auto-closure after 7 days in ReturnPending
- Photo cleanup after 1 year retention period
- Automatic lost marking after 30 days overdue

**Key Decisions**:
- Email-only notifications (no push notifications in v1)
- 7-day owner confirmation window with auto-closure
- 1-year photo retention policy
- Exactly 3 photos per documentation session
- State machine with 7 explicit status values
- Extension approval required from owner

## Recommended Next Steps

1. Create detailed engineering specification with:
   - Complete database schema with indexes
   - API endpoint specifications with request/response schemas
   - Background job scheduling and retry policies
   - Email template designs and delivery configuration

2. Set up infrastructure dependencies:
   - Background job processing (Hangfire)
   - Email delivery service integration
   - Photo storage configuration (Azure Blob/S3)
   - Redis caching for dashboard performance

---

**This feature is ready for detailed engineering specification.**