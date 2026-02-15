# User Profiles & Community Verification - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: December 19, 2024

---

## Summary

After reviewing the specification, I've identified 8 areas that need clarification before implementation can begin. These questions address:
- Critical data model and business logic gaps
- Address verification implementation approach
- Rating system behavior and integrity
- User interaction flows and permissions

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What exactly constitutes a "completed exchange" that triggers rating eligibility?

**Context**: The spec mentions ratings happen "after completed exchanges" and "after tool return confirmation", but the rating system depends on knowing precisely when an exchange is complete. This affects the entire rating workflow trigger.

**Options**:
- **Option A**: Completed = borrower marks tool as "returned" (self-reported)
  - Impact: Simple trigger, immediate rating prompts
  - Trade-offs: Relies on borrower honesty, lender might not agree tool was returned
  
- **Option B**: Completed = both parties confirm return (borrower says "returned", lender says "received")
  - Impact: Need confirmation workflow, ratings only trigger after both confirmations
  - Trade-offs: More reliable, but complex workflow and potential deadlock if one party doesn't confirm
  
- **Option C**: Completed = lender marks loan as "complete" (lender controls)
  - Impact: Only lender can trigger rating phase
  - Trade-offs: Gives lender control (they own the tool), but borrower has no agency

**Recommendation for MVP**: Option A (borrower self-report). Simpler implementation, can add lender confirmation in v2 if disputes arise.

---

### Q2: How do we handle the neighborhood verification mapping?

**Context**: Spec says "System verifies postal code matches claimed neighborhood community" but doesn't define how neighborhoods map to postal codes, or who maintains this mapping.

**Options**:
- **Option A**: Hard-coded postal code → neighborhood mapping table in database
  - Impact: Need to manually create and maintain neighborhood boundaries
  - Trade-offs: Full control, but requires ongoing maintenance as communities grow
  
- **Option B**: Admin interface for managing postal code → neighborhood mappings
  - Impact: Need admin UI for community managers to define boundaries
  - Trade-offs: Scalable, but adds admin interface complexity to v1
  
- **Option C**: Users select neighborhood from dropdown, system validates postal code is reasonable (same city/region)
  - Impact: Loose verification - check postal code is in same general area
  - Trade-offs: Much simpler, less precise but prevents obvious fake addresses

**Recommendation for MVP**: Option C (loose verification). Prevents most fake addresses without requiring detailed neighborhood mapping. Can tighten in v2.

---

### Q3: What specific user information is required vs optional during profile setup?

**Context**: Spec mentions "name, neighborhood, profile photo optional" but doesn't specify validation rules or what happens with missing required information.

**Options**:
- **Option A**: Required: Full name, address for verification. Optional: Photo, bio
  - Impact: Can't complete signup without real name and address
  - Trade-offs: Better trust/verification, but higher signup friction
  
- **Option B**: Required: Display name (could be pseudonym), postal code. Optional: Full name, photo, bio
  - Impact: Lower friction signup, but less verification
  - Trade-offs: More privacy-friendly, but reduces trust indicators
  
- **Option C**: Required: Full name, address. Optional: Photo, bio, but strong encouragement to complete
  - Impact: Same as A, but with UX nudges to complete profile
  - Trade-offs: Best of both - verification + encouraging completeness

**Recommendation for MVP**: Option A (require full name and address). Tool lending involves valuable items - better to err on side of trust/verification.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q4: What happens when users try to interact before verification is complete?

**Context**: Spec says "Unverified users can browse but cannot send borrowing requests until verified" but doesn't detail the verification process timing or user experience.

**Options**:
- **Option A**: Instant verification - check postal code immediately during signup
  - Impact: Users verified immediately if postal code is valid
  - Trade-offs: Seamless UX, but only catches obviously fake addresses
  
- **Option B**: Manual admin approval - all verifications reviewed by admin
  - Impact: Need admin review queue, users wait for approval
  - Trade-offs: Most secure, but creates bottleneck and delays
  
- **Option C**: Automatic verification with manual review for edge cases
  - Impact: Most addresses auto-verify, unclear cases go to admin queue
  - Trade-offs: Good balance, but need to define "unclear cases"

**Recommendation for MVP**: Option A (instant verification). Simple postal code validation prevents most abuse, manual review can be added later if needed.

