# Neighborhood-Based Communities - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: December 19, 2024

---

## Summary

After reviewing the specification, I've identified **8** areas that need clarification before implementation can begin. These questions address:
- Geographic boundary definitions and calculations
- Community creation and management logic
- Data validation and constraints
- User experience edge cases

The feature concept is solid, but several critical decisions about geographic calculations and community behavior need product input to proceed with implementation.

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: How do we define community boundaries precisely?

**Context**: The PRD mentions "postal/zip code with radius settings (0.5-2 miles typically)" but postal codes vary enormously in size. Some urban postal codes are 0.2 miles across, while rural ones can be 20+ miles. This fundamentally affects how communities are created and what "adjacent" means.

**Options**:
- **Option A**: Fixed radius from postal code centroid (e.g., 1.5 miles)
  - Impact: Consistent community sizes, simple distance calculations
  - Trade-offs: May not respect natural neighborhood boundaries, rural areas get tiny communities
  
- **Option B**: Adaptive radius based on population density
  - Impact: Dense areas get smaller radius, rural areas get larger radius
  - Trade-offs: More complex logic, but better matches real-world neighborhood sizes
  
- **Option C**: Postal code boundaries with minimum radius override
  - Impact: Use actual postal boundaries but ensure minimum 1-mile radius
  - Trade-offs: Respects official boundaries but adds complexity for small postal codes

**Recommendation for MVP**: Option A (fixed 1.5-mile radius). Simplest to implement and test, can enhance with adaptive logic in v2.

---

### Q2: When exactly are new communities created automatically?

**Context**: PRD says system "assigns them to appropriate community or creates one if none exists" but doesn't specify the logic. This affects database growth and user experience significantly.

**Options**:
- **Option A**: Create new community for every unique postal code
  - Impact: Many small communities, especially in rural areas
  - Trade-offs: Simple logic but could create ghost towns with 1-2 users
  
- **Option B**: Create community only if no existing community within X miles
  - Impact: Fewer, larger communities that might span multiple postal codes
  - Trade-offs: Better user density but postal codes might span multiple communities
  
- **Option C**: Create community immediately but merge small ones monthly
  - Impact: Responsive creation with cleanup background job
  - Trade-offs: More complex, users might get moved between communities

**Recommendation for MVP**: Option B (create only if no community within 3 miles). Prevents community fragmentation while ensuring reasonable coverage.

---

### Q3: What defines "adjacent communities" for discovery expansion?

**Context**: Users can "expand to include adjacent communities" but the calculation method isn't specified. This affects which tools users can discover and search performance.

**Options**:
- **Option A**: Communities whose center points are within 5 miles
  - Impact: Simple distance calculation, predictable results
  - Trade-offs: Might include communities that don't actually border geographically
  
- **Option B**: Communities whose boundaries overlap or touch
  - Impact: True geographic adjacency, more accurate
  - Trade-offs: Complex geometric calculations, harder to optimize queries
  
- **Option C**: Communities in same or neighboring postal codes
  - Impact: Leverage postal code hierarchy, very fast queries
  - Trade-offs: Depends on postal code system, might miss nearby areas

**Recommendation for MVP**: Option A (5-mile radius from center). Balances accuracy with implementation simplicity.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q4: What are the exact validation rules for address during signup?

**Context**: PRD mentions "postal/zip code + street name for verification" but validation requirements affect user onboarding flow and data quality.

**Options**:
- **Option A**: Just verify postal code exists, street name optional
  - Impact: Fast signup, lower accuracy
  - Trade-offs: Some users might game the system with fake addresses
  
- **Option B**: Require valid postal code + street name, no geocoding verification
  - Impact: Medium validation, relies on user honesty
  - Trade-offs: Balances user experience with data quality
  
- **Option C**: Full address verification with geocoding API
  - Impact: Highest accuracy, slower signup process
  - Trade-offs: External API dependency, potential signup abandonment

**Recommendation for MVP**: Option B. Good balance of data quality and user experience, can enhance verification later.

---

### Q5: How should community stats be calculated and updated?

**Context**: Community dashboard shows "total members, active lenders, tools available, loans completed this month" but calculation method affects performance and accuracy.

**Options**:
- **Option A**: Calculate stats in real-time on page load
  - Impact: Always current data, but slow page loads
  - Trade-offs: Accurate but poor performance as communities grow
  
- **Option B**: Daily batch job updates cached stats
  - Impact: Fast page loads, stats up to 24 hours old
  - Trade-offs: Great performance but slightly stale data
  
- **Option C**: Update stats on each relevant action (new member, loan completion)
  - Impact: Current stats with good performance
  - Trade-offs: More complex event handling, potential race conditions

**Recommendation for MVP**: Option B (daily batch update). Simple to implement and test, performance scales well.

---

### Q6: What's the minimum viable threshold for community activity warnings?

**Context**: PRD mentions "Communities with no activity for 60+ days get gentle nudges" but doesn't specify what constitutes "activity" or what the nudges are.

**Options**:
- **Option A**: Activity = any user login from community members
  - Impact: Low bar, most communities stay "active"
  - Trade-offs: Easy to track but might not indicate real engagement
  
- **Option B**: Activity = tools shared or borrowing requests made
  - Impact: Higher bar, focuses on actual tool sharing
  - Trade-offs: Better measure of tool sharing but might discourage new communities
  
- **Option C**: Activity = successful loan completions
  - Impact: Highest bar, only counts actual tool sharing success
  - Trade-offs: Most meaningful metric but very strict for new communities

**Recommendation for MVP**: Option B (tool sharing activity). Best balance of meaningful activity without being too restrictive.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q7: How should we handle users who move to different neighborhoods?

**Context**: Users might relocate and need to change communities, but PRD only mentions "address re-verification" without specifying the process.

**Options**:
- **Option A**: Allow address updates once per year with full re-verification
  - Impact: Prevents gaming while allowing legitimate moves
  - Trade-offs: Simple rule but might frustrate users who move twice
  
- **Option B**: Allow address updates anytime with manual review
  - Impact: Flexible but requires moderation resources
  - Trade-offs: Better user experience but operational overhead
  
- **Option C**: Automatic community transfer when user updates address
  - Impact: Seamless user experience
  - Trade-offs: Risk of users gaming location for better tool access

**Recommendation for MVP**: Option A. Prevents abuse while handling the common case (annual moves).

---

### Q8: Should community guidelines have character limits and approval process?

**Context**: PRD mentions "early adopters/active members can propose guideline updates" but doesn't specify content limits or approval workflow.

**Options**:
- **Option A**: Free-form text up to 2000 characters, immediate publication
  - Impact: Simple implementation, fast updates
  - Trade-offs: Risk of inappropriate content, no quality control
  
- **Option B**: Structured guideline categories with dropdown options
  - Impact: Consistent format, prevents abuse
  - Trade-offs: Less flexible, might not cover all local needs
  
- **Option C**: Free-form text with simple voting (3+ member approval)
  - Impact: Community-moderated content with reasonable safeguards
  - Trade-offs: More complex but balanced approach

**Recommendation for MVP**: Option B (structured categories). Safer for MVP, can add free-form sections in v2 if needed.

---

## Notes for Product

- The geographic calculations (Q1-Q3) are foundational and will significantly impact user experience and performance
- Consider starting with simpler geographic logic for MVP and enhancing based on user feedback
- Community management features (Q6-Q8) can use conservative defaults initially
- Happy to iterate on these answers - some decisions might raise follow-up questions about implementation details