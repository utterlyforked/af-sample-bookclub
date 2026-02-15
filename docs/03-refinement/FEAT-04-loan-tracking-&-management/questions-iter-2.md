# Loan Tracking & Management - Technical Review (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: December 19, 2024

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. All critical questions from the initial review have been answered clearly in v1.1, providing unambiguous guidance for core functionality, edge cases, and business logic.

## What's Clear

### Data Model
- Loan entity with status enum (Pending, Active, Completed, Cancelled, Disputed Return)
- Due dates stored as TIMESTAMPTZ (end-of-day in user's timezone)
- Extension tracking with request counter (max 2 per loan)
- Return confirmation workflow with borrower initiation + owner confirmation
- Complete loan history retention regardless of completion status
- User loan limits: 5 active borrowed, 10 active lent (enforced at request submission)

### Business Logic
- **Loan Activation**: Immediate when owner accepts request (no pickup confirmation)
- **Due Date Handling**: Date-only UI, 11:59 PM system processing in user timezone
- **Return Process**: Borrower marks returned → Owner confirms → Status = Completed
- **Extension Rules**: Max 2 requests per loan (denied requests count toward limit)
- **Overdue Logic**: Notifications at 1 day and 3 days overdue, then no more automated messages
- **Dispute Handling**: After 7 days without return confirmation → "Disputed Return" status

### API Design
- Loan CRUD with status transitions
- Return confirmation endpoints (borrower initiate, owner confirm)
- Extension request/approval workflow
- Loan history with filtering (status, date range, tool type, other party)
- Overdue loan queries for notification system
- Loan limit validation at request submission

### UI/UX
- Dashboard showing active loans with due dates and contact info
- Clear status indicators throughout loan history (✅❌⚠️🔄)
- Extension counter display ("1 of 2 extensions used")
- Immediate feedback for loan limit violations
- Optional notes on return confirmation
- Tool listings show loan status ("Currently on loan, returns [date]")

### Edge Cases
- **Never picked up**: Owner can mark as "Cancelled" with reason
- **Confirmation timeout**: Reminders at 48 hours, dispute flag at 7 days
- **Overdue escalation**: Owner can mark "Lost/Unreturned" after 7 days
- **Limit edge cases**: Only "Active" loans count, not "Pending" requests
- **Timezone handling**: All comparisons in UTC, display in user timezone

## Implementation Notes

**Database**:
- Loans table with foreign keys to Users (borrower_id, lender_id) and Tools (tool_id)
- Status enum: Pending, Active, Completed, Cancelled, Disputed Return
- Extension counter (tinyint, max 2)
- Due date as TIMESTAMPTZ
- Return confirmation fields (borrower_marked_returned_at, owner_confirmed_at)

**Authorization**:
- Only borrowers can mark loans as returned
- Only tool owners can confirm returns and approve extensions
- Both parties can view loan details and history
- Users can only see their own loans (borrowed or lent)

**Validation**:
- Loan limits checked at request submission (5 borrowed, 10 lent active)
- Extension requests blocked after 2 attempts
- Due dates must be future dates when creating loan
- Return confirmation requires active loan status

**Key Decisions**:
- Immediate loan activation (no pickup confirmation)
- Date-only due dates with end-of-day processing
- Borrower-initiated return confirmation
- Two-strike overdue notification policy
- Complete loan history retention

**Background Jobs**:
- Daily job for due date reminders (1 day before, day of)
- Daily job for overdue notifications (1 day, 3 days after)
- Weekly cleanup job for disputed return escalation

## Recommended Next Steps

1. Create engineering specification with detailed implementation plan
2. Design database schema with proper indexes for loan queries
3. Set up Hangfire background jobs for notification system
4. Plan notification templates and delivery mechanism

---

**This feature is ready for detailed engineering specification.**