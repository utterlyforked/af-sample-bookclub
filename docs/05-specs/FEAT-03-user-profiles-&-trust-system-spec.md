# User Profiles & Trust System — Engineering Spec

**Type**: feature  
**Component**: user-profiles-trust-system  
**Dependencies**: foundation-spec (User, Auth, Storage), FEAT-02 (BorrowRequest, BorrowRequestApproval), FEAT-04 (Transaction)  
**Status**: Ready for Implementation

---

## Overview

This component enables users to establish identity, showcase sharing history, and assess trustworthiness through profiles, verification badges, and bidirectional ratings. It owns `UserProfile`, `Rating`, `Verification`, and `ProblemReport` entities. It reads from foundation entities (`User`) and FEAT-02/FEAT-04 entities (`Transaction`, `Tool`) for statistics calculation. Profile views occur during borrow request reviews. Ratings are collected after transaction confirmation. Statistics are cached and refreshed every 1 minute via background job. Rating windows open at transaction confirmation and close exactly 168 hours later (timezone-agnostic).

---

## Data Model

### UserProfile

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Same as User.id (1:1 relationship) |
| user_id | UUID | FK → User.id, unique, not null | 1:1 with User |
| full_name | string(200) | not null | Display name (first + last) |
| neighborhood | string(100) | not null | Displayed publicly (e.g., "Green Valley") |
| city | string(100) | not null | Displayed publicly (e.g., "Portland") |
| street_address | string(300) | nullable | Full address, never displayed publicly |
| bio | string(300) | nullable | Plain text with line breaks, HTML stripped |
| profile_photo_url | string(500) | nullable | Azure Blob Storage URL |
| phone_number | string(15) | nullable | E.164 format (e.g., +15035551234) |
| phone_verified | boolean | not null, default false | Phone verification status |
| phone_verification_attempts | JSONB | nullable | Tracks SMS sends and wrong code entries |
| address_verified | boolean | not null, default false | Manual verification by admin |
| cached_tools_owned | int | not null, default 0 | Count of active tools owned |
| cached_tools_shared | int | not null, default 0 | Count of confirmed transactions as lender |
| cached_current_borrows | int | not null, default 0 | Count of active transactions as borrower |
| cached_average_rating | decimal(3,2) | nullable | Average star rating (e.g., 4.73), null if < 3 ratings |
| cached_rating_count | int | not null, default 0 | Total visible ratings received |
| stats_last_updated | timestamp | not null | UTC timestamp of last cache update |
| created_at | timestamp | not null | UTC timestamp |
| updated_at | timestamp | not null | UTC timestamp |

**Indexes**:
- `(user_id)` unique
- `(neighborhood, city)` composite (for neighborhood directory)
- `(phone_number)` unique, partial (WHERE phone_number IS NOT NULL)

**Relationships**:
- Belongs to `User` via `user_id` (1:1)
- Has many `Rating` as rated user (cascade nullify on delete)
- Has many `Rating` as rater (cascade nullify on delete)
- Has many `Verification` (cascade delete)

**Constraints**:
- `CHECK (char_length(bio) <= 300)` (text element count enforced in application layer)
- `CHECK (phone_number ~ '^\+[1-9]\d{1,14}$')` (E.164 format)
- `CHECK (cached_average_rating IS NULL OR (cached_average_rating >= 1.0 AND cached_average_rating <= 5.0))`

---

### Rating

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| transaction_id | UUID | FK → Transaction.id, not null | Transaction being rated |
| rater_id | UUID | FK → User.id, not null | User submitting rating |
| rated_user_id | UUID | FK → User.id, not null | User being rated |
| stars | int | not null, CHECK (stars >= 1 AND stars <= 5) | Star rating 1-5 |
| review_text | string(500) | nullable | Plain text with line breaks, HTML stripped |
| visible | boolean | not null, default false | Mutual reveal after both rate or 7 days |
| created_at | timestamp | not null | UTC timestamp |
| updated_at | timestamp | not null | UTC timestamp |

