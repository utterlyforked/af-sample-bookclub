# User Profiles & Trust System - Product Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification (2025-01-10)
- v1.1 - Iteration 1 clarifications (2025-01-10) - Added: transaction completion triggers, rating workflows, account deletion policy, rating window mechanics, verification processes, anti-gaming measures, profile statistics calculation, rating visibility, borrow counts, neighborhood usage, moderation workflows, bio formatting, date display, and statistics update strategy

---

## Feature Overview

The User Profiles & Trust System is the foundation for building confidence within the ToolShare community. It enables users to establish their identity, showcase their sharing history, and assess the trustworthiness of others before entering into lending relationships.

This feature addresses the core challenge of peer-to-peer tool sharing: trusting strangers with valuable equipment. By providing transparent profile information, verified credentials, and community ratings, we create an environment where tool owners feel confident lending and borrowers can prove their reliability.

The trust system is bidirectional - both borrowers and lenders can rate each other after transactions complete, creating accountability and recognizing good community members. Over time, users build reputation through successful transactions, making it easier to borrow from and lend to more community members.

This feature integrates deeply with borrowing requests (FEAT-02) - profiles are viewed during request review, and ratings are collected after borrow tracking (FEAT-04) completes a transaction cycle.

---

## User Stories

- As a new user, I want to create a profile with my neighborhood and introduction so that others know who I am
- As a tool owner, I want to see a borrower's history and ratings so that I can assess trustworthiness before approving a request
- As a borrower, I want to rate my experience after returning a tool so that good owners are recognized and future borrowers can make informed decisions
- As any user, I want verification badges to identify trusted community members so that I can lend and borrow with confidence
- As a tool owner reviewing a request, I want to quickly see key trust indicators (rating, completed borrows, member duration) so I can make fast approval decisions
- As a user with a good track record, I want my profile to showcase my reliability so that I can access more tools from the community

---

## Acceptance Criteria (UPDATED v1.1)

- Users can create and edit profiles containing: full name, neighborhood, profile photo, and bio (max 300 characters, plain text with line breaks)
- Profile displays key statistics: number of tools owned, total successful borrows as lender, current items borrowed (including overdue), and average rating (5-star scale)
- Both borrowers and lenders can submit 5-star ratings with optional written reviews (max 500 characters) after transaction completion
- Ratings are mutual - both parties rate each other independently within a 7-day window from transaction completion
- Rating window closes 7 days after transaction marked as "Returned - Confirmed" OR auto-confirmed; unsubmitted ratings are forfeited
- Profile shows verification badges: email verified (required at signup), phone verified (optional - v1 implementation), address verified (deferred to v2)
- Full street address is never displayed publicly - only neighborhood name and city are shown
- Approved borrowers receive full address only after request approval for pickup coordination
- Profile displays transaction history showing completed borrows with dates, ratings received (with rater identity visible), and reviews
- Users cannot rate the same transaction twice or edit ratings after submission
- Average rating is simple mean of all ratings received (no time weighting), displays as "New User" until at least 3 rated transactions complete
- Account deletion uses soft-delete: profile shows "[User Unavailable]" but ratings/reviews remain visible and count in other users' averages
- Users with overdue items show warning banner on profile: "⚠️ Has overdue items"
- Problem reports are separate from ratings - both can be submitted for same transaction

---

## Detailed Specifications (UPDATED v1.1)

### Transaction Completion & Rating Triggers

**Decision**: Ratings trigger when transaction reaches "Returned - Confirmed" status, with automatic fallback if lender doesn't confirm within 7 days of due date.

**Rationale**: Protects borrowers from lenders who neglect to confirm returns. Ensures both parties always have opportunity to rate, preventing one party from blocking the rating process. Balances lender control (they confirm condition) with automatic progression (prevents indefinite limbo).

**Transaction Flow Integration**:
- FEAT-04 manages transaction status: "Active" → "Return Initiated by Borrower" → "Returned - Confirmed by Lender"
- When lender confirms return (or 7 days after due date passes without confirmation), transaction status becomes "Returned - Confirmed"
- Status change triggers rating window opening for both parties
- Both parties receive notification: "Rate your experience with [Name] - you have 7 days"

