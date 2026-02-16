# Community & Location-Based Discovery - Technical Review (Iteration 3)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 3
**Date**: 2025-01-10

---

## Summary

This feature specification is **sufficiently detailed to proceed with implementation**. After two thorough iteration cycles addressing 16 clarifying questions, all critical technical ambiguities have been resolved. The spec now provides clear direction on data models, API contracts, authorization rules, edge case handling, and UI behaviors.

The specification demonstrates excellent product thinking - decisions are justified with user impact analysis, edge cases are thoroughly addressed, and implementation guidance is concrete without being prescriptive about architecture choices.

---

## What's Clear

### Data Model

**Users Table**:
- Location stored as `latitude` (NUMERIC 10,7) and `longitude` (NUMERIC 10,7)
- `neighborhood` (VARCHAR 50) - user-provided or postal code fallback
- `location_accuracy` (VARCHAR 20) - values: `'precise'` or `'postal_code'`
- No city/state fields in v1 (single-metro scope)

**UserFollows Table** (many-to-many):
- `follower_user_id` → `followed_user_id` relationship
- `created_at` timestamp for chronological sorting
- Unique constraint on (follower_user_id, followed_user_id)
- Private visibility (users can only see their own following/followers lists)

**ActivityEvents Table**:
- `event_type` (VARCHAR 50) - values: `'NewToolListed'`, `'SuccessfulBorrow'`
- `tool_id`, `tool_name`, `tool_category` - denormalized for performance
- `neighborhood` (VARCHAR 50) - copied from owner at event creation time
- `created_at` (TIMESTAMP) - for chronological feed display
- Events created on state transitions: draft→published (NewToolListed), borrow→returned (SuccessfulBorrow)

**Tools Table Extensions**:
- `status` field already exists from Feature 1 (values: `'draft'`, `'published'`)
- `published_at` timestamp triggers activity event creation
- `current_borrow_id` determines availability for map pin validation

### Business Logic

**Geocoding Strategy** (v1.1):
- Primary: Address geocoding via third-party API (Google/Mapbox)
- Fallback: Postal code geocoding if address fails
- Set `location_accuracy` flag to distinguish precision levels
- Re-geocode on address update in profile settings

**Search Radius**:
- Default: 5 miles
- Options: 1, 5, 10, 25 miles (user-selectable)
- Radius synchronized across home page and stats page via `sessionStorage`
- Persists within session, resets to 5 miles on new session
- Haversine formula for distance calculations in database queries

**Follow System**:
- One-way relationships (A follows B ≠ B follows A)
- No notifications on follow/unfollow events
- Follow action creates `UserFollow` record with `created_at` timestamp
- Unfollow soft-deletes record (or hard-deletes, implementation choice)
- No mutual-follow detection or special "friends" status in v1

**Map Pin Validation** (v1.2):
- Map data cached for 5 minutes (balance freshness/performance)
- On pin click: API call to `GET /api/v1/tools/{id}/availability`
- If available → show popup with tool details + "View Details" link
- If unavailable → show toast "This tool is no longer available"
- Loading state shows spinner overlay on clicked pin

**Activity Feed Events** (v1.2):
- NewToolListed: Fires on draft→published status transition ONLY
- SuccessfulBorrow: Fires when borrow status becomes 'returned' (Feature 2 workflow)
- Events include neighborhood name only (no city/state - single-metro scope)
- Feed displays most recent 50 events (cached 5 minutes, refreshes on page load)

### API Design

**Endpoints Defined**:

