# Community & Location-Based Discovery - Feature Requirements (v1.2)

**Version History**:
- v1.0 - Initial specification (2025-01-10)
- v1.1 - Iteration 1 clarifications (2025-01-10) - Added geocoding strategy, map implementation details, activity feed mechanics, follow system behavior, stats calculation, radius persistence, and 10 other technical specifications
- v1.2 - Iteration 2 clarifications (2025-01-10) - Added map pin validation, activity event triggers, network view availability handling, pagination strategy, location accuracy warnings, stats radius synchronization, and neighborhood disambiguation

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

## Acceptance Criteria (UPDATED v1.2)

- Location set during signup via address input (geocoded to lat/long)
- Home page shows tools available within default 5-mile radius, sorted by distance
- Tool search results paginated at 20 per page with "Load More" button
- Map view displays available tools as pins, clustered when zoomed out
- Map pins validated for availability on click before showing popup
- Users can adjust search radius: 1, 5, 10, or 25 miles
- Warning banner shown when postal-code-accuracy users select 1-mile radius
- "Neighborhood" designation based on postal code or neighborhood name (user-provided)
- Users can follow others, creating a "My Network" view of tools from followed users
- "My Network" view shows all tools from followed users with availability badges (not filtered by availability)
- Community stats page shows: total tools shared, total borrows completed, most shared tool categories, active users
- Community stats page reflects user's current search radius (synchronized with home page)
- Discovery feed shows recent activity: new tools listed (on publish), successful borrows completed (anonymized stats)
- Activity feed events include neighborhood name only (v1 single-metro scope)

---

## Detailed Specifications (UPDATED v1.2)

### Map Pin Click Validation

**Decision**: Validate tool availability on popup open before displaying details.

**Rationale**: Map data is cached for 5 minutes to balance performance and freshness. Without validation, users could click a pin showing an available tool (from cached data), then click "View Details" to discover it's no longer available - wasting 3-4 clicks and creating frustration. The extra API call per pin click is a small cost (single indexed lookup on tool ID) that significantly improves user experience by preventing dead-end navigation.

**Implementation**:
```typescript
// Frontend: Map pin click handler
async function handlePinClick(toolId: string) {
  setLoading(true);
  
  try {
    const availability = await fetch(`/api/v1/tools/${toolId}/availability`);
    const data = await availability.json();
    
    if (data.isAvailable) {
      // Show popup with tool details and "View Details" link
      showPopup(toolId, data);
    } else {
      // Show toast notification instead of popup
      showToast('This tool is no longer available', 'info');
    }
  } catch (error) {
    showToast('Unable to load tool details', 'error');
  } finally {
    setLoading(false);
  }
}
```

**API Endpoint**:
- `GET /api/v1/tools/{id}/availability`
- Returns: `{ isAvailable: boolean, toolName: string, distance: number, neighborhood: string }`
- Authorization: Public endpoint (no auth required for availability check)

