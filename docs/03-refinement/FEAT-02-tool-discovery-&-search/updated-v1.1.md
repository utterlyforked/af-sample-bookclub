# Tool Discovery & Search - Feature Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification  
- v1.1 - Iteration 1 clarifications (added: availability model, distance calculations, search performance limits, location privacy)

---

## Feature Overview

The Tool Discovery & Search feature enables users to find tools they need within their local community through an intuitive search and filtering system. This is the core "shopping" experience of the platform - users arrive with a specific tool need and must be able to quickly find available options nearby.

The feature addresses the fundamental user journey: "I need a pressure washer this weekend" → "Here are 3 available within 2 miles of you." It combines text search, geolocation-based filtering, and availability checking to surface the most relevant and accessible tools for each user's specific situation and timeline.

This feature is critical for user adoption - if people can't easily find what they need, the entire platform fails. The search must be fast, accurate, and optimized for mobile use since many searches will happen on-site ("I need this tool right now for my current project").

---

## User Stories

- As someone needing a tool, I want to search by tool type and see all available options in my area so I can find what I need
- As someone needing a tool, I want to see how far away each tool is and when it's available so I can plan my project
- As someone needing a tool, I want to filter by distance, availability, and tool condition so I can find the best option
- As a mobile user on a job site, I want to quickly search for tools near my current location so I can solve problems without going home
- As a project planner, I want to see which tools are available during my planned work dates so I can coordinate my timeline

---

## Acceptance Criteria (UPDATED v1.1)

- Search works by tool name, category (power tools, garden tools, etc.), and keyword using PostgreSQL full-text search
- Results show approximate distance from user (±15% accuracy), current availability status, owner rating, and tool condition
- Users can filter by maximum distance (0.5, 1, 2, 5 miles), current availability, and tool condition (like new, good, acceptable)
- Each tool listing shows clear photos, detailed description, and owner contact preferences
- Search results load within 2 seconds and return maximum 50 results sorted by distance
- Users can search from their saved home location or update their neighborhood-level location
- Search handles common misspellings through PostgreSQL text search with basic synonym support
- No real-time availability updates - users see availability status at search time

---

## Detailed Specifications (UPDATED v1.1)

**Tool Availability Model**

**Decision**: Simple boolean availability per tool (is_available field)

**Rationale**: For MVP, we need fast queries and simple state management. Users can message owners about specific dates if needed. Complex date-range booking can be added in v2 when we understand usage patterns better.

**Examples**:
- Tool marked "available" shows in search results with green "Available Now" indicator
- Tool marked "unavailable" (being borrowed) doesn't appear in search results
- When tool is returned, owner marks it available again

**Edge Cases**:
- If owner doesn't mark tool as unavailable when lending, multiple users might request it - handled in borrowing request flow with "sorry, just taken" message

---

**Distance Calculations**

**Decision**: Haversine formula (straight-line distance) with 1.3x multiplier to approximate driving distance

**Rationale**: For local tool sharing within 5 miles, straight-line approximation is sufficient and keeps searches fast. Users understand "about X miles" rather than exact driving directions. No external API costs or latency.

**Examples**:
- User location: 123 Main St, Tool location: 456 Oak Ave
- Straight-line distance: 1.2 miles → Displayed as "About 1.6 miles away"
- In urban areas with grid streets, this approximates driving distance well

**Edge Cases**:
- In areas with rivers, mountains, or complex geography, distance might be less accurate
- Users can see tool location on map if they need exact driving directions

---

**Search Performance & Limits**

**Decision**: Maximum 50 search results, sorted by distance, must load within 2 seconds

**Rationale**: Most users will find what they need in the closest 50 tools. Limiting results keeps queries fast and UI manageable. Focus on showing the best options rather than exhaustive lists.

**Examples**:
- Search for "drill" returns 50 closest drills within user's selected radius
- If 200 drills exist in 5-mile radius, show closest 50
- Results pagination not needed for MVP

**Edge Cases**:
- If fewer than 50 results exist, show all available results
- If search is too restrictive (0 results), suggest expanding radius or browsing categories

---

**Location Privacy & Storage**

**Decision**: Users set neighborhood-level "home location" stored as approximate coordinates (ZIP+4 centroid level precision)

**Rationale**: Balances search accuracy with privacy. Users don't want exact home coordinates stored, but need consistent search results. ~0.1 mile accuracy is sufficient for tool sharing.

**Examples**:
- User enters "Downtown Seattle" or ZIP code 98101
- System stores centroid coordinates for that area: (47.6062, -122.3321)
- All searches use this approximate location consistently

**Edge Cases**:
- Users can update location anytime in settings
- Mobile users can temporarily search from "current location" without updating saved location

---

**Search Logic & Matching**

**Decision**: PostgreSQL full-text search with basic synonym table for common tool variations

