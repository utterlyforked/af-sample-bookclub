# Community & Location-Based Discovery - Product Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: location privacy model, availability semantics, follow system scope, activity feed behavior, statistics definitions)

---

## Feature Overview

Community & Location-Based Discovery enables users to explore their local tool-sharing ecosystem through geography-based search, visual mapping, and social connections. This feature transforms ToolShare from a simple tool catalog into a neighborhood discovery platform where users can see what's available nearby, build relationships with frequent tool partners, and understand the health of their local sharing community.

The feature serves three primary purposes:

1. **Geographic Discovery**: Help users find tools within practical pickup distance using radius search and map visualization
2. **Social Network**: Enable users to follow reliable neighbors and prioritize tools from their trusted network
3. **Community Health**: Provide transparency into sharing activity and engagement to validate the platform's value

This feature is critical for user retention - new users need to immediately see an active, well-stocked community to justify investing time in the platform. The map view provides an engaging, visual way to explore availability, while the follow system encourages repeat transactions with trusted neighbors.

---

## User Stories

- As a new user, I want to see what tools are available in my neighborhood so that I can join an active sharing community
- As a user, I want to follow neighbors whose tools I borrow frequently so that I can easily see their new listings
- As a user, I want to see a map view of available tools so that I can visualize what's nearby
- As a community organizer, I want to see aggregate statistics for my area so that I can understand tool-sharing activity
- As a borrower planning a project, I want to adjust my search radius to find specialized tools that might be slightly farther away
- As a user browsing casually, I want to see recent community activity to feel connected to the sharing ecosystem

---

## Acceptance Criteria

- Location set during signup via address input (geocoded to lat/long)
- Home page shows tools available within default 5-mile radius, sorted by distance
- Map view displays available tools as pins, clustered when zoomed out
- Users can adjust search radius: 1, 5, 10, or 25 miles
- "Neighborhood" designation based on postal code or neighborhood name (user-provided)
- Users can follow others, creating a "My Network" view of tools from followed users
- Community stats page shows: total tools shared, total borrows completed, most shared tool categories, active users
- Discovery feed shows recent activity: new tools listed, successful borrows completed (anonymized stats)

---

## Detailed Specifications (UPDATED v1.1)

### Location Privacy & Data Storage

**Decision**: Store only coordinates and neighborhood name in v1. Full addresses will be added in Feature 2 (Borrow Request & Communication) when pickup coordination requirements are defined.

**Rationale**: We should not store data we don't yet use. Feature 2's pickup coordination flow hasn't been specified, so we don't know:
- What address format is needed (full street address vs. intersection vs. general area)
- When addresses should be shared (after request approval? after deposit payment?)
- What privacy controls users expect (opt-out of lending? audit logs?)

Storing addresses prematurely creates security liability and might require schema changes when Feature 2 defines actual requirements. Better to add address storage when we know exactly how it will be used.

**Implementation**:
- Signup form requests street address for geocoding purposes only
- Address is geocoded to latitude/longitude via geocoding service (see tech decisions below)
- Coordinates stored in `users` table: `latitude` (decimal), `longitude` (decimal)
- User provides "neighborhood name" (free text, max 50 chars, e.g., "Maple Grove")
- If user leaves neighborhood blank, default to postal code (extracted from address before discarding)
- Address itself is **not persisted** in v1 database
- When Feature 2 is specified, we'll add address fields and may require users to re-enter address when they first want to lend (acceptable UX trade-off for cleaner v1 architecture)

**Public Display**:
- User profiles and tool listings show: `[Neighborhood Name]` + `~X.X miles away`
- Example: "Maple Grove · ~2.3 miles away"
- Distance calculated using haversine formula from viewer's coordinates to owner's coordinates

**Edge Cases**:
- If geocoding fails for submitted address → fall back to postal code centroid (see Q8 answer)
- If user enters invalid neighborhood name (empty, special chars) → use postal code
- Rural addresses without clear neighborhoods → postal code is appropriate fallback

---

### Tool Availability Semantics

**Decision**: "Available tools" means tools that are **not currently borrowed** (status check against active borrows).

