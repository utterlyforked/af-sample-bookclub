# Community & Location-Based Discovery - Feature Requirements

**Version**: 1.0  
**Date**: 2025-01-10  
**Status**: Initial - Awaiting Tech Lead Review

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

## Functional Requirements

### Location Setup & Privacy

**What**: Capture user location during signup and use it for all distance calculations while protecting exact address privacy.

**Why**: Distance-based search is core to usefulness, but users need confidence their exact address isn't exposed publicly.

**Behavior**:
- During signup, require street address input
- Geocode address to latitude/longitude coordinates for distance calculations
- Store full address in database (needed for approved pickup coordination - see Feature 2)
- Ask user to provide "neighborhood name" (free text, max 50 chars, e.g., "Maple Grove", "Downtown", "West Side")
- Default neighborhood to postal code if user leaves blank
- Display only neighborhood name publicly (never full address)
- In tool listings and profiles, show "~2.3 miles away" (calculated from coordinates) + neighborhood name
- Full address revealed only to borrowers after owner approves request (handled in Feature 2)

---

### Radius-Based Tool Search

**What**: Filter tool listings by distance from the user's location with adjustable radius.

**Why**: Users want to borrow from nearby neighbors for convenient pickup/return, but should be able to expand search for rare tools.

**Behavior**:
- Default radius: 5 miles (reasonable driving distance for most suburbs)
- Radius selector with preset options: 1 mile, 5 miles, 10 miles, 25 miles
- Calculate distance using haversine formula from user's coordinates to tool owner's coordinates
- Display results sorted by distance (nearest first)
- Each listing shows distance rounded to 1 decimal place (e.g., "2.3 miles away")
- Distance calculated as straight-line ("as the crow flies"), not driving distance
- Radius persists in user session but resets to 5 miles on new login
- Search executes on page load with default radius; no separate "search" button needed
- Radius change immediately refreshes results

---

### Map View

**What**: Interactive map showing available tools as location pins with clustering and detail popups.

**Why**: Visual representation makes discovery intuitive and helps users understand geographic distribution of tools.

**Behavior**:
- Map toggle button switches between list view and map view
- Map centers on user's location with current search radius shown as a circle overlay
- Each available tool shows as a pin at owner's approximate location (randomized within 0.1 mile for privacy)
- Pin color-coded by category (Power Tools = red, Hand Tools = blue, Gardening = green, etc.)
- When zoomed out, pins cluster (e.g., "5 tools") to avoid clutter
- Clicking cluster zooms in to expand
- Clicking individual pin shows popup: tool photo, title, category, distance, "View Details" button
- Map respects current radius setting; changing radius updates visible pins
- Map uses Leaflet.js with OpenStreetMap tiles (free, no API key needed)

---

### Follow System

**What**: Allow users to follow other users and view a filtered feed of tools from their network.

**Why**: After successful borrows, users want to prioritize familiar, trusted neighbors for future needs without searching.

**Behavior**:
- "Follow" button appears on user profiles
- Follow is one-directional (like Twitter, not mutual friendship like Facebook)
- Following someone does not notify them (low-friction, non-awkward)
- User's profile shows "Following: 12" count (clickable to see list)
- User's profile shows "Followers: 8" count (clickable to see list)
- "My Network" tab on home page shows tools from followed users only
- "My Network" view shows tools sorted by date listed (newest first), not distance
- Each tool in "My Network" view shows which followed user owns it
- No limit on number of follows
- Unfollow available from profile or following list (no confirmation prompt needed)

---

### Community Statistics Dashboard

**What**: Aggregate metrics page showing overall platform health and activity in user's area.

**Why**: New users need validation that the community is active; existing users want to see impact and growth.

**Behavior**:
- "Community Stats" link in main navigation
- Stats scoped to user's current search radius (defaults to 5 miles)
- Metrics displayed:
  - **Total Tools Shared**: Count of all tool listings within radius
  - **Total Borrows Completed**: Count of successful borrow transactions (status = returned/confirmed)
  - **Active Users**: Count of users within radius who have listed tools OR completed a borrow in last 90 days
  - **Most Shared Categories**: Bar chart showing tool count by category (top 5)
  - **Top Contributors**: List of 5 users with most tools listed (anonymized as "User in [Neighborhood] - 23 tools")
- Stats update daily (not real-time; cached for performance)
- "Last updated: [date]" timestamp shown
- No personally identifiable information displayed (no names, only counts and neighborhoods)

---

### Discovery Activity Feed

**What**: Recent activity stream showing anonymized community sharing events.

**Why**: Creates sense of active community and social proof; encourages participation through visibility.

