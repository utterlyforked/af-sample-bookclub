# Borrowing Request System - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: February 15, 2025

---

## Summary

After reviewing the specification, I've identified 8 areas that need clarification before implementation can begin. These questions address:
- Core data model and business logic
- Request lifecycle and state management
- Communication system boundaries
- Authorization and validation rules

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What exactly happens when a request is "approved with changes"?

**Context**: The PRD mentions owners can "approve with changes" and modify dates/times/conditions, but the workflow after that is unclear. This affects the entire state machine design and user experience flow.

**Options**:
- **Option A**: Changes go back to borrower for acceptance/rejection
  - Impact: Need additional request states (pending_borrower_approval), more complex workflow
  - Trade-offs: Fair to borrower but adds friction and delays
  
- **Option B**: Owner changes are automatically accepted
  - Impact: Simpler state machine, direct approval flow
  - Trade-offs: Faster but borrower might not agree to changes
  
- **Option C**: Changes create a new counter-proposal that replaces original
  - Impact: Need counter-proposal tracking, potentially multiple rounds
  - Trade-offs: Most flexible but most complex

**Recommendation for MVP**: Option A (borrower must accept changes). Ensures both parties agree to final terms, which is critical for binding agreements.

---

### Q2: Can multiple users request the same tool for overlapping dates?

**Context**: PRD mentions "first-come-first-served" for overlapping requests but doesn't clarify if overlapping requests can even be submitted, or if they're blocked at creation time.

**Options**:
- **Option A**: Block overlapping requests at submission
  - Impact: Need real-time availability checking, simpler request management
  - Trade-offs: Clear for users but less flexible if first request gets declined
  
- **Option B**: Allow overlapping requests, auto-decline conflicting ones when first is approved
  - Impact: More complex state management, need to handle bulk declines
  - Trade-offs: More flexible but potentially confusing for users
  
- **Option C**: Allow overlapping with waitlist functionality
  - Impact: Complex queue management, notification system for waitlist
  - Trade-offs: Best UX but significantly more complex

**Recommendation for MVP**: Option A (block overlapping). Clearest user experience and simplest implementation. Can add waitlist in v2 if needed.

---

### Q3: What are the exact states a BorrowRequest can have?

**Context**: PRD mentions various statuses but doesn't provide a complete state diagram. This is fundamental to the database design and business logic.

**Options**:
- **Option A**: Simple states (pending, approved, declined, expired)
  - Impact: Simple enum, straightforward state transitions
  - Trade-offs: Might not handle "approved with changes" workflow well
  
- **Option B**: Extended states (pending, approved, declined, expired, counter_proposed, awaiting_borrower_response)
  - Impact: More complex state machine but handles all workflows
  - Trade-offs: Complete but more complexity in UI and logic
  
- **Option C**: Separate status for request vs agreement (request can be approved but agreement pending acknowledgment)
  - Impact: Two-phase system with separate entities
  - Trade-offs: Most accurate to real workflow but adds complexity

**Recommendation for MVP**: Option B (extended states). Properly models the counter-proposal workflow which is a key feature.

---

### Q4: Are BorrowRequest and LoanAgreement separate database entities?

**Context**: PRD mentions both but relationship isn't clear. This affects the entire data model architecture.

**Options**:
- **Option A**: Same entity - BorrowRequest becomes LoanAgreement when approved
  - Impact: Single table, status field drives behavior
  - Trade-offs: Simpler but mixes concerns (request data vs agreement data)
  
- **Option B**: Separate entities - LoanAgreement created from approved BorrowRequest
  - Impact: Two tables with foreign key relationship
  - Trade-offs: Cleaner separation but more joins for queries
  
- **Option C**: BorrowRequest contains embedded LoanAgreement data when approved
  - Impact: JSON/JSONB field for agreement terms
  - Trade-offs: Flexible but harder to query agreement-specific data

**Recommendation for MVP**: Option B (separate entities). Clean separation of concerns and easier to extend agreement functionality later.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q5: What specific data is required vs optional in a borrow request?

**Context**: PRD lists various fields but doesn't specify validation rules. This affects form design and database constraints.

**Options**:
- **Option A**: Minimal required (start_date, end_date, intended_use)
  - Impact: Simple validation, quick request submission
  - Trade-offs: Might lack context for owner decisions
  
- **Option B**: Comprehensive required (all fields mentioned in PRD)
  - Impact: Complex form, more validation logic
  - Trade-offs: Better context but might deter requests
  
- **Option C**: Smart defaults based on tool type
  - Impact: Dynamic form logic based on tool category
  - Trade-offs: Best UX but more complex implementation

**Recommendation for MVP**: Option A with intended_use required. Core fields for basic functionality, can expand later based on usage patterns.

---

### Q6: How should we handle message attachments and storage?

**Context**: PRD mentions photo attachments in communication thread but no storage or size limits specified.

**Options**:
- **Option A**: No attachments in MVP
  - Impact: Text-only messaging system
  - Trade-offs: Much simpler but loses valuable functionality
  
- **Option B**: Image attachments only, 5MB limit, stored in blob storage
  - Impact: File upload logic, storage costs, image processing
  - Trade-offs: Useful feature but adds complexity and storage costs
  
- **Option C**: Any file type, larger limits
  - Impact: Security scanning, virus checking, more storage
  - Trade-offs: Very flexible but significant security concerns

**Recommendation for MVP**: Option B (images only, 5MB limit). Covers the main use case (showing tool condition/project) with manageable complexity.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q7: What's the maximum message length and conversation limits?

**Context**: Need to prevent abuse and plan storage requirements for the messaging system.

**Options**:
- **Option A**: 1000 character limit, 100 messages per request
  - Impact: Simple validation, reasonable storage
  - Trade-offs: Should handle most conversations
  
- **Option B**: 2000 character limit, unlimited messages
  - Impact: More storage, need pagination for long threads
  - Trade-offs: More flexible but unbounded growth
  
- **Option C**: Dynamic limits based on user reputation
  - Impact: Complex business logic for limits
  - Trade-offs: Prevents spam but adds complexity

**Recommendation for MVP**: Option A (1000 chars, 100 messages). Should handle legitimate use cases while preventing abuse.

---

### Q8: Should automatic approval rules be part of MVP?

**Context**: PRD mentions "automatic approval rules for trusted borrowers" but this adds significant complexity.

**Options**:
- **Option A**: No automatic approval in MVP
  - Impact: All requests require manual owner action
  - Trade-offs: Simpler implementation but more manual work for owners
  
- **Option B**: Simple auto-approval (checkbox: "auto-approve requests from users with 4+ stars")
  - Impact: Basic rule engine, rating system dependency
  - Trade-offs: Useful but adds complexity and edge cases
  
- **Option C**: Advanced rule engine (time of day, specific users, loan duration, etc.)
  - Impact: Complex rule system, UI for rule management
  - Trade-offs: Very powerful but major feature in itself

**Recommendation for MVP**: Option A (no auto-approval). Keep initial version simple, add this enhancement in v2 based on user feedback.

---

## Notes for Product

- All questions focus on core functionality - no implementation details
- Recommendations prioritize MVP simplicity while maintaining core value
- Several questions affect database schema significantly - need answers before development starts
- Happy to do another iteration if these answers raise new questions about integration points

Once these are answered, I can proceed to create detailed technical specifications.