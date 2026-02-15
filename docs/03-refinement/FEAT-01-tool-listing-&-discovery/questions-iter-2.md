# Tool Listing & Discovery - Technical Review (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: December 19, 2024

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. All critical questions from the previous iteration have been answered clearly with specific validation rules, search behavior, photo handling, and location implementation details.

## What's Clear

### Data Model
- Tool entity with title (100 chars max), description (1000 chars max), category (from predefined flat list), availability status
- Photo entity linked to tools (max 5 per tool, JPEG/PNG, 5MB max each)
- User entity with postal code for location-based search
- Activity tracking with "last_active" timestamp on users
- Postal code adjacency lookup table for search radius

### Business Logic
- Fuzzy duplicate detection at 75% similarity with warning + override option
- Photo processing pipeline: validate → generate 3 sizes (150x150, 400x300, 1200x900) → compress to 85% quality
- Search ranking algorithm: exact title match (100pts) → partial title (50pts) → description (25pts) → category (15pts) minus distance penalty
- Activity indicators shown after 30+ days of owner inactivity
- Search scope includes user's postal code + adjacent postal codes

### API Design
- Tool CRUD endpoints with validation per specified rules
- Photo upload endpoint with multi-part form support
- Search endpoint with query params for text, category, postal code filters
- Duplicate check endpoint for real-time warnings during listing creation
- Results pagination limited to 50 items for performance

### UI/UX
- Search results ordered by relevance score then distance
- "No results" page with specific suggestions (broader keywords, different category, expand areas)
- Photo gallery with drag-and-drop reordering, lightbox view
- Activity indicators: gray text for 30-90 days, orange with warning icon for 90+ days
- Form validation preserves user input during errors

### Edge Cases
- Empty/whitespace validation with clear error messages
- Upload failure handling with retry mechanism and progress indicators
- Invalid postal code searches return "No tools in that area"
- Minimum one photo requirement enforced
- Community reporting mechanism for inappropriate photos with 24-hour manual review

## Implementation Notes

**Database**:
- Tool table with varchar(100) title, varchar(1000) description, enum category, boolean available, timestamps
- Photo table with tool_id foreign key, file_path, display_order, created_at
- User table with postal_code varchar(10), last_active_at timestamp
- PostalCodeAdjacency lookup table for search radius calculations

**Authorization**:
- Tool owners can edit/delete only their own listings
- Any authenticated user can create listings and search
- Photo reporting available to all authenticated users

**Validation**:
- Tool name: 100 chars max, alphanumeric + periods, hyphens, spaces, parentheses
- Description: 1000 chars max, full text including line breaks
- Photos: JPEG/PNG only, 5MB max per file, max 5 files per listing
- Postal codes validated against known postal code database

**Key Decisions**:
- Postal code based location (privacy-friendly, no GPS required)
- Flat category structure with ~15 predefined options
- Fixed photo cropping/scaling with no user control
- Simple text-match + distance scoring for search results
- Activity tracking without automatic availability changes
- Community reporting with manual review for inappropriate content

## Recommended Next Steps

1. Create engineering specification with detailed implementation plan
2. Set up postal code adjacency database/service
3. Design photo storage structure and CDN integration
4. Implement search indexing strategy for performance

---

**This feature is ready for detailed engineering specification.**