# Community & Location-Based Discovery — Engineering Spec

**Type**: feature
**Component**: community-location-discovery
**Dependencies**: foundation-spec, FEAT-01-tool-listings, FEAT-02-booking-and-borrowing
**Status**: Ready for Implementation

---

## Overview

The Community & Location-Based Discovery feature enables geographic tool search, visual map exploration, social following, and community activity monitoring. Users discover tools within configurable radius, visualize availability on maps, follow trusted neighbors, and view aggregate community statistics. This feature owns the `UserFollow` and `ActivityEvent` entities, and reads from foundation entities (`User`, `Tool`) and FEAT-01/FEAT-02 tool/borrow state.

---

## Data Model

### UserFollow

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | integer | PK, auto-increment, not null | Generated on insert |
| follower_user_id | integer | FK to users.id, not null | User who is following |
| followed_user_id | integer | FK to users.id, not null | User being followed |
| created_at | timestamp | not null, default UTC now | When follow relationship created |

**Indexes**:
- `(follower_user_id, followed_user_id)` unique
- `(followed_user_id)` non-unique (for follower list queries)

**Relationships**:
- Belongs to `User` via `follower_user_id` (cascade delete)
- Belongs to `User` via `followed_user_id` (cascade delete)

**Constraints**:
- `CHECK (follower_user_id != followed_user_id)` - cannot follow self

---

### ActivityEvent

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | integer | PK, auto-increment, not null | Generated on insert |
| event_type | string(50) | not null | Enum: 'new_tool_listed', 'successful_borrow' |
| tool_id | integer | FK to tools.id, nullable | Reference to tool (null if tool deleted) |
| tool_name | string(200) | not null | Denormalized for display after deletion |
| tool_category | string(100) | not null | Denormalized for borrow events |
| neighborhood | string(50) | not null | Owner's neighborhood at event time |
| created_at | timestamp | not null, default UTC now | When event occurred |

**Indexes**:
- `(created_at DESC)` non-unique (for feed chronological sorting)
- `(tool_id)` non-unique (for tool-specific activity lookup)

**Relationships**:
- References `Tool` via `tool_id` (set null on delete, not cascade)

**Constraints**:
- None beyond type validation

---

### User (Extended from Foundation)

**New fields added to foundation User entity**:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| neighborhood | string(50) | not null | User-provided or postal code fallback |
| location_accuracy | string(20) | not null | Enum: 'precise', 'postal_code' |
| search_radius_miles | integer | not null, default 5 | User's last selected radius (1, 5, 10, 25) |

**Note**: `latitude`, `longitude` already defined in foundation spec. These extensions support location-based features.

---

## API Endpoints

### POST /api/v1/users/{userId}/follow

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated (any logged-in user)

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|------------|
| userId | integer | Must exist, cannot equal current user ID |

**Request body**: None

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| followedUserId | integer | ID of user now followed |
| followerCount | integer | Updated follower count for followed user |
| followingCount | integer | Updated following count for current user |
| createdAt | ISO 8601 datetime | UTC timestamp |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 404 | User ID not found |
| 409 | Already following this user |
| 400 | Attempting to follow self |

---

### DELETE /api/v1/users/{userId}/follow

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated (any logged-in user)

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|------------|
| userId | integer | Must exist, must currently be following |

**Request body**: None

**Success response** `204 No Content`

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 404 | User ID not found or not currently following |

---

### GET /api/v1/users/{userId}/following

**Auth**: Required (Bearer JWT)  
**Authorization**: Owner (userId must match authenticated user)

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|------------|
| userId | integer | Must match current user ID |

**Query parameters**: None

