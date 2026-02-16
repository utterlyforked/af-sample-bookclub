# User Profiles & Trust System - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: 2025-01-10

---

## Summary

After reviewing the specification, I've identified **14** areas that need clarification before implementation can begin. These questions address:
- Rating calculation and display logic
- Data privacy and deletion policies
- Transaction completion workflow dependencies
- Address verification process details
- User identity and security concerns
- Edge case handling for ratings and profiles

The spec is quite thorough, but there are critical gaps around how ratings integrate with the transaction lifecycle, what "transaction completion" actually means, and several data retention/privacy decisions that will significantly impact implementation.

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What defines "transaction completion" that triggers rating opportunities?

**Context**: The spec says ratings trigger when borrow status changes to "Returned - Confirmed" but this feature doesn't own the transaction lifecycle (FEAT-04 does). Need to understand:
- Is this an event we subscribe to?
- What's the exact status flow in FEAT-04?
- Can transactions be marked complete without a return confirmation?
- What if lender never confirms return?

**Options**:

- **Option A: Rating trigger is "Lender marks item as returned"**
  - Impact: Simple, single trigger point
  - Trade-offs: Lender controls when ratings open; borrower can't rate if lender never confirms
  - Database: Rating window starts at `transaction.return_confirmed_at`
  
- **Option B: Rating trigger is "Borrower returns + lender confirms OR due date + 7 days passes"**
  - Impact: Automatic fallback if lender doesn't confirm
  - Trade-offs: More complex logic, but protects against lender neglect
  - Database: Need background job to check for auto-trigger conditions
  
- **Option C: Rating trigger is "Transaction reaches any terminal status"**
  - Impact: Ratings possible even for cancelled/disputed transactions
  - Trade-offs: More rating opportunities, but might include incomplete borrows
  - Database: Multiple trigger conditions to handle

**Recommendation for MVP**: Need FEAT-04 transaction status flow documented first, but lean toward **Option B** - protects both parties and ensures ratings always have opportunity to be submitted. Prevents lender from blocking ratings by never confirming return.

---

### Q2: Can users rate transactions that had reported problems?

**Context**: The spec mentions "Transactions with reported issues show warning icon + issue description if lender marked return as having problems" but doesn't clarify if ratings still happen or if problem reports replace ratings.

**Options**:

- **Option A: Problem reports are separate from ratings - both happen**
  - Impact: Lender marks "Returned with damage" AND submits 1-star rating with explanation
  - Trade-offs: More complete data, but two separate forms to fill out
  - Database: `transactions.issue_reported` boolean + `ratings.stars` and `ratings.review_text`
  
- **Option B: Problem reports replace ratings - choose one or the other**
  - Impact: If lender marks "Returned with damage", no star rating - just issue report
  - Trade-offs: Simpler UX, but loses numeric rating data for problem transactions
  - Database: Either `rating` record OR `issue_report` record per transaction per party
  
- **Option C: Problem reports auto-create 1-star ratings**
  - Impact: Marking item as damaged automatically submits 1-star rating; borrower still rates separately
  - Trade-offs: Ensures problems affect rating, but removes nuance (minor scratch = same as destroyed?)
  - Database: `issue_report` triggers automatic `rating` creation

**Recommendation for MVP**: **Option A** - keep them separate. Problem reports are factual ("tool returned with crack in handle"), ratings are subjective ("1 star - tool returned damaged, borrower unresponsive about repair"). Both are valuable signals.

---

### Q3: How do we handle account deletion with respect to ratings and transaction history?

**Context**: Spec says "deleted accounts show '[User Unavailable]' in transaction history; ratings and reviews remain visible (anonymized)". Need details on:
- Do statistics on OTHER users' profiles change when someone deletes account?
- Are deleted user's ratings still counted in averages?
- Can deleted users be re-identified through their review text?

**Options**:

- **Option A: Soft delete - preserve all data, just hide profile**
  - Impact: `users.deleted_at` timestamp; profile returns 404 but user_id still exists in database
  - Trade-offs: Full data integrity preserved, ratings still count, transaction history intact
  - Database: Add `deleted_at` column, filter queries with `WHERE deleted_at IS NULL`
  - Rating calculation: Deleted users' ratings still count in other users' averages
  