```
GET /api/v1/tools/nearby
  Query Params: latitude, longitude, radius, page=0, pageSize=20
  Returns: { tools: Tool[], page: int, pageSize: int, total: int, nextPage: int|null }
  Authorization: Public (no auth required)

GET /api/v1/tools/{id}/availability
  Returns: { isAvailable: bool, toolName: string, distance: number, neighborhood: string }
  Authorization: Public
  Edge Cases: 404 treated same as unavailable, don't expose deletion status

GET /api/v1/tools/network
  Query Params: page=0, pageSize=20
  Returns: Same pagination structure as /nearby
  Authorization: Required (uses JWT to identify followed users)
  Includes availability flag in each tool object

GET /api/v1/users/{userId}/following
  Returns: [ { id, displayName, neighborhood, toolCount, followedAt } ]
  Authorization: Required, 403 if requester ≠ userId
  Sorted by followedAt DESC (most recent first)

GET /api/v1/users/{userId}/followers
  Returns: Same structure as /following
  Authorization: Required, 403 if requester ≠ userId

POST /api/v1/users/{userId}/follow
  Body: { followedUserId: int }
  Returns: 201 Created or 409 Conflict if already following
  Authorization: Required, requester must match userId

DELETE /api/v1/users/{userId}/follow/{followedUserId}
  Returns: 204 No Content or 404 if not following
  Authorization: Required, requester must match userId

GET /api/v1/community/stats
  Query Params: latitude, longitude, radius
  Returns: { totalTools, totalBorrows, topCategories: [], activeUsers }
  Cache: Redis key `community_stats:{lat}:{lng}:{radius}`, TTL 24 hours
  Authorization: Public
```

### UI/UX Specifications

**Home Page - Nearby Tools**:
- Grid layout: 1 column (mobile), 2 columns (tablet), 3 columns (desktop)
- Default sort: Distance ascending (nearest first)
- Pagination: "Load More" button at bottom
- Loading state: Skeleton cards during fetch
- Empty state: "No tools found within [X] miles. Try expanding your search radius."

**Map View**:
- Displays all tools within radius (no pagination)
- Clustering when zoomed out (density threshold: 10 pins within 50px)
- Pin colors: Green (available), Gray (borrowed)
- On click: Spinner overlay → API call → popup or toast
- Popup includes: Tool name, category, distance, owner neighborhood, "View Details" button

**My Network View**:
- Shows all tools from followed users (not filtered by availability)
- Sort: Published date descending (newest first)
- Availability badge: Green "Available" or Gray "Currently Borrowed"
- Button state: Enabled "Request to Borrow" or Disabled "Unavailable"
- Empty state: "Follow neighbors to see their tools here. Visit profiles and click 'Follow'."

**Radius Selector** (appears on Home, Map, Stats pages):
- Button group with 4 options: [1] [5] [10] [25] miles
- Active button has primary styling, inactive have secondary
- Warning banner (yellow background) appears below selector when postal-code user selects 1 mile
- Banner text: "⚠️ Your location is approximate (based on postal code). Distances may vary. [Update your address] for more accurate results."

**Following/Followers Lists** (modal):
- Opens on click of "Following: X" or "Followers: Y" counts on own profile
- Each row: Avatar, display name, neighborhood, tool count, action button
- Following list: "Unfollow" button (shows confirmation: "Are you sure? This user won't be notified.")
- Followers list: "Remove" button (removes them from following you)
- Sort: Most recent relationships first (created_at DESC)

**Community Stats Page**:
- Hero metrics cards: Total Tools Shared, Total Borrows Completed, Active Users (past 30 days)
- Top Categories chart: Horizontal bar chart showing top 5 tool categories by count
- Radius selector at top (synchronized with home page via `useSearchRadius()` hook)
- All metrics scoped to current radius selection
- Refresh indicator when radius changes

**Activity Feed** (sidebar widget or dedicated page):
- Displays 50 most recent events
- NewToolListed: "New tool listed: **[Tool Name]** in [Neighborhood]"
- SuccessfulBorrow: "Successful borrow: **[Tool Category]** borrowed in [Neighborhood]"
- Relative timestamps: "2 hours ago", "Yesterday", "3 days ago"
- Auto-refreshes every 5 minutes (polling or SSE)

### Edge Cases Addressed

**Geocoding Failures**:
- Address API fails → fallback to postal code geocoding
- Postal code fails → reject signup with error: "Unable to verify location. Please check your address."
- Set `location_accuracy = 'postal_code'` on fallback, `'precise'` on success

**Map Pin Edge Cases**:
- Tool deleted between map load and pin click → 404 treated as unavailable, show toast
- Network error on availability check → show toast "Unable to load tool details. Please try again."
- Tool becomes unavailable during popup display → user clicks "View Details" → detail page shows accurate status

**Follow System Edge Cases**:
- User tries to follow self → API returns 400 Bad Request "Cannot follow yourself"
- User follows, then followed user deletes account → orphaned UserFollow records cleaned up by background job (daily sweep)
- User A follows B, B follows A → treated as two independent relationships (no "mutual" badge in v1)

