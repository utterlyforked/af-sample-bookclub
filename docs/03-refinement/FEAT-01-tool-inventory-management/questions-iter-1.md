# Tool Inventory Management - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: February 15, 2025

---

## Summary

After reviewing the specification, I've identified 8 areas that need clarification before implementation can begin. These questions address:
- Core data model constraints and validation rules
- Photo management and storage architecture
- Authorization and ownership rules
- Status management and business logic
- Edge case handling for concurrent operations

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What are the exact validation rules and constraints for tool fields?

**Context**: The PRD mentions field requirements but lacks specific validation rules needed for database design and API validation.

**Options**:
- **Option A: Minimal constraints**
  - Title: 3-100 chars, Description: 20-2000 chars, No brand/model validation
  - Impact: Simple validation, permissive data entry
  - Trade-offs: Risk of poor quality listings, harder to search/filter
  
- **Option B: Moderate constraints**
  - Title: 5-150 chars, Description: 20-2000 chars, Brand/model optional 50 chars each
  - Estimated value: $0-$10,000, Year purchased: 1950-current year
  - Impact: Balanced validation encouraging quality while not restrictive
  - Trade-offs: Good data quality, some edge cases rejected
  
- **Option C: Strict constraints**
  - Title must include tool type, Brand required from dropdown, Model required
  - Impact: High-quality structured data, excellent searchability
  - Trade-offs: Friction during entry, might discourage listings

**Recommendation for MVP**: Option B - provides good data quality without being overly restrictive, can tighten later based on data quality observed.

---

### Q2: How should we handle tool photos in terms of storage, processing, and deletion?

**Context**: PRD mentions 5 photos max with compression but lacks specifics about storage architecture, what happens to photos when tools are deleted, and processing pipeline.

**Options**:
- **Option A: Simple blob storage with immediate processing**
  - Upload → resize/compress immediately → store in blob storage
  - Photo URLs stored directly in database
  - Photos deleted when tool deleted
  - Impact: Simple implementation, immediate feedback
  - Trade-offs: Slower uploads, potential timeouts on large images
  
- **Option B: Async processing with queue**
  - Upload → temporary storage → background job processes → move to final storage
  - Database tracks processing status per photo
  - Impact: Faster uploads, more robust processing
  - Trade-offs: More complex, users see "processing" state
  
- **Option C: Hybrid with CDN**
  - Direct upload to blob storage with CDN
  - Background job creates optimized versions (thumbnail, medium, full)
  - Database stores multiple URLs per photo
  - Impact: Fast uploads, optimized delivery, multiple sizes
  - Trade-offs: Most complex, higher storage costs

**Recommendation for MVP**: Option A with async optimization later. Get basic functionality working, can enhance processing pipeline in v2.

---

### Q3: Can multiple users co-own tools, or is ownership always individual?

**Context**: PRD assumes single ownership but doesn't explicitly state this. Affects authorization model and UI design.

**Options**:
- **Option A: Single owner only**
  - One User → many Tools relationship
  - Only tool owner can edit/delete/manage availability
  - Impact: Simple authorization, clear responsibility
  - Trade-offs: Can't handle shared tools between roommates/partners
  
- **Option B: Support co-ownership**
  - Tool has primary owner + optional co-owners
  - All owners can manage the tool
  - Impact: More complex authorization, sharing permissions
  - Trade-offs: Handles real-world scenarios but adds complexity
  
- **Option C: Primary owner with delegates**
  - Single owner can grant management permissions to others
  - Audit trail of who made changes
  - Impact: Flexible but maintains clear ownership hierarchy
  - Trade-offs: Most flexible but most complex to implement

**Recommendation for MVP**: Option A (single owner). Vast majority of tools have single owners, can add co-ownership in v2 if users request it.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q4: What happens when a user tries to delete a tool that has historical loan data?

**Context**: PRD mentions blocking deletion if "currently on loan" but doesn't address tools with completed loan history.

**Options**:
- **Option A: Hard delete everything**
  - Delete tool and all associated loan records
  - Impact: Clean database, no orphaned data
  - Trade-offs: Lose valuable sharing history and analytics
  
- **Option B: Soft delete with history preservation**
  - Mark tool as deleted but keep all data
  - Hide from active listings but preserve in loan history
  - Impact: Maintain data integrity and analytics
  - Trade-offs: Database grows over time, need cleanup strategy
  
- **Option C: Archive system**
  - Move deleted tools to separate archive table
  - Loan history references archive
  - Impact: Clean active tables, preserved history
  - Trade-offs: More complex queries for historical data