- **Option B: Anonymize user data but keep ratings**
  - Impact: Replace name with "[User Unavailable]", delete bio/photo, keep ratings intact
  - Trade-offs: More privacy-friendly, but can't un-delete account
  - Database: Overwrite PII fields with null/placeholder, keep user_id for referential integrity
  - Rating calculation: Ratings preserved and still count
  
- **Option C: Full delete with rating orphaning**
  - Impact: Delete user record, set `ratings.rater_id` to null for orphaned ratings
  - Trade-offs: True deletion, but breaks referential integrity and complicates queries
  - Database: Nullable foreign keys, complex query logic to handle orphaned records
  - Rating calculation: Orphaned ratings still count but can't trace back to user

**Recommendation for MVP**: **Option A (soft delete)** - preserves data integrity, enables account restoration if user changes mind within 30 days, and avoids complex migration logic. Make it permanent after 30-day grace period if you want GDPR compliance path.

**Follow-up needed**: Does "anonymized" mean we keep the actual review text? If review says "Thanks John for lending me the drill, your house on 123 Oak St was easy to find!" that's not really anonymous. Should we strip reviews on deletion?

---

### Q4: What's the exact 7-day rating window logic when only one party submits?

**Context**: Spec says "Neither party sees the other's rating until both submit OR 7 days pass (whichever comes first)". Need clarification on visibility timing and notification behavior.

**Options**:

- **Option A: 7-day window from transaction completion**
  - Impact: Window opens when transaction marked complete, closes 7 days later
  - Trade-offs: Simple, but both parties see same deadline
  - Implementation: Single `rating_window_closes_at` timestamp
  
- **Option B: 7-day window from first rating submission**
  - Impact: Alice rates on Day 1, Bob has until Day 8 total (7 days after Alice)
  - Trade-offs: Extends window for second rater, more fair but complex
  - Implementation: `first_rating_submitted_at` + 7 days OR `transaction_completed_at` + 14 days
  
- **Option C: Independent 7-day windows for each party**
  - Impact: Alice has 7 days from completion, Bob has 7 days from completion, windows independent
  - Trade-offs: Could have Alice rate on Day 7, Bob never rates - when does Alice's rating become visible?
  - Implementation: Per-user rating deadlines, complex visibility rules

**Recommendation for MVP**: **Option A** - simplest to implement and understand. Both parties get notification "You have 7 days to rate this transaction" with same countdown. If only one submits, that rating becomes visible after 7 days.

**Clarification needed**: If Bob rates on Day 2 but Alice never rates, does Bob's rating show immediately on Day 8, or do we wait longer since Alice still *could* rate?

---

### Q5: How do phone and address verification actually work from user perspective?

**Context**: Spec mentions SMS codes for phone and "admin manually reviews" for address, but missing critical workflow details.

**Phone Verification Questions**:
- Can users verify multiple phone numbers or just one?
- Can they change phone number after verification?
- Does changing phone number remove the badge until re-verified?
- What happens if SMS doesn't arrive (retry mechanism)?

**Address Verification Questions**:
- What exactly does user submit for address verification?
- Photo of utility bill? Government ID? Both?
- What's the submission interface?
- How does admin verify - what do they check against?
- What's the rejection message if verification fails?
- Can user retry immediately or is there a cooldown?

**Options**:

- **Option A: Phone = one number at a time, changing requires re-verification**
  - Impact: `users.phone` and `users.phone_verified_at` - changing phone sets verified_at to null
  - Trade-offs: Simple, but annoying if user legitimately changes numbers
  
- **Option B: Phone = verify once, badge permanent even if number changes**
  - Impact: Badge means "has verified A phone number at some point"
  - Trade-offs: Easier UX, but badge becomes less meaningful over time

**Address Verification Options**:

- **Option A: User uploads photo of utility bill, admin compares to registered address**
  - Impact: Need file upload, image storage, admin review queue with approve/reject
  - Trade-offs: Standard approach, but slow and manual
  
- **Option B: Defer address verification to v2 - mark as "Coming Soon" in v1**
  - Impact: Show badge slot grayed out with "Address verification available soon"
  - Trade-offs: Simpler v1, but loses trust signal for high-value tools

**Recommendation for MVP**: 

