# Lesson Planning & Management - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: December 19, 2024

---

## Summary

After reviewing the specification, I've identified 8 areas that need clarification before implementation can begin. These questions address:
- Content organization and versioning
- Resource management and storage
- Assessment structure and grading
- User permissions and collaboration
- Data persistence and sharing

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: Can lesson plans be edited after creation, and how do we handle versioning?

**Context**: The PRD mentions creating and managing lesson plans but doesn't specify if they can be modified after creation. This affects:
- Database design (need version tracking?)
- Resource references (what if linked resources change?)
- Sharing behavior (does shared plan update when original changes?)

**Options**:
- **Option A**: Immutable lesson plans
  - Impact: Simple implementation, no versioning needed
  - Trade-offs: Users must duplicate to make changes, but no confusion about versions
  
- **Option B**: Editable with auto-versioning
  - Impact: Need version history table, complex sharing logic
  - Trade-offs: Full flexibility but complex to implement and understand
  
- **Option C**: Editable but overwrite (no versioning)
  - Impact: Simple updates, track modified_at timestamp
  - Trade-offs: Good UX, but shared plans change unexpectedly

**Recommendation for MVP**: Option C (simple editing). Teachers expect to refine lesson plans. Can add versioning in v2 if needed.

---

### Q2: What's the data model for assessments within lesson plans?

**Context**: PRD mentions "assessments" as part of lesson plans but doesn't define structure. Need to know:
- Are assessments just descriptions or structured data?
- Do they have types (quiz, project, homework)?
- Are they linked to specific learning objectives?

**Options**:
- **Option A**: Simple text field for assessment notes
  - Impact: Just add `assessment_notes` text column
  - Trade-offs: Very simple, but limited functionality
  
- **Option B**: Structured assessment objects
  - Impact: Separate assessments table with type, points, rubrics
  - Trade-offs: Much more powerful but complex to implement
  
- **Option C**: Mixed approach - structured metadata + description
  - Impact: Assessment table with type/points + description field
  - Trade-offs: Balance of structure and flexibility

**Recommendation for MVP**: Option A (text field). Teachers can describe assessments freely. Can enhance with structure in v2 based on usage patterns.

---

### Q3: How are educational resources stored and managed?

**Context**: PRD mentions "link educational resources" but doesn't specify:
- Are resources uploaded files or external links?
- What file types/sizes are supported?
- Who can see/use linked resources?

**Options**:
- **Option A**: External links only
  - Impact: Store URLs in resources table, no file storage needed
  - Trade-offs: Simple implementation, but links can break
  
- **Option B**: File uploads only
  - Impact: Need file storage (S3/similar), size limits, file management
  - Trade-offs: Reliable but requires storage infrastructure
  
- **Option C**: Both links and uploads
  - Impact: Resource table with type field, file storage for uploads
  - Trade-offs: Maximum flexibility but most complex

**Recommendation for MVP**: Option A (links only). Simpler to implement, teachers often use existing online resources. Can add uploads in v2.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q4: What are the permission levels for lesson plan sharing and collaboration?

**Context**: PRD mentions sharing but doesn't define permission model:
- Can shared plans be edited by others?
- Are there view-only vs edit permissions?
- Can teachers share with specific individuals or just make public?

**Options**:
- **Option A**: View-only sharing
  - Impact: Simple sharing table with lesson_plan_id + shared_with_user_id
  - Trade-offs: Safe but limited collaboration
  
- **Option B**: Role-based sharing (view/edit)
  - Impact: Add permission_level to sharing table
  - Trade-offs: More flexible, slight complexity increase
  
- **Option C**: Full collaboration with ownership transfer
  - Impact: Complex permissions, conflict resolution needed
  - Trade-offs: Most flexible but significantly more complex

**Recommendation for MVP**: Option B (role-based). Teachers need both "look at this" and "help me build this" sharing modes.

---

### Q5: How should lesson plans be organized and categorized?

**Context**: PRD mentions teachers can "organize" lesson plans but doesn't specify:
- Are there folders/categories?
- Can plans have tags or subjects?
- How are they sorted by default?

**Options**:
- **Option A**: Simple chronological list
  - Impact: Just sort by created_at/updated_at
  - Trade-offs: Very simple but gets unwieldy with many plans
  
- **Option B**: Subject-based categories
  - Impact: Add subject field, filter/group by subject
  - Trade-offs: Logical organization, easy to implement
  
- **Option C**: Flexible tagging system
  - Impact: Tags table with many-to-many relationship
  - Trade-offs: Maximum flexibility but more complex UI

**Recommendation for MVP**: Option B (subject categories). Teachers think in subjects, simple to implement and understand.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q6: What are the size/content limits for lesson plan components?

**Context**: Need practical limits for database design and UI:

**Options**:
- **Option A**: Conservative limits
  - Impact: Title 200 chars, objectives 500 chars each, notes 2000 chars
  - Trade-offs: Ensures good performance, might feel restrictive
  
- **Option B**: Generous limits
  - Impact: Title 500 chars, objectives 1000 chars each, notes 10000 chars
  - Trade-offs: Accommodates detailed plans, slight performance impact

**Recommendation for MVP**: Option B (generous). Teachers write detailed plans, better to be accommodating.

---

### Q7: Should there be templates or starting points for lesson plans?

**Context**: PRD doesn't mention templates but could improve UX:

**Options**:
- **Option A**: Start with blank lesson plan
  - Impact: Simple create form, user fills everything
  - Trade-offs: Simple to implement but might be intimidating
  
- **Option B**: Provide basic template structure
  - Impact: Pre-populate with sample objectives/activities
  - Trade-offs: Helps new users, minimal additional complexity

**Recommendation for MVP**: Option A (blank start). Focus on core functionality first, can add templates based on user feedback.

---

### Q8: How should learning objectives be structured within a lesson plan?

**Context**: PRD mentions "learning objectives" but not their structure:

**Options**:
- **Option A**: Simple text list
  - Impact: Text field with line breaks or simple array
  - Trade-offs: Easy to implement and use
  
- **Option B**: Structured objectives with categories
  - Impact: Separate objectives table with type/category fields
  - Trade-offs: More educational value but added complexity

**Recommendation for MVP**: Option A (simple list). Teachers can write objectives naturally, can add structure later if needed.

---

## Notes for Product

- The lesson planning domain has many established patterns in education - happy to research best practices if helpful
- File storage will require infrastructure decisions if we go with uploads
- Consider teacher workflow: most plan lessons iteratively over time rather than in single sessions
- Once these are answered, I can proceed to implementation