# User Profiles & Trust System - Product Requirements (v1.2)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: rating workflow, deletion policies, verification flow, statistics caching)
- v1.2 - Iteration 2 clarifications (added: transaction completion mechanics, timezone handling, phone verification limits, statistics update strategy)

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

## Acceptance Criteria (UPDATED v1.2)

- Users can create and edit profiles containing: full name, neighborhood, profile photo, and bio (max 300 characters)
- Profile displays key statistics: number of tools owned, total successful borrows as lender, current items borrowed, and average rating (5-star scale)
- Both borrowers and lenders can submit 5-star ratings with optional written reviews (max 500 characters) after transaction completion
- Ratings are mutual - both parties rate each other independently after a borrow is marked complete
- Profile shows verification badges: email verified (required at signup), phone verified (optional), address verified (optional)
- Full street address is never displayed publicly - only neighborhood name and city are shown
- Approved borrowers receive full address only after request approval for pickup coordination
- Profile displays transaction history showing completed borrows with dates, ratings received, and reviews
- Users cannot rate the same transaction twice or edit ratings after submission
- Average rating calculation excludes transactions without ratings and displays as "New User" until at least 3 rated transactions complete
- **Due dates are immutable once transactions start - no extensions or modifications** (v1.2)
- **Rating windows close exactly 168 hours after transaction confirmation, regardless of timezone** (v1.2)
- **Phone verification limited to 3 incorrect code attempts and 5 SMS sends per phone number per 24-hour period** (v1.2)
- **Profile statistics cached and updated every 1 minute via background job for optimal performance** (v1.2)

---

## Detailed Specifications (UPDATED v1.2)

### Transaction Completion & Due Date Mechanics

**Decision**: Due dates are **immutable** after transaction creation. No extensions, no modifications.

**Rationale**: Simplicity for MVP. Clear expectations for both parties - when you approve a request, the due date is locked. If borrowers need more time, they must negotiate with lender *before* the due date, who can choose to create a new transaction or handle it informally. Prevents gaming the system with infinite extensions.

**Implementation**:
- `transactions.due_date` set at request approval time (defined by FEAT-02)
- `transactions.auto_confirm_at` calculated as `due_date + 14 days` (7 days past due + 7 days grace)
- Background job runs hourly, checks for transactions where `NOW() > auto_confirm_at AND status = 'Return Initiated'`
- Auto-confirmation sets `status = 'Returned - Confirmed'` and `confirmed_at = NOW()`
- Rating window opens immediately: `rating_window_closes_at = confirmed_at + 168 hours`

**Example Flow**:
1. **May 10**: Request approved, due date set to **May 14, 3:00 PM**
2. **May 14, 3:00 PM**: Due date passes (borrower has tool)
3. **May 21, 3:00 PM**: Auto-confirmation deadline (14 days from due date)
4. **May 22, 10:00 AM**: Borrower clicks "Mark as Returned"
5. **May 22, 2:00 PM**: Lender confirms return → Status becomes "Returned - Confirmed" → Rating window opens
6. **May 29, 2:00 PM**: Rating window closes (exactly 168 hours later)

**Edge Cases**:
- **Borrower never marks as returned**: After `auto_confirm_at`, status auto-transitions to "Returned - Confirmed" even without borrower action
- **Lender never confirms return**: Same as above - auto-confirmation after `auto_confirm_at`
- **Problem report during return**: Lender clicks "Report Problem" → Submits report → Status **immediately** becomes "Returned - Confirmed" → Rating window opens (problem report is implicit confirmation; see Q3 answer below)

**Database Columns**:
```csharp
// transactions table
due_date TIMESTAMP NOT NULL              // Immutable, set at creation
auto_confirm_at TIMESTAMP NOT NULL       // due_date + 14 days
confirmed_at TIMESTAMP NULL              // When status became "Returned - Confirmed"
rating_window_closes_at TIMESTAMP NULL   // confirmed_at + 168 hours
```

---

### Rating Window Timezone Handling

**Decision**: Rating windows are **168 hours exactly** from transaction confirmation, timezone-agnostic.

**Rationale**: Fairness and simplicity. Every user gets the exact same duration (7 days = 168 hours), regardless of timezone. Database stores UTC timestamps, no timezone math required. Countdown timers are intuitive ("4 days, 3 hours remaining").

