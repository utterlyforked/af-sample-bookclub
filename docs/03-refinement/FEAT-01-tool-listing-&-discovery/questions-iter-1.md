# Tool Listing & Discovery - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: December 19, 2024

---

## Summary

After reviewing the specification, I've identified 8 areas that need clarification before implementation can begin. These questions address:
- Data validation and constraints
- Search behavior and performance requirements
- Photo handling specifics
- Location privacy implementation
- User experience edge cases

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What are the exact validation rules for tool listings?

**Context**: The PRD mentions required/optional fields but doesn't specify length limits, validation rules, or character restrictions. This affects database schema design, form validation, and API contracts.

**Options**:
- **Option A: Conservative limits**
  - Tool name: 100 chars max, alphanumeric + basic punctuation
  - Description: 1000 chars max, full text allowed
  - Impact: Prevents abuse, ensures good UI display, simple validation
  - Trade-offs: Might truncate detailed descriptions
  
- **Option B: Generous limits**
  - Tool name: 200 chars max, most characters allowed
  - Description: 5000 chars max, rich text formatting
  - Impact: More flexibility for detailed listings, complex validation needed
  - Trade-offs: Potential for spam/abuse, harder to display consistently

**Recommendation for MVP**: Option A. Clear limits prevent edge cases, users can always contact directly for additional details.

---

### Q2: How should location-based search work exactly?

**Context**: PRD mentions "2 mile default radius" and "neighborhood level" privacy, but doesn't specify how location is stored, calculated, or what happens at community boundaries.

**Options**:
- **Option A: User sets neighborhood manually**
  - Users select from predefined neighborhoods during signup
  - Search within same neighborhood + adjacent ones
  - Impact: Simple implementation, respects community boundaries
  - Trade-offs: Less precise, requires neighborhood data maintenance
  
- **Option B: Coordinate-based with privacy zones**
  - Store user coordinates, search by radius calculation
  - Display only postal code or neighborhood name publicly
  - Impact: Most accurate distance, flexible radius
  - Trade-offs: More complex privacy handling, requires coordinate permissions

- **Option C: Postal code based**
  - Users provide postal code, search within postal code + adjacent ones
  - Display postal code area publicly
  - Impact: Good balance of precision and privacy
  - Trade-offs: Postal code boundaries might not match logical neighborhoods

**Recommendation for MVP**: Option C (postal code based). Easier to implement than coordinates, more precise than manual neighborhoods.

---

### Q3: What happens when users upload invalid or inappropriate photos?

**Context**: PRD mentions photo upload requirements but doesn't address moderation, inappropriate content, or technical failures during upload.

**Options**:
- **Option A: Basic technical validation only**
  - Validate file type, size, basic image format
  - No content moderation initially
  - Impact: Fast uploads, minimal complexity
  - Trade-offs: Risk of inappropriate content, users must self-police
  
- **Option B: Automated content screening**
  - Technical validation + automated inappropriate content detection
  - Auto-reject flagged images with human review option
  - Impact: Safer community, requires third-party service integration
  - Trade-offs: More complexity, potential false positives, additional costs

- **Option C: Community reporting system**
  - Basic validation + user reporting mechanism
  - Manual review of reported images
  - Impact: Community self-moderation, manageable workload
  - Trade-offs: Reactive rather than proactive, requires moderation process

**Recommendation for MVP**: Option A with reporting mechanism. Focus on technical validation first, add community reporting, expand to automated screening later if needed.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q4: How should search results be ranked when multiple tools match?

**Context**: PRD mentions "relevance and distance" but doesn't specify the exact algorithm or weighting between factors.

**Options**:
- **Option A: Simple text match + distance**
  - Exact title match (100 pts) > partial title (50 pts) > description match (25 pts)
  - Subtract distance in miles from score
  - Impact: Predictable results, easy to debug
  - Trade-offs: Might prioritize far-away perfect matches over nearby good matches
  
