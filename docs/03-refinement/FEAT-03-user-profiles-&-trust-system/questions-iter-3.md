# User Profiles & Trust System - Technical Review (Iteration 3)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 3
**Date**: 2025-01-10

---

## Summary

This feature specification is **sufficiently detailed to proceed with implementation**. All critical questions from iterations 1 and 2 have been answered with clear, specific decisions. The spec now provides unambiguous guidance on:

- Transaction completion mechanics and due date immutability
- Rating window calculations and timezone handling
- Problem report workflows and status transitions
- Concurrent rating submissions and visibility logic
- Phone verification security limits
- Profile statistics caching strategy
- Text sanitization and character counting

The remaining implementation decisions (database schema details, service layer architecture, specific library choices) are appropriately left to the engineering specification phase.

---

## What's Clear

### Data Model

**Users Table**:
- Core fields: `full_name`, `email` (unique), `neighborhood`, `city`, `bio` (max 300 chars), `profile_photo_url`
- Verification badges: `email_verified` (required), `phone_verified` (optional), `address_verified` (optional)
- Phone: stored as `phone_number VARCHAR(15)` in E.164 format (+1XXXXXXXXXX)
- Security tracking: `phone_verification_attempts JSONB` with structure `{sms_sends: [], wrong_codes: [], locked_until: null}`
- Cached statistics: `cached_tools_owned`, `cached_tools_shared`, `cached_current_borrows`, `cached_average_rating DECIMAL(3,2)`, `cached_rating_count`, `stats_last_updated`
- Audit: `created_at`, `updated_at`, `deleted_at` (soft delete)

**Transactions Table** (owned by FEAT-02/FEAT-04 but impacts this feature):
- Status transitions: `Active` → `Return Initiated` → `Returned - Confirmed` → rating window opens
- Time fields: `due_date` (immutable), `auto_confirm_at` (due_date + 14 days), `confirmed_at`, `rating_window_closes_at` (confirmed_at + 168 hours)
- Problem reports: `problem_report_id INT NULL` references separate `problem_reports` table

**Ratings Table**:
- Bidirectional: both `rater_id` and `rated_user_id` on same transaction
- Fields: `transaction_id`, `rater_id`, `rated_user_id`, `stars INT (1-5)`, `review TEXT (max 500 chars)`, `visible BOOLEAN`, `created_at`
- Unique constraint: `(transaction_id, rater_id)` prevents duplicate ratings
- Visibility logic: `visible=false` on insert, background job flips to `true` when both parties rate or 7 days pass

**Problem Reports Table** (owned by FEAT-04):
- Fields: `transaction_id`, `reported_by` (always lender), `issue_type ENUM`, `description TEXT`, `photo_urls TEXT[]`, `created_at`
- Relationship: `transactions.problem_report_id` → `problem_reports.id`

### Business Logic

**Rating Workflow**:
1. Transaction must be in "Returned - Confirmed" status before ratings allowed
2. Rating window opens at `confirmed_at`, closes at `confirmed_at + 168 hours` (exactly 7 days)
3. Both parties rate independently, ratings invisible until:
   - Both submit ratings → background job (runs every 1 minute) flips `visible=true`
   - 7 days pass → background job flips both to `visible=true` (even if only one submitted)
4. No editing or deleting ratings after submission
5. Users cannot rate same transaction twice (DB constraint enforces)

**Transaction Confirmation**:
- **Three paths to confirmation**:
  1. Lender clicks "Confirm Return (No Issues)" → immediate confirmation
  2. Lender submits problem report → immediate confirmation (implicit)
  3. Neither action taken → auto-confirmation at `auto_confirm_at` (14 days after due date)
- **Due dates are immutable** - no extensions, set at request approval and never modified
- Problem reports don't block status progression - they're metadata on confirmed transactions

**Phone Verification**:
- **SMS Send Limit**: 5 sends per phone number per 24 hours (initial + 4 resends)
- **Incorrect Code Limit**: 3 wrong entries per phone number per 24 hours (across all verification attempts)
- Limits tracked in `phone_verification_attempts` JSONB column
- Lockout duration: 24 hours (no permanent bans)
- Background job clears attempts older than 24 hours every hour
- New code invalidates previous code (only most recent valid)
- Phone number changes reset verification status (must re-verify new number)

**Profile Statistics**:
- All statistics cached in `users` table, updated every 1 minute via Hangfire recurring job
- Job targets users with recent activity (last 5 minutes) to optimize performance
- Optional immediate updates on critical events (transaction confirmed, rating submitted) for sub-second staleness
- Average rating displayed as "New User" until at least 3 rated transactions complete

**Text Sanitization**:
- Strip all HTML tags (XSS prevention)
- Preserve line breaks, limit to max 2 consecutive `\n` (prevents whitespace walls)
- Allow emojis, count using text elements (emoji = 1 character)
- Character limits: bio 300, reviews 500 (enforced on text element count, not byte length)
- Display: escape HTML special chars, replace `\n` with `<br>`
- URLs allowed as plain text, not clickable (v1 simplicity)