**Phone**: **Option A** - one phone number, re-verify on change. Clear and secure.

**Address**: **Option B** - defer to v2. Manual admin review is a bottleneck and doesn't scale. Mark as "coming soon" and research automated options (integrate with identity verification API) for v2.

**Alternative for Address**: If you want address verification in v1, need detailed spec on:
1. Exact upload requirements (accepted file types, size limits)
2. What admin sees in review queue
3. Approval criteria documentation for admins
4. User-facing explanation of what to submit

---

### Q6: What prevents rating manipulation and gaming?

**Context**: Spec has some protections (can't rate same transaction twice, can't edit after submission) but missing several attack vectors.

**Potential Issues**:
- User creates multiple accounts, borrows from themselves, gives self 5-star ratings
- User coordinates with friend to do fake transactions for rating boost
- User deletes account and recreates to reset bad ratings
- User retaliates with 1-star rating because they received 1-star

**Options**:

- **Option A: Trust the system as-is - rely on community reporting**
  - Impact: No additional anti-gaming measures
  - Trade-offs: Simple, but vulnerable to manipulation
  
- **Option B: Add basic fraud detection flags**
  - Impact: Flag suspicious patterns (same IP addresses, rapid rating exchanges, new account with many high ratings)
  - Trade-offs: Some complexity, but catches obvious manipulation
  - Implementation: Admin review queue for flagged accounts
  
- **Option C: Require verified phone/address before rating others**
  - Impact: Only verified users can submit ratings
  - Trade-offs: Stronger trust, but creates friction for new users

**Recommendation for MVP**: **Option A** with manual monitoring. Build the system, monitor for abuse in early days, add automated detection in v2 when you see real patterns. Don't over-engineer before you have data.

**However**: Need answer on retaliation ratings - should there be a rule like "You cannot rate someone who has already rated you until X hours pass"? Or is mutual rating acceptable even if one person clearly retaliated?

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q7: What's the calculation when a user has both positive and negative ratings in the recent period?

**Context**: Spec says "average rating calculation excludes transactions without ratings and displays as 'New User' until at least 3 rated transactions complete" but doesn't specify:
- Is it simple mean of all ratings ever, or weighted by recency?
- Do old ratings expire or decrease in weight over time?
- Is there a maximum number of ratings considered (e.g., last 50)?

**Options**:

- **Option A: Simple mean of all ratings, no time weighting**
  - Impact: `AVG(ratings.stars) WHERE rated_user_id = X`
  - Trade-offs: Simple but 50 old ratings dilute recent improvement
  - Database: Straightforward query or cached value
  
- **Option B: Weighted by recency - last 90 days worth more**
  - Impact: Recent ratings weighted 2x, older ratings weighted 1x
  - Trade-offs: Reflects current behavior better, but more complex
  - Database: Need `ratings.created_at` in calculation
  
- **Option C: Rolling window - only last 50 ratings count**
  - Impact: `AVG(latest 50 ratings)` - older ratings don't count
  - Trade-offs: Caps influence of very old ratings, but might seem arbitrary
  - Database: Subquery for latest N ratings per user

**Recommendation for MVP**: **Option A** - simple mean of all ratings. It's transparent, easy to understand, and aligns with user expectations ("I have 4.8 stars from 47 ratings"). Can add recency weighting in v2 if users complain about inability to recover from early mistakes.

---

### Q8: Can users see WHO rated them, or just the aggregate rating?

**Context**: Spec shows transaction history with "Rating received" but doesn't clarify if the rater's identity is visible.

**Options**:

- **Option A: Full transparency - show who rated you and their rating**
  - Impact: "John Smith rated you 5 stars: 'Great borrower!'"
  - Trade-offs: Complete transparency, but might discourage honest negative ratings (fear of retaliation)
  
- **Option B: Anonymous ratings - can't see who rated you**
  - Impact: Just see "You received 4 stars on [transaction]" without rater identity
  - Trade-offs: More honest ratings, but less accountability and no context
  
- **Option C: Show identity only after mutual rating or window closes**
  - Impact: Blind rating during window, revealed after
  - Trade-offs: Balances honesty during rating period with transparency after

**Recommendation for MVP**: **Option A** - full transparency. The transaction history already shows who you interacted with, so hiding the rater's identity is futile and confusing. Plus, accountability cuts both ways - knowing your rating is public encourages fairness.