---

### Q5: Can users rate/review the same person multiple times across different loans?

**Context**: Spec says "Users cannot rate the same person multiple times for the same loan" but doesn't clarify behavior across multiple loans between the same users.

**Options**:
- **Option A**: One rating per loan - users can rate each other multiple times if they do multiple loans
  - Impact: Rating history grows with relationship, multiple ratings between same users
  - Trade-offs: Reflects ongoing relationship, but potential for rating retaliation across loans
  
- **Option B**: One rating ever per user pair - first completed loan enables rating, subsequent loans don't
  - Impact: Only one rating between any two users, based on first interaction
  - Trade-offs: Simpler, prevents rating games, but doesn't reflect user improvement over time
  
- **Option C**: One rating per loan, but newer ratings replace older ones between same users
  - Impact: Always shows most recent experience between users
  - Trade-offs: Reflects current relationship, but loses rating history

**Recommendation for MVP**: Option A (one rating per loan). Most comprehensive feedback, reflects that users can improve or decline over time.

---

### Q6: How long should we wait before showing submitted ratings?

**Context**: Spec mentions "Ratings appear within 48 hours of submission (prevents immediate retaliation)" but doesn't specify exact timing or what happens if only one party rates.

**Options**:
- **Option A**: Both ratings appear together after both submitted OR 48 hours, whichever comes first
  - Impact: Ratings always appear in pairs or after timeout
  - Trade-offs: Fair system, but incomplete ratings might never show if one person doesn't participate
  
- **Option B**: Each rating appears exactly 48 hours after individual submission
  - Impact: Simple delay, ratings appear independently
  - Trade-offs: Predictable timing, but first rater might see retaliation rating before theirs appears
  
- **Option C**: Both ratings appear together immediately if submitted within 24 hours, otherwise 48-hour delay applies
  - Impact: Fast appearance for mutual raters, delay for one-sided ratings
  - Trade-offs: Rewards mutual participation, but complex logic

**Recommendation for MVP**: Option B (48-hour delay per rating). Simplest implementation, consistent behavior.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q7: What's the character limit and validation rules for user bios and reviews?

**Context**: Spec mentions "bio (optional, 200 chars max)" and "written review (500 character limit)" but doesn't specify content validation or formatting.

**Options**:
- **Option A**: Plain text only, basic profanity filter, no formatting
  - Impact: Simple text storage and display
  - Trade-offs: Clean and simple, but limited expression
  
- **Option B**: Allow basic markdown (bold, italic), basic profanity filter
  - Impact: Need markdown parsing and sanitization
  - Trade-offs: Better expression, but more complex and potential XSS risks
  
- **Option C**: Plain text with URL detection and link conversion
  - Impact: Auto-convert URLs to links, otherwise plain text
  - Trade-offs: Useful feature, moderate complexity

**Recommendation**: Option A (plain text only). Keep it simple for v1, can enhance formatting later.

---

### Q8: How should we calculate and display response time indicators?

**Context**: Spec mentions "Usually responds within 2 hours" based on historical message response times, but doesn't define the calculation method or minimum data requirements.

**Options**:
- **Option A**: Average response time over last 10 messages, require minimum 5 messages to display
  - Impact: Need to track message timestamps and calculate averages
  - Trade-offs: Accurate representation, but new users won't have indicator for a while
  
- **Option B**: Median response time over last 30 days, show "New member" if insufficient data
  - Impact: Time-based calculation, more robust against outliers
  - Trade-offs: Better statistical measure, but more complex calculation
  
- **Option C**: Simple categories: "Usually responds quickly" (< 4 hours), "Usually responds within a day" (< 24 hours), or no indicator
  - Impact: Simpler calculation and display, less precise but easier to understand
  - Trade-offs: Less precise but clearer user understanding

**Recommendation**: Option C (simple categories). Easier to understand and implement, provides useful guidance without over-precision.

---

## Notes for Product

- The address verification approach (Q2) will significantly impact development complexity - please prioritize this decision
- Rating system behavior (Q1, Q5, Q6) affects database design and user workflows - need these answers to proceed
- Happy to do another iteration if these answers raise new questions about data flows or technical constraints
- Once these are answered, I can proceed with detailed database schema and API specification