**Implementation**:
- All timestamps stored as `TIMESTAMP` (UTC) in PostgreSQL
- `rating_window_closes_at = confirmed_at + INTERVAL '168 hours'`
- Frontend displays countdown timer: "Rating closes in 4 days, 3 hours"
- Notifications sent at user's local time using their profile timezone preference

**Example**:
- **Transaction confirms**: May 15, 2:00 PM UTC
- **Alice (Pacific Time, UTC-7)**: Sees "Rating closes May 22 at 7:00 AM" (2:00 PM UTC = 7:00 AM PST)
- **Bob (Eastern Time, UTC-4)**: Sees "Rating closes May 22 at 10:00 AM" (2:00 PM UTC = 10:00 AM EST)
- **Actual close time**: May 22, 2:00 PM UTC (same absolute moment for both)

**Notifications**:
- **Day 5 reminder** (May 20, 2:00 PM UTC): Both receive email at their local times
  - Alice: Delivered May 20, 7:00 AM PST ("2 days remaining")
  - Bob: Delivered May 20, 10:00 AM EST ("2 days remaining")
- **Expiration**: Both windows close at same UTC moment, converted to local time for display

**Display Logic**:
```typescript
// Frontend countdown component
const hoursRemaining = Math.floor(
  (ratingWindowClosesAt.getTime() - Date.now()) / (1000 * 60 * 60)
);
const daysRemaining = Math.floor(hoursRemaining / 24);
const hoursRemainingToday = hoursRemaining % 24;

return `${daysRemaining} days, ${hoursRemainingToday} hours remaining`;
```

**Trade-off Acknowledged**: The "closes at 2:00 PM on May 22" in the spec was an example, not a requirement. Actual close time depends on when the transaction was confirmed. This is clearer for users ("you have 7 days from now") than calendar-based deadlines ("you have until end of day May 22").

---

### Problem Reports & Transaction Confirmation

**Decision**: Submitting a problem report **immediately** transitions transaction to "Returned - Confirmed" status.

**Rationale**: Problem report submission is implicit confirmation that the lender has inspected the tool and verified it's back in their possession. No need for separate "Confirm Return" button after reporting problems - that's redundant. Keeps workflow simple and linear.

**Workflow**:
1. Borrower clicks "Mark as Returned" → Status becomes "Return Initiated"
2. Lender has 3 options:
   - **Option A**: Click "Confirm Return (No Issues)" → Status becomes "Returned - Confirmed"
   - **Option B**: Click "Report Problem" → Problem report form appears
   - **Option C**: Do nothing → Auto-confirmation after 7 days past due date
3. If lender chooses **Option B**:
   - Fill out problem report form (select issue type, add description, upload photos)
   - Click "Submit Report"
   - **Immediately**: Status becomes "Returned - Confirmed", `confirmed_at = NOW()`
   - Problem report saved as metadata on transaction: `transactions.problem_report_id → problem_reports.id`
   - Rating window opens (both parties can now rate)

**Status Flow**:
```
Active → Return Initiated → [Problem Report Submitted] → Returned - Confirmed → Rating Window Open → Ratings Complete/Expired
                         OR [Confirm No Issues]    ↗
                         OR [Auto-Confirm]        ↗
```

**Database Schema**:
```csharp
// transactions table
status ENUM('Active', 'Return Initiated', 'Returned - Confirmed', 'Cancelled')
problem_report_id INT NULL REFERENCES problem_reports(id)
confirmed_at TIMESTAMP NULL

// problem_reports table (owned by FEAT-04)
id SERIAL PRIMARY KEY
transaction_id INT NOT NULL REFERENCES transactions(id)
reported_by INT NOT NULL REFERENCES users(id)  // Always lender
issue_type ENUM('damage', 'missing_parts', 'not_cleaned', 'late_return', 'other')
description TEXT NOT NULL
photo_urls TEXT[]
created_at TIMESTAMP NOT NULL
```

**Visibility**:
- Problem report visible to **both parties** after submission (transparency)
- Problem report affects lender's rating decision ("tool was damaged") but doesn't prevent rating
- Borrower sees: "Lender reported an issue: [description]" on their transaction history
- Transaction history shows: "Completed with reported issue: [issue_type]"

**Future Consideration (v2)**: Dispute resolution if borrower contests problem report. For v1, problem reports are informational only - no financial penalties or automated consequences.

---

### Concurrent Rating Submission

**Decision**: Use **eventual consistency** with 1-minute background job to handle mutual rating visibility.

