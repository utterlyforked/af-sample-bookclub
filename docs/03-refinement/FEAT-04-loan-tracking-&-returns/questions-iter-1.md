# Loan Tracking & Returns - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: February 15, 2025

---

## Summary

After reviewing the specification, I've identified 8 areas that need clarification before implementation can begin. These questions address:
- Core data model and business logic
- Photo handling and storage requirements
- Notification timing and delivery mechanisms
- User authorization and edge case handling

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What defines a "loan" and when is it created?

**Context**: The PRD mentions tracking "active loans" but doesn't specify when a loan record is created. This affects the entire data model and workflow triggers.

**Options**:
- **Option A**: Loan created when borrowing request is approved
  - Impact: Loan exists before physical pickup, can track "approved but not picked up" state
  - Trade-offs: Need additional status field, handles no-shows cleanly
  
- **Option B**: Loan created when borrower confirms pickup with condition photos
  - Impact: Only "real" loans exist in system, pickup photos are always required
  - Trade-offs: Simpler states, but approved requests that aren't picked up need different tracking
  
- **Option C**: Two-step process - "approved loan" becomes "active loan" at pickup
  - Impact: Need to handle state transition, pickup confirmation required
  - Trade-offs: Most accurate but adds complexity

**Recommendation for MVP**: Option B (loan created at pickup). Clean separation between requests and actual loans, pickup photos always available for return comparison.

---

### Q2: How are condition photos structured and what's required?

**Context**: PRD mentions "2-3 photos" at pickup/return but doesn't specify mandatory categories or validation requirements. This affects storage design and UI workflow.

**Options**:
- **Option A**: Flexible photo count - borrower takes as many as needed (2-10 range)
  - Impact: Simple UI, users decide what's important
  - Trade-offs: Inconsistent documentation, hard to enforce coverage
  
- **Option B**: Required categories - "overall view", "close-up details", "serial/model number"
  - Impact: Structured storage, consistent documentation across all loans
  - Trade-offs: More complex UI, might feel rigid for simple tools
  
- **Option C**: Mandatory 3 photos minimum, with suggested categories but flexible content
  - Impact: Ensures adequate documentation without strict categorization
  - Trade-offs: Balanced approach, some photos might be redundant

**Recommendation for MVP**: Option C (3 photos minimum, flexible). Ensures documentation without overcomplicating the workflow. Can add structured categories in v2 if needed.

---

### Q3: What constitutes "owner confirmation" for returns?

**Context**: PRD requires both parties to confirm return, but doesn't specify what owner must do or timing requirements.

**Options**:
- **Option A**: Owner must physically inspect tool and actively confirm via app
  - Impact: Requires owner to be available/responsive for loan to close
  - Trade-offs: Most secure, but could delay completion if owner is slow to respond
  
- **Option B**: Owner has 48 hours to dispute, auto-confirms if no response
  - Impact: Returns close automatically, reduces owner burden
  - Trade-offs: Less explicit confirmation, owner might miss damage
  
- **Option C**: Owner confirms via app, but borrower can auto-close after 7 days
  - Impact: Balanced - encourages owner response but doesn't block forever
  - Trade-offs: Reasonable middle ground, clear timeline expectations

**Recommendation for MVP**: Option C (owner confirms, 7-day auto-close). Encourages active participation while preventing indefinite pending states.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q4: How do reminder notifications work technically?

**Context**: PRD specifies reminder timing (48hr, 24hr, day-of) but not delivery mechanism or failure handling.

**Options**:
- **Option A**: Push notifications with email backup if push fails
  - Impact: Need push notification infrastructure + email templates
  - Trade-offs: Best user experience, more complex to implement
  
- **Option B**: Email notifications only
  - Impact: Simpler implementation, works for all users
  - Trade-offs: Less immediate than push, might end up in spam
  
- **Option C**: In-app notifications (shown when user opens app) plus email
  - Impact: No push infrastructure needed, guaranteed delivery
  - Trade-offs: User must open app to see notifications