**Indexes**:
- `(transaction_id, rater_id)` unique (prevents duplicate ratings)
- `(rated_user_id, visible)` composite (for profile page rating queries)
- `(transaction_id, visible)` composite (for mutual reveal job)
- `(created_at)` (for ordering)

**Relationships**:
- Belongs to `Transaction` via `transaction_id` (cascade delete)
- Belongs to `User` via `rater_id` (cascade nullify, display "[User Unavailable]")
- Belongs to `User` via `rated_user_id` (cascade nullify)

**Constraints**:
- `CHECK (char_length(review_text) <= 500)` (text element count enforced in application layer)
- `UNIQUE (transaction_id, rater_id)` (cannot rate same transaction twice)

---

### Verification

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| user_id | UUID | FK → User.id, not null | User being verified |
| verification_type | enum | not null | 'email', 'phone', 'address' |
| verification_code | string(6) | nullable | 6-digit code for phone verification |
| code_expires_at | timestamp | nullable | Code expiration (10 minutes from send) |
| verified_at | timestamp | nullable | UTC timestamp when verified |
| verified_by | UUID | FK → User.id, nullable | Admin user ID (for address verification) |
| created_at | timestamp | not null | UTC timestamp |
| updated_at | timestamp | not null | UTC timestamp |

**Indexes**:
- `(user_id, verification_type)` composite (at most 1 active per type)
- `(verification_code)` (for code lookup, partial WHERE verification_code IS NOT NULL)
- `(code_expires_at)` (for cleanup job)

**Relationships**:
- Belongs to `User` via `user_id` (cascade delete)
- Belongs to `User` via `verified_by` (cascade nullify)

**Constraints**:
- `CHECK (verification_type IN ('email', 'phone', 'address'))`
- `CHECK (verification_code IS NULL OR verification_code ~ '^\d{6}$')`
- `UNIQUE (user_id, verification_type, verified_at)` partial (WHERE verified_at IS NOT NULL)

---

### ProblemReport

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| transaction_id | UUID | FK → Transaction.id, not null | Transaction with issue |
| reported_by | UUID | FK → User.id, not null | Always the lender |
| issue_type | enum | not null | 'damage', 'missing_parts', 'not_cleaned', 'late_return', 'other' |
| description | string(1000) | not null | Plain text description |
| photo_urls | text[] | nullable | Array of Azure Blob Storage URLs |
| created_at | timestamp | not null | UTC timestamp |
| updated_at | timestamp | not null | UTC timestamp |

