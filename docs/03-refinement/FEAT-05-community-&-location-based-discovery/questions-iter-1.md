# Community & Location-Based Discovery - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: 2025-01-10

---

## Summary

After reviewing the specification, I've identified **16 areas** that need clarification before implementation can begin. These questions address:
- Location privacy and data security
- Search and filtering behavior
- Follow system mechanics
- Map visualization boundaries
- Activity feed data sources
- Community statistics calculation scope
- Performance and data retention

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: How should we handle address privacy when full addresses are stored for Feature 2 pickup coordination?

**Context**: The PRD states "full address revealed only to borrowers after owner approves request (handled in Feature 2)." However, Feature 2 hasn't been defined yet. This creates a dependency that blocks implementation because we need to know:
- Who can see full addresses and under what conditions?
- Do we need audit logging for address access?
- Can users opt-out of sharing full addresses (and thus not be able to lend)?
- What happens if Feature 2 introduces different privacy rules?

**Options**:

- **Option A: Store full address now, defer access control to Feature 2**
  - Impact: Build location features with coordinates only; address column exists but no UI exposes it yet
  - Trade-offs: Clean separation but creates unused data; might need schema changes when Feature 2 defines access rules
  - Database: `users` table has `address_line1`, `address_line2`, `city`, `state`, `postal_code` fields (never exposed via API in this feature)

- **Option B: Only store coordinates now, add address storage in Feature 2**
  - Impact: This feature uses lat/long only; Feature 2 adds address fields when pickup coordination is defined
  - Trade-offs: Cleaner (don't store what we don't use), but might require users to re-enter address later
  - Database: `users` table has only `latitude`, `longitude`, `neighborhood` in v1

- **Option C: Store address but require explicit consent flag**
  - Impact: Add `address_sharing_consent` boolean; only users who consent can lend (borrowing OK without consent)
  - Trade-offs: Complex onboarding, might reduce lender participation, but legally safer
  - Database: Adds consent tracking, audit log for address access

**Recommendation for MVP**: **Option B** (coordinates only now). Don't build features for undefined requirements. When Feature 2 is spec'd, we'll know exactly what address data we need and can add it then. This avoids premature optimization and potential privacy issues. Users would re-enter address when they first want to lend (acceptable UX trade-off).

---

### Q2: What should "available tools" mean for search and map results?

**Context**: The PRD says "Home page shows tools available within default 5-mile radius" and "Map view displays available tools as pins." But "available" isn't defined. Does it mean:
- Tools with status = "available" (not currently borrowed)?
- Tools that exist in the system regardless of current borrow status?
- Tools where owner is active (logged in recently)?
- Tools that meet some other criteria?

This affects query performance and user expectations.

**Options**:

- **Option A: Available = not currently borrowed**
  - Impact: Query joins to Borrows table, filters where no active borrow exists OR borrow status = "returned"
  - Trade-offs: Most intuitive for users (shows what they can request now), but more complex query
  - Database: `WHERE NOT EXISTS (SELECT 1 FROM borrows WHERE tool_id = tools.id AND status IN ('pending', 'approved', 'borrowed'))`

- **Option B: Available = all tools, regardless of borrow status**
  - Impact: Simple query, just distance filter
  - Trade-offs: User might click a tool and find it's currently borrowed (frustrating UX)
  - Database: `SELECT * FROM tools WHERE...` (no borrow check)

- **Option C: Available = not borrowed AND owner is active (logged in within 90 days)**
  - Impact: Query joins users table, checks last_login_at timestamp
  - Trade-offs: Prevents showing tools from abandoned accounts, but adds complexity
  - Database: `JOIN users ON tools.user_id = users.id WHERE users.last_login_at > NOW() - INTERVAL '90 days'`

**Recommendation for MVP**: **Option A** (not currently borrowed). Users expect "available" to mean "I can request this now." Showing borrowed tools wastes their time. The query complexity is manageable with proper indexing.

---

### Q3: Should radius search include only tools listed by users within the radius, or tools physically located within the radius?

**Context**: The PRD calculates distance "from user's coordinates to tool owner's coordinates." But what if an owner within my radius has temporarily moved a tool elsewhere (future feature), or what if we want to show tools FROM nearby users even if the tool is stored at a different location (workshop, storage unit)?

This seems theoretical but actually matters: is radius about **where the owner lives** or **where the tool is physically located**?

**Options**:

