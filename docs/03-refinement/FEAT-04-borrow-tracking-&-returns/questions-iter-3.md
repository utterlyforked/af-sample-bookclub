# Borrow Tracking & Returns - Technical Review (Iteration 3)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 3
**Date**: 2025-01-14

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. After two rounds of clarifications, all critical questions have been answered clearly. The spec now provides unambiguous guidance on data flow, business rules, edge cases, and user experience.

## What's Clear

### Data Model

- **Borrow entity** with complete lifecycle tracking:
  - Status transitions: Active → PendingReturnConfirmation → Completed
  - Dual due dates: OriginalDueDate (immutable) + CurrentDueDate (updated by extensions)
  - Owner timezone stored (IANA format) for consistent time calculations
  - ReturnMarkedDate and ReturnConfirmedDate for workflow tracking
  
- **ExtensionRequest** with timeout mechanism:
  - 72-hour expiration with Status = TimedOut if no owner response
  - Counter-offer support via Type enum (Initial vs CounterOffer)
  - Max 14 days per extension, max 28 days cumulative duration
  - No limit on number of extension attempts
  
- **ReturnConfirmation** with dispute handling:
  - Condition enum: Good vs HasIssues
  - BorrowerRebuttal field (max 500 chars) for damage disputes
  - RebuttalAddedAt timestamp, 30-day window for adding rebuttals
  - AutoConfirmed boolean flag for 7-day auto-confirmation cases
  - ConfirmedBy can be OwnerId or System user for auto-confirms
  - Photos stored as JSON array (max 5), only allowed when HasIssues
  
- **Notification & Reminder tracking**:
  - BorrowReminder entity prevents duplicate reminders
  - Notification entity for in-app notification center
  - EmailDeliveryLog tracks email success/failure for reliability monitoring
  - DeliveredVia enum tracks dual-channel delivery (Email, InApp, Both)

### Business Logic

- **Due time specificity**: All borrows due at 6:00 PM (18:00) in owner's local timezone
  
- **Overdue thresholds clearly defined**:
  - Day 0 (due date after 6 PM): Yellow "Due Today" → Yellow "1 Day Overdue"
  - Days 1-2: Yellow badges, yellow-orange UI styling
  - Days 3+: Red badges, red UI styling, more urgent messaging
  - Days 7+: Escalation notification to both parties
  
- **Auto-confirmation logic**:
  - Triggers exactly 7 days (168 hours) after ReturnMarkedDate
  - Background job runs daily at 2:00 AM UTC
  - Creates ReturnConfirmation with Condition=Good, ConfirmedBy=System, AutoConfirmed=true
  - Both parties notified, tool returns to Available status
  - Borrower not penalized in trust score (treated same as owner-confirmed)
  
- **Extension request timeout**:
  - Expires after 72 hours with no owner response
  - Background job marks as TimedOut, borrower notified
  - UI shows countdown timer for borrower
  - Can request again after timeout (no blocking)
  
- **Damage dispute process**:
  - Owner reports issues → Borrower notified → Borrower can add rebuttal within 30 days
  - Rebuttal optional, one-time only, max 500 characters
  - Both perspectives visible in transaction history permanently
  - Future trust system can weight disputed vs undisputed damage differently
  
- **Late return consequences (v1)**:
  - No automatic restrictions or suspensions
  - No monetary penalties
  - Documented in transaction history: "Returned 3 days late"
  - Visible to owners when reviewing future borrow requests
  - Data collected for future reputation system enhancements

### API Design

**Borrower Actions**:
- `POST /api/v1/borrows/{id}/mark-returned` - Mark tool as returned (optional return notes)
- `POST /api/v1/borrows/{id}/extension-requests` - Request extension (new due date + reason)
- `POST /api/v1/return-confirmations/{id}/rebuttal` - Add rebuttal to damage report
- `POST /api/v1/borrows/{id}/notes` - Add private note to transaction
- `GET /api/v1/borrows/active` - Get active borrows for logged-in user
- `GET /api/v1/borrows/history` - Get transaction history with filters

**Owner Actions**:
- `POST /api/v1/return-confirmations` - Confirm return (condition, photos, notes)
- `PUT /api/v1/extension-requests/{id}/approve` - Approve extension
- `PUT /api/v1/extension-requests/{id}/deny` - Deny extension (reason required)
- `PUT /api/v1/extension-requests/{id}/counter-offer` - Counter with different date