**Automatic Confirmation Logic**:
- If borrower marks "Returned" but lender doesn't respond within 7 days of due date + 7 days grace period (14 days total after due date), system auto-confirms return
- Auto-confirmation prevents lender from blocking rating process by ignoring return notification
- Auto-confirmed transactions trigger same rating flow as manually confirmed

**Edge Case - Lender Never Confirms**:
- Borrower marks returned on due date
- Lender ignores notification for 7 days
- System auto-confirms return on day 8
- Rating window opens automatically
- Transaction appears in both users' history as "Completed (Auto-confirmed)"

**Examples**:
- **Happy Path**: Borrower returns drill on May 15. Lender confirms same day. Both receive rating prompt immediately. 7-day window runs May 15-22.
- **Auto-Confirm Path**: Borrower returns saw on June 1 (due date). Lender doesn't respond. System auto-confirms on June 8. Rating window opens June 8-15.
- **Early Return**: Borrower returns tool June 3 (due date June 10). Lender confirms June 3. Rating window opens immediately, runs June 3-10.

---

### Problem Reports & Ratings (Separate Systems)

**Decision**: Problem reports and ratings are independent - lenders can submit both for the same transaction.

**Rationale**: Problem reports are factual records ("tool returned with cracked handle, see photo"), while ratings are subjective assessments ("1 star - borrower unresponsive about damage"). Both provide valuable but different information. Separating them allows nuance (minor scratch = 4 stars, destroyed tool = 1 star + formal problem report).

**Workflow**:
1. Lender marks return as "Returned with Issues" in FEAT-04
2. Lender fills problem report: issue description, optional photo, damage severity
3. Problem report saved to transaction record
4. Transaction still progresses to "Returned - Confirmed" status
5. Rating window opens normally for both parties
6. Lender separately submits rating (typically low stars) with review explaining issue
7. Borrower can also submit rating (might dispute or acknowledge mistake)

**Display on Profile**:
- Transaction history shows warning icon for transactions with problem reports
- Clicking transaction shows: problem report details + both parties' ratings/reviews
- Problem report visible to anyone viewing transaction, not just the two parties

**Examples**:
- **Minor Issue**: Lender reports "Small scratch on handle (photo attached)" + rates 4 stars "Tool returned with minor damage, but borrower was communicative and apologetic"
- **Major Issue**: Lender reports "Motor burned out, tool non-functional (photo attached)" + rates 1 star "Tool destroyed, borrower denied responsibility"
- **Disputed Issue**: Lender reports damage, rates 2 stars. Borrower rates 5 stars with review "Tool was already damaged when picked up, lender trying to blame me"

---

### Account Deletion & Data Retention

**Decision**: Soft-delete with 30-day grace period, then permanent anonymization. Ratings and reviews remain visible and count in averages.

**Rationale**: Preserves trust system integrity - removing someone's ratings when they delete account would artificially inflate other users' averages and erase valuable trust signals. Soft-delete allows account recovery if user changes mind. After grace period, anonymize personal data but keep transactional/rating data for community benefit.

**Deletion Workflow**:
1. User clicks "Delete Account" in settings
2. Warning shown: "Your account will be deactivated. Ratings and transaction history will remain visible as '[User Unavailable]'. You can reactivate within 30 days."
3. User confirms deletion
4. Immediate effects:
   - `users.deleted_at` timestamp set to current time
   - Profile becomes inaccessible (404 page)
   - User cannot log in
   - Active tool listings set to "Temporarily Unavailable"
   - Pending borrow requests auto-rejected with message "User account no longer active"
5. After 30 days:
   - Background job runs nightly to find `deleted_at > 30 days ago`
   - Personal data anonymized: name → "[User Unavailable]", email → null, phone → null, profile_photo_url → null, bio → null
   - Address kept for transaction history integrity but not displayed
   - user_id preserved for foreign key relationships
   - Transaction history, ratings, and reviews remain unchanged

