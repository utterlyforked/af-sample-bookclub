# Borrow Tracking & Returns - Technical Questions (Iteration 2)

**Status**: NEEDS CLARIFICATION
**Iteration**: 2
**Date**: 2025-01-14

---

## Summary

After reviewing the v1.1 specification, I've identified **8 areas** that need clarification before implementation can begin. The v1.1 iteration resolved many critical questions from iteration 1, but several important edge cases and behavioral details remain ambiguous. These questions address:

- Return condition assessment workflow
- Photo upload and storage constraints
- Extension request timing and auto-expiration
- Owner non-responsive scenarios
- Late return penalties and enforcement
- Transaction history data retention
- Notification delivery failures
- Concurrent action race conditions

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What happens if owner reports issues but borrower disputes the damage?

**Context**: The spec describes owners confirming returns with "Good condition" or "Has issues" but doesn't address disputes. This is critical because:
- Trust/reputation scores will be affected by damage reports
- Users need a path to contest unfair damage claims
- System needs to determine whose account of condition is "official"
- Affects database finality (can return confirmations be amended?)

**Options**:

- **Option A: Confirmation is final, no dispute mechanism in v1**
  - Impact: Owner's condition assessment stands as permanent record
  - Trade-offs: Simple implementation, but might feel unfair to borrowers who disagree
  - UI: Show damage report to borrower, allow text response in ratings (but can't change condition)
  - Database: `ReturnConfirmation.Condition` is immutable once set
  
- **Option B: Borrower can flag dispute, admin reviews**
  - Impact: Add `DisputeFlag` boolean + `DisputeReason` text field to ReturnConfirmation
  - Trade-offs: More fair, but requires admin intervention workflow (out of scope for v1?)
  - UI: Borrower sees "Disagree with damage report?" link → dispute form
  - Database: Dispute flags visible to admins, condition stays in disputed state until resolved
  
- **Option C: Borrower can add rebuttal notes visible in history**
  - Impact: Add `BorrowerRebuttal` text field (max 500 chars) to ReturnConfirmation
  - Trade-offs: Both sides documented, no admin needed, but no resolution mechanism
  - UI: If owner reports issues, borrower notified and can add their perspective
  - Database: Both owner notes and borrower rebuttal stored, displayed together in history

**Recommendation for MVP**: Option C (rebuttal notes). Preserves both perspectives without requiring admin dispute resolution. Provides transparency and fairness signal without complex workflows. Can add formal dispute process in v2 if needed.

---

### Q2: Can owners upload photos when confirming "Good condition" or only when reporting issues?

**Context**: Spec says owners can upload "up to 5 photos" when confirming returns but doesn't clarify if this applies to both conditions or just "Has issues". This affects:
- Storage costs and upload flow complexity
- Whether "Good condition" confirmations need photo evidence
- User expectations about documentation requirements

**Options**:

- **Option A: Photos only for "Has issues" condition**
  - Impact: Photo upload UI only appears when owner selects "Has issues" radio button
  - Trade-offs: Simpler, reduces storage costs, but owners can't document good returns
  - Workflow: Good condition = quick confirm (no photos). Issues = photos required (at least 1?)
  - Storage: Significantly fewer photos stored (~10% of returns vs 100%)
  
- **Option B: Photos optional for both conditions**
  - Impact: Photo upload always available, regardless of condition selected
  - Trade-offs: Owners can document returns either way, but most won't upload for good condition
  - Workflow: Both conditions show upload area, but photos optional (0-5)
  - Storage: Slightly more storage used, but most good returns still no photos
  
- **Option C: Photos required for issues, blocked for good condition**
  - Impact: "Has issues" requires at least 1 photo, "Good condition" hides upload UI entirely
  - Trade-offs: Enforces evidence for damage claims, but strictest approach
  - Validation: Backend rejects issue reports without photos
  - Storage: Minimal, but owners might game system (mark good to avoid photo requirement)

**Recommendation for MVP**: Option A (photos only for issues, optional). Simplest implementation that focuses documentation on problem cases. Photos rarely needed for good returns. Can relax to Option B in v2 if users request documenting good condition.

---

### Q3: How long do pending extension requests remain open before timing out?

**Context**: Spec mentions extension requests can "time out" and counts toward the 3-request limit, but doesn't specify the timeout duration. This affects:
- When borrowers should follow up with owners
- Whether requests sit pending until due date arrives
- System cleanup job timing

**Options**:

- **Option A: No automatic timeout, pending until owner responds or due date passes**
  - Impact: Extension requests stay pending indefinitely until action
  - Trade-offs: Simple (no timeout job), but requests could languish for weeks
  - UI: Owner sees pending requests in notifications until they act
  - Cleanup: Only cancelled when due date passes without approval
  
- **Option B: 48-hour timeout**
  - Impact: If owner doesn't respond within 48 hours, request auto-denied
  - Trade-offs: Forces owner attention quickly, but might be too aggressive
  - Notification: "Your extension request expired - owner didn't respond within 48 hours"
  - Database: Background job marks expired requests as "Timed Out" status
  
- **Option C: 72-hour timeout**
  - Impact: 3-day window for owner to respond before auto-denial
  - Trade-offs: Balanced - gives owners weekend to respond, but doesn't leave borrowers hanging
  - UI: Request shows countdown: "Expires in 2 days" to create urgency
  - Database: `ExtensionRequest.ExpiresAt = RequestedDate + 72 hours`
  
- **Option D: Timeout = days until due date (dynamic)**
  - Impact: If due in 5 days, request expires in 5 days (at due date)
  - Trade-offs: Intuitive (owner has until due date), but very long for far-future requests
  - Edge case: Request made 10 days before due date could sit pending for 10 days

**Recommendation for MVP**: Option C (72-hour timeout). Reasonable urgency for owner while being flexible. Background job runs daily, marks requests as "Timed Out" where `RequestedDate + 72h < UtcNow AND Status = Pending`. Borrower notified to either return tool or contact owner directly.

---

### Q4: When exactly are email reminders sent relative to the 6:00 PM due time?

**Context**: Spec says reminders sent "1 day before due date and on the due date" but doesn't specify exact timing. The 6:00 PM due time is critical context. This affects:
- Whether "1 day before" means 24 hours before 6 PM or 6 PM the day before
- What time "due date" reminder goes out (morning? noon? near 6 PM?)
- Coordination with timezone handling

**Options**:

- **Option A: Fixed time reminders (9:00 AM in owner's timezone)**
  - "1 day before" reminder: 9:00 AM the day before due date
  - "Due today" reminder: 9:00 AM on due date (9 hours before 6 PM deadline)
  - Impact: Simple cron schedule, predictable timing
  - Trade-offs: All users get reminders at same time-of-day, but not precisely 24h before
  
- **Option B: Exact 24-hour and 3-hour windows**
  - "1 day before" reminder: Exactly 24 hours before due time (6 PM day before)
  - "Due today" reminder: 3 hours before due time (3 PM on due date)
  - Impact: More complex scheduling, but mathematically precise
  - Trade-offs: Reminders spread throughout day based on individual due times
  
- **Option C: Hybrid - day-before at fixed time, due-day at 9 AM**
  - "1 day before" reminder: 6:00 PM the day before (exactly 24h before)
  - "Due today" reminder: 9:00 AM on due date
  - Impact: Balance of precision and predictability
  - Trade-offs: Day-before matches due time, morning reminder gives full day to act

**Recommendation for MVP**: Option A (9 AM fixed times in owner's timezone). Simpler batch job processing, predictable user experience. Borrowers receive morning reminder with full day to coordinate return. Avoids reminder spam at odd hours.

**Database Impact**: 
- Background job runs hourly, queries borrows where `CurrentDueDate` is tomorrow/today in owner's timezone
- Marks reminder sent in `BorrowReminder` tracking table to prevent duplicates

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q5: What happens if borrower marks returned but owner never confirms (beyond the 7-day auto-confirm)?

**Context**: Spec has 7-day auto-confirmation as "Good condition," but doesn't address what happens to the borrower's reputation or trust score in this scenario. Does auto-confirmation count the same as owner-confirmed? This affects:
- Trust score calculation (is auto-confirm equal to owner-confirmed?)
- Whether this is visible in history differently
- Incentives for owners to actually confirm

**Options**:

- **Option A: Auto-confirmation treated identically to owner confirmation**
  - Impact: No distinction in trust score, no special flag in history
  - Trade-offs: Simple, but doesn't signal owner negligence
  - Display: History shows "Returned - Good condition" regardless of confirmation method
  
- **Option B: Auto-confirmation marked but affects trust equally**
  - Impact: Trust score same, but history shows "(Auto-confirmed)"
  - Trade-offs: Transparency about what happened, but still benefits borrower equally
  - Display: "Returned - Good condition (Auto-confirmed after 7 days)"
  - Database: `ConfirmedBy = System` distinguishes this case
  
- **Option C: Auto-confirmation worth less trust points**
  - Impact: Owner-confirmed return = +5 trust, auto-confirmed = +3 trust
  - Trade-offs: Incentivizes owner engagement, but penalizes borrower for owner behavior
  - Risk: Feels unfair to borrower who returned on time but owner ghosted

**Recommendation for MVP**: Option B (marked as auto-confirmed, equal trust). Borrower shouldn't be penalized for owner non-responsiveness. Transparency via "(Auto-confirmed)" label provides context without punishment. Can analyze data later to see if pattern of auto-confirms correlates with other trust signals.

---

### Q6: Are there any consequences for borrowers who repeatedly return tools late?

**Context**: Spec flags overdue items visually and presumably affects trust/reputation, but doesn't explicitly state consequences. This affects:
- Whether late returns just affect reputation passively or trigger active restrictions
- Platform enforcement of responsible borrowing
- Owner confidence in lending through platform

**Options**:

- **Option A: No explicit restrictions, only reputation impact**
  - Impact: Late returns visible in history, affect trust score calculation (v2 feature?)
  - Trade-offs: Soft incentive, relies on community reputation working
  - Enforcement: Owners can see history and decline requests from serial late-returners
  
- **Option B: Warning system with eventual temporary suspension**
  - Impact: After 3 late returns in 6 months, 30-day borrowing suspension
  - Trade-offs: Clear consequences, but requires warning/suspension workflow
  - Notifications: "This is your 2nd late return. One more and borrowing will be paused."
  
- **Option C: Escalating late fees (requires payment system)**
  - Impact: Overdue tools accrue daily late fee ($5/day after 3 days overdue)
  - Trade-offs: Strong deterrent, but requires payment processing (out of scope for MVP?)
  - Blocker: No payment system in tech stack yet

**Recommendation for MVP**: Option A (reputation only). Keep MVP focused on tracking and transparency. Late returns visible in history, affect trust score (when that system is built), and owners can make informed decisions. Can add escalating restrictions in v2 based on abuse patterns observed. Avoids building payment/suspension systems prematurely.

---

### Q7: How long is transaction history retained? Forever or with data retention limits?

**Context**: Spec says history shows "completed AND cancelled borrows" but doesn't address long-term retention. This affects:
- Database growth over time (millions of records per year)
- Compliance (GDPR right to be forgotten, data minimization)
- Query performance on history tab

**Options**:

- **Option A: Retain forever, no automatic deletion**
  - Impact: Complete audit trail, database grows indefinitely
  - Trade-offs: Best for disputes, but scaling concerns
  - Mitigation: Archive old records to cold storage after 2+ years
  
- **Option B: Hard delete after 7 years**
  - Impact: Comply with typical record retention policies
  - Trade-offs: Balance of auditability and data minimization
  - Implementation: Background job soft-deletes borrows older than 7 years
  
- **Option C: Retain completed forever, delete cancelled after 1 year**
  - Impact: Completed borrows kept for reputation, cancelled cleaned up
  - Trade-offs: Reduces noise (most cancelled are abandoned), keeps what matters
  - Rationale: Cancelled-before-pickup borrows have minimal value long-term

**Recommendation for MVP**: Option A (retain forever, plan for archival). Start with complete retention, defer deletion decisions until we see usage patterns and storage costs. Add soft-delete mechanism in v2 when retention policy is defined by legal/compliance. For MVP, focus on indexing history queries efficiently (partition by year?).

**Database Impact**: Index on `(UserId, Status, ReturnConfirmedDate DESC)` for fast history queries. Consider partitioning `Borrows` table by year once volume grows.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q8: What happens if email notifications fail to deliver (bounced email, full inbox, etc.)?

**Context**: Spec relies heavily on email reminders ("1 day before," "due today," "owner hasn't confirmed"). Email delivery isn't 100% reliable. This affects:
- Whether users miss critical deadlines due to email issues
- Fallback communication channels
- System resilience

**Options**:

- **Option A: Email only, no retry or fallback**
  - Impact: Users responsible for checking dashboard if emails fail
  - Trade-offs: Simplest, but users might genuinely miss reminders
  - Mitigation: In-app notification badge counts serve as backup
  
- **Option B: Email + in-app notification redundancy**
  - Impact: All reminders sent via both email AND in-app notification center
  - Trade-offs: Higher delivery confidence, but requires notification system
  - UI: Notification bell icon shows unread count
  
- **Option C: Email with retry logic for bounces**
  - Impact: If email bounces, retry 2x at 1-hour intervals
  - Trade-offs: Better delivery, but still no guarantee user sees it
  - Monitoring: Log bounce rates, alert if user has persistent delivery issues

**Recommendation for MVP**: Option B (email + in-app notifications). Notification system likely already planned for platform (message alerts, etc.), so extend it to reminders. Provides redundancy without complex retry logic. Users who miss emails still see notifications when they log in.

**Database Impact**: `Notification` table with `Type` enum (Reminder_DueSoon, Reminder_DueToday, Return_Pending, etc.), `Read` boolean, `CreatedAt` timestamp. Frontend polls or uses WebSocket for real-time updates.

---

## Notes for Product

- **Q1 (damage disputes)** is critical - affects trust system design and user fairness perception
- **Q2 (photo requirements)** impacts storage costs significantly - need decision before infrastructure sizing
- **Q3 (extension timeouts)** blocks extension request implementation - need exact timing rules
- **Q4 (reminder timing)** affects user experience quality - need to coordinate with timezone decisions

Once these 8 questions are answered, I can proceed to detailed technical specification. Several answers may raise follow-up questions about trust score calculation and reputation system, which appears to be a separate feature (FEAT-05?) but intersects heavily with this one.

Happy to do iteration 3 if needed to finalize edge cases.