### Authorization

**Profile Viewing**:
- Public read access to all user profiles (trust requires transparency)
- Full street address hidden - only neighborhood and city visible
- Full address revealed only to approved borrowers (after request approval, for pickup coordination)

**Profile Editing**:
- Users can edit own profile only: `full_name`, `neighborhood`, `bio`, `profile_photo_url`
- Name changes logged in audit trail (prevents impersonation abuse)
- Email cannot be changed (unique identifier for login)
- Phone number changes reset verification status

**Rating Submission**:
- Both parties in transaction can submit one rating each
- Must wait until transaction status = "Returned - Confirmed"
- Must submit within 7-day window (`rating_window_closes_at`)
- Cannot rate transactions where user is not borrower or lender
- Cannot rate same transaction twice (DB constraint)
- Cannot edit or delete ratings after submission

**Verification**:
- Email verification required at signup (enforced by auth system)
- Phone verification optional, user-initiated
- Address verification optional (future feature - manual review by admin)

### API Design

**Profile Endpoints**:
```
GET    /api/v1/users/{id}/profile           # View profile (public)
PATCH  /api/v1/users/{id}/profile           # Edit own profile
POST   /api/v1/users/{id}/verify-phone      # Initiate phone verification
POST   /api/v1/users/{id}/verify-phone-code # Submit verification code
GET    /api/v1/users/{id}/ratings           # View ratings received (paginated)
GET    /api/v1/users/{id}/transactions      # View transaction history (own only)
```

**Rating Endpoints**:
```
POST   /api/v1/transactions/{id}/rate       # Submit rating
GET    /api/v1/transactions/{id}/my-rating  # Check if I've rated this transaction
```

**Request/Response Examples**:
```json
GET /api/v1/users/123/profile
Response 200:
{
  "id": 123,
  "name": "Alice Johnson",
  "neighborhood": "Green Valley",
  "city": "Portland",
  "memberSince": "2024-03-15T00:00:00Z",
  "bio": "Love woodworking and happy to share tools!",
  "statistics": {
    "toolsOwned": 12,
    "toolsShared": 47,
    "currentBorrows": 2,
    "averageRating": 4.8,
    "ratingCount": 35,
    "lastUpdated": "2025-01-10T15:42:00Z"
  },
  "verifications": {
    "email": true,
    "phone": true,
    "address": false
  }
}

POST /api/v1/transactions/456/rate
Request:
{
  "stars": 5,
  "review": "Great experience! Tool was in perfect condition and Alice was very helpful with pickup."
}
Response 201:
{
  "id": 789,
  "transactionId": 456,
  "stars": 5,
  "review": "Great experience!...",
  "visible": false,
  "message": "Thanks! Your rating will be visible after the other party rates or in 7 days."
}
```

### Edge Cases

**Transaction Auto-Confirmation**:
- Borrower never marks as returned → Auto-confirms at `auto_confirm_at` (14 days after due date)
- Lender never confirms return → Same auto-confirmation logic applies
- Both parties inactive → Background job handles auto-confirmation, rating window opens anyway

**Concurrent Rating Submissions**:
- Both submit at exact same second → Both inserts succeed with `visible=false`, background job flips both to visible within 1 minute
- One submits, other never submits → After 7 days, first rating becomes visible even without second rating

**Phone Verification Edge Cases**:
- User hits 5 SMS sends → Wait 24 hours, all limits reset automatically
- User hits 3 wrong codes → Wait 24 hours, can request new codes
- User changes phone number mid-verification → Old verification attempts cleared, starts fresh with new number
- SMS never arrives → Can resend up to 4 times (5 total sends), then must wait 24 hours

**Rating Window Expiration**:
- Transaction confirmed at 2:00 PM UTC on May 15 → Window closes at 2:00 PM UTC on May 22 (exactly 168 hours later)
- User in different timezone sees same deadline converted to local time (e.g., "May 22 at 7:00 AM PST")
- Notifications sent at user's local time using profile timezone preference

**Account Deletion**:
- User deletes account → Soft delete (`deleted_at` set)
- Profile shows "[User Unavailable]" but ratings remain visible (anonymized)
- Transaction history shows deleted user's ratings to preserve trust data for other party
- Tools automatically delisted, active transactions handled by FEAT-04 cancellation logic

**Text Input Edge Cases**:
- User pastes HTML → Tags stripped, plain text preserved
- User enters 10 consecutive line breaks → Normalized to 2 line breaks max
- Bio with emoji: "I love tools! 🔨🪛🪚" → Counts as 19 characters (emojis = 1 each)
- User enters 301 characters → Backend returns 400 Bad Request with count ("currently 301")

---

## Implementation Notes

