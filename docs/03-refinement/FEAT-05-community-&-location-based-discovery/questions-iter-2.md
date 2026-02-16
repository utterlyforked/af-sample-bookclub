# Community & Location-Based Discovery - Technical Questions (Iteration 2)

**Status**: NEEDS CLARIFICATION
**Iteration**: 2
**Date**: 2025-01-10

---

## Summary

After reviewing the v1.1 specification (which excellently addressed all 16 questions from Iteration 1), I've identified **7 remaining areas** that need clarification before implementation can begin. These questions address:

- Map pin interaction behavior and data flow
- Activity feed event selection and ordering
- Follow system UI integration points
- Statistics page caching and staleness handling
- Search result pagination and performance
- Edge case handling for location data

The specification is in very good shape - these are mostly edge cases and implementation-critical details that emerged after the first round of clarifications.

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: How should map pin clicks interact with tool availability changes?

**Context**: The spec says map data is cached for 5 minutes, but pins open popups with "View Details" buttons. If a user clicks a pin at 4:59 of the cache window, then clicks "View Details" at 5:01 (after cache expired), they might land on a tool detail page showing "Currently Unavailable" - creating a confusing experience.

**Options**:

- **Option A: No validation, allow stale clicks**
  - Impact: User clicks cached pin → navigates to detail page → sees "unavailable" message
  - Trade-offs: Simple implementation, but potentially frustrating UX (3-4 clicks wasted)
  - Implementation: Pin popup just contains link to `/tools/{id}`, detail page shows current status
  
- **Option B: Validate availability on popup open**
  - Impact: When user clicks pin, fetch current availability before showing popup
  - Trade-offs: Extra API call per click, but prevents stale navigation
  - Implementation: Click handler → `GET /api/v1/tools/{id}/availability` → if available show popup, if not show toast "This tool is no longer available"
  
- **Option C: Show availability timestamp in popup**
  - Impact: Popup displays "As of 3 minutes ago" with current availability
  - Trade-offs: User informed of staleness, makes their own decision
  - Implementation: Cache timestamp stored with pin data, displayed in popup

**Recommendation for MVP**: Option B (validate on popup open). The extra API call is small cost (single lookup, indexed query), and preventing users from clicking through to unavailable tools significantly improves experience. Map browsing is exploratory; when user clicks a specific pin, they're showing intent - worth validating freshness at that moment.

---

### Q2: What determines which tools appear in Activity Feed "New Tool Listed" events?

**Context**: The spec says "Recent Activity" shows last 20 events within radius, including "New tool listed" events. But it doesn't specify **when** a tool qualifies for an event. Does this mean:
- Every tool creation triggers an event?
- Only when tool transitions from draft to published?
- Only when tool becomes available (not currently borrowed)?

This matters because Feature 1 (tool listing) might have draft states, or tools might be created but not immediately published.

**Options**:

- **Option A: Event created on any tool insertion**
  - Impact: `INSERT INTO activity_events` in tool creation controller
  - Trade-offs: Simple trigger, but might show tools user later deletes during setup
  
- **Option B: Event created when tool status becomes 'active' or 'published'**
  - Impact: Assumes tool has lifecycle states (draft → published)
  - Trade-offs: More accurate (only shows "real" listings), but requires coordination with Feature 1's tool lifecycle definition
  