**Behavior**:
- "Recent Activity" section on home page (below tool search results)
- Shows last 20 events within user's search radius
- Event types displayed:
  - "New tool listed: [Tool Name] in [Neighborhood]" (e.g., "New tool listed: DeWalt Drill in Maple Grove")
  - "Successful borrow: [Tool Category] borrowed in [Neighborhood]" (e.g., "Successful borrow: Power Tool borrowed in West Side")
- No user names shown in feed (privacy protection)
- Events show relative time (e.g., "2 hours ago", "3 days ago")
- Feed auto-refreshes when user changes search radius
- Feed updates every 5 minutes when page is active (polling)
- Clicking event navigates to tool detail page (for "new tool" events) or does nothing (for "borrow" events)

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:

- **User**: Already exists; needs `latitude`, `longitude`, `neighborhood` fields
- **UserFollow**: Junction table for follow relationships (`follower_user_id`, `followed_user_id`, `created_at`)
- **CommunityStats**: Cached statistics table (`area_identifier`, `radius`, `stats_json`, `calculated_at`)
- **ActivityEvent**: Feed events (`event_type`, `tool_id`, `tool_category`, `neighborhood`, `created_at`)

**Key Relationships**:
- User has many followers (via UserFollow)
- User follows many others (via UserFollow)
- Tools belong to Users (existing relationship)
- ActivityEvents reference Tools (for "new listing" events)

**Geospatial Queries**:
- Need to efficiently query tools within radius (PostGIS extension or haversine calculation in application code)
- Index on User coordinates for fast radius searches

---

## User Experience Flow

**New User Onboarding**:
1. User completes signup form including street address
2. System geocodes address to coordinates, asks for neighborhood name
3. User lands on home page showing tools within 5 miles, sorted by distance
4. User sees map toggle and switches to map view to visualize distribution
5. User sees "Community Stats" showing active ecosystem (validation)
6. User explores discovery feed to see recent activity

**Finding a Specific Tool**:
1. User searches for "chainsaw" (Feature 1 search)
2. Results show 2 chainsaws within 5 miles
3. User expands radius to 10 miles to find 3 more options
4. User switches to map view to see which is most convenient
5. User clicks pin on map, views tool popup, clicks "View Details"

**Building a Network**:
1. User successfully borrows a ladder from Alice
2. After return, user navigates to Alice's profile (from transaction history)
3. User clicks "Follow" button on Alice's profile
4. User sees "My Network" tab appear on home page
5. Future visits show Alice's 15 tools in "My Network" view
6. When Alice lists a new tool, it appears at top of user's "My Network" feed

---

## Edge Cases & Constraints

- **User has no address**: Cannot use platform; address required during signup (no workaround in v1)
- **Geocoding fails**: Show error message, require user to re-enter or correct address format
- **User moves**: No address change functionality in v1; user would need to contact support (defer to v2)
- **Search radius finds 0 tools**: Show message "No tools found within X miles. Try expanding your search radius." with prompt to increase
- **Map performance with many pins**: Clustering handles this; if area has 1000+ tools, clusters prevent slowdown
- **User follows themselves**: Prevented - "Follow" button does not appear on user's own profile
- **Following user with no tools**: Allowed; "My Network" will simply show empty state or only other followed users' tools
- **Community stats for rural areas**: May show low numbers; this is accurate reflection, not a bug
- **Privacy: exact location exposure**: Coordinates stored securely, never exposed via API; map pins randomized within 0.1 mile; only neighborhood name shown publicly

---

## Out of Scope for This Feature

- Driving directions to tool owner (user can copy address into Google Maps manually)
- "Suggested users to follow" recommendations (simple manual follow only)
- Notifications when followed user lists new tool (no real-time alerts in v1)
- Filtering discovery feed by category or event type (shows all events)
- Exporting community stats or historical trends (v1 is snapshot only)
- Private/hidden tool listings that don't appear in search (all listings are public)
- Custom neighborhood boundaries (uses simple postal code or user-provided name)
- Integration with external mapping services for better address validation (basic geocoding only)

---

## Open Questions for Tech Lead

- What geocoding service should we use? (Options: Google Geocoding API, Nominatim/OpenStreetMap, Azure Maps)
- Should we use PostGIS extension for geospatial queries or calculate haversine in application code? Performance implications?
- For map randomization (privacy protection), should we randomize pin location once at tool creation or on-the-fly each time map loads?
- How should we handle ActivityEvent cleanup? (Keep last 30 days? Last 1000 events? Storage growth concern?)
- Should CommunityStats calculation be a background job (Hangfire) or on-demand with caching? Update frequency?

---

## Dependencies

**Depends On**: 
- Feature 1 (Tool Listings) - must have tools to display
- Feature 3 (User Profiles) - follow system requires profiles
- User authentication & authorization (existing)

**Enables**: 
- Future: Notifications for followed user activity
- Future: Advanced search filters (combined with radius)
- Future: Neighborhood admin/moderator roles (based on community stats)