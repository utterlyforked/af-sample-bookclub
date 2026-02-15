# Borrowing Request & Communication System - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: December 19, 2024

---

## Summary

After reviewing the specification, I've identified 8 areas that need clarification before implementation can begin. These questions address:
- Core data model and business rules
- Request lifecycle and conflict resolution
- Communication boundaries and moderation
- Authorization and security constraints

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: Can users have multiple pending requests for the same tool?

**Context**: The PRD mentions "first-come-first-served for approval" but doesn't clarify if users can submit multiple requests for the same tool with different date ranges or if only one pending request per tool per user is allowed.

**Options**:
- **Option A**: One pending request per tool per user
  - Impact: Simple validation, prevents request spam
  - Trade-offs: User must cancel and resubmit if they want different dates
  - Database: Unique constraint on (UserId, ToolId, Status) where Status = Pending
  
- **Option B**: Multiple pending requests allowed for same tool
  - Impact: More complex conflict resolution, owners see multiple requests from same person
  - Trade-offs: Flexible for users, but could overwhelm tool owners
  - Database: No unique constraint needed

**Recommendation for MVP**: Option A (one pending request per tool per user). Prevents spam, keeps owner inbox manageable. User can cancel and resubmit with different dates if needed.

---

### Q2: What happens when request dates conflict with existing approved loans?

**Context**: PRD mentions preventing "double-booking" but doesn't specify the exact conflict resolution logic. Need to know how date overlaps are handled.

**Options**:
- **Option A**: Block new requests that overlap with approved loans
  - Impact: Validation on request submission checks existing approved requests
  - Trade-offs: Prevents conflicts, but reduces availability
  - Database: Query approved requests for date range conflicts
  
- **Option B**: Allow overlapping requests, let owner decide
  - Impact: Owner sees conflict warning but can still approve
  - Trade-offs: Maximum flexibility, but owner might accidentally double-book
  
- **Option C**: Queue conflicting requests automatically
  - Impact: Show "request for dates after current loan" option
  - Trade-offs: Complex queuing logic, notification chains

**Recommendation for MVP**: Option A (block overlapping requests). Show available dates to user, prevent owner from accidentally double-booking. Can add queuing in v2 if needed.

---

### Q3: When exactly does auto-decline trigger and can it be customized?

**Context**: PRD says "auto-decline after 48 hours if no response (configurable per user)" but doesn't specify if this is 48 hours from request creation or if owners can set their own timeouts.

**Options**:
- **Option A**: Fixed 48-hour timeout from request creation
  - Impact: Simple implementation, consistent user expectations
  - Trade-offs: No flexibility, might be too short/long for some users
  - Database: Single `created_at` + 48 hours check
  
- **Option B**: Owner sets their response timeout (12h-7days)
  - Impact: User preference setting, dynamic timeout per request
  - Trade-offs: Flexible, but borrowers don't know how long to wait
  - Database: User preference + request-specific timeout calculation
  
- **Option C**: Global 48h default, owner can customize per request
  - Impact: Owner can extend deadline when they see request
  - Trade-offs: Most flexible, but complex UI

**Recommendation for MVP**: Option A (fixed 48 hours). Simple, predictable. Can add customization in v2 based on user feedback.

---

### Q4: What constitutes "confirmation from both parties" for returned status?

**Context**: PRD states "Returned status requires confirmation from both parties" but doesn't specify the UI flow or what happens if one party doesn't confirm.

**Options**:
- **Option A**: Borrower initiates return, owner must confirm within 24h
  - Impact: Two-step process, automatic completion if owner doesn't respond
  - Trade-offs: Protects borrower from non-responsive owners
  - Database: `return_initiated_at`, `return_confirmed_at` fields
  
- **Option B**: Either party can mark returned, other must confirm
  - Impact: More flexible, either can initiate
  - Trade-offs: Could create confusion about who should initiate
  
- **Option C**: Both must actively click "confirm return" (no auto-confirm)
  - Impact: Requires action from both parties, can get stuck
  - Trade-offs: Most secure, but loans might never close

**Recommendation for MVP**: Option A (borrower initiates, owner confirms with auto-confirm). Borrower knows when they returned it, owner has chance to verify condition, automatic closure prevents stuck loans.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q5: What's the maximum number of simultaneous borrowing requests per user?

**Context**: No mention of rate limiting for borrowing requests. Need limits to prevent abuse and manage tool owner notification volume.

**Options**:
- **Option A**: 10 pending requests maximum per user
  - Impact: Simple validation on request creation
  - Trade-offs: Reasonable limit, prevents spam
  
- **Option B**: 5 pending requests maximum per user
  - Impact: Stricter limit, encourages focused requests
  - Trade-offs: Might feel restrictive for active users
  
- **Option C**: No limit on requests
  - Impact: No validation needed
  - Trade-offs: Risk of spam, overwhelmed tool owners

**Recommendation for MVP**: Option A (10 pending requests max). Allows legitimate users to request multiple tools while preventing abuse.

---

### Q6: How should we handle message notifications for active conversations?

**Context**: PRD mentions email notifications for new messages but doesn't specify frequency limits or conversation threading.

**Options**:
- **Option A**: Immediate email for every message
  - Impact: Real-time notifications, simple implementation
  - Trade-offs: Could become spam in active conversations
  
- **Option B**: Bundle notifications (max 1 email per hour per conversation)
  - Impact: Digest-style emails with multiple messages
  - Trade-offs: Less spam, but slower response times
  
- **Option C**: First message immediate, then daily digest for follow-ups
  - Impact: Balance of urgency and noise reduction
  - Trade-offs: Complex logic, but good user experience

**Recommendation for MVP**: Option A (immediate emails) with user setting to disable per-message notifications. Simple implementation, user can control their inbox.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q7: Should we show request/message history to future potential borrowers?

**Context**: PRD mentions preserving communication history but doesn't specify visibility. This affects privacy and trust building.

**Options**:
- **Option A**: History visible only to participants
  - Impact: Full privacy, no public visibility
  - Trade-offs: Private, but new borrowers can't see owner communication style
  
- **Option B**: Show aggregated stats ("responds within 2 hours typically")
  - Impact: Computed metrics without exposing actual messages
  - Trade-offs: Helpful context without privacy concerns

**Recommendation for MVP**: Option A (private history only). Focus on core functionality, can add aggregated stats in v2.

---

### Q8: What basic reporting mechanism do we need for inappropriate messages?

**Context**: PRD mentions "basic reporting mechanism" but doesn't define what actions are available or who handles reports.

**Options**:
- **Option A**: Simple "Report Message" button → admin email notification
  - Impact: Minimal implementation, manual admin review
  - Trade-offs: Basic coverage, requires manual intervention
  
- **Option B**: Report with category selection → admin dashboard
  - Impact: Structured reporting with categorization
  - Trade-offs: More complex, but better for tracking patterns
  
- **Option C**: Just block/mute functionality, no formal reporting
  - Impact: Users can stop receiving messages from problematic users
  - Trade-offs: Simplest, but no admin visibility into issues

**Recommendation for MVP**: Option A (report button → admin email). Covers the need with minimal implementation. Can enhance based on actual abuse patterns.

---

## Notes for Product

- All questions focus on business rules and user experience - no technical implementation choices
- These clarifications will enable clean database design and clear user flows
- Happy to do another iteration if these answers raise new questions
- Once answered, can proceed with detailed technical specification