**System**:
- Background job: Auto-confirm returns after 7 days
- Background job: Timeout extension requests after 72 hours
- Background job: Send reminders at 9:00 AM owner-timezone (runs hourly)
- Background job: Calculate overdue statuses (runs every 15 minutes)

### UI/UX

- **Dashboard tabs**: "I'm Borrowing" and "I'm Lending" with count badges
- **Active borrow display**: Tool photo, name, other party, dates, days remaining, status indicator
- **Overdue visual escalation**: Yellow (1-2 days) → Red (3+ days) with badge colors matching
- **Notification center**: Bell icon with unread count, dropdown with recent 10, full page view with filters
- **Dual-channel notifications**: All reminders sent via email + in-app for redundancy
- **Return confirmation modal**: Two-path UI (Good condition vs Has issues) with dynamic photo upload area
- **Extension request UI**: Date picker limited to max 14 days out, 28-day cumulative check, countdown timer for pending requests
- **Transaction history**: Searchable, filterable, paginated (20 per page), with timeline view in details

### Edge Cases

- **Owner doesn't confirm return**: 7-day auto-confirmation with visible "(Auto-confirmed)" label
- **Extension request ignored**: 72-hour timeout with "Timed Out" status, borrower notified
- **Damage dispute**: Borrower can add rebuttal within 30 days, both sides preserved permanently
- **Email delivery failure**: Logged in EmailDeliveryLog, user still gets in-app notification
- **Multiple extension requests**: Only one pending at a time, must wait for response or timeout
- **Extension during overdue**: Allowed if 1-2 days late, blocked if 3+ days overdue
- **Photos for good condition**: Upload area hidden in UI, validation prevents photo upload if Condition=Good
- **Transaction data retention**: Permanent retention, no automatic deletion, users cannot self-delete
- **Timezone consistency**: All calculations use owner's timezone (stored in Borrow.OwnerTimezone)
- **Concurrent operations**: Return marked + Extension request pending = Extension ignored, return workflow takes precedence

### Validation Rules

- Extension reason: Required, max 500 characters
- Extension new due date: Must be after CurrentDueDate, max 14 days from request, total duration ≤ 28 days
- Return notes (borrower): Optional, max 300 characters
- Owner notes (good condition): Optional, max 300 characters
- Issue description: Required if Condition=HasIssues, max 1000 characters
- Damage photos: Max 5, max 10MB each, JPEG/PNG only, only when HasIssues selected
- Borrower rebuttal: Optional, max 500 characters, one-time only, within 30 days of return confirmation
- Private notes: Max 500 characters
- Owner response to extension: Max 500 characters if denying

### Authorization

- **Mark as returned**: Only borrower of that specific borrow
- **Confirm return**: Only owner of that specific borrow
- **Request extension**: Only borrower, only if Status=Active, only if not 3+ days overdue
- **Approve/deny extension**: Only owner, only if request Status=Pending
- **Add rebuttal**: Only borrower, only if ReturnConfirmation.Condition=HasIssues, only within 30 days
- **Add private note**: Only the user who is either borrower or owner of that transaction
- **View active borrows**: User sees only their own (as borrower or owner)
- **View transaction history**: User sees only transactions where they are borrower or owner
- **View notification center**: User sees only their own notifications

### Key Decisions

- **Due time**: Fixed at 6:00 PM owner-timezone for consistency and clarity
- **Reminder timing**: 9:00 AM owner-timezone for all reminders (predictable, morning timing)
- **Auto-confirmation**: 7 days for owner response (balances accountability with grace period)
- **Extension timeout**: 72 hours for owner response (3 days reasonable, prevents indefinite pending)
- **Extension limits**: 14 days per request, 28 days total (prevents indefinite borrowing)
- **Rebuttal window**: 30 days to add rebuttal (reasonable time to notice and respond)
- **Late return handling**: No automatic penalties in v1 (data collection phase for future reputation system)
- **Photo upload**: Only for damage reports (prevents bloat, focuses on issues)
- **Data retention**: Permanent (dispute resolution, pattern detection, trust signals)
- **Notification redundancy**: Email + in-app dual delivery (reliability over email-only)
- **Overdue during extension**: Allowed if 1-2 days late (flexibility), blocked if 3+ (too late)

## Implementation Notes

