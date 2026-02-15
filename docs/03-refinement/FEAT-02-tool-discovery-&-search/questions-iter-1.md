# Tool Discovery & Search - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: February 15, 2025

---

## Summary

After reviewing the specification, I've identified 8 areas that need clarification before implementation can begin. These questions address:
- Core search behavior and data model
- Geolocation accuracy and performance requirements
- Tool availability state management
- User experience edge cases

The specification provides good context on the user journey but needs more precision around technical behaviors and constraints.

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: What is the exact data model for tool availability?

**Context**: The PRD mentions "availability dates", "blocked-out dates", and "existing loans" but doesn't specify how this works. This is fundamental to the search engine design.

**Options**:
- **Option A**: Simple boolean availability per tool
  - Impact: Fast queries, but no future booking support
  - Trade-offs: Can only show "available now" vs "not available"
  - Database: Single `is_available` boolean on Tool table
  
- **Option B**: Date-range based availability with blocked periods
  - Impact: Complex queries, need DateRange table with tool_id, start_date, end_date, type (blocked/booked)
  - Trade-offs: Supports future planning, but much more complex
  - Database: Tool table + ToolAvailability table with range queries
  
- **Option C**: Calendar-based with daily availability status
  - Impact: Daily availability records, good for calendar UI
  - Trade-offs: Large data volume, but intuitive model
  - Database: ToolAvailability table with tool_id, date, status

**Recommendation for MVP**: Option A (simple boolean). Users can message owners about future dates. Can migrate to Option B in v2 if date planning becomes important.

---

### Q2: How precise must distance calculations be?

**Context**: PRD mentions "driving distance, not straight-line" but doesn't specify precision requirements or performance constraints. This affects whether we use external APIs or approximations.

**Options**:
- **Option A**: External API calls (Google Maps/MapBox) for exact driving distance
  - Impact: Precise but slow (200-500ms per calculation), API costs
  - Trade-offs: Perfect accuracy, but expensive and slow for large result sets
  
- **Option B**: Haversine formula (straight-line) with 1.3x multiplier approximation
  - Impact: Fast database-only queries, ~15% accuracy vs actual driving
  - Trade-offs: Very fast, no API costs, but less accurate in complex geography
  
- **Option C**: Pre-calculated distance matrix for common locations
  - Impact: Fast lookups but requires background job to maintain
  - Trade-offs: Good balance, but complex to implement and maintain

**Recommendation for MVP**: Option B (Haversine approximation). For local tool sharing, straight-line + multiplier is sufficient. Users understand "about X miles" vs exact driving directions.

---

### Q3: What happens when multiple users are viewing the same tool simultaneously?

**Context**: PRD mentions "real-time availability updates" but doesn't specify the mechanism or timing requirements.

**Options**:
- **Option A**: No real-time updates - users see snapshot at search time
  - Impact: Simple implementation, tool might be unavailable when user clicks
  - Trade-offs: Can lead to "sorry, just taken" messages but much simpler
  
- **Option B**: SignalR/WebSocket updates for availability changes
  - Impact: Complex real-time infrastructure, immediate updates
  - Trade-offs: Better UX but significant technical complexity
  
- **Option C**: Optimistic UI with background polling every 30 seconds
  - Impact: Moderate complexity, reasonably fresh data
  - Trade-offs: Good balance of freshness vs complexity

**Recommendation for MVP**: Option A (no real-time). Show availability at search time, handle conflicts during the borrowing request flow. Real-time can be v2 feature.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q4: What are the maximum limits for search results and performance?

**Context**: PRD mentions "load within 2 seconds for queries under 100 tools" but doesn't specify what happens above 100 tools or how we limit results.

**Options**:
- **Option A**: Hard limit of 50 results, sorted by distance
  - Impact: Simple pagination, guaranteed fast performance
  - Trade-offs: Users might miss good options just outside the limit
  
- **Option B**: Return up to 100 results with pagination beyond that
  - Impact: Need pagination UI, more complex queries
  - Trade-offs: More complete results but more complex implementation
  
- **Option C**: Return top 20 with "show more" that expands radius
  - Impact: Progressive disclosure, encourages broader search if needed
  - Trade-offs: Good UX but requires radius expansion logic