**Rationale**: Simplicity and reliability. The sub-minute delay before mutual reveal is acceptable - users don't expect instant visibility anyway. Avoids complex database locking and potential deadlocks. Background job infrastructure already needed for statistics updates.

**Implementation**:
- Rating submission inserts row into `ratings` table with `visible = false`
- Background job (Hangfire recurring job, runs every 1 minute) checks for transactions with `COUNT(ratings) = 2 AND any rating has visible = false`
- Job updates both ratings: `UPDATE ratings SET visible = true WHERE transaction_id = X`
- Frontend polls for visibility change or uses WebSocket notification

**Workflow**:
```
10:00:00 AM - Alice submits rating for Transaction #123
            → INSERT INTO ratings (transaction_id=123, rater_id=1, stars=5, visible=false)
            → Alice sees: "Thanks! Your rating will be visible after Bob rates or in 7 days."

10:00:15 AM - Bob submits rating for Transaction #123
            → INSERT INTO ratings (transaction_id=123, rater_id=2, stars=4, visible=false)
            → Bob sees: "Thanks! Your rating will be visible after Alice rates or in 7 days."

10:01:00 AM - Background job runs
            → Detects Transaction #123 has 2 ratings, both invisible
            → UPDATE ratings SET visible=true WHERE transaction_id=123
            → Both Alice and Bob can now see each other's ratings

10:01:05 AM - Alice refreshes page → Sees Bob's 4-star rating and review
```

**Edge Case - Exact Same Second Submission**:
- Both inserts succeed (PostgreSQL handles concurrent inserts to `ratings` table)
- Background job finds 2 ratings on next run, flips visibility for both
- No race condition possible - job uses single UPDATE statement with WHERE clause

**Alternative Considered**: Serializable transactions with row locking for instant visibility. Rejected due to complexity and deadlock risk for minimal UX gain (1-minute delay is acceptable).

**Database Constraint**:
```sql
-- Prevent duplicate ratings from same user for same transaction
CREATE UNIQUE INDEX idx_ratings_unique 
ON ratings(transaction_id, rater_id);
```

---

### Phone Verification Limits & Security

**Decision**: **Separate limits** - 3 incorrect code attempts AND 5 SMS sends, both per phone number per 24 hours.

**Rationale**: Balances fraud prevention (stops brute force attacks on codes, prevents SMS spam) with legitimate use cases (user typos code, needs resend due to SMS delay). Separate limits are clearer: "You can request new codes up to 5 times" vs "You can enter wrong codes up to 3 times".

**Limits**:
1. **SMS Send Limit**: 5 sends per phone number per 24 hours
   - Includes initial send + 4 resends
   - "Didn't receive code?" button disabled after 5th send
   - Error: "Too many verification attempts. Try again after [timestamp]."

2. **Incorrect Code Limit**: 3 wrong code entries per phone number per 24 hours
   - Across all verification attempts (not reset when new code sent)
   - After 3rd wrong entry: "Too many incorrect codes. For security, phone verification is locked for 24 hours. Contact support if you need help."

**Implementation**:
```csharp
// users table
phone_verification_attempts JSONB NULL
// Structure: 
// {
//   "sms_sends": ["2025-01-10T14:30:00Z", "2025-01-10T14:35:00Z"],
//   "wrong_codes": ["2025-01-10T14:32:00Z"],
//   "locked_until": null
// }

// Verification flow
1. User enters phone number, clicks "Send Code"
2. Check: COUNT(sms_sends in last 24h) < 5?
   - If NO: Show error, disable button
   - If YES: Send SMS via Twilio, append timestamp to sms_sends array
3. User enters 6-digit code, clicks "Verify"
4. Check: COUNT(wrong_codes in last 24h) < 3?
   - If NO: Show error, set locked_until = NOW() + 24 hours
   - If YES: Validate code
5. If code wrong: Append timestamp to wrong_codes array, show "Incorrect code (X/3 attempts remaining)"
6. If code correct: Set phone_verified=true, clear verification_attempts, add verification badge
```

**Background Job**:
- Runs every hour
- Clears `phone_verification_attempts` where all timestamps > 24 hours old
- Removes `locked_until` where timestamp has passed

**Resend Logic**:
- "Didn't receive code?" button enabled after 30 seconds from last send
- Each resend counts toward 5-send limit
- New code invalidates previous code (only most recent code is valid)