**Network View Edge Cases**:
- User follows someone with 0 tools → shows empty state: "This user hasn't listed any tools yet"
- All followed users' tools are borrowed → shows full inventory with "Currently Borrowed" badges
- Followed user un-publishes tool (published→draft) → tool disappears from network view (query filters `Status == Published`)

**Stats Edge Cases**:
- No activity in selected radius → shows zeros with message: "No sharing activity in this area yet. Be the first to list a tool!"
- User changes radius mid-page-load → abort previous API call, fetch with new radius (cancel token pattern)
- Cache miss on stats → recalculate and cache for 24 hours

**Activity Feed Edge Cases**:
- User publishes tool, immediately borrows it out → both events fire (publish event + borrow event)
- Tool un-published after event created → event remains in feed (historical record, no retroactive deletion)
- Empty feed (new community) → shows "No recent activity. Share a tool to get started!"

**Pagination Edge Cases**:
- User on page 3, filter changes radius → reset to page 0 (new query context)
- Race condition: User clicks "Load More" twice rapidly → deduplicate requests via React Query
- Last page has fewer than 20 items → "Load More" button hidden, show "Showing X of X tools"

**Location Accuracy Edge Cases**:
- User updates address in settings → re-geocode, update lat/long/location_accuracy
- Re-geocoding fails → keep old location, show error: "Unable to verify address. Using previous location."
- User with postal-code accuracy selects 1-mile radius → show warning banner (doesn't block action)

---

## Implementation Notes

### Database

**Indexes Required**:
```sql
-- Geospatial search performance
CREATE INDEX idx_users_location ON users USING GIST (ll_to_earth(latitude, longitude));

-- Follow relationship lookups
CREATE INDEX idx_user_follows_follower ON user_follows(follower_user_id);
CREATE INDEX idx_user_follows_followed ON user_follows(followed_user_id);

-- Activity feed chronological query
CREATE INDEX idx_activity_events_created_at ON activity_events(created_at DESC);

-- Tool availability checks
CREATE INDEX idx_tools_status_borrow ON tools(status, current_borrow_id) WHERE status = 'published';
```

**Uniqueness Constraints**:
```sql
-- Prevent duplicate follows
ALTER TABLE user_follows ADD CONSTRAINT uq_user_follows_pair 
  UNIQUE (follower_user_id, followed_user_id);

-- Prevent self-follows at database level
ALTER TABLE user_follows ADD CONSTRAINT chk_no_self_follow 
  CHECK (follower_user_id <> followed_user_id);
```

### Authorization

**Public Endpoints** (no auth):
- `GET /api/v1/tools/nearby` - discovery requires no login
- `GET /api/v1/tools/{id}/availability` - map pin validation for anonymous users
- `GET /api/v1/community/stats` - public community health metrics

**Authenticated Endpoints**:
- `GET /api/v1/tools/network` - requires JWT to identify followed users
- `GET /api/v1/users/{userId}/following` - must match authenticated user ID
- `GET /api/v1/users/{userId}/followers` - must match authenticated user ID
- `POST /api/v1/users/{userId}/follow` - must match authenticated user ID
- `DELETE /api/v1/users/{userId}/follow/{followedUserId}` - must match authenticated user ID

**Authorization Patterns**:
```csharp
// Endpoint-level: Public access
[AllowAnonymous]
[HttpGet("nearby")]
public async Task<ActionResult<PagedToolsResponse>> GetNearbyTools(...)

// Endpoint-level: Requires authentication
[Authorize]
[HttpGet("network")]
public async Task<ActionResult<PagedToolsResponse>> GetNetworkTools(...)

// Method-level: Owner-only access
public async Task<ActionResult> GetFollowing(int userId)
{
    if (userId != CurrentUserId)
        return Forbid(); // Returns 403 with generic message
    // ... proceed with query
}
```

### Validation

**Input Validation Rules**:
- Latitude: Range -90.0 to 90.0
- Longitude: Range -180.0 to 180.0
- Radius: Enum [1, 5, 10, 25] miles only
- Page: Min 0, Max 1000 (prevent abuse)
- PageSize: Min 1, Max 100 (prevent oversized responses)
- UserId: Must exist in users table (foreign key validation)

**Business Logic Validation**:
- Cannot follow self (checked at API and database constraint level)
- Cannot follow same user twice (unique constraint)
- Tool availability check returns consistent schema even on 404 (don't leak deletion vs. borrowed state)

### Caching Strategy

**Map Data Cache**:
- Key: `map_tools:{lat}:{lng}:{radius}`
- TTL: 5 minutes
- Invalidation: On tool publish/unpublish within radius (complex - defer to v2)

**Stats Cache**:
- Key: `community_stats:{lat}:{lng}:{radius}`
- TTL: 24 hours
- Invalidation: On any tool publish or borrow completion (complex - accept stale data for v1)

**Activity Feed Cache**:
- Key: `activity_feed:global` (single metro scope)
- TTL: 5 minutes
- Invalidation: On new activity event creation (append to cache)

**Cache Miss Strategy**:
- Always query database on miss
- Write-through pattern: Create cache entry after database query
- Fail open: If Redis unavailable, bypass cache and query database directly

### Key Decisions

**Why 20 items per page?**  
Balances page weight (~300KB with images) vs. browsing efficiency. TanStack Query's infinite query prefetches next page, making "Load More" feel instant.

**Why 5-minute map cache?**  
Short enough that users see relatively fresh availability, long enough to prevent excessive API load (200 pins × 12 refreshes/hour = tolerable).

**Why 24-hour stats cache?**  
Stats are aggregate metrics that don't require real-time accuracy. Daily recalculation is sufficient for "community health" narrative.

**Why one-way follows vs. mutual "friends"?**  
One-way follows match Twitter/GitHub model - lower friction than Facebook-style mutual acceptance. Users can follow prolific tool owners without requiring reciprocation. Simpler implementation (no "pending" state).

**Why validate pins on click vs. polling?**  
Validation on click amortizes API cost - only check pins users interact with (1-5 per session) vs. polling all visible pins (50-200 every 5 minutes). User intent signal justifies freshness check.

**Why show unavailable tools in network view?**  
Following is relationship-building, not transactional filtering. Users want to monitor trusted neighbors' full inventory, not just what's available right now. Status badges provide transparency without hiding borrowed tools.

**Why single-metro scope for v1?**  
Simplifies neighborhood disambiguation (no city/state needed), reduces geocoding complexity, and allows validation of product-market fit before geographic expansion. Adding city/state fields later is straightforward migration.

---

## Recommended Next Steps

1. **Create Engineering Specification**:
   - Database schema DDL with indexes and constraints
   - API endpoint implementations with request/response contracts
   - Service layer architecture (tools service, follow service, stats service, activity service)
   - Cache layer integration (Redis client setup, key naming conventions, TTL policies)

2. **Set Up Infrastructure**:
   - Geocoding API integration (Google Maps or Mapbox - choose based on pricing/quota)
   - Redis instance for caching (local: Docker container, prod: Azure Cache or ElastiCache)
   - Background job for orphaned follow cleanup (Hangfire recurring job, daily 2am UTC)

3. **Frontend Component Hierarchy**:
   - `useSearchRadius()` hook (session storage sync)
   - Map component with clustering library (react-map-gl or Leaflet)
   - Pagination components with TanStack Query infinite query
   - Modal system for following/followers lists

4. **Testing Strategy**:
   - Unit tests: Haversine distance calculation, follow relationship validation, activity event creation
   - Integration tests: Geocoding API fallback behavior, cache hit/miss scenarios
   - E2E tests: Full user flow (signup → set radius → follow user → view network → request tool)

5. **Monitoring & Metrics**:
   - Track geocoding success rate (precise vs. postal fallback)
   - Monitor API latency for `/nearby` endpoint (target: p95 < 500ms)
   - Alert on cache hit rate drop below 80% (indicates misconfigured TTL or invalidation issues)
   - Log follow/unfollow events for analytics (engagement metric)

---

**This feature is ready for detailed engineering specification and implementation.**

The product team has done excellent work clarifying ambiguities through two iteration cycles. The specification now provides clear boundaries for engineering decisions while preserving flexibility in implementation details (ORM query optimization, React component structure, caching library choice). All critical questions have concrete answers with justified rationale.