**What Remains Visible After Deletion**:
- ✅ Ratings given by deleted user (still count in recipients' averages)
- ✅ Ratings received by deleted user (visible on transaction detail pages)
- ✅ Review text written by deleted user (shows as "Review by [User Unavailable]")
- ✅ Transaction history entries (shows "[User Unavailable]" as party name)
- ❌ Profile page (returns 404)
- ❌ Personal information (name, email, phone, photo, bio)
- ❌ Tool listings (removed or hidden)

**Review Text Privacy**:
- Review text is NOT automatically scrubbed on deletion
- Reviews are public community information, not personal data
- If review contains identifying information ("Thanks John at 123 Oak St"), it remains visible
- User can edit/remove reviews before deleting account if desired
- Post-deletion, users cannot edit reviews; must contact support for removal if inappropriate

**Statistics Impact on Other Users**:
- Deleted user's ratings continue counting in other users' average ratings
- Other users' "Tools Shared" counts include completed transactions with deleted user
- Transaction history on other users' profiles shows "[User Unavailable]" as counterparty

**Account Recovery**:
- Within 30 days: User can contact support to reactivate, full restoration
- After 30 days: Personal data anonymized, cannot be recovered
- No automated reactivation - must email support with verification

**Examples**:
- Alice deletes account May 1. Bob (who borrowed from Alice) still sees transaction in history as "Borrowed from [User Unavailable], May 2025, 5 stars". Bob's statistics unchanged.
- Alice's 4.9-star average rating from 30 transactions remains visible on those transaction detail pages as context for the other party's experience.
- Alice's reviews of other users remain visible: "Review by [User Unavailable]: Great tool, easy pickup, highly recommend!"

---

### Rating Window & Visibility Mechanics

**Decision**: Single 7-day window starting at transaction completion. Ratings remain hidden until both submit OR 7 days pass. After 7 days, any submitted ratings become visible and window closes permanently.

**Rationale**: Single deadline is simplest for users to understand ("you have until May 22 to rate"). Hiding ratings until both submit prevents retaliation bias. Seven-day expiration prevents indefinite limbo and encourages timely feedback while memories are fresh.

**Timeline**:
- **Day 0**: Transaction marked "Returned - Confirmed" at 2:00 PM on May 15
- **Day 0-7**: Rating window open. Both parties can submit ratings anytime.
- **Day 7**: Rating window closes at 2:00 PM on May 22 (exactly 168 hours later)
- **After Day 7**: No more rating submissions possible. Transaction permanently marked as complete.

**Visibility Rules**:

**Scenario A - Both parties rate within window**:
- Alice rates on Day 2, Bob rates on Day 4
- Neither sees the other's rating until Bob submits
- Moment Bob submits, both ratings become visible to both parties and on public profiles
- Window still open until Day 7, but ratings already visible and locked

**Scenario B - Only one party rates within window**:
- Alice rates on Day 2, Bob never rates
- Alice doesn't see her own rating on the transaction until Day 7
- Day 7 arrives: Alice's rating becomes visible, Bob's shows "Did not rate"
- Transaction shows in history: Alice gave 5 stars, Bob shows "—" (no rating)

**Scenario C - Neither party rates within window**:
- Day 7 arrives, neither submitted rating
- Transaction shows in history: Both parties show "—" (no rating)
- Transaction does NOT count toward "3 ratings minimum" for exiting "New User" status
- Transaction still counts in "Tools Shared" statistics

**Notifications**:
- **Day 0**: Both parties receive email + in-app: "Rate your experience with [Name] - 7 days remaining"
- **Day 5**: Reminder email to anyone who hasn't rated: "2 days left to rate your transaction with [Name]"
- **Day 7**: Window closes. Email to both: "Rating window closed for [Tool Name] transaction."
- **When both rate**: Instant notification to both: "You can now see [Name]'s rating of your transaction."

**User Experience During Window**:
- User's own submitted rating shows as "Submitted ⏱️ Waiting for [Other Party]" until mutual reveal
- Other party's rating shows as "Pending" until they submit or window closes
- Countdown timer shows: "Rating window closes in 4 days, 3 hours"

**Edge Case - One Party Rates at 11:59 PM on Day 6**:
- Rating submitted at 11:59 PM on Day 6
- Other party has until 2:00 PM on Day 7 (original deadline) to submit
- If they submit, immediate mutual reveal
- If deadline passes, first party's rating becomes visible at 2:00 PM Day 7

**Database Implementation**:
- `transactions.rating_window_opens_at`: Timestamp when transaction confirmed
- `transactions.rating_window_closes_at`: `rating_window_opens_at + 7 days`
- `ratings.created_at`: Timestamp when rating submitted
- `ratings.visible`: Boolean flag, set to true when both ratings submitted OR window closes

**Examples**:
- **Fast Mutual Rating**: Alice rates May 16 at 10 AM. Bob rates May 16 at 3 PM. Both see ratings immediately at 3 PM.
- **Slow Reveal**: Alice rates May 16. Bob doesn't rate. Alice sees her rating become public May 22 at 2 PM (7 days after transaction completion).
- **Procrastinator**: Bob waits until May 22 at 1:30 PM (30 minutes before deadline). Submits rating. Alice's rating (submitted May 16) and Bob's rating both immediately visible.

---

### Verification System Implementation

**Decision**: Email verification required (automatic at signup), phone verification optional (v1), address verification deferred to v2 with "Coming Soon" badge placeholder.

**Rationale**: Email verification is standard security practice and zero friction (user must verify to activate account). Phone verification adds meaningful trust signal without major complexity. Address verification requires manual admin review that doesn't scale and isn't critical for MVP - most trust comes from ratings, not address verification.

**Email Verification** (Required):
- User signs up with email + password
- System sends verification email with unique token link
- User must click link within 24 hours to activate account
- Until verified, user can log in but sees banner: "Verify your email to access all features"
- Unverified users cannot: list tools, send borrow requests, or rate others
- Unverified users can: browse tools, view profiles (read-only mode)
- Badge shows as ✓ Email (green) on profile after verification

**Phone Verification** (Optional):
- User navigates to Profile → Settings → Verification
- Enters phone number (format: US numbers only for v1, international in v2)
- Clicks "Send Verification Code"
- System sends 6-digit SMS code via Twilio (expires in 10 minutes)
- User enters code in form
- If correct: `users.phone_verified_at` timestamp set, badge appears
- If incorrect: Error message, 3 attempts allowed per phone number per 24 hours
- Badge shows as ✓ Phone (blue) on profile after verification

**Phone Verification - Changing Number**:
- User can change phone number in settings
- Changing number immediately removes ✓ Phone badge and sets `users.phone_verified_at` to null
- User must re-verify new number to regain badge
- Rationale: Prevents someone from verifying once, then changing to unverified number while keeping badge

**Phone Verification - SMS Doesn't Arrive**:
- "Didn't receive code? Resend" button (30-second cooldown between attempts)
- After 3 failed deliveries: "Having trouble? Contact support" message
- Support can manually verify phone number after identity check
- Rate limit: 5 SMS sends per phone number per 24 hours (prevents abuse)

**Address Verification** (Deferred to v2):
- Badge shows on profile as grayed-out with tooltip: "Address verification coming soon"
- Settings page shows: "Address Verification - Coming in a future update. We're exploring automated verification options."
- No submission form in v1
- Rationale: Manual admin review is bottleneck, doesn't scale, research automated solutions (identity verification API like Stripe Identity, Persona, or Plaid) for v2

**Future Address Verification Plan (v2)**:
- Integrate with third-party identity verification API
- User uploads government ID photo
- API verifies ID authenticity and extracts address
- Compare extracted address to registered address
- Auto-approve if match, manual review if close-but-not-exact
- Badge shows as ✓ Address (gold) after approval
- Expected turnaround: < 5 minutes for automated approval, 1-2 business days for manual review

**Verification Badge Display**:
- Profile page shows badges in prominent location below name and neighborhood
- Badge icons: ✓ Email (green checkmark), ✓ Phone (blue checkmark), ⏱️ Address (gray clock icon, coming soon)
- Tooltip on hover explains each badge
- Unverified badges don't show at all (not grayed out, just absent) - except Address shows as "coming soon"

**Examples**:
- New user signs up → receives email → clicks link → ✓ Email badge appears → account fully active
- User wants to borrow expensive tool → owner says "I'd prefer verified users" → user adds phone verification → receives SMS → enters code → ✓ Phone badge appears → owner approves request
- User changes phone number from 555-1234 to 555-5678 → ✓ Phone badge disappears → user re-verifies 555-5678 → badge reappears

---

### Anti-Gaming Measures

**Decision**: Launch v1 with basic system integrity protections (no self-rating, no duplicate ratings, no editing). Rely on community reporting and manual monitoring for fraud. Add automated detection in v2 based on observed abuse patterns.

**Rationale**: Don't over-engineer fraud detection before you have data on real attack vectors. MVP focus is legitimate users sharing tools, not sophisticated fraud prevention. Basic protections prevent accidental issues and obvious cheating. Manual monitoring catches coordinated abuse in early days. Build automated detection when you understand actual threats.

**Built-In Protections**:
- ✅ Users cannot rate transactions with themselves (enforced at API level)
- ✅ Unique database constraint on `[transaction_id, rater_id]` prevents duplicate ratings
- ✅ Ratings are immutable after submission (no editing)
- ✅ Email verification required before any platform activity (prevents throwaway accounts)
- ✅ Transaction history is public and auditable (community can spot fake patterns)

**Community Reporting**:
- Users can report suspicious profiles via "Report User" button
- Report form asks: "What's wrong?" with options: "Fake profile", "Suspicious ratings", "Harassment", "Other"
- Reports land in admin queue for manual review
- Admin can: dismiss report, warn user, suspend account, or permanently ban

**Manual Monitoring (MVP)**:
- Weekly admin review of: new accounts with >5 ratings in first week, accounts with all 5-star ratings, same IP addresses across multiple accounts
- Flag suspicious patterns for investigation
- Small community size in early days makes manual monitoring feasible

**Retaliation Ratings**:
- **Decision**: No restriction on rating someone who rated you first
- **Rationale**: Mutual rating is expected behavior. Preventing "retaliation" creates complexity (how long must you wait? what if it's legitimate low rating?). Trust the visibility of patterns (if someone has all 1-star ratings they gave but receives 4-5 stars, community sees they're the problem).
- Both parties rate independently within same 7-day window
- Neither sees the other's rating until both submit or window closes
- If rating seems retaliatory (1 star after receiving 1 star), context is visible in transaction history

**What We're NOT Building in v1**:
- ❌ Automated fraud detection algorithms
- ❌ IP address tracking and duplicate account detection
- ❌ Machine learning models for suspicious rating patterns
- ❌ Blocking/muting users (users can just not approve their requests)
- ❌ Verified ID requirement before rating

**When to Add Automated Detection (v2)**:
- If manual monitoring reveals consistent attack patterns
- If community reports exceed admin capacity to review
- If coordinated fraud impacts user trust (multiple users report same issue)

**Examples of Acceptable Patterns**:
- User A and User B exchange tools frequently, rate each other 5 stars every time → Legitimate friend behavior, not fraud
- New user gets 3 five-star ratings in first week → Could be legitimate (borrowed from neighbors), monitor but don't flag

**Examples of Suspicious Patterns** (Manual Review):
- User creates account, lists 10 expensive tools, gets 20 five-star ratings within 2 weeks, all from brand-new accounts → Flag for investigation
- Two accounts always rate each other 5 stars, never complete transactions with others → Possible coordinated fake ratings

---

### Average Rating Calculation

**Decision**: Simple arithmetic mean of all ratings received, ever. No time weighting, no recency bonuses, no maximum count. Display to 1 decimal place.

**Rationale**: Transparency and simplicity. Users understand "4.8 stars from 47 ratings" immediately. Time weighting adds complexity and feels manipulative ("why did my average change when I didn't get a new rating?"). Lifetime average creates accountability - past mistakes matter, but improve over time as good ratings accumulate.

**Calculation**:
```
Average Rating = SUM(ratings.stars WHERE rated_user_id = X) / COUNT(ratings WHERE rated_user_id = X)
```

**Display Rules**:
- Less than 3 ratings: Show "New User" instead of numeric rating
- 3+ ratings: Show average to 1 decimal place (e.g., "4.8 ★")
- Display format: "4.8 ★ (47 ratings)"
- Both "as lender" and "as borrower" ratings count in single average (no separation)

**Edge Cases**:
- User has 2 ratings (both 5 stars): Shows "New User" (threshold not met)
- User's 3rd rating arrives: Average calculated and displayed as "5.0 ★ (3 ratings)"
- User has 47 ratings averaging 4.83: Displayed as "4.8 ★ (47 ratings)" (rounded to 1 decimal)
- User has 50 old ratings (4.2 average) and 10 recent ratings (5.0 average): Average includes all 60, calculated as 4.3 overall (old ratings have equal weight)

**Why No Time Weighting**:
- Users expect ratings to work like eBay, Amazon, Airbnb (lifetime average)
- Time weighting feels like "the platform is hiding something"
- Early bad ratings create incentive to improve - removing that consequence reduces accountability
- If user genuinely reforms, new good ratings will naturally improve average over time

**Example Evolution**:
- User joins, completes 3 transactions, gets ratings: 5, 5, 4 → Average: 4.7 ★
- Months pass, 20 more transactions, all 5 stars → Average: (14 + 100) / 23 = 4.96 → Displayed as 5.0 ★
- Old lower ratings are diluted by volume of good ratings (natural improvement)

**Cache Strategy** (addresses Q14):
- Store `users.cached_average_rating` and `users.cached_rating_count` columns
- Update via event trigger when new rating submitted
- Background job (Hangfire) recalculates and updates cache
- Profile page loads cached value (no real-time calculation)
- Acceptable staleness: < 5 minutes (background job processes rating events every 1 minute)

---

### Rating Visibility & Identity

**Decision**: Full transparency - rater identity is always visible along with their rating. Transaction history shows: "John Smith rated you 4 stars: 'Tool worked great, pickup was easy.'"

**Rationale**: Transaction history already shows who you interacted with, so hiding rater identity is futile and creates confusion. Transparency creates accountability in both directions - lenders can't unfairly rate borrowers without consequence, borrowers can't trash lenders without visibility. Public ratings encourage fairness and civility.

**Display on Profile**:
- Transaction history entry shows:
  - Other party's name (linked to their profile)
  - Tool name (linked to listing if still active)
  - Transaction dates
  - **Rating received**: "John Smith rated you 4 ★" + review text
  - **Rating given**: "You rated John Smith 5 ★" + review text

**Display in Transaction Detail View**:
- Full transaction page shows both parties' names, photos, and ratings side-by-side
- Anyone can view transaction details via direct link (public info)
- Example: Alice and Bob's transaction shows both their ratings and reviews visible to anyone

**Why Full Transparency**:
- Reduces frivolous negative ratings (knowing your name is attached creates social pressure for fairness)
- Allows community to assess context (if someone has pattern of leaving 1-star ratings, others see that)
- Borrowers/lenders can respond to unfair ratings in their future interactions (explain context to next person)
- Aligns with transparency values of peer-to-peer community

**Trade-offs Accepted**:
- Some users may hesitate to leave honest negative ratings (fear of confrontation)
- Counter: Rating window mechanics prevent retaliation (both rate blindly), and patterns reveal bad actors
- If transparency causes rating avoidance, we'll see it in data (high percentage of "Did not rate" transactions) and can revisit in v2

**Anonymous Ratings - NOT Implemented**:
- Considered hiding rater identity, rejected because:
  - Reduces accountability (easier to leave unfair ratings)
  - Creates suspicion ("who gave me 1 star?!")
  - Loses social benefit (knowing trustworthy people endorsed you)

**Examples**:
- Alice rates Bob 5 stars. Bob sees: "Alice Johnson rated you 5 ★: 'Great borrower, returned drill in perfect condition!'"
- Later borrower reviews Bob's profile, sees Alice's rating, clicks Alice's profile, sees Alice is well-established user (4.9 stars, 30 transactions) → Bob's rating is credible
- If Bob had rated Alice poorly out of spite, Alice's future lenders see Bob also has low rating average → context reveals the issue

---

### Current Borrows Count & Overdue Items

**Decision**: "Current Borrows" statistic includes all unreturned tools (both on-time and overdue). Separate warning banner displays when user has overdue items.

**Rationale**: Keeps statistics simple - "Current Borrows: 3" means "this person currently has 3 tools out". Overdue status is important red flag shown separately, not hidden in statistics. Banner is more visible than trying to interpret numbers.

**Display on Profile**:
```
Tools Owned: 5
Tools Shared: 23
Current Borrows: 3    ← Includes overdue
Member Since: March 2025
```

If user has overdue items, banner shows prominently above statistics:
```
⚠️ This user has overdue items
```

Clicking banner/warning shows detail:
```
Overdue Items (2):
- Circular Saw (due May 10, now 5 days overdue)
- Ladder Extension (due May 12, now 3 days overdue)
```

**Calculation**:
```
Current Borrows = COUNT(transactions WHERE borrower_id = X AND status IN ['Active', 'Return Initiated', 'Overdue'])
```

**Overdue Status**:
- Transaction marked "Overdue" when current_date > due_date AND status still "Active"
- Background job runs nightly to update overdue transactions
- Overdue status does NOT automatically trigger low ratings (ratings are separate, manual)
- Overdue items remain in "Current Borrows" count until lender confirms return

**Edge Cases**:
- User has 2 active borrows (due next week) + 1 overdue borrow → Current Borrows: 3, warning banner shows
- User returns overdue item, lender confirms → Current Borrows decreases, warning banner disappears (if no other overdue)
- User has 0 current borrows but 1 overdue → Current Borrows: 1, warning banner shows (overdue items count as current until returned)

**Warning Banner Appearance**:
- Bright yellow/orange background, visible at top of profile
- Icon: ⚠️ (warning triangle)
- Text: "This user has overdue items" (doesn't specify count publicly to avoid shaming)
- Clicking warning shows full list (for reference during request review)

**Examples**:
- Alice is reviewing Bob's request to borrow her power drill. Bob's profile shows "Current Borrows: 2" and no warning → Bob currently has 2 tools but both on-time → Safe to lend
- Alice reviews Charlie's profile. Shows "Current Borrows: 4" and ⚠️ warning banner. Clicks warning, sees Charlie has 1 tool overdue by 8 days → Alice declines request or messages Charlie first
- After Charlie returns overdue tool, his profile updates: "Current Borrows: 3" (still has 3 other tools), warning disappears → Future lenders don't see the past issue

---

### Neighborhood Information Usage

**Decision**: Neighborhood is display-only in v1. Free-text field, no search/filter functionality, no validation. Users enter whatever they want, appears on profile for trust/familiarity signaling.

**Rationale**: Solves immediate use case (lenders see "this borrower is from my neighborhood" and feel more comfortable) without complex data management or moderation. Geographic search uses lat/long coordinates from address geocoding, not neighborhood name. Avoid premature optimization - see how users actually use neighborhood field before building search features.

**Implementation**:
- `users.neighborhood` VARCHAR(100) field
- Optional at signup (defaults to postal code area if left blank)
- Editable in profile settings anytime
- No validation or normalization (user can enter "Downtown", "Green Valley", "Near the Park", whatever)
- Displayed on profile as: "Neighborhood: Green Valley, Portland, OR"

**What Neighborhood Is NOT Used For**:
- ❌ Filtering tool listings by neighborhood (use lat/long distance instead)
- ❌ Neighborhood-based user groups or communities (v2 feature)
- ❌ Restricting visibility of tools to neighborhood (all tools visible to all users within geocoded distance)

**What Neighborhood IS Used For**:
- ✅ Social signaling on profile ("Oh, they're from my area!")
- ✅ Trust building ("I've heard of Green Valley, that's a nice neighborhood")
- ✅ Context in request review ("Same neighborhood as me, easier to coordinate pickup")

**Proximity Search Note**:
- Tool listings use geocoded lat/long from `users.address` for distance calculations
- Search query: "Show tools within 5 miles of my address"
- Neighborhood name doesn't factor into distance calculation
- If users want to filter by specific neighborhoods, consider in v2 after observing demand

**Future Considerations (v2)**:
- If many users enter similar neighborhood names, offer autocomplete suggestions
- If search by neighborhood is frequently requested, add manual neighborhood tagging (admin defines official names, users select from list)
- If neighborhood becomes organizing principle, build neighborhood pages (see all tools in "Green Valley")

**Examples**:
- User enters "Westside" as neighborhood → Profile displays "Westside, Seattle, WA"
- Another user in same postal code enters "West Seattle" → Different text, but both appear in proximity search results (based on lat/long)
- User leaves neighborhood blank → Defaults to "98117 Area, Seattle, WA" (postal code as fallback