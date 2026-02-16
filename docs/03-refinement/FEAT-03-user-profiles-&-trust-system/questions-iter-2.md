# User Profiles & Trust System - Technical Questions (Iteration 2)

**Status**: NEEDS CLARIFICATION
**Iteration**: 2
**Date**: 2025-01-10

---

## Summary

After reviewing the v1.1 specification, I've identified **8** areas that need clarification before implementation can begin. The v1.1 update answered many critical questions from iteration 1, but several important technical details remain ambiguous. These questions address:

- Transaction completion mechanics and edge cases
- Phone verification security and limitations
- Profile statistics calculation timing
- Concurrent rating scenarios
- Data model constraints

The specification is significantly improved from v1.0, with clear decisions on rating workflows, deletion policies, and verification processes. These remaining questions focus on precise implementation details needed for database design and API development.

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What defines the "due date" for transaction auto-confirmation?

**Context**: The spec states "7 days after due date passes without confirmation" for auto-confirmation, but the due date itself is defined in FEAT-04 (Borrow Tracking), which I don't have access to. I need to understand:
- Is due date set at request approval time or later?
- Can due date be extended/modified after transaction starts?
- If due date changes, does auto-confirmation timer reset?

This affects database design (`transactions.due_date` column type, timezone handling) and background job logic for auto-confirmation.

**Options**:

- **Option A: Due date is immutable after transaction starts**
  - Impact: Simple logic - `due_date + 14 days = auto_confirm_at`, set once at transaction creation
  - Trade-offs: No flexibility if borrower needs more time; lender must manually extend via FEAT-04
  - Database: Single `due_date TIMESTAMP NOT NULL`, single `auto_confirm_at TIMESTAMP NOT NULL`
  
- **Option B: Due date can be extended, auto-confirmation resets**
  - Impact: When `due_date` updated, recalculate `auto_confirm_at = new_due_date + 14 days`
  - Trade-offs: More flexible, but adds complexity; need to track due date change history
  - Database: `due_date TIMESTAMP NOT NULL`, `auto_confirm_at TIMESTAMP NOT NULL`, audit table for due date changes
  
- **Option C: Due date can be extended, but auto-confirmation never resets**
  - Impact: Auto-confirmation based on *original* due date, regardless of extensions
  - Trade-offs: Prevents gaming the system (infinite extensions to delay auto-confirmation), but may feel unfair
  - Database: `original_due_date TIMESTAMP NOT NULL`, `current_due_date TIMESTAMP NOT NULL`, `auto_confirm_at TIMESTAMP NOT NULL`

**Recommendation for MVP**: Option A (immutable due date). Simplest implementation, aligns with "borrow period set at request approval" model. If extensions are needed, handle via FEAT-04 creating a new transaction or manual lender intervention. Can add flexibility in v2 if users request it.

---

### Q2: How do we handle timezone for rating window deadlines across users in different timezones?

**Context**: Spec says "rating window closes at 2:00 PM on May 22 (exactly 168 hours later)", but users may be in different timezones. Need clarity on:
- Is 168 hours from transaction completion (timezone-agnostic duration)?
- Or is it calendar-based (closes at specific time on Day 7)?
- What timezone are notifications sent in?

This affects user experience (when notifications arrive), database storage (TIMESTAMP vs TIMESTAMPTZ), and display logic (countdown timers).

**Options**:

- **Option A: 168 hours exactly from transaction completion (timezone-agnostic)**
  - Impact: Store `rating_window_closes_at` as UTC timestamp, calculate as `confirmed_at + 168 hours`
  - Trade-offs: Fair (everyone gets exact same duration), but "closes at 2:00 PM" in spec is misleading
  - Display: Show countdown timer "4 days, 3 hours remaining" (always accurate)
  - Notifications: Send at user's local time (e.g., "closes tomorrow at 2:00 PM your time")
  