- **Option A: Radius based on owner's home address (as PRD states)**
  - Impact: Distance = user location to tool owner's location
  - Trade-offs: Simple, matches PRD language, assumes tool is at owner's home
  - Database: Single distance calculation using user coordinates

- **Option B: Radius based on tool's physical location (if different from owner's address)**
  - Impact: Need `tool_location_latitude` and `tool_location_longitude` fields on tools table
  - Trade-offs: More flexible for future features (storage units, workshops), but complex for v1
  - Database: Adds location fields to tools; defaults to owner's location if null

**Recommendation for MVP**: **Option A** (owner's address). The PRD clearly states "tool owner's coordinates" and there's no mention of tools having separate locations. Keep it simple. If users request "my chainsaw is at my workshop 10 miles away" feature later, we can add it in v2.

---

### Q4: How should the follow system interact with the radius search?

**Context**: The PRD says "'My Network' view shows tools from followed users only" and "sorted by date listed (newest first), not distance." But what if I follow a user who's 100 miles away? Do their tools appear in "My Network" even though they're outside my search radius?

**Options**:

- **Option A: "My Network" ignores radius completely**
  - Impact: Shows tools from ALL followed users regardless of distance
  - Trade-offs: User might follow someone across the country and see tools they can't realistically borrow
  - Query: `SELECT * FROM tools WHERE user_id IN (followed_users) ORDER BY created_at DESC`

- **Option B: "My Network" respects current radius setting**
  - Impact: Only shows tools from followed users within current radius
  - Trade-offs: More logical (shows borrowable tools), but user might wonder why followed user's tools disappeared when they changed radius
  - Query: `SELECT * FROM tools WHERE user_id IN (followed_users) AND distance < radius ORDER BY created_at DESC`

- **Option C: "My Network" has its own separate radius setting (default 25 miles)**
  - Impact: Two different radius controls - one for general search, one for network
  - Trade-offs: Flexible but complex UI; most users won't understand the difference

**Recommendation for MVP**: **Option A** (ignore radius). The follow system is about relationships, not geography. If I follow someone, I want to see their tools even if they're far away (maybe I follow them because they have rare tools worth driving for). The PRD already says "sorted by date, not distance," which implies distance is less important for network view.

---

### Q5: What should "Active Users" mean in Community Statistics?

**Context**: The PRD defines "Active Users" as "Count of users within radius who have listed tools OR completed a borrow in last 90 days." But this creates questions:
- Does "listed tools" mean currently has active listings, or has ever listed anything in last 90 days?
- Does "completed a borrow" mean as borrower, lender, or both?
- What if user's account is deleted but their historical borrows exist?

**Options**:

- **Option A: Active = has current tool listings OR participated in borrow (either role) in last 90 days**
  - Impact: `COUNT(DISTINCT users.id) WHERE (tools.user_id IS NOT NULL) OR (borrows created_at > 90 days ago AND user_id IN (borrower OR lender))`
  - Trade-offs: Broad definition, shows ecosystem health including both supply and demand
  
- **Option B: Active = logged in within last 90 days (simplest)**
  - Impact: `COUNT(users) WHERE last_login_at > NOW() - INTERVAL '90 days'`
  - Trade-offs: Simple query, but doesn't reflect actual platform engagement (could log in and do nothing)

- **Option C: Active = completed transaction (borrow returned/confirmed) in last 90 days**
  - Impact: `COUNT(DISTINCT users) FROM borrows WHERE status IN ('returned', 'confirmed') AND completed_at > 90 days ago`
  - Trade-offs: Strictest definition, shows real sharing activity, but might show low numbers in new communities

**Recommendation for MVP**: **Option A** (has listings OR participated in borrows). This matches the PRD language most closely and shows a healthy picture of the community (both supply side and demand side). It's more forgiving than Option C, which is good for encouraging new communities.

---

### Q6: Should the Activity Feed show events from the user's current radius, or from a fixed area?

**Context**: The PRD says "Shows last 20 events within user's search radius" and "Feed auto-refreshes when user changes search radius." This means:
- User sets radius to 1 mile → sees very few events
- User sets radius to 25 miles → sees many events
- Events disappear/appear as user adjusts slider

Is this the intended behavior, or should the feed show a consistent area (like "your neighborhood" = 10 miles always)?

**Options**:

- **Option A: Feed respects current radius setting (as PRD states)**
  - Impact: Feed dynamically updates when radius changes
  - Trade-offs: Might be confusing (events appear/disappear), but consistent with rest of page
  - Query: `WHERE event_location WITHIN current_radius`

- **Option B: Feed always shows fixed 10-mile radius regardless of search setting**
  - Impact: Feed stays consistent even when user changes tool search radius
  - Trade-offs: More stable UX, but disconnect between "tools within 5 miles" and "activity within 10 miles"
  - Query: `WHERE event_location WITHIN 10 miles`

- **Option C: Feed shows user's neighborhood (postal code) only**
  - Impact: Hyper-local feed, same neighborhood as user
  - Trade-offs: Very targeted, but might show too few events in sparse areas
  - Query: `WHERE event_neighborhood = user.neighborhood`

**Recommendation for MVP**: **Option A** (respects radius). The PRD is explicit about this behavior. It creates a consistent mental model: "Show me everything within X miles - tools AND activity." The dynamic update might surprise users at first, but it's logical and keeps the entire page synchronized.

---

### Q7: For "Successful borrow" events in Activity Feed, what counts as "successful"?

**Context**: The PRD shows event type "Successful borrow: [Tool Category] borrowed in [Neighborhood]." But Feature 2 (borrow workflow) isn't defined yet. We need to know:
- Is "successful" when request is approved?
- When item is picked up?
- When item is returned?
- When both parties confirm transaction is complete?

**Options**:

- **Option A: Successful = borrow status changes to "returned" or "confirmed"**
  - Impact: Only show event when transaction fully completes
  - Trade-offs: Most accurate ("successful" = finished), but events appear with delay (after return)
  - Timing: Event created when borrow.status transitions to 'returned' or 'confirmed'

- **Option B: Successful = borrow request approved by owner**
  - Impact: Event appears as soon as owner approves
  - Trade-offs: More immediate (active-feeling feed), but "successful" is misleading if borrow never completes
  - Timing: Event created when borrow.status transitions to 'approved'

- **Option C: Successful = borrower picks up item (status = "borrowed")**
  - Impact: Event when item leaves owner's possession
  - Trade-offs: Middle ground - proves transaction started, but doesn't wait for return
  - Timing: Event created when borrow.status transitions to 'borrowed'

**Recommendation for MVP**: **Option A** (returned/confirmed). "Successful borrow" implies a completed transaction. Showing approved or picked-up borrows as "successful" is dishonest if they're not finished. Yes, this means events appear later, but it accurately represents the sharing economy's health.

**Dependency Note**: This requires Feature 2 to define borrow status values. Assume: pending → approved → borrowed → returned → confirmed.

---

### Q8: How should we handle geocoding failures during signup?

**Context**: The PRD says "Geocoding fails: Show error message, require user to re-enter or correct address format." But this needs more detail:
- Can user bypass geocoding and sign up anyway?
- How many retry attempts before we suggest manual coordinate entry?
- What if geocoding service is down temporarily?
- Should we fall back to postal code centroid coordinates?

**Options**:

- **Option A: Geocoding is required; user cannot proceed until address resolves**
  - Impact: Signup form blocks on geocoding success
  - Trade-offs: Ensures data quality, but user might abandon signup if their address doesn't geocode (rural addresses, new subdivisions)
  - UX: "We couldn't find that address. Please check the spelling or try a nearby landmark."

- **Option B: Allow user to proceed with postal code centroid if geocoding fails**
  - Impact: Geocode to center of ZIP code as fallback
  - Trade-offs: Less accurate (might be off by 2-3 miles in large ZIP codes), but doesn't block signup
  - Database: Store `location_accuracy` field ('precise', 'postal_code', 'manual')

- **Option C: Allow user to manually place pin on map if geocoding fails**
  - Impact: Show map interface, user clicks their location
  - Trade-offs: Empowering, handles all edge cases, but complex onboarding UI
  - Database: Store how location was determined

**Recommendation for MVP**: **Option B** (postal code fallback). Rural addresses and new construction often fail geocoding. Falling back to ZIP code center means user can still use the platform (search within 5 miles still makes sense). Mark the location as less accurate and potentially prompt user to update later. This balances data quality with signup conversion.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q9: Should users be able to follow someone they've never interacted with?

**Context**: The PRD says follow is available from user profiles, but doesn't specify if there's any relationship requirement. Can I follow any user I discover, or only users I've borrowed from / lent to?

**Options**:

- **Option A: Can follow anyone with an active account**
  - Impact: Follow button appears on all user profiles
  - Trade-offs: Maximum flexibility, users can follow based on inventory, but might feel creepy
  - Privacy: Some users might be uncomfortable with being followed by strangers

- **Option B: Can only follow users after completing a transaction with them**
  - Impact: Follow button only appears on profiles of users with whom you have a returned/confirmed borrow (either direction)
  - Trade-offs: More intentional follows (based on trust), but limits network growth
  - Database: Query borrows table before showing follow button

- **Option C: Can follow anyone, but followed user can see who's following and block**
  - Impact: Follow freely, but add block/remove-follower functionality
  - Trade-offs: Most flexible, but requires blocking feature (scope creep)

**Recommendation for MVP**: **Option A** (follow anyone). The PRD says follow is "low-friction, non-awkward" and doesn't notify the followed user. This suggests a lightweight model like Twitter. If users complain about privacy, we can add blocking in v2. Over-restricting follows will limit network effects.

---

### Q10: How should "Most Shared Categories" in Community Stats handle ties?

**Context**: The PRD shows "Most Shared Categories: Bar chart showing tool count by category (top 5)." What if there are fewer than 5 categories with tools? What if categories 5 and 6 have the same count?

**Options**:

- **Option A: Show up to 5 categories, alphabetically sort ties, show message if < 5 exist**
  - Impact: If only 3 categories have tools, show 3 bars with message "Only 3 categories in your area"
  - Trade-offs: Simple, transparent, handles edge cases gracefully

- **Option B: Always show exactly 5 categories, pad with "Other" or empty bars**
  - Impact: If only 3 categories exist, show 3 real + 2 empty/grayed bars
  - Trade-offs: Consistent layout, but misleading (implies categories exist when they don't)

- **Option C: Show all categories if <= 5, or top 5 + "Other" if more than 5**
  - Impact: Dynamic: 3 categories = 3 bars, 8 categories = 5 bars + "Other" with count of remaining
  - Trade-offs: Flexible, but "Other" might have more tools than shown categories (confusing)

**Recommendation for MVP**: **Option A** (show up to 5, handle gracefully if fewer). Don't invent fake data. If a new community only has Power Tools and Gardening, show those two proudly. Add message: "Growing community - more categories coming soon!"

---

### Q11: Should map pins show real-time availability or cached data?

**Context**: The PRD says map shows "available tools" and mentions pins are color-coded by category. But as users borrow/return tools, availability changes. Should map reflect this immediately?

**Options**:

- **Option A: Map pins reflect current availability (query on page load)**
  - Impact: Every map view queries current borrow status
  - Trade-offs: Accurate data, but slower page load and more database load
  - Performance: Needs indexed queries, might be slow with 1000+ tools

- **Option B: Map pins cached (update every 5 minutes)**
  - Impact: Map shows slightly stale data
  - Trade-offs: Fast page load, reduced DB queries, but user might click pin and find tool unavailable
  - Implementation: Redis cache with 5-minute TTL

- **Option C: Map shows all tools regardless of borrow status (defer availability check to detail page)**
  - Impact: Map is simplified - just shows tool inventory, not real-time availability
  - Trade-offs: Very fast, but user experience is clicking a pin and seeing "Currently borrowed"
  - Aligns with: Q2 Option B (if we go that route)

**Recommendation for MVP**: **Option B** (5-minute cache). Maps are for discovery and getting a sense of what's around. Exact availability matters when requesting, not when browsing. A 5-minute cache is fresh enough (most borrows are days/weeks, not minutes) and prevents crushing the DB when 50 users load the map simultaneously.

---

### Q12: What should happen when a user unfollows someone?

**Context**: The PRD says "Unfollow available from profile or following list (no confirmation prompt needed)." But what about:
- Active borrows between the users - should unfollow be blocked?
- Tool requests in progress - does unfollow cancel them?
- Should there be an "undo" option?

**Options**:

- **Option A: Unfollow always allowed, no impact on transactions**
  - Impact: Simply removes follow relationship; borrows and requests continue normally
  - Trade-offs: Clean separation (follow is social, borrows are transactional), but might confuse users
  - UX: No warning, just "Unfollowed [User]" toast message

- **Option B: Unfollow blocked if active borrow exists**
  - Impact: Check for borrows with status != 'returned'/'confirmed' before allowing unfollow
  - Trade-offs: Prevents awkwardness (unfollowing during active borrow), but complicates simple action
  - UX: Show message "Can't unfollow while you have an active borrow with this user"

- **Option C: Unfollow allowed but shows confirmation if active relationship exists**
  - Impact: If active borrow, show "Are you sure? You have an active borrow with [User]" prompt
  - Trade-offs: Balanced approach, but adds UI complexity
  - Contradicts: PRD's "no confirmation prompt needed"

**Recommendation for MVP**: **Option A** (always allowed, no impact). The PRD explicitly says no confirmation, suggesting a lightweight action. Follow/unfollow is about discovery preferences, not contractual obligations. Keep it simple. If users complain about awkwardness, we can add soft warnings in v2.

---

### Q13: Should the neighborhood name be editable after signup?

**Context**: The PRD says neighborhood name is captured during signup (free text or defaulted to postal code). But what if:
- User typos their neighborhood name?
- User wants to change it for privacy (made it too specific)?
- User actually moves to a new neighborhood but keeps same approximate location?

**Options**:

- **Option A: Neighborhood name is editable from profile settings**
  - Impact: Add to user profile edit form (simple text input)
  - Trade-offs: Gives control, but neighborhood might become inconsistent across activity feed history
  - Database: Simply update user.neighborhood field

- **Option B: Neighborhood name is immutable (contact support to change)**
  - Impact: No UI for editing; support ticket required
  - Trade-offs: Prevents confusion (neighborhood history stays consistent), but frustrating for typos
  - Support burden: Might get requests, but rare

- **Option C: Neighborhood name editable but historical ActivityEvents retain old value**
  - Impact: Events table stores neighborhood at time of event (denormalized)
  - Trade-offs: Historical accuracy, but more complex (need to copy neighborhood to events)
  - Database: ActivityEvents.neighborhood is snapshot, not foreign key

**Recommendation for MVP**: **Option A** (editable). If someone typos "Maple Groev" they should be able to fix it. The PRD frames neighborhood as user-provided and casual (not a critical data field). Don't over-engineer. If historical consistency becomes important later (it probably won't), we can denormalize then.

---

### Q14: How should clustering work on the map when zoomed out?

**Context**: The PRD says "When zoomed out, pins cluster (e.g., '5 tools') to avoid clutter" and "Clicking cluster zooms in to expand." But Leaflet's clustering has many configuration options. We need to decide:
- At what zoom level does clustering activate?
- Maximum cluster size before it splits?
- Should clusters show category breakdown (e.g., "5 tools: 3 Power, 2 Garden")?

**Options**:

- **Option A: Use Leaflet.markercluster defaults (cluster until zoom 18)**
  - Impact: Automatic clustering behavior based on map zoom and pin proximity
  - Trade-offs: No customization, might cluster aggressively (2 pins close together cluster even when zoomed in)
  - Config: Default `maxClusterRadius: 80` pixels

- **Option B: Custom clustering - only cluster when 10+ pins within 0.5 mile**
  - Impact: More refined clustering (fewer small clusters)
  - Trade-offs: Better UX in suburban areas, but requires custom config
  - Config: `maxClusterRadius: 40`, `disableClusteringAtZoom: 15`

- **Option C: Show category breakdown in cluster popups**
  - Impact: Cluster shows "12 tools: 5 Power Tools, 4 Hand Tools, 3 Gardening"
  - Trade-offs: More informative, but requires custom cluster icon rendering
  - Complexity: Moderate (need to aggregate pin data in cluster)

**Recommendation for MVP**: **Option A** (use defaults). Leaflet.markercluster is battle-tested and works well out of the box. Don't optimize prematurely. If users complain that clusters are too aggressive or not informative enough, we can tune config or add category breakdown in v2. Ship fast.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q15: Should Activity Feed events be deletable or hideable?

**Context**: The PRD describes ActivityEvents being created for new listings and completed borrows. But what if:
- A user lists a tool, it appears in feed, then immediately deletes the tool?
- A user wants to remove their activity from public view?
- An event contains problematic content (tool name is offensive)?

**Options**:

- **Option A: Events are permanent and public (no deletion)**
  - Impact: Once created, events stay in feed until they age out (pushed off by newer events)
  - Trade-offs: Simple, shows authentic community activity, but no recourse for mistakes
  - Database: No delete functionality needed

- **Option B: Deleting a tool/completing borrow also deletes its event**
  - Impact: CASCADE delete from tools/borrows to activity_events
  - Trade-offs: Keeps feed accurate (doesn't show deleted tools), but might make feed flicker as items disappear
  - Database: Foreign key with ON DELETE CASCADE

- **Option C: Events soft-delete when source is deleted (marked hidden, not deleted)**
  - Impact: Add `is_visible` flag to activity_events; set to false when tool deleted
  - Trade-offs: Preserves historical data for stats, but query must filter `WHERE is_visible = true`
  - Database: Additional column and index

**Recommendation for MVP**: **Option B** (cascade delete). If a user deletes a tool, its "New tool listed" event should vanish from feed (otherwise users click dead links). For borrow events, keep them even if users delete accounts (anonymized anyway). This is simple and matches user expectations.

---

### Q16: Should Community Stats page show historical trends or just current snapshot?

**Context**: The PRD describes a stats page with metrics like "Total Tools Shared" and notes "Stats update daily (not real-time; cached for performance)." But it doesn't mention:
- Can users see how metrics have changed over time (graph)?
- Is it just current numbers, or "X tools (up 12% this month)"?
- Should we store historical snapshots for future trend analysis?

**Options**:

- **Option A: Current snapshot only (no historical data)**
  - Impact: Stats page shows counts as of today
  - Trade-offs: Simplest implementation, but no sense of growth trajectory
  - Database: Single row per area in community_stats table (upsert daily)

- **Option B: Show current + month-over-month change percentage**
  - Impact: Store previous month's stats, calculate % change, show "Total Tools: 127 (↑ 15% from last month)"
  - Trade-offs: More engaging (shows growth), modest complexity
  - Database: Archive last month's stats or store time series

- **Option C: Full historical dashboard with 30-day trend graphs**
  - Impact: Line charts showing tool count, borrow count, active users over past month
  - Trade-offs: Very engaging, but significant scope increase (charting library, data retention)
  - Database: Time-series data in community_stats_history table

**Recommendation for MVP**: **Option A** (snapshot only). The PRD explicitly says this is v1 validation ("new users need to see community is active"). Trends are nice-to-have but not essential. If the stats show "47 tools, 23 completed borrows, 15 active users" that's enough social proof. Add trends in v2 if users request it.

---

## Notes for Product

- **Open Questions in PRD**: The "Open Questions for Tech Lead" section asks about geocoding service, PostGIS vs. application-level haversine, map pin randomization, ActivityEvent cleanup, and CommunityStats job scheduling. These are **implementation details that I'll decide** - they don't need product input. I'll choose based on performance, security, and maintainability once the functional requirements above are clarified.

- **Feature 2 Dependency**: Several questions (Q1, Q7) are blocked by undefined Feature 2 (borrow workflow). Recommend defining Feature 2 next or at least clarifying borrow status flow so we can finalize this feature.

- **Privacy Consideration**: Q1 about address storage is the most critical. Your answer here affects database schema, security audit requirements, and legal compliance (GDPR, etc.). Don't rush this decision.

- If any answers conflict with previous iterations, please flag it (this is iteration 1, so no conflicts yet)

- Happy to do another iteration if these answers raise new questions

- Once these are answered, I can proceed to implementation

---

## Summary of Recommended Defaults (if you want to move fast)

If you want to ship quickly and defer edge case decisions to v2, here are my suggested defaults:

1. **Q1**: Store coordinates only now (address in Feature 2)
2. **Q2**: Available = not currently borrowed
3. **Q3**: Radius based on owner's address
4. **Q4**: "My Network" ignores radius
5. **Q5**: Active = has listings OR borrows in 90 days
6. **Q6**: Feed respects current radius
7. **Q7**: Successful = returned/confirmed (needs Feature 2 status definition)
8. **Q8**: Fall back to postal code centroid if geocoding fails
9. **Q9**: Can follow anyone
10. **Q10**: Show up to 5 categories (fewer if community is small)
11. **Q11**: Map data cached 5 minutes
12. **Q12**: Unfollow always allowed
13. **Q13**: Neighborhood name is editable
14. **Q14**: Use default Leaflet clustering
15. **Q15**: Cascade delete events when tool deleted
16. **Q16**: Current snapshot only (no trends)

These defaults prioritize **shipping a working feature quickly** while maintaining good UX. We can iterate based on user feedback.