**Recommendation for MVP**: Option B (email only). Reliable delivery, simpler implementation. Can add push notifications in v2.

---

### Q5: What are the exact loan status values and transitions?

**Context**: PRD mentions various states ("active", "completed", "overdue", "return disputed") but doesn't define the complete state machine.

**Options**:
- **Option A**: Simple states - Active, Overdue, Completed, Disputed
  - Impact: 4 states, clear transitions, easy to implement
  - Trade-offs: Might miss some nuanced states
  
- **Option B**: Detailed states - Active, DueSoon, Overdue, ReturnPending, ReturnDisputed, Completed, Lost
  - Impact: 7 states, covers all scenarios mentioned in PRD
  - Trade-offs: More complex but handles all cases explicitly
  
- **Option C**: Status + flags - Status (Active/Completed) + IsOverdue, IsDisputed flags
  - Impact: Flexible combination, easy to query subsets
  - Trade-offs: Multiple fields to maintain, more complex queries

**Recommendation for MVP**: Option B (detailed states). Matches PRD complexity and makes business logic explicit in the data model.

---

### Q6: Who can mark a tool as "lost" and what happens?

**Context**: PRD mentions marking tools as "lost" after 7+ days overdue but doesn't specify the exact process or consequences.

**Options**:
- **Option A**: Only tool owner can mark as lost, borrower gets reputation penalty
  - Impact: Owner controls escalation, need reputation system integration
  - Trade-offs: Owner might be reluctant to penalize neighbors
  
- **Option B**: Platform auto-marks as lost after 14 days overdue
  - Impact: Automatic escalation, consistent enforcement
  - Trade-offs: No flexibility for special circumstances
  
- **Option C**: Owner can mark lost after 7 days, auto-marks after 30 days
  - Impact: Owner choice with ultimate automatic enforcement
  - Trade-offs: Balanced approach, handles both active and inactive owners

**Recommendation for MVP**: Option C (owner choice after 7 days, auto after 30). Gives owners control while ensuring enforcement doesn't depend on owner engagement.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q7: How long should loan photos be retained?

**Context**: PRD mentions photos are "stored permanently" but this has cost and privacy implications.

**Options**:
- **Option A**: Permanent retention (photos never deleted)
  - Impact: Ever-growing storage costs, best for dispute resolution
  - Trade-offs: Privacy concerns, ongoing costs
  
- **Option B**: Delete photos 1 year after loan completion
  - Impact: Reasonable retention for disputes, manageable storage costs
  - Trade-offs: Very old disputes can't be resolved with photos
  
- **Option C**: Delete photos when both users accounts are deleted
  - Impact: User privacy-first approach, natural cleanup
  - Trade-offs: Might lose evidence if accounts churned

**Recommendation**: Option B (1-year retention). Balances dispute resolution needs with storage costs and privacy.

---

### Q8: Can loan return dates be extended, and how?

**Context**: PRD mentions "extend loan (if owner approves)" but doesn't specify the workflow or limits.

**Options**:
- **Option A**: Borrower can request extension, owner approves/denies via notification
  - Impact: Need extension request workflow, notification handling
  - Trade-offs: Formal process, clear approval trail
  
- **Option B**: Owner can manually update return date, stops overdue notifications
  - Impact: Owner-initiated only, simple implementation
  - Trade-offs: Borrower can't request, owner must be proactive
  
- **Option C**: Both parties can propose new dates, other party confirms
  - Impact: Most flexible, either party can initiate
  - Trade-offs: Most complex, potential for confusion

**Recommendation**: Option A (borrower requests, owner approves). Matches user story expectation and creates clear approval workflow.

---

## Notes for Product

- These questions focus on the core data model and workflows that must be defined before coding begins
- Photo handling and notification delivery are critical technical decisions that affect user experience
- Happy to do another iteration if these answers raise new questions about edge cases or integrations
- Once these are answered, I can proceed to detailed database schema and API design