---

### Q9: What happens to "Current Borrows" count when due date passes but item not returned?

**Context**: Profile shows "Current Borrows: Count of tools this user currently has borrowed (due date not yet passed)" but also mentions "Users with overdue items show warning indicator".

**Questions**:
- Does "Current Borrows" include overdue items?
- If someone has 2 active borrows (not yet due) and 1 overdue, what's displayed?
- Is there a separate "Overdue Items" count?

**Options**:

- **Option A: "Current Borrows" includes overdue items**
  - Impact: Count includes all unreturned tools regardless of due date
  - Trade-offs: Simple, but doesn't distinguish on-time vs. overdue
  - Display: "Current Borrows: 3 (⚠️ 1 overdue)"
  
- **Option B: Split into "Current Borrows" and "Overdue Items"**
  - Impact: Two separate counts on profile
  - Trade-offs: More precise, but clutters profile stats
  - Display: "Current Borrows: 2 | Overdue Items: 1"
  
- **Option C: Hide overdue from "Current Borrows", show only warning**
  - Impact: Count only includes on-time borrows; overdue items hidden in count but shown in warning banner
  - Trade-offs: Could be misleading (why is count lower than reality?)

**Recommendation for MVP**: **Option A** - "Current Borrows" includes overdue, but show warning separately: "⚠️ Has overdue items" as a prominent banner. Keep stats simple, use warning for red flag.

---

### Q10: How is neighborhood information used beyond display?

**Context**: Spec says users can customize neighborhood name (e.g., "Green Valley" instead of postal code), but doesn't explain:
- Is this searchable/filterable?
- Can users browse tools by neighborhood?
- Do neighborhood names have validation (free text or predefined list)?
- How do we handle duplicates (two users both call their area "Downtown")?

**Options**:

- **Option A: Neighborhood is display-only, no search/filter functionality**
  - Impact: Just a string field on user profile, no indexing needed
  - Trade-offs: Simplest for v1, but loses potential discovery feature
  
- **Option B: Neighborhood is searchable - users can filter tools by neighborhood name**
  - Impact: Need indexing, but free-text means duplicates/misspellings/inconsistency
  - Trade-offs: Useful feature, but messy data without moderation
  
- **Option C: Predefined neighborhood list per city**
  - Impact: Admin defines official neighborhood names, users select from dropdown
  - Trade-offs: Clean data, but requires initial setup and maintenance

**Recommendation for MVP**: **Option A** - display-only for v1. Users enter whatever they want, it shows on profile, but no search/filter functionality yet. Solves the immediate use case (lenders know "this borrower is from my neighborhood") without complex data management. Add filtering in v2 when you understand real usage patterns.

**Note**: You mentioned geocoding address to lat/long for "proximity calculations" but didn't specify what those calculations are. Is there a distance-based search feature I'm missing? If so, that's a separate question.

---

### Q11: What's the moderation workflow for reported profiles, photos, and reviews?

**Context**: Spec mentions users can report inappropriate photos and reviews, but doesn't detail:
- How do users report (button? form? categories?)
- What happens after report submitted?
- Who reviews reports and how quickly?
- What actions can moderators take?
- Does reported user get notified?

**Options**:

- **Option A: Simple report queue - admin manually reviews all reports**
  - Impact: "Report" button → confirmation → lands in admin queue → admin decides
  - Trade-offs: Works for small scale, but doesn't scale with growth
  
- **Option B: Automated thresholds - X reports triggers auto-action**
  - Impact: 3 reports on same photo → auto-hide until admin reviews
  - Trade-offs: Faster response, but vulnerable to brigading/abuse
  
- **Option C: Category-based reporting with different workflows**
  - Impact: "Spam" → auto-hide, "Inappropriate content" → urgent review, "Incorrect info" → low priority
  - Trade-offs: More sophisticated, but complex to build

**Recommendation for MVP**: **Option A** - simple report queue. Build basic admin panel with:
- List of reports (photo/review text, reporter, reason, date)
- Actions: "Dismiss report", "Hide content", "Warn user", "Suspend account"
- Email notification to reported user when action taken

Keep it simple for v1, add automation when report volume justifies it.