- **Option C: Event created on tool creation only if immediately available (not borrowed)**
  - Impact: Check availability at creation time (will always be true for new tools)
  - Trade-offs: Redundant check for new tools (they can't be borrowed yet)

**Recommendation for MVP**: Option B (event on publish transition) **IF** Feature 1 defines draft states, otherwise Option A (event on creation). Need to check Feature 1 spec: does tool listing have a "Save as Draft" vs "Publish Now" flow? If yes, only published tools should generate events. If no (all tool creations are immediately live), Option A is correct. **Please confirm Feature 1's tool lifecycle states.**

---

### Q3: How should "My Network" view handle users who followed someone, then that person's only tool gets borrowed?

**Context**: Spec says "My Network" shows tools from followed users globally, ignoring radius and availability logic. But if someone follows Alice (who has 1 drill), then Bob borrows that drill, does Alice disappear from "My Network" view entirely?

This relates to the broader question: **Does "My Network" apply the same availability filter (no active borrows) as "Nearby Tools", or does it show all tools from followed users regardless of availability?**

**Options**:

- **Option A: Apply availability filter to "My Network"**
  - Impact: Borrowed tools disappear from network view
  - Trade-offs: Consistent with "Nearby Tools" logic, but might make network view feel empty during high borrow activity
  - User experience: "Why did Alice's tools vanish? I just followed her yesterday."
  
- **Option B: Show all tools in "My Network" regardless of availability**
  - Impact: Tool cards show availability status badge ("Available" / "Currently Borrowed")
  - Trade-offs: User can see full network inventory, but can't request borrowed tools
  - User experience: "Alice has 5 tools, 2 available, 3 borrowed - I'll check back later"
  
- **Option C: Show unavailable tools but with prominent "Borrowed until [date]" messaging**
  - Impact: Same as B but with estimated return date (requires Feature 2 borrow duration data)
  - Trade-offs: Most informative, but depends on Feature 2 having return date fields
  - User experience: "Drill borrowed until Jan 15 - I can request it next week"

**Recommendation for MVP**: Option B (show all tools, badge availability). Rationale: Following someone is a conscious relationship-building action. Users want to see their network's full inventory, not a filtered view that makes popular tools disappear. The badge ("Available" in green, "Borrowed" in gray) provides clarity without hiding data. This also aligns with the spec's statement that "My Network" is about relationships, not immediate availability.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q4: How should search results be paginated when user has 200+ tools within radius?

**Context**: Spec doesn't mention pagination for tool search results (list view or network view). With default 5-mile radius in a dense urban area, this could easily return 100-500 tools, especially as the platform grows.

**Options**:

- **Option A: No pagination initially, show all results**
  - Impact: Single query loads all matching tools
  - Trade-offs: Simple for MVP, but will become performance issue as community grows
  - User experience: Long scrolling on mobile, slow page load with 500 results
  
- **Option B: Server-side pagination with "Load More" button**
  - Impact: Load 20 tools initially, "Load More" button fetches next 20
  - Trade-offs: Good performance, but requires cursor/offset pagination implementation
  - User experience: Click "Load More" to see next page (standard pattern)
  
- **Option C: Infinite scroll pagination**
  - Impact: Auto-load next page when user scrolls near bottom
  - Trade-offs: Smooth UX, but more complex frontend logic (intersection observer)
  - User experience: Seamless scrolling, no button clicks
  
- **Option D: Fixed page size with "1, 2, 3... Next" pagination**
  - Impact: Traditional pagination controls at bottom
  - Trade-offs: Clear page boundaries, but requires knowing total count
  - User experience: Familiar pattern, but more clicks than infinite scroll

**Recommendation for MVP**: Option B (Load More button, 20 per page). Simpler than infinite scroll, performs well, and provides clear feedback ("Showing 20 of 47 tools" with "Load More" button). As platform grows, can migrate to infinite scroll if users request it. For "My Network" view, same pagination applies (20 per page) since followed users could have many tools.

---

### Q5: What should happen when user's geocoding accuracy is 'postal_code' and they search with 1-mile radius?

**Context**: Spec defines fallback to postal code centroid if address geocoding fails, with `location_accuracy` field storing 'precise' or 'postal_code'. A postal code covers ~1-5 square miles. If user's location is postal code centroid, a 1-mile radius search might miss nearby tools or include distant tools from same ZIP.

**Options**:

- **Option A: Allow 1-mile searches with postal code accuracy, accept imprecision**
  - Impact: User location is ZIP centroid, 1-mile circle drawn from there
  - Trade-offs: Simple, but might miss tools from opposite side of ZIP code area
  - User experience: Some results feel "off" ("2.3 miles away" but actually closer/farther)
  
- **Option B: Force minimum 5-mile radius if location_accuracy is 'postal_code'**
  - Impact: Disable 1-mile option for users with postal code accuracy
  - Trade-offs: Prevents misleading results, but restricts user control
  - User experience: "1 mile" button grayed out with tooltip "Upgrade location accuracy for smaller radius"
  
- **Option C: Show warning banner when postal code user selects 1-mile radius**
  - Impact: Allow 1-mile selection but display: "Your location is approximate (postal code). Distances may vary."
  - Trade-offs: Transparency without restriction, user makes informed choice
  - User experience: Sees banner, decides if acceptable

**Recommendation for MVP**: Option C (warning banner). Rationale: Most users will have precise geocoding (address input during signup). For the small percentage with postal code fallback, showing a warning respects their autonomy while setting expectations. Forcing 5-mile minimum feels heavy-handed for edge case. If user complains about inaccuracy, they can update their address in profile settings (which would trigger re-geocoding).

---

### Q6: Should Community Stats page refresh when user changes search radius, or stay static until page reload?

**Context**: Spec says stats are "scoped to user's current search radius" and "cached for 24 hours." But home page lets users change radius dynamically. Should stats page also update dynamically, or show cached stats for whatever radius was active when page loaded?

**Options**:

- **Option A: Stats page reflects home page's current radius setting**
  - Impact: User changes radius on home page → navigates to stats → sees stats for new radius
  - Trade-offs: Consistent with home page behavior, but requires session/state management
  - Implementation: Store selected radius in session storage, stats page reads it
  
- **Option B: Stats page has its own independent radius selector**
  - Impact: Stats page includes radius buttons (1, 5, 10, 25), independent of home page
  - Trade-offs: User can explore stats for different radii without affecting search, but might confuse users expecting consistency
  - Implementation: Stats page state is local, doesn't sync with home page
  
- **Option C: Stats page always shows default 5-mile radius, ignoring user's search preference**
  - Impact: Stats are "community-wide default view," not personalized
  - Trade-offs: Simplest implementation, but inconsistent with home page ("Why do stats show 5 miles when I'm searching 10?")
  - Implementation: Hardcode 5-mile filter in stats query

**Recommendation for MVP**: Option A (stats reflect current search radius). Rationale: The spec explicitly states "stats scoped to user's current search radius," implying synchronization. Users expect consistency - if they're exploring their 10-mile area on home page, they want stats for that same area. Implementation is straightforward (store radius in session storage, read in stats page). Changing radius on stats page should update both stats and (if they navigate back) the home page search.

---

### Q7: How should Activity Feed handle neighborhoods with identical names in different regions?

**Context**: Spec uses neighborhood names for activity events ("New tool listed in Maple Grove"), but many cities have duplicate neighborhood names (e.g., "Downtown" exists in hundreds of cities). When displaying "Successful borrow: Power Tool borrowed in Downtown," users might not realize it's their downtown vs. another city's.

This is especially relevant if someone searches with 25-mile radius (could span multiple cities) or if database eventually contains users from multiple metropolitan areas.

**Options**:

- **Option A: Store and display neighborhood name only (current spec)**
  - Impact: Events show "Maple Grove" without city context
  - Trade-offs: Clean display, but ambiguous in multi-city scenarios
  - User experience: Works well if platform is single-metro-area, breaks if it expands
  
- **Option B: Store neighborhood + city, display both**
  - Impact: Events show "Maple Grove, Minneapolis"
  - Trade-offs: Unambiguous, but more verbose (longer event text)
  - Database: Add `city` field to users table, populate from geocoding
  
- **Option C: Display neighborhood + state abbreviation for clarity**
  - Impact: Events show "Maple Grove, MN"
  - Trade-offs: Clear enough for US users, concise
  - Database: Add `state` field to users table
  
- **Option D: Use postal code as tiebreaker (already stored as fallback)**
  - Impact: Events show "Maple Grove (55311)"
  - Trade-offs: Unambiguous but less human-friendly (users don't think in ZIP codes)

**Recommendation for MVP**: Option A (neighborhood only) **if** v1 launch is single-metro-area, Option B (neighborhood + city) **if** v1 will have users from multiple cities. Need clarification: **Is v1 launch scoped to a single metropolitan area, or will it be open to users from any location?** If single-metro, defer city/state fields until expansion. If multi-city from day one, add city field during signup (populate from geocoding) and display in activity events.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q8: Should "Following" and "Followers" counts on user profiles link to lists, and if so, what information do those lists show?

**Context**: Spec says user profile displays "Following: 12" and "Followers: 8" with note "(count, clickable to see list)." But doesn't define what the list view shows or who can access it.

**Options**:

- **Option A: Lists show usernames only**
  - Impact: Modal or page showing "Following: Alice, Bob, Carol..."
  - Trade-offs: Simple, preserves privacy, but not very useful
  
- **Option B: Lists show username + neighborhood + tool count**
  - Impact: "Following: Alice (Maple Grove, 12 tools), Bob (West Side, 3 tools)..."
  - Trade-offs: More informative, helps user remember why they followed someone
  - User experience: "Oh right, Bob is the one with the welding equipment"
  
- **Option C: Lists are private (only visible to account owner)**
  - Impact: Can see your own following/follower lists, but can't see who others follow
  - Trade-offs: Preserves privacy (some users might not want followers public), but less social
  
- **Option D: Lists are public (anyone can see anyone's following/followers)**
  - Impact: Click "Following: 12" on Alice's profile → see all 12 users Alice follows
  - Trade-offs: More transparent/social, matches Twitter model, but might feel invasive

**Recommendation for MVP**: Option B (username + neighborhood + tool count) + Option C (private lists). Show rich information to help account owner manage their network, but keep lists private to avoid social awkwardness ("Why didn't Bob follow me back?"). If users later request public lists, can add privacy toggle in v2. List should also include "Unfollow" button next to each user for easy cleanup.

---

## Notes for Product

- **Iteration 1 answers were excellent** - very clear, consistent, and comprehensive. The updated spec reads smoothly and leaves few ambiguities.

- **Feature 1 dependency**: Q2 requires knowing if tool listing has draft states. Please reference Feature 1's tool lifecycle specification or confirm tools are immediately published on creation.

- **Multi-city scope**: Q7 depends on v1 launch scope (single metro vs. multi-city). Please clarify intended geographic coverage for initial release.

- **Pagination strategy**: Q4 affects database query design (need to decide on page size and cursor strategy before implementing search endpoints). Recommend deciding this before engineering spec phase.

- Once these 7 questions are answered, I'm confident we can proceed to detailed engineering specification. The v1.1 document is well-structured and implementation-ready in all other respects.