**Rationale**: Native PostgreSQL search is fast and handles basic text matching well. Can build synonym dictionary over time based on user search patterns. Avoids complexity of external search service for MVP.

**Examples**:
- Search "drill" matches tools titled "Power Drill", "Cordless Drill", "Hammer Drill"
- Synonym table includes: wrench→spanner, mower→lawnmower, saw→circular saw
- Partial matches work: typing "chain" shows chainsaw results

**Edge Cases**:
- Misspellings beyond PostgreSQL's built-in fuzzy matching might not work
- Can add to synonym table based on failed search analytics

---

**No Results Experience**

**Decision**: Show "expand search radius" button and related tool categories when no results found

**Rationale**: Gives users immediate options to find alternatives without requiring complex recommendation algorithms. Most "no results" cases are due to too-restrictive radius.

**Examples**:
- Search for "jackhammer" in 0.5 mile radius finds nothing
- Show: "No jackhammers found within 0.5 miles. Try searching within 2 miles or browse Power Tools category"
- Display buttons: [Search 2 miles] [Browse Power Tools] [Browse All Categories]

**Edge Cases**:
- If expanding radius still finds nothing, show most popular tools in area
- Encourage users to post "looking for" request in future iteration

---

**Filtering Options**

**Decision**: Filter by distance radius, current availability, and tool condition only

**Rationale**: These are the three most important criteria for MVP. Tool value/grade filtering can be added later if users request it. Keep filtering simple to avoid decision paralysis.

**Examples**:
- Distance: 0.5, 1, 2, 5 miles (default: 2 miles)
- Availability: "Available now" checkbox (checked by default)
- Condition: "Like new", "Good", "Acceptable" checkboxes (all checked by default)

**Edge Cases**:
- Unchecking all condition filters shows no results - prevent this with UI validation
- Filters persist during search session but reset on new session

---

**Real-time Updates**

**Decision**: No real-time availability updates - users see tool availability status at time of search

**Rationale**: Real-time infrastructure adds significant complexity for minimal benefit in MVP. Tool availability doesn't change frequently enough to justify WebSocket connections. Handle conflicts during borrowing request process.

**Examples**:
- User searches at 2:00 PM, sees "pressure washer available"
- Another user borrows it at 2:15 PM
- Original user clicks "Contact Owner" at 2:30 PM, gets "Sorry, this tool was just borrowed" message
- System suggests similar available tools nearby

**Edge Cases**:
- Multiple users might try to borrow same tool simultaneously - first successful request wins
- Owners should mark tools unavailable promptly when lending them out

---

## Q&A History

### Iteration 1 - February 15, 2025

**Q1: What is the exact data model for tool availability?**  
**A**: Simple boolean availability per tool (is_available field). Users can message owners about specific dates. Complex date-range booking deferred to v2.

**Q2: How precise must distance calculations be?**  
**A**: Haversine formula with 1.3x multiplier approximation. Sufficient accuracy for local sharing without external API costs or latency.

**Q3: What happens when multiple users are viewing the same tool simultaneously?**  
**A**: No real-time updates. Show availability at search time, handle conflicts during borrowing request flow with "just taken" messages.

**Q4: What are the maximum limits for search results and performance?**  
**A**: Hard limit of 50 results sorted by distance. Guaranteed fast performance, pagination not needed for MVP.

**Q5: How should search handle tool categories and keywords?**  
**A**: PostgreSQL full-text search with basic synonym table. Build synonym dictionary over time based on user search patterns.

**Q6: How do we handle user location privacy and accuracy?**  
**A**: Users set neighborhood-level home location (ZIP+4 centroid precision). Balances privacy with search accuracy.

**Q7: What should the "no results found" experience include?**  
**A**: Show expand radius button and related categories. Simple and addresses most cases without complex recommendation algorithms.

**Q8: Should search support filtering by tool value/quality tier?**  
**A**: No, condition-based filtering only for MVP. Users can judge value from photos/descriptions. Value filtering can be added later if requested.

---

## Product Rationale

**Why simple boolean availability over date-range booking?**  
User research shows most tool sharing is spontaneous ("need this today/tomorrow"). Complex scheduling adds friction that could hurt adoption. Start simple, add complexity only when usage patterns prove it's needed.

**Why approximate distance over exact driving directions?**  
Tool sharing happens within neighborhoods where straight-line distance correlates well with driving distance. Exact routing adds 200-500ms per search result and API costs. Users can get driving directions when they decide to contact an owner.

**Why 50 result limit?**  
Analysis of similar platforms shows users rarely look beyond the first 20-30 results. 50 provides buffer while keeping performance predictable. Focus on showing the best matches rather than comprehensive listings.

**Why neighborhood-level location over exact GPS?**  
Privacy concerns around storing exact home coordinates outweigh marginal search accuracy benefits. 0.1-mile precision is sufficient for finding tools within 1-5 mile radius searches.