**Rationale**: Users expect "available" to mean "I can request this now." Showing tools that are currently borrowed wastes their time clicking through to detail pages only to find the tool is unavailable until next month. The query complexity (joining to borrows table) is manageable with proper indexing.

**Implementation**:
```sql
-- Available tools query
SELECT t.* 
FROM tools t
LEFT JOIN borrows b ON b.tool_id = t.id 
  AND b.status IN ('pending', 'approved', 'borrowed')
WHERE b.id IS NULL  -- No active borrow exists
  AND [distance filter]
ORDER BY distance ASC
```

**Borrow Status Values** (assumes Feature 2 will define these):
- `pending`: Request submitted, awaiting owner approval
- `approved`: Owner approved, awaiting pickup
- `borrowed`: Tool picked up, in borrower's possession
- `returned`: Tool returned, awaiting confirmation
- `confirmed`: Transaction complete

**Behavior**:
- Tool appears in search results only when no borrow record exists OR all borrow records are in `returned`/`confirmed` status
- When borrower submits request (status → `pending`), tool immediately disappears from search for other users
- When tool is returned and confirmed (status → `confirmed`), tool immediately reappears in search
- If owner has 3 chainsaws listed, and 1 is borrowed, only 2 appear in search (tools are individual listings)

**Edge Cases**:
- Abandoned borrows (status stuck in `borrowed` for months) → tool stays hidden until owner manually marks returned or admin intervenes (out of scope for v1)
- Concurrent requests (two users request same tool simultaneously) → both see it as available; first to get owner approval wins; second user gets notified "no longer available" (Feature 2 handles this)

---

### Radius-Based Search Scope

**Decision**: Radius search filters based on **tool owner's home address** (where owner account is registered), not tool physical location.

**Rationale**: The PRD states "distance from user's coordinates to tool owner's coordinates." There's no concept of tools having separate storage locations in v1. This is simple and matches user mental model: "Show me tools from neighbors within X miles." If users later request "my chainsaw is at my workshop 10 miles away" feature, we can add tool-specific location fields in v2.

**Implementation**:
- Distance calculated using haversine formula: `haversine(user.latitude, user.longitude, owner.latitude, owner.longitude)`
- Radius options: 1 mile, 5 miles, 10 miles, 25 miles (preset buttons, no custom input)
- Default radius: 5 miles (reasonable driving distance for most suburban neighborhoods)
- Radius persists in browser session storage but resets to 5 miles on new login
- All queries filter: `WHERE distance <= selected_radius`

**Haversine Formula** (for reference):
```
a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlong/2)
c = 2 * atan2(√a, √(1−a))
distance = R * c  (where R = Earth's radius = 3,959 miles)
```

**Behavior**:
- User changes radius from 5 to 10 miles → page immediately refreshes, new tools appear
- Results always sorted by distance ascending (nearest first)
- Distance displayed rounded to 1 decimal place: "2.3 miles away"
- If zero tools found within radius → show message: "No tools found within X miles. Try expanding your search radius." with prompt to click 10-mile or 25-mile button