**Error Messages**:
- After 1st wrong code: "Incorrect code. 2 attempts remaining."
- After 2nd wrong code: "Incorrect code. 1 attempt remaining. Make sure you're entering the code from the most recent text message."
- After 3rd wrong code: "Too many incorrect attempts. Phone verification is locked for 24 hours. If you need help, contact support@toolshare.com."
- After 5th SMS send: "Verification limit reached. You can try again after [timestamp]. If you're having issues receiving codes, contact support."

**Security Consideration**: Phone number changes are allowed but reset verification status. User must re-verify new number. This prevents takeover attacks where attacker changes phone to their own number.

---

### Profile Statistics Caching Strategy

**Decision**: **All statistics cached** in `users` table, updated every 1 minute via background job.

**Rationale**: Profile views are high-frequency (every time someone reviews a borrow request), so optimize for read speed. Sub-minute staleness is acceptable - "Tools Shared: 23" vs "Tools Shared: 24" doesn't materially affect trust decisions. Single SELECT on `users` table is faster than 4 COUNT queries.

**Cached Columns**:
```csharp
// users table
cached_tools_owned INT NOT NULL DEFAULT 0
cached_tools_shared INT NOT NULL DEFAULT 0
cached_current_borrows INT NOT NULL DEFAULT 0
cached_average_rating DECIMAL(3,2) NULL  // e.g., 4.73
cached_rating_count INT NOT NULL DEFAULT 0
stats_last_updated TIMESTAMP NOT NULL
```

**Background Job (Hangfire Recurring Job)**:
```csharp
// Runs every 1 minute
RecurringJob.AddOrUpdate(
    "update-user-statistics",
    () => UpdateUserStatistics(),
    "*/1 * * * *"  // Every 1 minute
);

// Job logic
public async Task UpdateUserStatistics()
{
    // Find users with recent activity (optimization: don't recalculate everyone)
    var activeUserIds = await db.Transactions
        .Where(t => t.UpdatedAt > DateTime.UtcNow.AddMinutes(-5))
        .Select(t => new[] { t.BorrowerId, t.LenderId })
        .SelectMany(ids => ids)
        .Distinct()
        .ToListAsync();

    foreach (var userId in activeUserIds)
    {
        // Calculate statistics
        var toolsOwned = await db.Tools
            .CountAsync(t => t.OwnerId == userId && t.Status == ToolStatus.Available);
        
        var toolsShared = await db.Transactions
            .CountAsync(t => t.LenderId == userId && t.Status == TransactionStatus.ReturnedConfirmed);
        
        var currentBorrows = await db.Transactions
            .CountAsync(t => t.BorrowerId == userId && t.Status == TransactionStatus.Active);
        
        var ratings = await db.Ratings
            .Where(r => r.RatedUserId == userId && r.Visible)
            .ToListAsync();
        
        var avgRating = ratings.Any() ? ratings.Average(r => r.Stars) : (decimal?)null;
        var ratingCount = ratings.Count;

        // Update cache
        await db.Users
            .Where(u => u.Id == userId)
            .ExecuteUpdateAsync(u => u
                .SetProperty(x => x.CachedToolsOwned, toolsOwned)
                .SetProperty(x => x.CachedToolsShared, toolsShared)
                .SetProperty(x => x.CachedCurrentBorrows, currentBorrows)
                .SetProperty(x => x.CachedAverageRating, avgRating)
                .SetProperty(x => x.CachedRatingCount, ratingCount)
                .SetProperty(x => x.StatsLastUpdated, DateTime.UtcNow)
            );
    }
}
```

**Immediate Update Triggers** (Optional Optimization):
- When tool listed/delisted: Enqueue job to update that user's `cached_tools_owned` immediately
- When transaction confirmed: Enqueue job to update both users' `cached_tools_shared` and `cached_current_borrows`
- When rating submitted: Enqueue job to update rated user's `cached_average_rating`

This gives **best-of-both-worlds**: sub-second updates for important events, plus 1-minute background job as safety net to catch any missed updates.

**Profile API Response**:
```json
GET /api/v1/users/123/profile

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
    "lastUpdated": "2025-01-10T15:42:00Z"  // For debugging staleness
  },
  "verifications": {
    "email": true,
    "phone": true,
    "address": false
  }
}
```

