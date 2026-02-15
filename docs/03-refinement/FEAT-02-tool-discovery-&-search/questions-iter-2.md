# Tool Discovery & Search - Technical Review (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: February 15, 2025

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. All critical questions from the first iteration have been answered clearly, and the product decisions provide concrete guidance for building the search functionality.

## What's Clear

### Data Model
- Tool entity with `is_available` boolean field for simple availability tracking
- User location stored as approximate coordinates (ZIP+4 centroid precision)
- Synonym table for search term variations (wrench→spanner, mower→lawnmower)
- Tool condition enum: "Like new", "Good", "Acceptable"

### Business Logic
- Haversine formula with 1.3x multiplier for distance approximation
- PostgreSQL full-text search with basic synonym matching
- No real-time updates - availability checked at search time
- Conflict resolution during borrowing request flow ("just taken" messages)
- Search radius options: 0.5, 1, 2, 5 miles (default: 2 miles)

### API Design
- Search endpoint returns maximum 50 results sorted by distance
- Filter parameters: radius, availability status, tool condition
- Response includes: approximate distance, availability status, owner rating, tool condition
- 2-second response time guarantee
- Location update endpoint for neighborhood-level coordinates

### UI/UX
- Default filters: 2-mile radius, available tools only, all conditions
- Distance displayed as "About X miles away" with ±15% accuracy disclaimer
- No results experience: expand radius button + category suggestions
- Green "Available Now" indicator for available tools
- Search persistence during session, reset on new session

### Edge Cases
- Multiple users requesting same tool: first successful request wins
- Zero results: show expand radius and category browse options
- Search performance: hard 50-result limit prevents slow queries
- Location privacy: approximate coordinates only, no exact addresses stored
- Misspellings: handled by PostgreSQL fuzzy matching + synonym table

## Implementation Notes

**Database**:
- Tools table: `is_available` boolean field (indexed)
- Users table: `location_lat`, `location_lng` for approximate coordinates
- Synonyms table: `search_term`, `canonical_term` for search variations
- Full-text search index on tool name, category, description fields

**Authorization**:
- Search available to all authenticated users
- Location updates restricted to user's own profile
- Tool availability status visible to all users

**Validation**:
- Search radius: 0.5-5 miles only
- Location coordinates: valid latitude/longitude ranges
- Search query: max 100 characters, basic sanitization

**Key Decisions**:
- Simple boolean availability (no date ranges for MVP)
- Approximate distance calculations (no external routing APIs)
- 50-result limit for consistent performance
- Neighborhood-level location storage for privacy
- No real-time availability updates

## Recommended Next Steps

1. Create engineering specification with detailed implementation plan
2. Set up PostgreSQL full-text search indexes
3. Build synonym seeding script for common tool variations
4. Create distance calculation utility functions

---

**This feature is ready for detailed engineering specification.**