- **Option B: Calendar-based (closes at midnight on Day 7 in user's timezone)**
  - Impact: Each user's deadline is different; Alice (PST) has until 11:59 PM May 22 PST, Bob (EST) until 11:59 PM May 22 EST
  - Trade-offs: Intuitive ("you have until end of day 7"), but unfair (Bob gets 3 fewer hours than Alice)
  - Display: Show date "Closes May 22" (simpler than countdown)
  
- **Option C: Calendar-based (closes at midnight Day 7 in transaction's origin timezone)**
  - Impact: Use lender's timezone as "transaction timezone", both parties' window closes at same absolute moment
  - Trade-offs: Fair (same deadline), but may confuse borrower ("why did it close at 9 PM my time?")
  - Display: Show both countdown and date "Closes May 22 at 11:59 PM PST (9 hours remaining for you)"

**Recommendation for MVP**: Option A (168 hours exactly). Simplest and fairest - database stores UTC timestamps, no timezone math, countdown timers are intuitive. The "2:00 PM" in spec is just an example; actual close time depends on when transaction confirmed. Notifications translate to user's local time for clarity.

---

### Q3: Can a transaction be "Returned - Confirmed" if there's a pending problem report?

**Context**: Spec describes workflow where lender marks "Returned with Issues" → submits problem report → transaction progresses to "Returned - Confirmed". But the status progression isn't entirely clear:

- Does "Returned with Issues" transition directly to "Returned - Confirmed" automatically?
- Or does lender manually confirm after submitting problem report?
- What if lender never confirms after reporting problem (similar to auto-confirmation scenario)?

This affects whether rating windows can open while problem reports are unresolved, and whether we need an intermediate status.

**Options**:

- **Option A: "Returned with Issues" auto-transitions to "Returned - Confirmed" after problem report submission**
  - Impact: Problem report submission is the confirmation; rating window opens immediately
  - Trade-offs: Fast (no waiting for lender), but lender might want to review return again after filing report
  - Workflow: Borrower marks returned → Lender clicks "Report Problem" → Submits report → Status instantly becomes "Returned - Confirmed" → Rating window opens
  
- **Option B: Lender must explicitly confirm after submitting problem report**
  - Impact: Problem report submission is separate from confirmation; lender clicks "Confirm Return" after report
  - Trade-offs: Gives lender control, but adds extra step (might forget to confirm after reporting)
  - Workflow: Borrower marks returned → Lender clicks "Report Problem" → Submits report → Lender clicks "Confirm Return" → Status becomes "Returned - Confirmed" → Rating window opens
  - Auto-confirmation still applies if lender never clicks "Confirm Return"
  
- **Option C: "Returned with Issues" is a terminal state, separate rating workflow**
  - Impact: Problem reports create different transaction end state; ratings work differently
  - Trade-offs: Complex, potentially confusing; spec suggests all completed transactions can be rated

**Recommendation for MVP**: Option A (auto-transition after problem report). Simplest workflow - submitting problem report is implicit confirmation that lender has inspected the tool. Keeps status flow linear: Active → Return Initiated → Returned with Issues → Returned - Confirmed. Problem report is just metadata attached to the confirmation, not a blocking state.

---

### Q4: What happens if both parties submit ratings at the exact same second?

**Context**: Spec says "Moment Bob submits, both ratings become visible to both parties". Need to clarify race condition handling:
- If Alice and Bob both click "Submit Rating" within milliseconds of each other
- Database sees two concurrent inserts trying to flip visibility flag
- How do we ensure both ratings become visible atomically?

This affects database transaction isolation level and API endpoint design.

**Options**:

- **Option A: Last-write-wins with eventual consistency**
  - Impact: Both inserts succeed, background job (runs every 1 min) detects both ratings exist, flips visibility
  - Trade-offs: Simple code, but users may see "Waiting for other party" for up to 1 minute even though both submitted
  - Database: No transaction coordination needed
  
- **Option B: Serialized database transaction with explicit locking**
  - Impact: Rating insert wrapped in transaction with `SELECT FOR UPDATE` on transaction row; check if other rating exists; flip visibility if both present
  - Trade-offs: Instant visibility (no delay), but more complex code and potential deadlocks
  - Database: Isolation level `Serializable`, explicit row locking
  
- **Option C: Event-driven with message queue**
  - Impact: Rating submission publishes event, consumer checks for mutual completion, updates visibility
  - Trade-offs: Decoupled and scalable, but adds infrastructure complexity (Hangfire as queue)
  - Database: No locking needed, eventual consistency within seconds

**Recommendation for MVP**: Option A (eventual consistency with background job). The 1-minute delay is acceptable - users don't expect instant mutual reveal anyway (they're rating independently). Simplest code, no deadlock risk. Background job already needed for other tasks (statistics updates), so no new infrastructure. Can optimize to Option B in v2 if users complain about delay.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q5: What's the maximum length for phone numbers after formatting?

**Context**: Spec says "US numbers only for v1, international in v2", but doesn't specify storage format or max length. Need to know:
- Store as entered (e.g., "(503) 555-1234") or normalized (e.g., "+15035551234")?
- What validation do we apply (format, length, country code)?
- How do we handle extensions (e.g., "555-1234 ext. 567")?

This affects database column size, validation logic, and Twilio API integration.

**Options**:

- **Option A: Store normalized E.164 format (+1XXXXXXXXXX), max 15 chars**
  - Impact: Use library (libphonenumber) to parse and normalize on submit; store "+15035551234"
  - Trade-offs: Consistent storage, easy validation, works with Twilio; but strips formatting users prefer
  - Database: `phone VARCHAR(15)`, CHECK constraint for E.164 format
  - Display: Re-format for display as "(503) 555-1234"
  
- **Option B: Store as user entered, max 20 chars**
  - Impact: Validate format loosely (10-11 digits present), store "(503) 555-1234" or "503-555-1234"
  - Trade-offs: Preserves user preference, but harder to deduplicate and validate
  - Database: `phone VARCHAR(20)`, extract digits for Twilio API calls
  
- **Option C: Store both normalized and display format**
  - Impact: `phone_normalized VARCHAR(15)` for API calls, `phone_display VARCHAR(20)` for UI
  - Trade-offs: Best UX (user sees their format, system uses normalized), but more storage
  - Database: Two columns, both indexed

**Recommendation for MVP**: Option A (normalized E.164). Standard practice for phone storage, prevents duplicate accounts with same number in different formats (e.g., "5035551234" vs "+1-503-555-1234"). Use libphonenumber to parse on input, re-format for display using same library. Twilio expects E.164, so this is simplest integration.

---

### Q6: How many SMS verification attempts are allowed before we lock out the phone number permanently?

**Context**: Spec says "3 attempts allowed per phone number per 24 hours" for entering incorrect codes, but also "5 SMS sends per phone number per 24 hours" for rate limiting. Need to clarify:

- Are these separate limits (3 wrong codes AND 5 SMS sends)?
- What happens after hitting limit (temporary lockout, permanent ban, contact support)?
- Does changing to a different phone number reset attempts?

This affects fraud prevention and user experience when legitimate users have issues.

**Options**:

- **Option A: Separate limits - 3 wrong codes, 5 SMS sends, both reset after 24 hours**
  - Impact: User can send 5 SMS (including resends), enter wrong code 3 times total; after either limit, wait 24 hours
  - Trade-offs: Protects against brute force and SMS abuse; but legitimate user who fat-fingers code 3 times is locked out
  - After lockout: "Too many attempts. Try again after [timestamp]" or "Contact support"
  
- **Option B: Combined limit - 5 total verification attempts (send + enter code), reset after 24 hours**
  - Impact: Each SMS send or wrong code entry counts toward same 5-attempt limit
  - Trade-offs: Simpler to track, stricter fraud prevention; but less forgiving to legitimate users
  
- **Option C: Escalating lockout - 3 attempts = 1 hour lockout, 5 attempts = 24 hour lockout, 10 attempts = permanent ban**
  - Impact: First few mistakes are short lockouts, repeat abuse is permanent
  - Trade-offs: More forgiving to mistakes, but more complex to implement
  - Requires: `phone_verification_attempts` table tracking timestamps and lockout state

**Recommendation for MVP**: Option A (separate limits, 24-hour reset). Balances fraud prevention with legitimate use cases. User who typos SMS code 3 times can still contact support to manually verify. Track attempts in `users.phone_verification_attempts` (JSON array of timestamps) and `users.phone_sms_sends` (separate JSON array). Background job clears attempts older than 24 hours.

---

### Q7: Should profile statistics (Tools Shared, Average Rating) update in real-time or via background job?

**Context**: Spec mentions "Background job (Hangfire) recalculates and updates cache" for average rating, and "acceptable staleness: < 5 minutes". Need to clarify if this applies to all statistics or just rating:

- Tools Owned: Real-time (updated when tool listed/delisted)?
- Tools Shared: Background job (recalculated after transaction completes)?
- Current Borrows: Real-time (updated when transaction status changes)?
- Average Rating: Background job (confirmed in spec)?

This affects whether we use cached columns vs. real-time queries, and impacts page load performance.

**Options**:

- **Option A: All statistics cached, background job updates every 1 minute**
  - Impact: `users.cached_tools_owned`, `cached_tools_shared`, `cached_current_borrows`, `cached_average_rating`
  - Trade-offs: Fast profile loads (single SELECT on users table), but all stats have < 1 min staleness
  - Implementation: Hangfire job runs every 1 minute, recalculates for users with recent activity
  
- **Option B: Real-time for simple counts, cached for expensive calculations**
  - Impact: Tools Owned and Current Borrows calculated on-the-fly (simple COUNT queries), Tools Shared and Average Rating cached
  - Trade-offs: More accurate for frequently-changing stats, but profile load requires 2 COUNT queries
  - Implementation: Profile API does `COUNT(tools WHERE owner_id = X)`, `COUNT(transactions WHERE borrower_id = X AND active)`
  
- **Option C: All statistics real-time (no caching)**
  - Impact: Every profile view triggers 4 aggregate queries
  - Trade-offs: Always accurate, but slow page loads (especially for users with hundreds of transactions)
  - Implementation: No cached columns, all stats calculated in API endpoint

**Recommendation for MVP**: Option A (all cached, 1-minute background job). Profile views are high-frequency operations (users check profiles before approving requests), so optimize for read speed. Sub-minute staleness is acceptable - "Tools Shared: 23" vs "Tools Shared: 24" doesn't affect trust decisions. Use Hangfire recurring job to update cache, trigger recalculation immediately on relevant events (transaction completed, rating submitted) for faster updates.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q8: What character encoding/sanitization do we apply to bio and review text?

**Context**: Spec says "bio (max 300 characters, plain text with line breaks)" and "reviews (max 500 characters)", but doesn't specify:
- Are HTML tags stripped or escaped?
- Are URLs allowed (clickable or plain text)?
- Are emojis counted as 1 character or more?
- How do we handle line breaks (preserve `\n`, convert to `<br>`, limit number of breaks)?

This affects XSS prevention, character counting accuracy, and display consistency.

**Options**:

- **Option A: Strip all HTML, preserve line breaks, allow emojis**
  - Impact: User enters text in textarea, we strip `<script>` and other HTML, store plain text with `\n`
  - Trade-offs: Safe (no XSS), simple; but users can't bold or italicize (spec says "plain text" anyway)
  - Display: Replace `\n` with `<br>` for rendering, escape other special chars
  - Character count: Count UTF-8 characters (emoji = 1 char)
  
- **Option B: Allow limited Markdown (bold, italic, links), sanitize output**
  - Impact: Parse Markdown server-side, generate safe HTML, store as HTML
  - Trade-offs: Better UX (users can emphasize points), but more complex and risks XSS if sanitizer fails
  - Spec contradiction: Spec says "plain text", this would enable formatting
  
- **Option C: Strip all special characters including line breaks, single-line text only**
  - Impact: Bio/review becomes single continuous string, no formatting
  - Trade-offs: Safest (impossible to inject anything), but poor UX (no paragraphs)
  - Spec contradiction: Spec explicitly says "plain text with line breaks"

**Recommendation for MVP**: Option A (strip HTML, preserve line breaks, allow emojis). Aligns with "plain text with line breaks" requirement. Use library like HtmlSanitizer or manual regex to strip tags on input. Store plain text with `\n`. On display, escape HTML special chars (`<`, `>`, `&`) then replace `\n` with `<br>`. Count characters using .NET's `StringInfo.LengthInTextElements` to handle emojis correctly. Limit to 10 line breaks max to prevent abuse (wall of whitespace).

---

## Notes for Product

### Clarifications That Would Help

1. **FEAT-04 Integration**: Several questions depend on Borrow Tracking mechanics (Q1, Q3). If FEAT-04 spec is available, share it so I can see full transaction lifecycle.

2. **Phone Verification Future**: Spec mentions "international in v2" - should I design phone number storage to accommodate international later (e.g., country code column), or optimize purely for US now and migrate schema in v2?

3. **Performance Expectations**: How many concurrent users do we expect for MVP? If < 1000 users, real-time statistics (Q7 Option C) might be viable. If > 10,000, caching is essential.

### Implementation Readiness

Once Q1-Q4 (Critical) are answered, I can begin database schema design. Q5-Q8 (High/Medium) have reasonable defaults if you want to defer decisions, but answering them now prevents rework later.

### Next Steps After Clarification

1. Create database migration with `users`, `transactions`, `ratings`, `verifications` tables
2. Design API endpoints: `GET /api/v1/users/:id/profile`, `POST /api/v1/ratings`, `POST /api/v1/verifications/phone`
3. Implement background jobs: rating window expiration, statistics cache updates, auto-confirmation
4. Build React components: ProfileView, RatingForm, VerificationFlow

---

**Happy to do iteration 3 if these answers raise new questions. The spec is in great shape - these are final technical details before implementation.**