**Recommendation for MVP**: Option A (50 results max). Most users will find what they need in the closest 50 tools. Can add pagination in v2 if users request it.

---

### Q5: How should search handle tool categories and keywords?

**Context**: PRD mentions searching by "tool name, category, and keyword" with "common misspellings and tool name variations" but doesn't specify the matching logic.

**Options**:
- **Option A**: Simple ILIKE pattern matching on tool title/description
  - Impact: Basic functionality, works with PostgreSQL full-text search
  - Trade-offs: Simple to implement but limited fuzzy matching
  
- **Option B**: Full-text search with custom synonym dictionary
  - Impact: Need to maintain synonym mappings (wrench→spanner, drill→boring tool)
  - Trade-offs: Better search quality but requires content maintenance
  
- **Option C**: Elasticsearch integration with fuzzy matching
  - Impact: Add Elasticsearch to tech stack, excellent search capabilities
  - Trade-offs: Much better search experience but adds infrastructure complexity

**Recommendation for MVP**: Option A (PostgreSQL full-text). Can build synonym table over time based on user search patterns. Elasticsearch can be v2 if search quality becomes an issue.

---

### Q6: How do we handle user location privacy and accuracy?

**Context**: PRD mentions GPS location, ZIP code fallback, but doesn't specify privacy controls or location accuracy requirements.

**Options**:
- **Option A**: Always request precise GPS, store user's exact coordinates
  - Impact: Most accurate distance calculations, privacy concerns
  - Trade-offs: Best search results but users might not want exact location stored
  
- **Option B**: Use GPS for search session only, don't store coordinates
  - Impact: Good accuracy, request location on every search session
  - Trade-offs: Privacy-friendly but slower search experience
  
- **Option C**: Let users set "home location" to neighborhood/ZIP level precision
  - Impact: Store approximate location (ZIP+4 centroid), consistent searches
  - Trade-offs: Good privacy balance, ~0.1 mile accuracy which is sufficient

**Recommendation for MVP**: Option C (neighborhood-level home location). Users set approximate location once, searches are consistent and privacy-friendly.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q7: What should the "no results found" experience include?

**Context**: PRD mentions showing "expand search radius suggestion and alternative tool recommendations" but doesn't specify the alternatives logic.

**Options**:
- **Option A**: Just show "expand radius" button and similar categories
  - Impact: Simple implementation, show related categories (power tools → hand tools)
  - Trade-offs: Basic but functional, no personalization
  
- **Option B**: Show specific alternative tools and suggestions to post request
  - Impact: Query for similar tools, encourage users to post "looking for" requests
  - Trade-offs: More helpful but requires similarity logic
  
- **Option C**: Show most popular tools in area + request-to-post flow
  - Impact: Fallback to "trending" tools nearby, easy request posting
  - Trade-offs: Good fallback but might not be relevant

**Recommendation for MVP**: Option A (expand radius + categories). Simple and addresses most cases. Better recommendations can be v2 feature.

---

### Q8: Should search support filtering by tool value/quality tier?

**Context**: PRD mentions filtering by "tool condition" but doesn't specify if users want to filter by tool value or quality tier (professional vs consumer grade).

**Options**:
- **Option A**: Only condition-based filtering (like new, good, acceptable)
  - Impact: Simple enum-based filtering on tool condition
  - Trade-offs: Basic quality filtering but misses professional vs consumer distinction
  
- **Option B**: Add value range filtering ($0-50, $50-200, $200+)
  - Impact: Need estimated_value field on tools, price range UI
  - Trade-offs: Helps users find appropriate quality level but adds complexity
  
- **Option C**: Add professional/prosumer/consumer grade tags
  - Impact: Need tool_grade field and tagging system
  - Trade-offs: More semantic than price but requires classification effort

**Recommendation for MVP**: Option A (condition only). Users can see tool condition and make value judgments from photos/descriptions. Value filtering can be added later if requested.

---

## Notes for Product

- The availability model (Q1) is the most critical decision - it affects search performance, UI complexity, and future feature possibilities
- Distance calculation approach (Q2) significantly impacts search speed and infrastructure costs
- Happy to do another iteration if these answers raise new questions about search architecture
- Once these are answered, I can proceed with detailed database schema and API specification