**Indexes**:
- `(transaction_id)` unique (only 1 problem report per transaction)
- `(reported_by)` (for user's report history)

**Relationships**:
- Belongs to `Transaction` via `transaction_id` (cascade delete)
- Belongs to `User` via `reported_by` (cascade nullify)

**Constraints**:
- `CHECK (issue_type IN ('damage', 'missing_parts', 'not_cleaned', 'late_return', 'other'))`
- `CHECK (char_length(description) <= 1000)`
- `CHECK (array_length(photo_urls, 1) <= 5)` (max 5 photos)

---

> **Note**: This spec owns only the entities listed above. Entities defined in the Foundation Spec (`User`, `Group`, `GroupMember`) and FEAT-02/FEAT-04 (`BorrowRequest`, `Transaction`, `Tool`) are referenced by name, not redefined.

---

## API Endpoints

### POST /api/v1/profiles

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated user creating their own profile

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| full_name | string | yes | 1-200 chars, non-empty after trim |
| neighborhood | string | yes | 1-100 chars, non-empty after trim |
| city | string | yes | 1-100 chars, non-empty after trim |
| street_address | string | no | max 300 chars |
| bio | string | no | max 300 text elements (grapheme clusters) |
| phone_number | string | no | Valid E.164 format (+1XXXXXXXXXX) |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Same as user_id |
| user_id | UUID | |
| full_name | string | |
| neighborhood | string | |
| city | string | |
| bio | string | Sanitized (HTML stripped, line breaks preserved) |
| profile_photo_url | string | null initially |
| phone_number | string | E.164 format |
| phone_verified | boolean | false initially |
| address_verified | boolean | false initially |
| statistics | object | All cached values |
| verifications | object | Badge status |
| created_at | ISO 8601 datetime | UTC |
| updated_at | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure (field-level errors) |
| 401 | Not authenticated |
| 409 | Profile already exists for this user |

---

### GET /api/v1/profiles/{user_id}

**Auth**: Required (Bearer JWT)  
**Authorization**: Any authenticated user (public profiles)

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| user_id | UUID | Valid UUID format |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| user_id | UUID | |
| full_name | string | "[User Unavailable]" if soft deleted |
| neighborhood | string | Public (e.g., "Green Valley") |
| city | string | Public (e.g., "Portland") |
| bio | string | Sanitized, null if empty |
| profile_photo_url | string | null if not uploaded |
| member_since | ISO 8601 date | From User.created_at |
| statistics | object | `{ tools_owned, tools_shared, current_borrows, average_rating, rating_count, last_updated }` |
| verifications | object | `{ email: boolean, phone: boolean, address: boolean }` |
| ratings | array | Top 10 most recent visible ratings |

**ratings array element**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| rater_name | string | "[User Unavailable]" if deleted |
| stars | int | 1-5 |
| review_text | string | null if not provided |
| created_at | ISO 8601 datetime | |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 404 | Profile not found |

---

### PUT /api/v1/profiles/{user_id}

**Auth**: Required (Bearer JWT)  
**Authorization**: Own profile only (user_id matches JWT claim)

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| user_id | UUID | Valid UUID, must match authenticated user |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| full_name | string | yes | 1-200 chars, non-empty after trim |
| neighborhood | string | yes | 1-100 chars, non-empty after trim |
| city | string | yes | 1-100 chars, non-empty after trim |
| street_address | string | no | max 300 chars |
| bio | string | no | max 300 text elements |
| phone_number | string | no | Valid E.164 format |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| user_id | UUID | |
| full_name | string | |
| neighborhood | string | |
| city | string | |
| bio | string | Sanitized |
| profile_photo_url | string | |
| phone_number | string | |
| phone_verified | boolean | Reset to false if phone_number changed |
| address_verified | boolean | Reset to false if street_address changed |
| statistics | object | |
| verifications | object | |
| updated_at | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure |
| 401 | Not authenticated |
| 403 | Not authorized (wrong user) |
| 404 | Profile not found |

---

### POST /api/v1/profiles/{user_id}/photo

**Auth**: Required (Bearer JWT)  
**Authorization**: Own profile only

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| user_id | UUID | Valid UUID, must match authenticated user |

**Request body**: multipart/form-data
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| photo | file | yes | image/jpeg or image/png, max 5MB, min 200x200px |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| profile_photo_url | string | Azure Blob Storage URL |
| updated_at | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid file type, size, or dimensions |
| 401 | Not authenticated |
| 403 | Not authorized (wrong user) |
| 404 | Profile not found |
| 413 | File too large (> 5MB) |

---

### POST /api/v1/verifications/phone/send-code

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated user

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| phone_number | string | yes | Valid E.164 format |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| code_expires_at | ISO 8601 datetime | 10 minutes from now (UTC) |
| attempts_remaining | int | SMS sends remaining (out of 5 per 24h) |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid phone number format |
| 401 | Not authenticated |
| 429 | Rate limit exceeded (5 SMS per phone per 24h) |

---

### POST /api/v1/verifications/phone/verify-code

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated user

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| phone_number | string | yes | Valid E.164 format |
| code | string | yes | 6 digits |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| verified | boolean | true |
| verified_at | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid code format or phone number |
| 401 | Not authenticated |
| 403 | Code expired or incorrect (shows attempts remaining) |
| 429 | Too many incorrect attempts (3 per phone per 24h) |

---

### POST /api/v1/transactions/{transaction_id}/ratings

**Auth**: Required (Bearer JWT)  
**Authorization**: Must be borrower or lender on the transaction

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| transaction_id | UUID | Valid UUID |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| stars | int | yes | 1-5 |
| review_text | string | no | max 500 text elements |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| transaction_id | UUID | |
| rater_id | UUID | Authenticated user |
| rated_user_id | UUID | Other party |
| stars | int | |
| review_text | string | Sanitized, null if empty |
| visible | boolean | false until mutual reveal |
| created_at | ISO 8601 datetime | UTC |
| rating_window_closes_at | ISO 8601 datetime | Transaction's window close time |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure or rating window closed |
| 401 | Not authenticated |
| 403 | Not authorized (not party to transaction) |
| 404 | Transaction not found |
| 409 | Already rated this transaction |

---

### GET /api/v1/transactions/{transaction_id}/ratings

**Auth**: Required (Bearer JWT)  
**Authorization**: Must be borrower or lender on the transaction

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| transaction_id | UUID | Valid UUID |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| ratings | array | Both ratings if visible, empty if not |
| rating_window_closes_at | ISO 8601 datetime | null if already closed |
| can_rate | boolean | true if window open and user hasn't rated |

**ratings array element**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| rater_name | string | |
| rated_user_name | string | |
| stars | int | |
| review_text | string | |
| visible | boolean | |
| created_at | ISO 8601 datetime | |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | Not authorized (not party to transaction) |
| 404 | Transaction not found |

---

### POST /api/v1/transactions/{transaction_id}/problem-report

**Auth**: Required (Bearer JWT)  
**Authorization**: Must be lender on the transaction

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| transaction_id | UUID | Valid UUID |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| issue_type | enum | yes | 'damage', 'missing_parts', 'not_cleaned', 'late_return', 'other' |
| description | string | yes | 1-1000 chars, non-empty after trim |
| photo_urls | string[] | no | max 5 URLs, each max 500 chars |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| transaction_id | UUID | |
| reported_by | UUID | Lender user ID |
| issue_type | enum | |
| description | string | Sanitized |
| photo_urls | string[] | |
| created_at | ISO 8601 datetime | UTC |
| transaction_status | string | "Returned - Confirmed" (auto-transitioned) |
| rating_window_closes_at | ISO 8601 datetime | Opened immediately |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure or transaction not in "Return Initiated" status |
| 401 | Not authenticated |
| 403 | Not authorized (not lender) |
| 404 | Transaction not found |
| 409 | Problem report already submitted for this transaction |

---

### GET /api/v1/transactions/{transaction_id}/problem-report

**Auth**: Required (Bearer JWT)  
**Authorization**: Must be borrower or lender on the transaction

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| transaction_id | UUID | Valid UUID |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| transaction_id | UUID | |
| reported_by | UUID | |
| reporter_name | string | |
| issue_type | enum | |
| description | string | |
| photo_urls | string[] | |
| created_at | ISO 8601 datetime | |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | Not authorized (not party to transaction) |
| 404 | Transaction or problem report not found |

---

## Business Rules

1. Email verification is completed during user registration (owned by Foundation Spec) — all users have email_verified = true.
2. Full street addresses are never displayed publicly — only neighborhood and city are shown on profiles.
3. Approved borrowers receive full street addresses only after request approval via private message or transaction details.
4. Users may change their phone number, but phone_verified resets to false and requires re-verification.
5. Users may change their street address, but address_verified resets to false and requires admin re-verification.
6. Average rating displays as null (shown as "New User" in UI) until user has at least 3 visible ratings.
7. Rating windows open exactly when transaction status becomes "Returned - Confirmed" (via lender confirmation, borrower auto-confirmation, or problem report submission).
8. Rating windows close exactly 168 hours (7 days) after `confirmed_at` timestamp, regardless of timezone.
9. Due dates are immutable once transactions are created — no extensions or modifications allowed.
10. Auto-confirmation occurs 14 days after due_date (7 days overdue + 7 days grace) if lender has not confirmed return.
11. Submitting a problem report immediately transitions transaction to "Returned - Confirmed" status and opens rating window.
12. Both ratings become visible simultaneously when both parties have rated OR when 7-day window expires, whichever comes first.
13. Users cannot rate the same transaction twice or edit ratings after submission.
14. Phone verification allows maximum 3 incorrect code attempts per phone number per 24 hours.
15. Phone verification allows maximum 5 SMS sends per phone number per 24 hours (initial + 4 resends).
16. Verification codes expire 10 minutes after generation.
17. Phone numbers are stored in normalized E.164 format (+1XXXXXXXXXX).
18. Profile statistics are cached and updated every 1 minute via background job.
19. Text fields (bio, review_text) have HTML tags stripped and line breaks preserved, with maximum 2 consecutive line breaks allowed.
20. Character limits count text elements (grapheme clusters) to properly handle emojis as single characters.
21. Profile photo uploads must be JPEG or PNG, maximum 5MB, minimum 200x200 pixels.
22. Deleted user profiles display as "[User Unavailable]" but ratings remain visible (anonymized).
23. Transaction history shows "Deleted User" for counterparty name if account deleted.
24. Only one active problem report allowed per transaction (enforced via unique constraint).
25. Problem reports are visible to both parties after submission for transparency.

---

## Validation Rules

| Field | Rule | Error message |
|-------|------|---------------|
| full_name | Required, 1-200 chars, non-empty after trim | "Full name is required" / "Full name must be 200 characters or less" |
| neighborhood | Required, 1-100 chars, non-empty after trim | "Neighborhood is required" / "Neighborhood must be 100 characters or less" |
| city | Required, 1-100 chars, non-empty after trim | "City is required" / "City must be 100 characters or less" |
| street_address | Optional, max 300 chars | "Street address must be 300 characters or less" |
| bio | Optional, max 300 text elements | "Bio must be 300 characters or less (currently {count})" |
| phone_number | Optional, valid E.164 format | "Invalid phone number format (use +1XXXXXXXXXX)" |
| profile_photo | image/jpeg or image/png, max 5MB, min 200x200px | "Photo must be JPG or PNG" / "Photo must be under 5MB" / "Photo must be at least 200x200 pixels" |
| stars | Required, integer 1-5 | "Rating is required" / "Rating must be between 1 and 5 stars" |
| review_text | Optional, max 500 text elements | "Review must be 500 characters or less (currently {count})" |
| verification_code | Required, exactly 6 digits | "Verification code must be 6 digits" |
| issue_type | Required, valid enum value | "Issue type is required" / "Invalid issue type" |
| problem_description | Required, 1-1000 chars, non-empty after trim | "Description is required" / "Description must be 1000 characters or less" |
| photo_urls | Optional, max 5 URLs, each max 500 chars | "Maximum 5 photos allowed" / "Photo URL too long" |

---

## Authorization

| Action | Required policy | Notes |
|--------|----------------|-------|
| Create profile | Authenticated | Own profile only (user_id from JWT) |
| View profile | Authenticated | Any user can view any profile (public) |
| Edit profile | Authenticated | Own profile only |
| Upload profile photo | Authenticated | Own profile only |
| Send phone verification code | Authenticated | Own phone number only |
| Verify phone code | Authenticated | Own phone number only |
| Submit rating | TransactionParty | Must be borrower or lender on transaction |
| View transaction ratings | TransactionParty | Must be borrower or lender on transaction |
| Submit problem report | TransactionLender | Must be lender on transaction |
| View problem report | TransactionParty | Must be borrower or lender on transaction |

**Policy Definitions**:
- **Authenticated**: Valid JWT token in request
- **TransactionParty**: `transaction.borrower_id == user_id OR transaction.lender_id == user_id`
- **TransactionLender**: `transaction.lender_id == user_id`

---

## Acceptance Criteria

- [ ] User can create profile with full_name, neighborhood, city, and optional bio
- [ ] Profile displays cached statistics: tools_owned, tools_shared, current_borrows, average_rating, rating_count
- [ ] Average rating displays null (shown as "New User") until user has 3+ visible ratings
- [ ] Profile shows verification badges: email (always true), phone (after verification), address (after admin approval)
- [ ] Full street address never displayed publicly — only neighborhood and city shown
- [ ] User can upload profile photo (JPEG/PNG, max 5MB, min 200x200px) and it stores in Azure Blob Storage
- [ ] User can change phone number, but phone_verified resets to false
- [ ] Phone verification sends 6-digit code via Twilio, expires after 10 minutes
- [ ] Phone verification allows max 5 SMS sends per phone per 24 hours
- [ ] Phone verification allows max 3 incorrect code attempts per phone per 24 hours
- [ ] Phone numbers stored in E.164 format (+1XXXXXXXXXX) and displayed as (503) 555-1234
- [ ] Borrower and lender can each submit 5-star rating with optional 500-char review after transaction confirmation
- [ ] Rating submission validates transaction status is "Returned - Confirmed"
- [ ] Rating submission validates rating window has not closed (168 hours from confirmation)
- [ ] User cannot rate same transaction twice (409 Conflict)
- [ ] Ratings stored with visible = false initially
- [ ] Both ratings flip to visible = true when both parties have rated (background job runs every 1 minute)
- [ ] Both ratings flip to visible = true when 168-hour window expires, regardless of whether both parties rated
- [ ] Profile displays top 10 most recent visible ratings with stars, review_text, rater_name, created_at
- [ ] Deleted users show as "[User Unavailable]" in rater_name but ratings remain visible
- [ ] Rating window opens exactly when transaction status becomes "Returned - Confirmed"
- [ ] Rating window closes exactly 168 hours after confirmed_at timestamp
- [ ] Due dates are immutable after transaction creation — no extensions allowed
- [ ] Transaction auto-confirms 14 days after due_date if lender has not confirmed return (background job runs hourly)
- [ ] Lender can submit problem report with issue_type, description, and up to 5 photos
- [ ] Submitting problem report immediately transitions transaction to "Returned - Confirmed" and opens rating window
- [ ] Problem report visible to both borrower and lender after submission
- [ ] Only one problem report allowed per transaction (409 Conflict if duplicate)
- [ ] Profile statistics cached and updated every 1 minute via background job
- [ ] Background job calculates: cached_tools_owned (active tools), cached_tools_shared (confirmed transactions as lender), cached_current_borrows (active transactions as borrower), cached_average_rating (avg of visible ratings), cached_rating_count (count of visible ratings)
- [ ] Bio and review_text have HTML tags stripped, line breaks preserved, max 2 consecutive line breaks
- [ ] Character limits count text elements (grapheme clusters) so emojis = 1 character
- [ ] Profile creation returns 409 if profile already exists for user
- [ ] Profile update returns 403 if user_id does not match authenticated user
- [ ] Rating submission returns 403 if user is not borrower or lender on transaction
- [ ] Problem report submission returns 403 if user is not lender on transaction
- [ ] Phone verification send returns 429 if 5 SMS sends exceeded in 24 hours
- [ ] Phone verification verify returns 429 if 3 incorrect attempts exceeded in 24 hours
- [ ] All timestamps stored as UTC in database and returned as ISO 8601 in API responses

---

## Security Requirements

**From AppSec Review:**

- Phone verification codes must be cryptographically random (use `System.Security.Cryptography.RandomNumberGenerator`), not `Random` class
- Rate limiting enforced at application layer: max 5 SMS sends per phone per 24h, max 3 incorrect codes per phone per 24h
- Phone verification attempts tracked in `phone_verification_attempts` JSONB column with timestamps, cleaned by background job after 24 hours
- Profile photos stored in Azure Blob Storage with private container access, served via signed URLs with 1-hour expiration
- Photo uploads validated for file type (magic number check, not just extension), max size (5MB), and dimensions (min 200x200px)
- Text inputs sanitized to strip HTML tags using `HtmlSanitizer` library before storage
- Character limits enforced using `StringInfo.LengthInTextElements` to prevent emoji-based overflow attacks
- Authorization policies enforce transaction party membership before allowing rating submission or problem report viewing
- Soft delete user profiles (set `deleted_at`, never actually DELETE) to preserve rating integrity
- Rating visibility logic prevents information leakage — ratings invisible until mutual reveal or window exp