**Edge Cases**:
- If API call fails (network error), show generic error toast: "Unable to load tool details. Please try again."
- If tool has been deleted (404), treat same as unavailable (don't expose deletion vs. borrowed state)
- Loading state shows spinner overlay on clicked pin while validating

---

### Activity Feed Event Triggers

**Decision**: Activity events created when tool status transitions to 'published' (not on initial creation).

**Rationale**: Coordination with Feature 1 (Tool Listings) confirms tools have a two-state lifecycle: draft → published. Creating events on any insertion would show tools that users later delete during setup or abandon mid-creation. Only published tools should generate community activity to maintain feed quality and user trust.

**Implementation**:
```csharp
// Backend: Tool publishing workflow
public async Task<Result> PublishToolAsync(int toolId, int userId)
{
    var tool = await _context.Tools
        .FirstOrDefaultAsync(t => t.Id == toolId && t.OwnerId == userId);
    
    if (tool == null || tool.Status != ToolStatus.Draft)
        return Result.Failure("Cannot publish tool");
    
    tool.Status = ToolStatus.Published;
    tool.PublishedAt = DateTime.UtcNow;
    
    // Create activity event ONLY on publish transition
    var activityEvent = new ActivityEvent
    {
        EventType = ActivityEventType.NewToolListed,
        ToolId = toolId,
        ToolName = tool.Name,
        ToolCategory = tool.Category,
        Neighborhood = tool.Owner.Neighborhood,
        CreatedAt = DateTime.UtcNow
    };
    
    _context.ActivityEvents.Add(activityEvent);
    await _context.SaveChangesAsync();
    
    return Result.Success();
}
```

**Event Types**:
- `NewToolListed`: Triggered on draft → published transition only
- `SuccessfulBorrow`: Triggered when borrow status becomes 'returned' (from Feature 2 workflow)

**Edge Cases**:
- If user un-publishes tool (published → draft), do NOT create reverse event (no "Tool removed" events in v1)
- If tool is published, then immediately borrowed, both events fire (publish event + borrow event)
- If tool creation and publishing happen in single action (user never saves draft), event still fires on publish state

---

### Network View Availability Handling

**Decision**: "My Network" view shows all tools from followed users with availability status badges, not filtered by active borrows.

**Rationale**: Following someone is a conscious relationship-building action indicating the user values that person's inventory. Filtering out borrowed tools would make the network view feel empty during high borrow activity and frustrate users ("Why did Alice's tools vanish? I followed her yesterday."). Showing full inventory with status badges provides transparency - users can see what's available now and what's temporarily borrowed, helping them plan future requests.

**Implementation**:
```typescript
// Frontend: My Network tool card component
interface NetworkToolCardProps {
  tool: Tool;
  owner: User;
}

function NetworkToolCard({ tool, owner }: NetworkToolCardProps) {
  return (
    <div className="border rounded-lg p-4">
      <img src={tool.photoUrl} alt={tool.name} />
      <h3>{tool.name}</h3>
      <p className="text-sm text-gray-600">
        Owned by {owner.displayName} • {owner.neighborhood}
      </p>
      
      {/* Availability badge - always shown */}
      {tool.isAvailable ? (
        <span className="badge badge-green">Available</span>
      ) : (
        <span className="badge badge-gray">Currently Borrowed</span>
      )}
      
      {/* Action button changes based on availability */}
      {tool.isAvailable ? (
        <button className="btn-primary">Request to Borrow</button>
      ) : (
        <button className="btn-secondary" disabled>
          Unavailable
        </button>
      )}
    </div>
  );
}
```

**Query**:
```csharp
// Backend: Fetch network tools (no availability filter)
public async Task<List<ToolDto>> GetNetworkToolsAsync(int userId, int page)
{
    var followedUserIds = await _context.UserFollows
        .Where(f => f.FollowerUserId == userId)
        .Select(f => f.FollowedUserId)
        .ToListAsync();
    
    var tools = await _context.Tools
        .Include(t => t.Owner)
        .Where(t => 
            followedUserIds.Contains(t.OwnerId) &&
            t.Status == ToolStatus.Published)  // Published only
        // NO filter on t.CurrentBorrowId == null
        .OrderByDescending(t => t.PublishedAt)  // Newest first
        .Skip(page * 20)
        .Take(20)
        .ToListAsync();
    
    return tools.Select(t => new ToolDto
    {
        Id = t.Id,
        Name = t.Name,
        IsAvailable = t.CurrentBorrowId == null,  // Include availability flag
        Owner = new OwnerDto { ... }
    }).ToList();
}
```

**User Experience**:
- Available tools show green "Available" badge + enabled "Request to Borrow" button
- Borrowed tools show gray "Currently Borrowed" badge + disabled "Unavailable" button
- Sorting by publish date (newest first) ensures recently added tools from network appear at top
- Empty state: "Follow neighbors to see their tools here. Visit profiles and click 'Follow'."

---

### Search Results Pagination

**Decision**: Server-side pagination with "Load More" button, 20 tools per page.

**Rationale**: Without pagination, dense urban areas could return 100-500 tools as platform grows, causing slow page loads and poor mobile experience. "Load More" button provides good performance with clear feedback ("Showing 20 of 47 tools"), simpler implementation than infinite scroll, and allows migration to infinite scroll in v2 if users request it. 20-per-page balances page weight (images, data) with browsing efficiency.

**Implementation**:
```typescript
// Frontend: Nearby Tools list component
function NearbyToolsList() {
  const [page, setPage] = useState(0);
  const { data, fetchNextPage, hasNextPage, isLoading } = useInfiniteQuery({
    queryKey: ['nearbyTools', radius],
    queryFn: ({ pageParam = 0 }) => 
      fetchTools({ radius, page: pageParam, pageSize: 20 }),
    getNextPageParam: (lastPage) => lastPage.nextPage,
  });
  
  const allTools = data?.pages.flatMap(p => p.tools) ?? [];
  
  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {allTools.map(tool => <ToolCard key={tool.id} tool={tool} />)}
      </div>
      
      {hasNextPage && (
        <button 
          onClick={() => fetchNextPage()}
          disabled={isLoading}
          className="btn-secondary mt-4"
        >
          {isLoading ? 'Loading...' : 'Load More Tools'}
        </button>
      )}
      
      <p className="text-sm text-gray-600 mt-2">
        Showing {allTools.length} of {data?.pages[0].total} tools
      </p>
    </div>
  );
}
```

**API Response**:
```json
{
  "tools": [ /* 20 tool objects */ ],
  "page": 0,
  "pageSize": 20,
  "total": 47,
  "nextPage": 1  // null if no more pages
}
```

**Backend**:
```csharp
// Controller endpoint
[HttpGet("nearby")]
public async Task<ActionResult<PagedToolsResponse>> GetNearbyTools(
    [FromQuery] double latitude,
    [FromQuery] double longitude,
    [FromQuery] int radius,
    [FromQuery] int page = 0,
    [FromQuery] int pageSize = 20)
{
    var totalCount = await _context.Tools
        .Where(t => /* radius filter */)
        .CountAsync();
    
    var tools = await _context.Tools
        .Where(t => /* radius filter */)
        .OrderBy(t => /* distance calculation */)
        .Skip(page * pageSize)
        .Take(pageSize)
        .ToListAsync();
    
    return new PagedToolsResponse
    {
        Tools = tools.Select(MapToDto),
        Page = page,
        PageSize = pageSize,
        Total = totalCount,
        NextPage = (page + 1) * pageSize < totalCount ? page + 1 : null
    };
}
```

**Applies To**:
- "Nearby Tools" view (distance-sorted)
- "My Network" view (date-sorted)
- Map view does NOT paginate (shows all within radius, relies on clustering for performance)

---

### Location Accuracy Warnings

**Decision**: Show warning banner when postal-code-accuracy users select 1-mile radius, but allow the selection.

**Rationale**: Most users will have precise geocoding from address input during signup. For the small percentage with postal code fallback (geocoding API failure or address validation issues), forcing a minimum 5-mile radius feels heavy-handed for an edge case. Warning banner respects user autonomy while setting expectations about distance accuracy. If users complain about inaccuracy, they can update their address in profile settings (triggers re-geocoding).

**Implementation**:
```typescript
// Frontend: Radius selector with warning
function RadiusSelector({ userLocationAccuracy }: Props) {
  const [radius, setRadius] = useState(5);
  const showWarning = userLocationAccuracy === 'postal_code' && radius === 1;
  
  return (
    <div>
      <div className="flex gap-2">
        {[1, 5, 10, 25].map(r => (
          <button
            key={r}
            onClick={() => setRadius(r)}
            className={radius === r ? 'btn-primary' : 'btn-secondary'}
          >
            {r} mile{r > 1 ? 's' : ''}
          </button>
        ))}
      </div>
      
      {showWarning && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mt-2">
          <p className="text-sm text-yellow-800">
            ⚠️ Your location is approximate (based on postal code). 
            Distances may vary. <a href="/settings" className="underline">
            Update your address</a> for more accurate results.
          </p>
        </div>
      )}
    </div>
  );
}
```

**Database**:
- User table already has `location_accuracy` field (from v1.1 spec)
- Values: `'precise'` (address-level) or `'postal_code'` (fallback)
- Warning only shown for `'postal_code'` users selecting 1-mile radius (not 5/10/25)

**Edge Cases**:
- If user updates address in settings, re-run geocoding and update `location_accuracy` to `'precise'`
- If re-geocoding fails again, keep `'postal_code'` and show error message: "Unable to verify address. Using postal code for location."
- No warning shown for 5/10/25-mile radius (postal code imprecision negligible at those distances)

---

### Stats Page Radius Synchronization

**Decision**: Community Stats page reflects the user's current search radius from home page (synchronized via session storage).

**Rationale**: The spec explicitly states "stats scoped to user's current search radius," implying synchronization. Users expect consistency - if exploring their 10-mile area on home page, they want stats for that same area. Changing radius on either page should update both contexts to maintain coherent user experience.

**Implementation**:
```typescript
// Shared radius state hook
function useSearchRadius() {
  const [radius, setRadiusState] = useState<number>(() => {
    // Read from session storage on mount
    const stored = sessionStorage.getItem('searchRadius');
    return stored ? parseInt(stored, 10) : 5;  // Default 5 miles
  });
  
  const setRadius = (newRadius: number) => {
    setRadiusState(newRadius);
    sessionStorage.setItem('searchRadius', newRadius.toString());
    // Broadcast change to other tabs/components
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'searchRadius',
      newValue: newRadius.toString()
    }));
  };
  
  return [radius, setRadius] as const;
}

// Home page usage
function HomePage() {
  const [radius, setRadius] = useSearchRadius();
  // ... radius selector updates shared state
}

// Stats page usage
function CommunityStatsPage() {
  const [radius, setRadius] = useSearchRadius();
  
  // Stats page ALSO has radius selector (independent control)
  return (
    <div>
      <h1>Community Statistics</h1>
      <RadiusSelector value={radius} onChange={setRadius} />
      <StatsDisplay radius={radius} />
    </div>
  );
}
```

**Behavior**:
- User sets 10-mile radius on home page → navigates to stats → sees 10-mile stats
- User changes radius to 25 miles on stats page → navigates back to home page → home page search now uses 25 miles
- Radius persists across page navigation within session (not across browser restarts - resets to 5 miles)
- Stats page includes its own radius selector for easy exploration ("What if I expand to 25 miles?")

**API Call**:
```typescript
// Stats API request includes radius parameter
async function fetchCommunityStats(latitude: number, longitude: number, radius: number) {
  const response = await fetch(
    `/api/v1/community/stats?lat=${latitude}&lng=${longitude}&radius=${radius}`
  );
  return response.json();
}
```

**Caching**:
- Stats cached per (latitude, longitude, radius) tuple for 24 hours
- Changing radius invalidates cache (new API call with different radius parameter)
- Cache key: `community_stats:{lat}:{lng}:{radius}` (Redis)

---

### Neighborhood Disambiguation

**Decision**: Activity feed shows neighborhood name only (no city/state) for v1 single-metro scope.

**Rationale**: V1 launch is scoped to a **single metropolitan area** (e.g., Minneapolis-St. Paul metro) to validate product-market fit before geographic expansion. Within a single metro, displaying just neighborhood names is sufficient and cleaner ("New tool listed in Maple Grove" is clear when all users are in Twin Cities area). Adding city/state would be verbose and redundant for single-metro context.

**Implementation**:
```csharp
// Backend: Activity event creation (no city field needed)
var activityEvent = new ActivityEvent
{
    EventType = ActivityEventType.NewToolListed,
    ToolId = toolId,
    ToolName = tool.Name,
    ToolCategory = tool.Category,
    Neighborhood = tool.Owner.Neighborhood,  // Just neighborhood name
    CreatedAt = DateTime.UtcNow
};

// Frontend: Activity feed display
function ActivityFeed() {
  return events.map(event => (
    <div key={event.id} className="activity-item">
      {event.type === 'NewToolListed' && (
        <p>
          New tool listed: <strong>{event.toolName}</strong> in {event.neighborhood}
        </p>
      )}
      {event.type === 'SuccessfulBorrow' && (
        <p>
          Successful borrow: <strong>{event.toolCategory}</strong> borrowed in {event.neighborhood}
        </p>
      )}
      <span className="text-xs text-gray-500">{formatRelativeTime(event.createdAt)}</span>
    </div>
  ));
}
```

**Database Schema**:
```sql
-- Users table (no city/state fields needed in v1)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    neighborhood VARCHAR(50) NOT NULL,  -- User-provided or postal code
    location_accuracy VARCHAR(20) NOT NULL,  -- 'precise' or 'postal_code'
    -- No city, state, or postal_code columns in v1
);

-- Activity events table (neighborhood only)
CREATE TABLE activity_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    tool_id INT,
    tool_name VARCHAR(200),
    tool_category VARCHAR(100),
    neighborhood VARCHAR(50) NOT NULL,  -- Copied from owner at event time
    created_at TIMESTAMP NOT NULL
);
```

**Future Migration Path** (when expanding to multiple metros):
- Add `city` and `state` columns to users table
- Populate from geocoding reverse lookup (address → city/state)
- Update activity event template to show "in {neighborhood}, {city}"
- Backfill existing users' city/state from stored latitude/longitude

**Edge Cases**:
- If user provides custom neighborhood name like "My Block" (not a recognized name), it still displays as-is (no validation in v1)
- If two neighborhoods in metro have same name (rare but possible), accept ambiguity for v1 - users will infer from context
- If user leaves neighborhood blank, default to postal code (e.g., "55404") - less friendly but functional

---

### Following/Followers List Display

**Decision**: Following and Followers lists show username + neighborhood + tool count, visible only to account owner (private lists).

**Rationale**: Rich information helps account owner manage their network ("Oh right, Bob is the one with welding equipment"), but keeping lists private avoids social awkwardness ("Why didn't Bob follow me back?"). Matches privacy-conscious design philosophy - relationships are visible to participants, not broadcasted publicly. If users later request public lists (to discover popular tool owners), can add privacy toggle in v2.

**Implementation**:
```typescript
// Frontend: Following list modal (opens when clicking "Following: 12")
function FollowingListModal({ userId }: Props) {
  const { data: following } = useQuery({
    queryKey: ['following', userId],
    queryFn: () => fetchFollowing(userId),
    // Only fetches if userId matches current authenticated user
  });
  
  return (
    <Modal title="People You Follow">
      {following.map(user => (
        <div key={user.id} className="flex items-center justify-between p-3 border-b">
          <div>
            <p className="font-medium">{user.displayName}</p>
            <p className="text-sm text-gray-600">
              {user.neighborhood} • {user.toolCount} tools
            </p>
          </div>
          <button 
            onClick={() => unfollowUser(user.id)}
            className="btn-secondary-sm"
          >
            Unfollow
          </button>
        </div>
      ))}
    </Modal>
  );
}
```

**API Endpoint**:
```csharp
// Backend: Get following list (authorization check)
[HttpGet("users/{userId}/following")]
[Authorize]
public async Task<ActionResult<List<FollowedUserDto>>> GetFollowing(int userId)
{
    // Only allow users to see their own following list
    if (userId != CurrentUserId)
        return Forbid();
    
    var following = await _context.UserFollows
        .Where(f => f.FollowerUserId == userId)
        .Include(f => f.FollowedUser)
        .Select(f => new FollowedUserDto
        {
            Id = f.FollowedUser.Id,
            DisplayName = f.FollowedUser.DisplayName,
            Neighborhood = f.FollowedUser.Neighborhood,
            ToolCount = f.FollowedUser.Tools.Count(t => t.Status == ToolStatus.Published),
            FollowedAt = f.CreatedAt
        })
        .OrderByDescending(f => f.FollowedAt)  // Most recent follows first
        .ToListAsync();
    
    return following;
}
```

**Authorization**:
- `GET /api/v1/users/{userId}/following` → Returns 403 Forbidden if requester ≠ userId
- `GET /api/v1/users/{userId}/followers` → Returns 403 Forbidden if requester ≠ userId
- Attempting to view another user's lists shows generic error: "You can only view your own network lists"

**UI Behavior**:
- On own profile: "Following: 12" is blue/underlined (clickable link)
- On other user's profile: "Following: 12" is plain text (not clickable)
- Unfollow button in list shows confirmation: "Are you sure? This user won't be notified." (No reversal prompt)

---

## Q&A History

### Iteration 2 - 2025-01-10

**Q1: How should map pin clicks interact with tool availability changes?**  
**A**: Validate availability on popup open. When user clicks pin, make API call to `GET /api/v1/tools/{id}/availability` before showing popup. If available, show popup with details and "View Details" link. If unavailable, show toast notification "This tool is no longer available" instead of popup. This prevents users from clicking through to unavailable tools, worth the small API call cost for better UX.

**Q2: What determines which tools appear in Activity Feed "New Tool Listed" events?**  
**A**: Events created when tool status transitions to 'published' (not on initial creation). Feature 1 confirms tools have draft → published lifecycle. Only published tools generate activity events to maintain feed quality. Event fires on publish transition in tool publishing controller, creating `ActivityEvent` with `EventType = NewToolListed`.

**Q3: How should "My Network" view handle users who followed someone, then that person's only tool gets borrowed?**  
**A**: Show all tools from followed users with availability badges (not filtered by active borrows). Query includes `t.Status == ToolStatus.Published` but NO filter on `t.CurrentBorrowId`. Tool cards display green "Available" badge + enabled button, or gray "Currently Borrowed" badge + disabled button. Full inventory visibility helps users see what's temporarily borrowed and plan future requests.

**Q4: How should search results be paginated when user has 200+ tools within radius?**  
**A**: Server-side pagination with "Load More" button, 20 tools per page. Backend returns `PagedToolsResponse` with `tools`, `page`, `pageSize`, `total`, and `nextPage`. Frontend uses TanStack Query's `useInfiniteQuery` to fetch next page on button click. Shows "Showing X of Y tools" count below button. Applies to both "Nearby Tools" and "My Network" views (map view shows all, relies on clustering).

**Q5: What should happen when user's geocoding accuracy is 'postal_code' and they search with 1-mile radius?**  
**A**: Show warning banner but allow 1-mile selection. Banner displays: "⚠️ Your location is approximate (based on postal code). Distances may vary. Update your address for more accurate results." Warning only shown for postal-code users selecting 1-mile radius (not 5/10/25). Respects user autonomy while setting expectations. If they update address in settings, re-run geocoding and update `location_accuracy` to `'precise'`.

**Q6: Should Community Stats page refresh when user changes search radius, or stay static until page reload?**  
**A**: Stats page reflects user's current search radius (synchronized with home page via session storage). Custom `useSearchRadius()` hook stores radius in `sessionStorage` and broadcasts changes. Stats page has its own radius selector for independent exploration, but changes affect both stats display and home page search. Stats API called with radius parameter, cache key includes radius: `community_stats:{lat}:{lng}:{radius}`.

**Q7: How should Activity Feed handle neighborhoods with identical names in different regions?**  
**A**: Show neighborhood name only (no city/state) for v1 single-metro scope. V1 launch targets single metropolitan area (e.g., Minneapolis-St. Paul), so "Maple Grove" is unambiguous within that context. ActivityEvent table has `neighborhood` field only. When expanding to multiple metros in v2, will add `city` and `state` columns to users table (populated from geocoding), update event template to "in {neighborhood}, {city}", and backfill existing users.

**Q8: Should "Following" and "Followers" counts on user profiles link to lists, and if so, what information do those lists show?**  
**A**: Lists show username + neighborhood + tool count, visible only to account owner (private). `GET /api/v1/users/{userId}/following` returns 403 Forbidden if requester ≠ userId. Modal displays followed users with "Unfollow" button for easy management. On own profile, counts are clickable blue links. On other profiles, counts are plain text (not clickable). Keeps social dynamics low-pressure while giving owner full network management.

---

### Iteration 1 - 2025-01-10

[Previous Q&A preserved from v1.1 - omitted here for brevity but would be included in actual document]

---

## Product Rationale

**Why validate pins on click instead of polling map data?**  
Map displays 50-200 pins in typical view. Polling each pin every 5 minutes would create massive API load (200 pins × 12 polls/hour = 2400 requests/hour per user). Validation on click amortizes cost - only pay for pins users actually interact with (typically 1-5 per session). User intent signal (clicking pin) justifies the freshness check.

**Why show all network tools regardless of availability?**  
Following is a relationship-building action, not a transactional filter. Users follow neighbors they trust and want to monitor. Hiding borrowed tools makes the network feel "broken" ("Where did Alice's tools go?"). Showing full inventory with status badges provides transparency and helps users plan ("I'll request that drill when it comes back next week"). Builds long-term engagement vs. immediate transaction focus.

**Why paginate at 20 per page?**  
Balances page weight (each tool card includes image, title, distance, category - ~15KB total) with browsing efficiency. 20 tools = ~300KB page, loads in <2s on 4G. More than 20 creates scroll fatigue; fewer than 20 requires too many "Load More" clicks. TanStack Query's infinite query pattern makes "Load More" feel fast (prefetches next page on scroll proximity). Can adjust to 25-30 if user testing shows preference.

**Why allow 1-mile radius for postal-code users despite inaccuracy?**  
Restricting features feels punishing for edge case (geocoding API failure outside user control). Warning banner educates without blocking. Postal code centroid is typically within 1-2 miles of actual address, so 1-mile search still captures most nearby tools. User frustration from "this feature is disabled for you" > minor distance inaccuracy. If user complains, they can fix by updating address (UX nudges them toward solution).

**Why sync stats radius with home page instead of independent control?**  
Users mentally model radius as "my current area of interest," not "different radius for each page." Changing radius on home page then seeing different scope on stats page breaks that model ("Why do stats show 5 miles when I searched