**Database**:
- PostgreSQL 16+ with `TIMESTAMP` columns (UTC timezone) for all time fields
- JSONB column for `phone_verification_attempts` (flexible structure, no schema changes for additional tracking)
- E.164 format validation CHECK constraint on `users.phone_number`: `CHECK (phone_number ~ '^\+[1-9]\d{1,14}$')`
- Unique index on `ratings(transaction_id, rater_id)` prevents duplicate ratings
- Soft delete on `users` table preserves referential integrity for ratings/transactions

**Authorization**:
- Profile view endpoint public (no auth required) - transparency builds trust
- Profile edit requires `userId == authenticatedUserId` check
- Rating submission requires `transactionId` belongs to authenticated user (as borrower OR lender)
- Phone verification endpoints require authentication (user can only verify own phone)

**Validation**:
- Bio max 300 text elements (use `StringInfo.LengthInTextElements` in C#)
- Review max 500 text elements
- Phone number validated with libphonenumber library before storage
- Star rating 1-5 integer (enforced by DB CHECK constraint and API validation)
- Transaction must be "Returned - Confirmed" before accepting ratings (status check)
- Rating window expiration check: `NOW() <= rating_window_closes_at` before accepting rating

**Background Jobs (Hangfire)**:
1. **Update User Statistics** - Runs every 1 minute
   - Targets users with `transactions.updated_at > NOW() - 5 minutes` (optimization)
   - Recalculates all cached statistics from source tables
   - Updates `users` table cached columns

2. **Flip Rating Visibility** - Runs every 1 minute
   - Finds transactions with 2 ratings where any rating has `visible=false`
   - Also finds transactions where `rating_window_closes_at < NOW()` and ratings exist with `visible=false`
   - Single UPDATE statement: `UPDATE ratings SET visible=true WHERE transaction_id IN (...)`

3. **Auto-Confirm Transactions** - Runs every 1 hour
   - Finds transactions where `status='Return Initiated' AND NOW() > auto_confirm_at`
   - Updates status to 'Returned - Confirmed', sets `confirmed_at=NOW()`, calculates `rating_window_closes_at`

4. **Clear Phone Verification Attempts** - Runs every 1 hour
   - Finds users where all timestamps in `phone_verification_attempts.sms_sends` and `.wrong_codes` are > 24 hours old
   - Clears `phone_verification_attempts` JSONB field
   - Removes `locked_until` if timestamp passed

**Key Decisions**:
- Due dates immutable (no extensions) - simplifies logic, prevents gaming
- Rating windows are 168-hour durations (not calendar days) - fair across timezones
- Problem reports implicitly confirm transactions - cleaner UX, fewer button clicks
- Eventual consistency for rating visibility (1-minute delay) - avoids complex locking
- Separate SMS send and wrong code limits - balances security with legitimate use cases
- All statistics cached with 1-minute updates - optimizes read-heavy profile views
- Emojis counted as 1 character using text elements - aligns with user expectations

**Third-Party Integrations**:
- **Twilio** for SMS verification (send codes, validate phone numbers)
- **libphonenumber** library (Google) for phone number parsing and E.164 normalization
- **Azure Blob Storage / S3** for profile photos (URL stored in database)
- **Hangfire** for background job scheduling (statistics updates, rating visibility, auto-confirmation)

**Security Considerations**:
- Phone verification attempts tracked per phone number (not per user) - prevents account switching attacks
- Rate limiting on phone verification endpoints (application-level, separate from per-phone limits)
- HTML sanitization prevents XSS in bio/review display
- Soft delete preserves data integrity while respecting user deletion requests
- Rating visibility delay prevents strategic rating based on other party's rating

---

## Recommended Next Steps

1. **Create detailed engineering specification** with:
   - Complete database schema (all columns, indexes, constraints)
   - Entity Framework Core entity models and relationships
   - API endpoint implementations (controllers, DTOs, validation)
   - Background job implementations (Hangfire job classes)
   - Service layer architecture (UserProfileService, RatingService, VerificationService)

2. **Set up infrastructure dependencies**:
   - Twilio account and API keys
   - Azure Blob Storage / S3 bucket for profile photos
   - Hangfire dashboard configuration
   - Redis cache for statistics (optional optimization)

3. **Define database migrations**:
   - Initial schema creation for `users`, `ratings`, `problem_reports` tables
   - Add cached statistics columns to `users`
   - Add transaction time tracking columns to `transactions` (coordinate with FEAT-04)
   - Create indexes for performance (user lookups, rating queries, transaction status checks)

4. **Plan integration with FEAT-02 and FEAT-04**:
   - Profile viewing during borrow request review (FEAT-02 calls profile API)
   - Transaction status updates trigger rating window opening (FEAT-04 updates `confirmed_at`)
   - Problem report submission transitions transaction status (coordinate status enum)

---

**This feature is ready for detailed engineering specification and implementation.**