**UI Display**:
- No "last updated" timestamp shown to users (they don't care)
- Admin panel shows `stats_last_updated` for debugging cache issues
- If cache is > 5 minutes stale, show warning in admin panel

---

### Text Field Sanitization & Character Limits

**Decision**: Strip all HTML tags, preserve line breaks, allow emojis. Character count using UTF-8 text elements.

**Rationale**: Aligns with "plain text with line breaks" requirement. Safe from XSS attacks. Emojis are common in casual communication ("Thanks! 😊") and should be allowed. Line breaks enable readable paragraphs without allowing rich formatting.

**Implementation**:
```csharp
// Sanitization service
public class TextSanitizer
{
    public static string SanitizeBio(string input)
    {
        if (string.IsNullOrWhiteSpace(input)) return "";
        
        // Strip all HTML tags
        var withoutHtml = Regex.Replace(input, "<.*?>", "");
        
        // Normalize line breaks (handle \r\n, \r, \n)
        var normalized = withoutHtml.Replace("\r\n", "\n").Replace("\r", "\n");
        
        // Limit consecutive line breaks (max 2 = 1 blank line)
        var limitedBreaks = Regex.Replace(normalized, "\n{3,}", "\n\n");
        
        // Trim whitespace
        var trimmed = limitedBreaks.Trim();
        
        // Enforce character limit (counting text elements for emoji support)
        if (new StringInfo(trimmed).LengthInTextElements > 300)
        {
            // Truncate at 300 text elements (emoji = 1 element)
            var elements = StringInfo.GetTextElementEnumerator(trimmed);
            var result = new StringBuilder();
            int count = 0;
            while (elements.MoveNext() && count < 300)
            {
                result.Append(elements.GetTextElement());
                count++;
            }
            trimmed = result.ToString();
        }
        
        return trimmed;
    }
    
    public static string SanitizeReview(string input)
    {
        // Same logic as bio, but 500 char limit
        // (implementation details similar to above)
    }
}

// Display in frontend (React)
function ProfileBio({ bio }: { bio: string }) {
  // Escape HTML special chars, then replace \n with <br>
  const sanitized = bio
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
  
  return (
    <p 
      className="bio-text"
      dangerouslySetInnerHTML={{ 
        __html: sanitized.replace(/\n/g, '<br>') 
      }}
    />
  );
}
```

**Character Counting (Frontend)**:
```typescript
// Real-time character counter in textarea
function CharacterCounter({ value, maxLength }: { value: string; maxLength: number }) {
  // Use Intl.Segmenter for accurate emoji counting
  const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
  const segments = Array.from(segmenter.segment(value));
  const count = segments.length;
  
  return (
    <div className="text-sm text-gray-600">
      {count} / {maxLength} characters
      {count > maxLength && (
        <span className="text-red-600 ml-2">
          ({count - maxLength} over limit)
        </span>
      )}
    </div>
  );
}
```

**Validation**:
- Backend validates character count using `StringInfo.LengthInTextElements` (C# equivalent of grapheme counting)
- Returns 400 Bad Request if bio > 300 or review > 500 text elements
- Error message: "Bio must be 300 characters or less (currently 347)"

**URL Handling**:
- URLs are allowed but displayed as plain text (not clickable)
- Frontend can optionally detect URLs and make them clickable using `Linkify` library
- Decision: For v1, keep URLs as plain text. Clickable links in v2 if users request it.

**Example**:
```
Input: "I love woodworking! 🪚\n\nCheck out my Instagram: <script>alert('xss')</script>\n\n\n\nHappy to help neighbors! 😊"

After sanitization: "I love woodworking! 🪚\n\nCheck out my Instagram: \n\nHappy to help neighbors! 😊"

Character count: 71 text elements (emojis count as 1 each)

HTML display: 
"I love woodworking! 🪚<br><br>Check out my Instagram: <br><br>Happy to help neighbors! 😊"
```

---

## Q&A History

### Iteration 2 - 2025-01-10

**Q1: What defines the "due date" for transaction auto-confirmation?**  
**A**: Due dates are **immutable** after transaction creation. Set at request approval time by FEAT-02, never modified. Auto-confirmation occurs 14 days after due date (7 days overdue + 7 days grace period). No extensions supported in v1 - borrowers must negotiate with lender before due date if more time needed. See "Transaction Completion & Due Date Mechanics" section for full workflow.

**Q2: How do we handle timezone for rating window deadlines across users in different timezones?**  
**A**: Rating windows are **timezone-agnostic durations** - exactly 168 hours from transaction confirmation. All timestamps stored as UTC in database. Frontend displays countdown timers ("4 days, 3 hours remaining") and converts to user's local timezone for date display ("Closes May 22 at 7:00 AM PST"). Notifications sent at user's local time. Everyone gets same duration, no unfair timezone advantages. See "Rating Window Timezone Handling" section.

**Q3: Can a transaction be "Returned - Confirmed" if there's a pending problem report?**  
**A**: Yes - submitting a problem report **immediately** confirms the transaction. Problem report submission is implicit confirmation that lender has inspected the tool. No separate "Confirm Return" button after reporting problems. Status flow: Return Initiated → [Problem Report Submitted] → Returned - Confirmed → Rating Window Opens. Problem reports are metadata on confirmed transactions, don't block progression. See "Problem Reports & Transaction Confirmation" section.

**Q4: What happens if both parties submit ratings at the exact same second?**  
**A**: **Eventual consistency** via 1-minute background job. Both rating inserts succeed immediately (stored with `visible=false`). Background job runs every minute, detects transactions with 2 invisible ratings, flips both to `visible=true`. Sub-minute delay is acceptable - users don't expect instant mutual reveal. Avoids complex locking and deadlock risks. See "Concurrent Rating Submission" section.

**Q5: What's the maximum length for phone numbers after formatting?**  
**A**: Store in **normalized E.164 format** (+1XXXXXXXXXX), max 15 characters. Use libphonenumber library to parse user input and normalize to E.164 on submission. Database column: `VARCHAR(15)` with CHECK constraint for E.164 format. Re-format for display as "(503) 555-1234" using same library. Twilio integration uses E.164 format directly. US numbers only for v1, international support in v2.

**Q6: How many SMS verification attempts are allowed before we lock out the phone number permanently?**  
**A**: **Separate limits**: 3 incorrect code attempts AND 5 SMS sends, both per phone number per 24 hours. After hitting either limit, user must wait 24 hours (no permanent ban). Tracks attempts in `users.phone_verification_attempts` JSONB column. Background job clears attempts older than 24 hours. "Resend Code" button disabled after 5th send. Wrong code entry shows "X/3 attempts remaining". See "Phone Verification Limits & Security" section.

**Q7: Should profile statistics (Tools Shared, Average Rating) update in real-time or via background job?**  
**A**: **All statistics cached**, updated every 1 minute via Hangfire background job. Columns: `cached_tools_owned`, `cached_tools_shared`, `cached_current_borrows`, `cached_average_rating`, `cached_rating_count` on `users` table. Profile views do single SELECT (fast), no aggregate queries. Sub-minute staleness acceptable for trust decisions. Optional: Immediate updates on critical events (transaction confirmed, rating submitted) for < 1 second staleness. See "Profile Statistics Caching Strategy" section.

**Q8: What character encoding/sanitization do we apply to bio and review text?**  
**A**: **Strip all HTML tags, preserve line breaks, allow emojis**. Character count using `StringInfo.LengthInTextElements` (C# / `Intl.Segmenter` in JS) so emojis = 1 character. Limit to 2 consecutive line breaks (prevents whitespace walls). Display: escape HTML special chars (`<`, `>`, `&`), then replace `\n` with `<br>`. URLs allowed as plain text (not clickable in v1). Max 300 chars for bio, 500 for reviews. See "Text Field Sanitization & Character Limits" section.

---

### Iteration 1 - 2025-01-09

**Q1: When does the 7-day rating window open?**  
**A**: Exactly when transaction status changes to "Returned - Confirmed". Lender confirms return OR 7 days after due date passes (auto-confirmation). Both parties notified simultaneously, 7-day countdown starts immediately.

**Q2: What if only one person rates within 7 days?**  
**A**: Both ratings become visible after 7 days pass, regardless of whether the other party rated. Prevents strategic withholding of ratings. After window closes, no ratings can be submitted.

**Q3: Are usernames unique?**  
**A**: No separate usernames. Full name (first + last) is display name, not guaranteed unique. Email is unique identifier (used for login). This is a book club, not social media - real names build trust.

**Q4: Can users change their names after signup?**  
**A**: Yes, but logged in audit trail. Prevents abuse/impersonation while allowing legitimate name changes (marriage, legal name changes). Admin can review suspicious name changes.

**Q5: What happens to ratings when a user deletes their account?**  
**A**: Soft delete - profile shows "[User Unavailable]" but ratings remain visible (anonymized). Preserves trust data for other party. Transaction history shows deleted