**Question for Product**: What's the expected moderation SLA? Same-day review? 48 hours? Helps prioritize urgency of tooling.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q12: How does bio field handle special characters, line breaks, and URLs?

**Context**: Spec says "Bio field accepts plain text only (no rich formatting), max 300 characters" but doesn't specify:
- Are line breaks allowed (enter key creates `<br>`)?
- Are URLs auto-linked or displayed as plain text?
- Are emojis allowed?
- Is HTML escaped/sanitized?

**Options**:

- **Option A: Plain text only - no line breaks, no links, no emojis**
  - Impact: Single `<p>` tag with escaped text
  - Trade-offs: Safest but least expressive
  
- **Option B: Plain text with line breaks preserved**
  - Impact: Convert `\n` to `<br>` on display
  - Trade-offs: Allows basic formatting without XSS risk
  
- **Option C: Plain text with auto-linked URLs**
  - Impact: Detect URLs and wrap in `<a>` tags on display
  - Trade-offs: More useful but need URL validation

**Recommendation for MVP**: **Option B** - allow line breaks, but convert URLs to plain text (no clickable links to prevent phishing). Emojis allowed as they're just Unicode characters. Standard HTML escaping for XSS protection.

---

### Q13: What's the format for displaying "Member Since" date?

**Context**: Spec says "Member since [Month Year]" but this affects how users assess trustworthiness.

**Options**:

- **Option A: Month + Year only**
  - Display: "Member since January 2025"
  - Impact: Hides specific day, rounds to month
  
- **Option B: Relative time for recent, absolute for older**
  - Display: "Member for 3 months" (if < 12 months), then "Member since Jan 2024"
  - Impact: More intuitive for recent members
  
- **Option C: Always relative**
  - Display: "Member for 8 months" or "Member for 2 years"
  - Impact: Easy to parse, but less precise

**Recommendation for MVP**: **Option A** - "Member since [Month Year]" as specified. Simple, unambiguous, aligns with spec. Don't overthink it.

---

### Q14: Should profile stats update in real-time or have acceptable delay?

**Context**: Spec says "Statistics update in real-time as transactions complete" but this could mean:
- Immediate database recalculation on every page load
- Cached with periodic refresh
- Event-driven updates

**Options**:

- **Option A: Compute on every profile view**
  - Impact: `COUNT(*)` queries on every page load
  - Trade-offs: Always accurate, but database load for popular users
  
- **Option B: Cache statistics, refresh on relevant events**
  - Impact: `users.cached_stats` JSON column updated when transaction completes or rating submitted
  - Trade-offs: Fast reads, slightly stale data (seconds to minutes)
  
- **Option C: Nightly batch update**
  - Impact: Background job recalculates all user stats once per day
  - Trade-offs: Minimal load, but stats could be 24h stale

**Recommendation for MVP**: **Option B** - event-driven cache updates. When transaction completes, rating submitted, or tool added/removed, trigger background job to recalculate that user's stats and cache in user table. Fast profile loads, acceptably fresh data (within minutes). Use the Hangfire background job system from your stack.

---

## Notes for Product

- **Transaction lifecycle dependency**: Questions Q1, Q2, and Q4 are blocked until we have FEAT-04's transaction status flow documented. Suggest reviewing that feature spec next and ensuring it explicitly defines the "Returned - Confirmed" state and what triggers it.

- **Address verification scope**: Strongly recommend deferring address verification (Q5) to v2 unless you have dedicated admin resources for manual reviews. This will be a bottleneck and doesn't provide enough value for MVP if phone verification is available.

- **Privacy vs. transparency**: Questions Q3, Q8, and Q12 all involve balancing openness (builds trust) with privacy (protects users). Recommend leaning toward transparency for MVP since peer-to-peer sharing requires trust, but be prepared to add privacy controls in v2 if users push back.

- **Anti-gaming measures** (Q6): Don't over-engineer fraud detection for v1. Launch with basic system, monitor manually, add automated detection when you see real abuse patterns.

- **If any answers conflict with previous iterations, please flag it** - this is iteration 1, so no conflicts yet.

- **Happy to do another iteration if these answers raise new questions** - expect Q1/Q2/Q4 answers to generate follow-ups about transaction integration.

Once these are answered, the feature will be ready for detailed engineering specification.