- **Option B: Weighted relevance scoring**
  - Text relevance (60%) + proximity bonus (30%) + recency (10%)
  - Boost recently updated listings slightly
  - Impact: More balanced results considering multiple factors
  - Trade-offs: More complex, harder for users to predict result order

**Recommendation for MVP**: Option A. Users understand "best match, closest first" intuitively. Can enhance with Option B later based on user feedback.

---

### Q5: What should happen when tool owners don't respond to requests?

**Context**: This feature creates listings but doesn't handle the borrowing workflow. However, stale or unresponsive listings hurt the discovery experience.

**Options**:
- **Option A: No automatic handling**
  - Rely on users to manage their own listing availability
  - Impact: Simplest implementation, no automated changes to user data
  - Trade-offs: Potential for stale listings, frustrated borrowers
  
- **Option B: Inactive listing detection**
  - Track when listings last had owner activity
  - Flag listings as "potentially inactive" after 30 days of no owner response
  - Impact: Better user experience, helps identify stale listings
  - Trade-offs: Requires tracking owner activity across features

- **Option C: Auto-disable unresponsive listings**
  - Automatically mark listings unavailable after prolonged inactivity
  - Send email notification to owners before disabling
  - Impact: Keeps search results fresh, forces owners to stay engaged
  - Trade-offs: Might disable listings of owners who are just selective

**Recommendation for MVP**: Option B. Track activity for future features, show "last active" indicators to help borrowers make informed requests.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q6: How should we handle duplicate tool listings from the same user?

**Context**: PRD mentions preventing duplicates but doesn't define what constitutes a duplicate or how strict the matching should be.

**Options**:
- **Option A: Exact title match prevention**
  - Block identical tool names from same user
  - Impact: Prevents obvious duplicates, simple validation
  - Trade-offs: User can't list two identical tools (e.g., two drills)
  
- **Option B: Similar listing detection**
  - Warn about similar titles/descriptions, allow override
  - Impact: Flexible but guides users away from duplicates
  - Trade-offs: More complex matching logic
  
- **Option C: No duplicate prevention**
  - Allow users to list whatever they want
  - Impact: Simplest implementation
  - Trade-offs: Potential for spam or confusion

**Recommendation for MVP**: Option B. Show warning like "You have a similar listing: [title]" with option to proceed or edit existing.

---

### Q7: What photo features are needed beyond basic upload?

**Context**: PRD mentions "compression and thumbnails" but doesn't specify sizes, quality levels, or user controls.

**Options**:
- **Option A: Fixed thumbnail sizes**
  - Generate: thumbnail (150x150), medium (400x300), full (1200x900)
  - Automatic cropping/scaling, no user control
  - Impact: Consistent UI, predictable performance
  - Trade-offs: Might crop important parts of images
  
- **Option B: Multiple sizes + user cropping**
  - Same sizes as Option A, but users can adjust crop area
  - Impact: Better image quality, user control over framing
  - Trade-offs: More complex upload flow, additional UI needed

**Recommendation for MVP**: Option A. Users can always retake photos if cropping looks bad. Add user cropping in v2 if requested.

---

### Q8: Should tool categories be hierarchical or flat?

**Context**: PRD mentions "predefined categories" but doesn't specify if subcategories are needed (e.g., Power Tools > Drills > Cordless Drills).

**Options**:
- **Option A: Flat category list**
  - Single level: "Power Tools", "Hand Tools", "Garden Tools", etc.
  - Impact: Simple UI, easy search/filter implementation
  - Trade-offs: Might have too many categories as platform grows
  
- **Option B: Two-level hierarchy**
  - Main categories with subcategories: Power Tools > [Drills, Saws, Sanders]
  - Impact: Better organization, more precise filtering
  - Trade-offs: More complex UI, users might not know which subcategory to choose

**Recommendation for MVP**: Option A. Start with ~15 well-chosen flat categories. Can add subcategories later when we have data on which categories have too many tools.

---

## Notes for Product

- Once these questions are answered, the feature should be ready for implementation
- The data model section will need updates based on your answers, but the core entities are clear
- Happy to do iteration 2 if these answers raise new questions about edge cases