**Performance Consideration**:
- For MVP, calculate haversine in application code (C#)
- If performance becomes issue with large user base, migrate to PostGIS spatial queries
- Index on (latitude, longitude) columns for bounding box pre-filter before haversine calculation

---

### Follow System Behavior

**Decision**: Users can follow **anyone with an active account**, regardless of prior interaction. "My Network" view shows tools from followed users **ignoring radius** (global scope).

**Rationale**: 
1. **Open following**: The PRD describes following as "low-friction, non-awkward" and doesn't notify the followed user, suggesting a Twitter-like model. Restricting follows to only previous transaction partners would limit network effects and make discovery harder. Users should be able to follow someone because they have great tool inventory, not just because they've borrowed from them.

2. **Radius-independent network**: The PRD explicitly states "My Network" view is "sorted by date listed (newest first), not distance," implying distance is less relevant for network view. The follow system is about **relationships**, not geography. If I follow someone because they have rare woodworking tools, I want to see their tools even if they're 20 miles away (worth driving for specialized equipment). Applying radius to network view would create confusion when followed users' tools disappear/reappear as radius changes.

**Implementation**:

**Following**:
- "Follow" button appears on all user profiles (except user's own profile)
- No transaction history required
- Click "Follow" → immediate, no confirmation prompt
- Follow is one-directional (not mutual friendship)
- No notification sent to followed user
- User profile displays:
  - "Following: 12" (count, clickable to see list)
  - "Followers: 8" (count, clickable to see list)
- No limit on number of follows

**Unfollowing**:
- "Unfollow" button on followed user's profile or in Following list
- No confirmation prompt (PRD explicitly states "no confirmation prompt needed")
- Unfollow always allowed, even if active borrow exists
- Rationale: Follow/unfollow is a discovery preference, not a contractual obligation. Keeping it lightweight prevents awkwardness. Active borrows are transactions; follows are bookmarks.
- Unfollow → immediate, shows toast: "Unfollowed [Username]"

**My Network View**:
- Tab on home page: "Nearby Tools" (default) | "My Network"
- "My Network" shows tools where `tool.owner_id IN (SELECT followed_user_id FROM user_follows WHERE follower_user_id = current_user.id)`
- Query does NOT filter by radius (shows all tools from followed users globally)
- Sorted by `tool.created_at DESC` (newest listings first)
- Each tool card shows which followed user owns it: "[Tool Name] · Listed by [Username] · 12.4 miles away"
- Distance still calculated and displayed (for information), but not used for filtering or sorting
- If user follows zero people → "My Network" tab shows empty state: "Follow neighbors to see their tools here. Browse Nearby Tools to discover who to follow!"

**Edge Cases**:
- User follows someone 100 miles away → their tools appear in My Network (expected behavior)
- User follows someone, that person deletes account → follow relationship auto-deleted (CASCADE)
- User follows 50 people, none have tools listed → empty state with count: "You're following 50 people, but none have listed tools yet"

---

### Community Statistics Definitions

**Decision**: "Active Users" counts distinct users within radius who have **current tool listings OR participated in a borrow** (as borrower or lender) in the last 90 days.

**Rationale**: This definition matches the PRD language ("listed tools OR completed a borrow") and provides a balanced view of community health showing both supply side (people offering tools) and demand side (people borrowing). It's more forgiving than "completed transaction only," which is good for encouraging participation in new communities.

**Implementation**:

**Active Users Query**:
```sql
SELECT COUNT(DISTINCT u.id)
FROM users u
WHERE ST_Distance(u.location, center_location) <= radius
  AND (
    -- Has current tool listings
    EXISTS (
      SELECT 1 FROM tools t 
      WHERE t.user_id = u.id 
        AND t.deleted_at IS NULL
    )
    OR
    -- Participated in borrow (either role) in last 90 days
    EXISTS (
      SELECT 1 FROM borrows b
      WHERE (b.borrower_id = u.id OR b.lender_id = u.id)
        AND b.updated_at > NOW() - INTERVAL '90 days'
    )
  )
```

**All Statistics** (scoped to user's current search radius):

1. **Total Tools Shared**: Count of all tool listings within radius (regardless of availability)
   - Query: `COUNT(*) FROM tools WHERE owner within radius AND deleted_at IS NULL`

2. **Total Borrows Completed**: Count of borrow transactions with status `returned` or `confirmed`
   - Query: `COUNT(*) FROM borrows WHERE (borrower OR lender) within radius AND status IN ('returned', 'confirmed')`
   - Rationale: "Completed" means transaction finished successfully, not just requested or approved

3. **Active Users**: As defined above (listings OR borrows in 90 days)

4. **Most Shared Categories**: Top 5 tool categories by count
   - Query: `SELECT category, COUNT(*) FROM tools WHERE owner within radius GROUP BY category ORDER BY COUNT(*) DESC LIMIT 5`
   - Handles ties: If categories 5 and 6 have same count, alphabetically sort tied categories
   - Handles sparse data: If only 3 categories exist, show 3 bars with message "Only 3 categories in your area - growing community!"

5. **Top Contributors** (anonymized): 5 users with most tools listed
   - Display: "User in [Neighborhood] - 23 tools" (no usernames)
   - Query: `SELECT neighborhood, COUNT(*) FROM users JOIN tools GROUP BY user_id ORDER BY COUNT DESC LIMIT 5`

**Behavior**:
- Stats page linked in main navigation: "Community Stats"
- Stats scoped to user's current search radius (same as tool search)
- User changes radius → stats update to reflect new area
- Stats cached for 24 hours (updated daily via background job)
- "Last updated: January 10, 2025" timestamp displayed
- No real-time updates (avoids database load)
- Stats page includes explanation: "Statistics reflect activity within [X] miles of your location"

**Presentation**:
- Numbers displayed with formatting: "1,247 tools" (not "1247")
- Bar chart for categories using simple HTML/CSS bars (no charting library needed for MVP)
- Mobile-responsive grid layout

**V1 Scope**:
- Current snapshot only (no historical trends or "up 12% this month")
- Rationale: Trends are nice-to-have but not essential for validating community activity. If stats show "47 tools, 23 borrows, 15 active users," that's sufficient social proof for new users. Add trends in v2 if users request.

---

### Activity Feed Behavior

**Decision**: Activity feed shows events within user's **current search radius** (dynamically updates when radius changes). "Successful borrow" events appear when borrow status reaches `returned` or `confirmed`.

**Rationale**: 
1. **Radius-linked feed**: Keeps entire page consistent - "Show me everything within X miles: tools, activity, stats." The dynamic update reinforces the radius concept. Alternative (fixed 10-mile feed regardless of search radius) would create disconnect between tools shown and activity shown.

2. **Successful = completed**: "Successful borrow" implies a finished transaction. Showing approved or picked-up borrows as "successful" would be misleading if they're never returned. Yes, events appear with delay (after return), but this accurately represents sharing economy health.

**Implementation**:

**Event Types**:

1. **New Tool Listed**
   - Trigger: When tool status changes to active/published
   - Display: "New tool listed: [Tool Name] in [Neighborhood]"
   - Example: "New tool listed: DeWalt Cordless Drill in Maple Grove"
   - Clicking event → navigates to tool detail page

2. **Successful Borrow**
   - Trigger: When borrow status transitions to `returned` OR `confirmed`
   - Display: "Successful borrow: [Tool Category] borrowed in [Neighborhood]"
   - Example: "Successful borrow: Power Tool borrowed in West Side"
   - Rationale for category (not tool name): Privacy - don't reveal specific tool borrowed
   - Clicking event → no action (not linked)

**Event Creation**:
```sql
-- Insert event when tool listed
INSERT INTO activity_events (event_type, tool_id, tool_category, neighborhood, created_at)
VALUES ('new_tool', tool.id, tool.category, owner.neighborhood, NOW())

-- Insert event when borrow completed
INSERT INTO activity_events (event_type, tool_category, neighborhood, created_at)
VALUES ('successful_borrow', borrow.tool.category, borrower.neighborhood, NOW())
-- Note: No tool_id or user_id stored for privacy
```

**Feed Behavior**:
- "Recent Activity" section on home page (below tool search results)
- Shows last 20 events within user's current search radius
- Query: `SELECT * FROM activity_events WHERE neighborhood.location within radius ORDER BY created_at DESC LIMIT 20`
- Events display relative time: "2 hours ago", "3 days ago", "1 week ago" (using time-ago library)
- Feed refreshes when user changes search radius (immediate update)
- Feed auto-refreshes every 5 minutes while page active (polling, not WebSockets)
- If fewer than 20 events exist → show all available with message "Showing all recent activity in your area"
- If zero events → show message "No recent activity yet. Be the first to list a tool!"

**Event Lifecycle**:
- Events are permanent (no deletion by users)
- If tool is deleted → cascade delete its "new tool" event (foreign key: `ON DELETE CASCADE`)
  - Rationale: Prevents dead links (clicking event to see deleted tool)
- Borrow events persist even if users delete accounts (already anonymized)
- Event cleanup: Automatically delete events older than 90 days (background job)
  - Rationale: Feed only shows last 20; old events consume storage unnecessarily

**Privacy**:
- No usernames shown (ever)
- Borrow events show category only (not specific tool name)
- Neighborhood shown (not full address)
- No way to identify which user performed action

---

### Map Visualization

**Decision**: Map pins show tools with availability **cached for 5 minutes**. Use **default Leaflet.markercluster settings** for pin clustering.

**Rationale**: 
1. **Caching**: Maps are for discovery and getting a sense of what's around. Exact real-time availability matters when requesting, not when browsing. A 5-minute cache is fresh enough (most borrows span days/weeks, not minutes) and prevents crushing the database when many users load the map simultaneously.

2. **Default clustering**: Leaflet.markercluster is battle-tested and works well out of the box. Don't optimize prematurely. Ship fast, tune later if users complain.

**Implementation**:

**Map Display**:
- Toggle button on home page: "List View" | "Map View"
- Map centers on user's location (from coordinates)
- Current search radius shown as circle overlay (semi-transparent border)
- Map uses Leaflet.js with OpenStreetMap tiles (free, no API key)
- Map height: 600px on desktop, 400px on mobile

**Pin Display**:
- Each available tool shown as pin at owner's **randomized location**
  - Randomization: Add ±0.1 mile random offset to owner's coordinates (jitter)
  - Purpose: Prevent exact address identification from multiple tool listings
  - Randomization happens once at tool creation (stored in `tool.display_latitude`, `tool.display_longitude`)
  - Consistent location for same tool across page loads (not re-randomized every view)

**Pin Color Coding** (by category):
- Power Tools: Red (#EF4444)
- Hand Tools: Blue (#3B82F6)
- Gardening: Green (#10B981)
- Ladders & Scaffolding: Orange (#F97316)
- Outdoor Equipment: Purple (#8B5CF6)
- Other: Gray (#6B7280)

**Clustering**:
- Library: Leaflet.markercluster
- Config: Default settings (`maxClusterRadius: 80px`, clustering up to zoom level 18)
- Cluster icon shows count: "5 tools"
- Clicking cluster → zooms in to expand
- No category breakdown in clusters for v1 (e.g., "5 tools: 3 Power, 2 Garden")
  - Rationale: Requires custom rendering; default numeric clusters are sufficient for MVP

**Pin Popups**:
- Clicking individual pin shows popup:
  - Tool photo (thumbnail, 100x100px)
  - Tool title (truncated to 50 chars if needed)
  - Category icon + name
  - Distance: "2.3 miles away"
  - "View Details" button → navigates to tool detail page

**Behavior**:
- Map respects current radius setting
- Changing radius updates visible pins immediately
- Map shows only "available" tools (same availability logic as list view)
- Map data cached in Redis for 5 minutes:
  - Cache key: `map_tools_{user_id}_{radius}_{timestamp_floor_5min}`
  - If cache miss → query database, populate cache
  - Cache expires after 5 minutes (TTL)

**Edge Cases**:
- User has zero tools in radius → map shows only center marker (user's location) with message overlay "No tools nearby. Try expanding your radius."
- Map fails to load (network issue, tile server down) → show fallback message "Map unavailable. Switch to List View." with button to toggle
- User's coordinates invalid (null/corrupt) → center map on default location (e.g., city center) with warning banner

---

### Neighborhood Name Editing

**Decision**: Neighborhood name is **editable** from user profile settings (simple text input).

**Rationale**: If someone typos "Maple Groev" during signup, they should be able to fix it. The PRD frames neighborhood as user-provided and casual (not a critical data field like address). Don't over-engineer. Historical activity feed events won't be updated (they retain original neighborhood at time of event), but this is acceptable - most users won't notice, and consistency of historical data is not critical for this feature.

**Implementation**:
- User profile settings page includes "Neighborhood" text input
- Max length: 50 characters
- Validation: Allow letters, numbers, spaces, hyphens, apostrophes (e.g., "O'Brien's Corner")
- Empty input → default back to postal code
- Update propagates immediately to profile, tool listings, future activity events
- No change to historical activity_events records (neighborhood value at time of event is preserved)

---

## Q&A History

### Iteration 1 - 2025-01-10

**Q1: How should we handle address privacy when full addresses are stored for Feature 2 pickup coordination?**  
**A**: Don't store addresses in v1. Store only coordinates and neighborhood name. When Feature 2 defines pickup coordination requirements, we'll add address fields then and may require users to re-enter addresses when they first want to lend. This avoids building for undefined requirements and prevents security liability.

**Q2: What should "available tools" mean for search and map results?**  
**A**: Available = not currently borrowed. Query filters out tools with active borrows (status in pending/approved/borrowed). Tools become available again when returned/confirmed.

**Q3: Should radius search include only tools listed by users within the radius, or tools physically located within the radius?**  
**A**: Radius based on owner's home address (where owner account is registered). No concept of separate tool storage locations in v1.

**Q4: How should the follow system interact with the radius search?**  
**A**: "My Network" view ignores radius completely. Shows tools from ALL followed users globally, sorted by date listed. Follow is about relationships, not geography.

**Q5: What should "Active Users" mean in Community Statistics?**  
**A**: Count of distinct users within radius who have current tool listings OR participated in a borrow (either role) in the last 90 days. Balances supply and demand sides.

**Q6: Should the Activity Feed show events from the user's current radius, or from a fixed area?**  
**A**: Feed respects current radius setting. Dynamically updates when user changes radius. Keeps entire page consistent (tools, activity, stats all within X miles).

**Q7: For "Successful borrow" events in Activity Feed, what counts as "successful"?**  
**A**: Successful = borrow status reaches `returned` or `confirmed`. Only show events for completed transactions, not approved or picked-up. Events appear with delay but accurately represent sharing economy health.

**Q8: How should we handle geocoding failures during signup?**  
**A**: Fall back to postal code centroid if full address geocoding fails. Store `location_accuracy` field ('precise' or 'postal_code'). This prevents signup blocking while maintaining reasonable location accuracy.

**Q9: Should users be able to follow someone they've never interacted with?**  
**A**: Yes, can follow anyone with an active account. No transaction history required. Follow is low-friction like Twitter, not mutual friendship.

**Q10: How should "Most Shared Categories" in Community Stats handle ties?**  
**A**: Show up to 5 categories. If fewer than 5 exist, show actual count with message "Only X categories in your area - growing community!" Sort ties alphabetically. Don't invent fake data.

**Q11: Should map pins show real-time availability or cached data?**  
**A**: Cached for 5 minutes (Redis). Maps are for discovery, not real-time monitoring. Fresh enough for browsing, prevents database load.

**Q12: What should happen when a user unfollows someone?**  
**A**: Unfollow always allowed, no confirmation prompt, no impact on active borrows. Follow/unfollow is discovery preference, not contractual obligation. Keep lightweight.

**Q13: Should the neighborhood name be editable after signup?**  
**A**: Yes, editable from profile settings. Simple text input, max 50 chars. Fixes typos and allows privacy adjustments. Historical activity events retain original neighborhood (no retroactive updates).

**Q14: How should clustering work on the map when zoomed out?**  
**A**: Use Leaflet.markercluster default settings. Don't customize prematurely. Ship fast, tune if users complain about clustering behavior.

**Q15: Should Activity Feed events be deletable or hideable?**  
**A**: Cascade delete events when source tool is deleted (prevents dead links). Borrow events persist even if users delete accounts (already anonymized). Auto-delete events older than 90 days (background cleanup).

**Q16: Should Community Stats page show historical trends or just current snapshot?**  
**A**: Current snapshot only. No "up 12% this month" or trend graphs in v1. Sufficient to show current numbers for social proof. Add trends in v2 if users request.

---

## Product Rationale

### Why coordinates-only storage in v1?

Feature 2 (pickup coordination) hasn't been specified yet. We don't know:
- What address granularity is needed (street address vs. intersection)
- When addresses are shared (after approval? after deposit?)
- What privacy controls users expect

Building address storage now creates:
- Security liability (storing sensitive data we don't use)
- Risk of schema changes when Feature 2 defines different requirements
- Potential GDPR/privacy compliance issues

Better to wait until Feature 2 clarifies actual needs, then add address fields and collection flow. Requiring users to re-enter address when they first want to lend is acceptable UX trade-off.

### Why is "My Network" global (ignoring radius)?

The follow system is fundamentally about **relationships**, not geography. Users follow someone for three reasons:
1. Repeated successful borrows (trust)
2. Rare/specialized tool inventory (worth driving for)
3. Active community member (frequent new listings)

All three use cases break if radius filtering is applied:
- User follows trusted neighbor who moves 10 miles away → tools disappear (frustrating)
- User follows someone 20 miles away with rare woodworking tools → wants to see those tools always, not only when radius set to 25 miles
- User follows active lister → wants to see new listings immediately, not conditionally

The PRD explicitly says "My Network" is "sorted by date, not distance," signaling distance is secondary. Distance is still displayed for information, but not used for filtering.

### Why cache map data for 5 minutes?

Alternative would be real-time queries every map view. Problems:
- Database load: Map might render 100+ pins; querying availability for each = 100+ joins to borrows table
- Concurrent users: If 50 users load map simultaneously, that's 5,000 queries in seconds
- Minimal benefit: Tools are typically borrowed for days/weeks, not minutes. A tool becoming available 5 minutes ago vs. real-time is not meaningful.

Cache trade-off:
- ✅ Dramatically reduces database load
- ✅ Faster page load for users
- ✅ Enables map to scale to more users
- ❌ User might click pin and find tool just became unavailable (acceptable - they'd discover this on detail page anyway)

Cache invalidation not worth complexity in v1. 5-minute TTL is good balance.

### Why allow following anyone (not just transaction partners)?

Restricting follows to transaction partners would:
- Limit network growth (slow cold start for new users)
- Prevent discovery (can't follow someone with great inventory until you borrow from them first)
- Create chicken-egg problem (need to borrow to follow, but want to follow to see what's available)

Open following enables:
- User browses map, sees user with 20 power tools, clicks profile, follows them to monitor inventory
- User joins platform, searches for neighbors, follows 5-10 active lenders before first borrow
- Faster community building (users can follow proactively, not reactively)

PRD describes following as "low-friction, non-awkward" with no notifications, suggesting lightweight Twitter model, not intimate Facebook friendship.

### Why show only completed borrows (returned/confirmed) in activity feed?

"Successful borrow" is user-facing language implying completion. Alternatives:
- Show approved borrows → misleading if transaction never completes (user cancels, ghosted, etc.)
- Show picked-up borrows → better, but still not truly "successful" until returned

Completed transactions (returned/confirmed) are the only proof of actual sharing economy activity. This is what matters for:
- New users evaluating if community is active (completed transactions = validation)
- Community health metrics (successful exchanges, not just intent)
- Social proof (tangible results, not pending requests)

Trade-off: Events appear with delay (days/weeks after pickup). Acceptable because feed's purpose is showing **sustained activity**, not real-time updates.

---

## Technical Decisions (For Implementation)

These decisions are made by Tech Lead based on functional requirements above. Documented here for reference.

**Geocoding Service**: Use Nominatim (OpenStreetMap) for v1
- Rationale: Free, no API key, sufficient accuracy for neighborhood-level matching
- Fallback: If Nominatim fails, use postal code centroid lookup (offline database)

**Geospatial Queries**: Calculate haversine distance in application code (C#)
- Rationale: Simpler than PostGIS for MVP; avoids PostgreSQL extension dependency
- Optimization: Pre-filter with bounding box (lat ± radius, long ± radius) before haversine calculation
- Future: Migrate to PostGIS if query performance becomes bottleneck (>10,000 users)

**Map Pin Randomization**: Randomize once at tool creation, store in database
- Fields: `tool.display_latitude`, `tool.display_longitude` (separate from owner's actual coordinates)
- Rationale: Consistent pin location across page loads; avoids recomputing jitter every map view
- Algorithm: `display_lat = owner_lat + random(-0.1, 0.1) miles`

**Activity Event Storage**: Keep last 90 days only
- Background job runs daily: `DELETE FROM activity_events WHERE created_at < NOW() - INTERVAL '90 days'`
- Rationale: Feed shows last 20; old events aren't displayed and consume storage
- Index: `(created_at DESC, neighborhood)` for fast feed queries

**Community Stats Calculation**: Background job (Hangfire) runs daily at 2 AM
- Calculates stats for common radius values (1, 5, 10, 25 miles) across all neighborhoods
- Stores in `community