**Success response** `200 OK`:
```typescript
{
  following: [
    {
      id: number,
      displayName: string,
      neighborhood: string,
      toolCount: number,
      followedAt: ISO 8601 datetime
    }
  ]
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User ID does not match authenticated user |

---

### GET /api/v1/users/{userId}/followers

**Auth**: Required (Bearer JWT)  
**Authorization**: Owner (userId must match authenticated user)

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|------------|
| userId | integer | Must match current user ID |

**Query parameters**: None

**Success response** `200 OK`:
```typescript
{
  followers: [
    {
      id: number,
      displayName: string,
      neighborhood: string,
      toolCount: number,
      followedAt: ISO 8601 datetime
    }
  ]
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User ID does not match authenticated user |

---

### GET /api/v1/tools/nearby

**Auth**: None (public endpoint)  
**Authorization**: None

**Query parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| latitude | decimal(10,7) | yes | Valid latitude (-90 to 90) |
| longitude | decimal(10,7) | yes | Valid longitude (-180 to 180) |
| radius | integer | yes | One of: 1, 5, 10, 25 |
| page | integer | no | Default 0, min 0 |
| pageSize | integer | no | Default 20, min 1, max 100 |

**Success response** `200 OK`:
```typescript
{
  tools: [
    {
      id: number,
      name: string,
      category: string,
      photoUrl: string,
      isAvailable: boolean,
      distanceMiles: decimal(4,2),
      owner: {
        id: number,
        displayName: string,
        neighborhood: string
      }
    }
  ],
  page: number,
  pageSize: number,
  total: number,
  nextPage: number | null
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid coordinates or radius |

---

### GET /api/v1/tools/map

**Auth**: None (public endpoint)  
**Authorization**: None

**Query parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| latitude | decimal(10,7) | yes | Valid latitude (-90 to 90) |
| longitude | decimal(10,7) | yes | Valid longitude (-180 to 180) |
| radius | integer | yes | One of: 1, 5, 10, 25 |

**Success response** `200 OK`:
```typescript
{
  tools: [
    {
      id: number,
      name: string,
      category: string,
      latitude: decimal(10,7),
      longitude: decimal(10,7),
      isAvailable: boolean
    }
  ],
  centerLatitude: decimal(10,7),
  centerLongitude: decimal(10,7),
  radiusMiles: number
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid coordinates or radius |

**Notes**:
- Returns ALL tools within radius (no pagination) for map rendering
- Response cached for 5 minutes per (lat, lng, radius) tuple

---

### GET /api/v1/tools/{id}/availability

**Auth**: None (public endpoint)  
**Authorization**: None

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|------------|
| id | integer | Must exist |

**Query parameters**: None

**Success response** `200 OK`:
```typescript
{
  isAvailable: boolean,
  toolName: string,
  distanceMiles: decimal(4,2),
  neighborhood: string
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 404 | Tool not found or deleted |

**Notes**:
- Used for map pin click validation
- Does not return full tool details, only availability status

---

### GET /api/v1/tools/network

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated (any logged-in user)

**Query parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| page | integer | no | Default 0, min 0 |
| pageSize | integer | no | Default 20, min 1, max 100 |

**Success response** `200 OK`:
```typescript
{
  tools: [
    {
      id: number,
      name: string,
      category: string,
      photoUrl: string,
      isAvailable: boolean,
      owner: {
        id: number,
        displayName: string,
        neighborhood: string
      },
      publishedAt: ISO 8601 datetime
    }
  ],
  page: number,
  pageSize: number,
  total: number,
  nextPage: number | null
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |

**Notes**:
- Returns tools from all followed users (no radius filter)
- Includes unavailable tools with availability badge
- Sorted by publishedAt DESC (newest first)

---

### GET /api/v1/community/stats

**Auth**: None (public endpoint)  
**Authorization**: None

**Query parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| latitude | decimal(10,7) | yes | Valid latitude (-90 to 90) |
| longitude | decimal(10,7) | yes | Valid longitude (-180 to 180) |
| radius | integer | yes | One of: 1, 5, 10, 25 |

**Success response** `200 OK`:
```typescript
{
  totalToolsShared: number,
  totalBorrowsCompleted: number,
  activeUsers: number,
  topCategories: [
    {
      category: string,
      count: number
    }
  ],
  radiusMiles: number
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid coordinates or radius |

**Notes**:
- All statistics scoped to specified radius
- Cached for 24 hours per (lat, lng, radius) tuple
- `topCategories` limited to top 5 categories by tool count

---

### GET /api/v1/community/activity

**Auth**: None (public endpoint)  
**Authorization**: None

**Query parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| latitude | decimal(10,7) | yes | Valid latitude (-90 to 90) |
| longitude | decimal(10,7) | yes | Valid longitude (-180 to 180) |
| radius | integer | yes | One of: 1, 5, 10, 25 |
| page | integer | no | Default 0, min 0 |
| pageSize | integer | no | Default 20, min 1, max 50 |

**Success response** `200 OK`:
```typescript
{
  events: [
    {
      id: number,
      eventType: 'new_tool_listed' | 'successful_borrow',
      toolName: string,
      toolCategory: string,
      neighborhood: string,
      createdAt: ISO 8601 datetime
    }
  ],
  page: number,
  pageSize: number,
  total: number,
  nextPage: number | null
}
```

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid coordinates or radius |

**Notes**:
- Events scoped to specified radius
- Sorted by createdAt DESC (newest first)
- Tool names shown even if tool deleted (denormalized data)

---

## Business Rules

1. Users cannot follow themselves (enforced by database constraint and API validation).
2. A user can follow another user only once (unique constraint on follower_user_id + followed_user_id).
3. Unfollowing is idempotent - no error if already unfollowed, returns 204 No Content.
4. Following/follower lists are private - only the account owner can view them via API.
5. Search radius persists in session storage across page navigation within session, resets to 5 miles on new session.
6. Activity events are created only when tool status transitions to 'published' (not on draft creation).
7. Activity events for successful borrows created when borrow status becomes 'returned' (coordinated with FEAT-02).
8. Map pin availability validation occurs on every pin click before displaying popup.
9. Map tool data cached for 5 minutes per (latitude, longitude, radius) tuple.
10. Community statistics cached for 24 hours per (latitude, longitude, radius) tuple.
11. Tools in "My Network" view are not filtered by availability - all published tools from followed users shown with availability badges.
12. Distance calculations use Haversine formula with Earth radius 3,959 miles (not straight-line distance).
13. Radius selector accepts only discrete values: 1, 5, 10, or 25 miles (no arbitrary values).
14. Location accuracy warning shown only for 'postal_code' accuracy users selecting 1-mile radius.
15. Activity events include neighborhood name only (no city/state) for v1 single-metro scope.
16. Tool count in following/follower lists includes only published tools (not drafts or deleted).
17. Pagination applies to "Nearby Tools" and "My Network" views, but not map view (map shows all tools within radius).
18. Following a user does not trigger notification to the followed user (no social pressure).
19. Users may follow up to 500 users (soft limit enforced at API level, no database constraint).
20. Geographic queries use indexed PostGIS or spatial index for performance on large datasets.

---

## Validation Rules

| Field | Rule | Error message |
|-------|------|---------------|
| userId (follow/unfollow) | Must exist in users table | "User not found" |
| userId (follow) | Cannot equal authenticated user ID | "Cannot follow yourself" |
| latitude | Required, decimal, -90 to 90 | "Invalid latitude" |
| longitude | Required, decimal, -180 to 180 | "Invalid longitude" |
| radius | Required, one of [1, 5, 10, 25] | "Radius must be 1, 5, 10, or 25 miles" |
| page | Optional, integer, min 0 | "Page must be 0 or greater" |
| pageSize | Optional, integer, min 1, max varies by endpoint | "Page size must be between 1 and {max}" |
| search_radius_miles (User field) | One of [1, 5, 10, 25] | "Invalid search radius" |
| neighborhood (User field) | Required, max 50 chars | "Neighborhood is required" / "Neighborhood too long" |
| location_accuracy (User field) | One of ['precise', 'postal_code'] | "Invalid location accuracy value" |

---

## Authorization

| Action | Required policy | Notes |
|--------|----------------|-------|
| Follow user | Authenticated | Any logged-in user can follow any other user |
| Unfollow user | Authenticated | Any logged-in user can unfollow anyone |
| View following list | Owner | userId must match authenticated user |
| View followers list | Owner | userId must match authenticated user |
| Get nearby tools | None | Public endpoint |
| Get map tools | None | Public endpoint |
| Get tool availability | None | Public endpoint |
| Get network tools | Authenticated | Any logged-in user sees their own network |
| Get community stats | None | Public endpoint |
| Get activity feed | None | Public endpoint |

---

## Acceptance Criteria

- [ ] User can follow another user and see follower/following counts increment
- [ ] User cannot follow themselves - returns 400 Bad Request
- [ ] User cannot follow same user twice - returns 409 Conflict
- [ ] User can unfollow a user and see counts decrement
- [ ] Following/follower lists show username, neighborhood, tool count, and follow date
- [ ] Following/follower lists return 403 when requested by non-owner
- [ ] Nearby tools endpoint returns tools within specified radius sorted by distance
- [ ] Nearby tools endpoint paginates at 20 per page with "Load More" capability
- [ ] Map endpoint returns all tools within radius without pagination
- [ ] Map tool data cached for 5 minutes per coordinate/radius tuple
- [ ] Clicking map pin validates tool availability before showing popup
- [ ] Unavailable tool pin click shows toast notification, not popup
- [ ] Network tools view shows all published tools from followed users
- [ ] Network tools view includes availability badge (green "Available" or gray "Currently Borrowed")
- [ ] Network tools view paginated at 20 per page, sorted by publishedAt DESC
- [ ] Community stats show total tools, borrows, active users, and top 5 categories
- [ ] Community stats scoped to user's specified radius
- [ ] Community stats cached for 24 hours per coordinate/radius tuple
- [ ] Activity feed shows "new tool listed" events when tool status becomes 'published'
- [ ] Activity feed shows "successful borrow" events when borrow status becomes 'returned'
- [ ] Activity feed events display neighborhood name only (no city/state)
- [ ] Activity feed paginated at 20 per page with "Load More" button
- [ ] Activity feed sorted by createdAt DESC (newest first)
- [ ] Search radius selector allows only values: 1, 5, 10, 25 miles
- [ ] Search radius persists across page navigation within session
- [ ] Warning banner shown when 'postal_code' accuracy user selects 1-mile radius
- [ ] Warning banner includes link to settings page to update address
- [ ] Distance calculations use Haversine formula (not straight-line)
- [ ] Tool count in following/follower lists includes only published tools
- [ ] Following a user does not send notification to followed user
- [ ] Users can follow up to 500 users before receiving "Follow limit reached" error
- [ ] Empty state shown in network view: "Follow neighbors to see their tools here"
- [ ] Empty state shown in activity feed: "No recent activity in this area"
- [ ] Following/follower counts clickable on own profile, plain text on others' profiles

---

## Security Requirements

- Following/follower lists are private - enforce owner-only authorization at API level.
- Do not expose full user location coordinates in public API responses - use neighborhood names only.
- Rate limit follow/unfollow actions to 100 per user per hour to prevent spam/abuse.
- Rate limit nearby tools API to 60 requests per IP per minute to prevent scraping.
- Activity feed tool names denormalized at event creation to prevent information leakage via deleted tool lookups.
- Map endpoint returns only tool ID, name, category, coordinates, availability - no owner email or phone.
- Cache keys for stats and map data include coordinate hashes to prevent cache enumeration attacks.
- JWT tokens required for network tools endpoint - do not leak followed user relationships to unauthenticated users.
- Distance calculations performed server-side - do not trust client-provided distances.
- Validate radius parameter to prevent database performance issues from arbitrary large radius values.

---

## Out of Scope

- Notifications when someone follows you (deferred to future notification system)
- Block/mute user functionality (deferred to moderation feature)
- Following/follower list search or filtering (deferred to v2 if lists grow large)
- Export following/follower list to CSV (no current requirement)
- Mutual follow badges or "friends" designation (not in v1 social model)
- Activity feed filtering by event type (show all events in v1)
- Activity feed real-time updates via WebSockets (polling/refresh only in v1)
- Map clustering algorithm configuration (use default clustering with sensible thresholds)
- Geocoding address input to coordinates (handled by foundation signup flow)
- Reverse geocoding coordinates to neighborhood names (user provides neighborhood during signup)
- Multi-metro support - city/state fields in User table (v1 scoped to single metro)
- Custom neighborhood boundary definitions (use postal codes or user-provided names)
- Distance unit preference (miles only in v1 - no kilometers)
- Test plans (owned by QA spec)
- Implementation code (engineer's responsibility)