**Recommendation for MVP**: Option B (soft delete). Sharing history is valuable for community trust and analytics. Can add archival process later if performance becomes an issue.

---

### Q5: How should "Temporarily Unavailable" work - does it expire automatically or require manual management?

**Context**: PRD mentions "estimated return to availability" but doesn't specify if this is automatic or just informational.

**Options**:
- **Option A: Manual only**
  - Owner sets status to "Temporarily Unavailable"
  - Must manually change back to "Available"
  - Estimated date is display-only
  - Impact: Simple implementation, full owner control
  - Trade-offs: Tools might stay unavailable if owner forgets
  
- **Option B: Automatic with override**
  - System automatically returns tools to "Available" on estimated date
  - Owner gets notification and can extend if needed
  - Impact: Ensures tools return to availability
  - Trade-offs: Need background job, notifications system
  
- **Option C: Reminder system**
  - Manual management but system sends reminders
  - "Your drill has been unavailable for 2 weeks - still need it?"
  - Impact: Balances automation with owner control
  - Trade-offs: Less automated but reduces forgotten unavailable tools

**Recommendation for MVP**: Option A (manual only). Keep it simple for v1, can add automation based on how users actually behave with the feature.

---

### Q6: Should we enforce uniqueness constraints on tool titles within a user's inventory?

**Context**: PRD mentions "Allow duplicates (someone might have multiple drills)" but this needs clarification for UX and data integrity.

**Options**:
- **Option A: No uniqueness constraint**
  - Users can have multiple "Cordless Drill" entries
  - Impact: Maximum flexibility, handles multiple identical tools
  - Trade-offs: Potential confusion in UI, harder to distinguish tools
  
- **Option B: Suggest uniqueness with override**
  - Warn "You already have a 'Cordless Drill' - continue anyway?"
  - Allow duplicates but encourage differentiation
  - Impact: Guides users toward better organization
  - Trade-offs: Extra UI complexity, users can still create duplicates
  
- **Option C: Enforce meaningful differences**
  - Require title + brand combination to be unique per user
  - Force users to differentiate (e.g., "Cordless Drill - Makita", "Cordless Drill - DeWalt")
  - Impact: Cleaner data, easier tool identification
  - Trade-offs: More restrictive, might frustrate users with truly identical tools

**Recommendation for MVP**: Option B - gentle guidance toward unique names while allowing flexibility. Improves UX without being overly restrictive.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q7: How should the estimated value field behave and what validation should it have?

**Context**: PRD mentions $0-$10,000 range with high/low warnings but doesn't specify decimal precision or warning thresholds.

**Options**:
- **Option A: Integer dollars only**
  - Store as integer, $1-$10,000 range
  - Warning if under $10 or over $1,000
  - Impact: Simple storage and display
  - Trade-offs: Can't represent sub-dollar values (not realistic anyway)
  
- **Option B: Two decimal precision**
  - Store as decimal(8,2), allow cents
  - Same warning thresholds
  - Impact: More precise but unnecessary complexity
  - Trade-offs: Users unlikely to care about cents for tool values
  
- **Option C: Smart defaults by category**
  - Suggest value ranges based on tool category
  - Hand tools: $10-$200, Power tools: $50-$800, etc.
  - Impact: Better user guidance, more realistic values
  - Trade-offs: Need to maintain category-based suggestions

**Recommendation**: Option A with smart category hints. Integer values are sufficient, can add category-based guidance text without complex validation.

---

### Q8: What should happen when a user changes a tool's category after it has loan history?

**Context**: PRD says "Allow category changes even with loan history" but this affects analytics and search history.

**Options**:
- **Option A: Simple category update**
  - Just update the category, loan history unchanged
  - Impact: Simple implementation
  - Trade-offs: Analytics lose category consistency over time
  
- **Option B: Track category history**
  - Keep log of category changes with dates
  - Analytics can show category at time of loan
  - Impact: Accurate historical analytics
  - Trade-offs: More complex data model
  
- **Option C: Warning with confirmation**
  - Show "This will affect how your tool appears in search - continue?"
  - Simple update but with user awareness
  - Impact: User education without complexity
  - Trade-offs: Extra UI step but better user understanding

**Recommendation**: Option C - simple implementation with user education. Category changes should be rare enough that a confirmation step is reasonable.

---

## Notes for Product

- Several questions relate to data quality vs. user friction - leaning toward permissive for MVP with ability to tighten later
- Photo management is the most technically complex area - recommend starting simple
- The soft delete approach for tools preserves valuable community data
- Happy to do another iteration if these answers raise new questions about implementation approach