**Database**:
- `Borrow` table with `OwnerTimezone` string field (IANA format)
- `CurrentDueDate` separate from `OriginalDueDate` for extension tracking
- `ExtensionRequest.ExpiresAt` calculated field (RequestedDate + 72h)
- `ReturnConfirmation.AutoConfirmed` boolean for 7-day auto-confirm cases
- `ReturnConfirmation.BorrowerRebuttal` and `RebuttalAddedAt` for dispute handling
- `BorrowReminder` deduplication table to prevent duplicate notifications
- `Notification` table for in-app notification center
- `EmailDeliveryLog` for email reliability monitoring
- Indexes: `(UserId, Status, ReturnConfirmedDate DESC)` for history queries
- Indexes: `(Status, ReturnMarkedDate)` for auto-confirmation job
- Indexes: `(Status, RequestedDate)` for extension timeout job

**Background Jobs (Hangfire)**:
- **Auto-confirm returns**: Daily at 2:00 AM UTC, query `Status=PendingReturnConfirmation AND ReturnMarkedDate < UtcNow - 7 days`
- **Timeout extensions**: Daily at 2:00 AM UTC, query `Status=Pending AND RequestedDate + 72h < UtcNow`
- **Send reminders**: Runs hourly, queries borrows due tomorrow/today in timezones where it's currently 9:00 AM
- **Calculate overdue**: Runs every 15 minutes, updates overdue badges based on CurrentDueDate + 18h in owner timezone

**Timezone Handling**:
- Store owner's timezone in `Borrow.OwnerTimezone` on creation (from User profile)
- All due date calculations use `CurrentDueDate.ToOwnerTimezone().AddHours(18)` for 6 PM due time
- Reminder job converts UTC → owner timezone to find 9:00 AM send time
- Display all dates in owner's timezone in UI for consistency

**Notification Delivery**:
- Create `Notification` record first (in-app)
- Send email asynchronously via background job
- Log email attempt in `EmailDeliveryLog` with Status=Sent/Bounced/Failed
- If email fails, user still has in-app notification (graceful degradation)
- Frontend polls notification API every 60s or uses WebSocket for real-time updates

**Photo Storage**:
- Upload to Azure Blob Storage (or S3) in `/damage-reports/{BorrowId}/` folder
- Generate presigned URLs with 1-hour expiration for viewing
- Store URLs as JSON array in `ReturnConfirmation.Photos` field
- Validate file size (max 10MB), type (JPEG/PNG only), count (max 5) before upload
- Only show upload UI when "Has issues" radio selected (dynamic form)

**Security**:
- Validate UserId from JWT matches BorrowerId/OwnerId for all actions
- Check borrow Status before allowing actions (e.g., can't mark returned if already Completed)
- Check extension eligibility (not 3+ days overdue, no pending request)
- Check rebuttal eligibility (HasIssues condition, within 30 days, not already submitted)
- Sanitize all user input (HTML encode descriptions, notes, reasons)

**Performance**:
- Paginate transaction history (20 per page)
- Index `(UserId, Status)` for fast active borrow queries
- Cache notification count in Redis (key: `notif:count:{UserId}`, TTL: 60s)
- Batch reminder sends (process 100 borrows at a time to avoid memory issues)
- Consider read replicas for transaction history queries if volume grows

## Recommended Next Steps

1. **Create engineering specification** with:
   - Detailed database schema (all fields, types, indexes, constraints)
   - API endpoint specifications (request/response DTOs, status codes, error responses)
   - Background job implementation details (scheduling, error handling, retry logic)
   - Frontend component breakdown (pages, modals, forms, state management)
   - Timezone conversion utility functions
   - Photo upload service integration
   
2. **Set up Hangfire** for background jobs:
   - Configure recurring jobs for auto-confirm, timeout, reminders, overdue calculations
   - Set up job dashboard for monitoring
   - Implement idempotency (use BorrowReminder table to prevent duplicate sends)
   
3. **Implement notification system**:
   - Notification API endpoints (list, mark read, count)
   - Email templates for all notification types
   - In-app notification UI component
   - WebSocket or polling mechanism for real-time updates
   
4. **Build dual-channel delivery**:
   - Notification service that sends both email + in-app
   - EmailDeliveryLog tracking
   - Admin dashboard for monitoring email failures

---

**This feature is ready for detailed engineering specification and implementation.**