# Tool Listings — Engineering Spec

**Type**: feature
**Component**: tool-listings
**Dependencies**: foundation-spec
**Status**: Ready for Implementation

---

## Overview

The Tool Listings feature enables users to create, manage, and search a catalog of shareable tools. Tool owners create listings with photos, descriptions, and metadata; borrowers search by category, location, and availability. This feature owns the `Tool`, `ToolPhoto`, and `ToolCategory` entities and their complete lifecycle (CRUD operations). It reads from Foundation entities (`User`, `Location`) but does not modify them. Search results use PostGIS spatial queries to calculate distance and respect privacy constraints by rounding distances and displaying only neighborhood-level location data.

---

## Data Model

### Tool

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| user_id | UUID | FK → User, not null | Owner of the tool |
| title | VARCHAR(100) | not null | Tool name/title |
| category_id | UUID | FK → ToolCategory, not null | Predefined category |
| description | TEXT | not null, max 2000 chars | Full tool description |
| condition_notes | VARCHAR(500) | nullable | Optional condition details |
| status | VARCHAR(30) | not null, default 'Available' | Enum: 'Available', 'Currently Borrowed', 'Temporarily Unavailable' |
| location_lat | DECIMAL(10, 8) | not null | Latitude (copied from User) |
| location_lng | DECIMAL(11, 8) | not null | Longitude (copied from User) |
| primary_photo_id | UUID | FK → ToolPhoto, nullable | First photo in display order |
| created_at | TIMESTAMP | not null, default NOW() | UTC timestamp |
| updated_at | TIMESTAMP | not null, default NOW() | UTC timestamp, updated on edit |

**Indexes**:
- `(user_id)` - for owner's tool list queries
- `(category_id)` - for category filtering
- `(status)` - for availability filtering
- `GIST (location_lng, location_lat)` - PostGIS spatial index for distance queries

**Relationships**:
- Belongs to `User` via `user_id` (ON DELETE CASCADE)
- Belongs to `ToolCategory` via `category_id` (ON DELETE RESTRICT)
- Has many `ToolPhoto` (cascade delete)
- Belongs to `ToolPhoto` via `primary_photo_id` (ON DELETE SET NULL)

**Constraints**:
- CHECK: `status IN ('Available', 'Currently Borrowed', 'Temporarily Unavailable')`
- CHECK: `length(description) <= 2000`
- CHECK: `length(condition_notes) <= 500`
- CHECK: `location_lat BETWEEN -90 AND 90`
- CHECK: `location_lng BETWEEN -180 AND 180`

---

### ToolPhoto

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| tool_id | UUID | FK → Tool, not null | Parent tool |
| image_url | VARCHAR(500) | not null | Full-size image blob URL |
| thumbnail_url | VARCHAR(500) | not null | 400px thumbnail blob URL |
| display_order | INT | not null | 1-based ordering (1 = primary) |
| uploaded_at | TIMESTAMP | not null, default NOW() | UTC timestamp |

**Indexes**:
- `(tool_id, display_order)` - for ordered photo retrieval

**Relationships**:
- Belongs to `Tool` via `tool_id` (ON DELETE CASCADE)

**Constraints**:
- CHECK: `display_order >= 1`
- UNIQUE: `(tool_id, display_order)` - no duplicate orders per tool

---

### ToolCategory

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| name | VARCHAR(50) | unique, not null | Category display name |
| slug | VARCHAR(50) | unique, not null | URL-safe identifier |
| display_order | INT | not null | Sort order in UI |

**Indexes**:
- `(slug)` unique
- `(display_order)` - for sorted category lists

**Seed Data** (immutable in v1):
```
Power Tools      | power-tools       | 1
Hand Tools       | hand-tools        | 2
Gardening        | gardening         | 3
Ladders & Access | ladders-access    | 4
Automotive       | automotive        | 5
Specialty Equipment | specialty-equipment | 6
```

**Relationships**:
- Has many `Tool` (restrict delete - cannot delete category with existing tools)

---

> **Note**: This spec owns only the entities listed above. Foundation entities (`User`, `Location`) are referenced by name and read via foreign keys, but not redefined or modified by this feature.

---

## API Endpoints

### POST /api/v1/tools

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated (any verified user)

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| title | string | yes | non-empty, max 100 chars |
| categoryId | UUID | yes | must exist in ToolCategory |
| description | string | yes | non-empty, max 2000 chars |
| conditionNotes | string | no | max 500 chars |
| photoIds | UUID[] | yes | 1-5 UUIDs, all must exist in temp photo storage |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Tool ID |
| title | string | |
| categoryId | UUID | |
| description | string | |
| conditionNotes | string | null if not provided |
| status | string | Always "Available" on creation |
| photos | Photo[] | Ordered array (displayOrder ASC) |
| createdAt | ISO 8601 datetime | UTC |
| updatedAt | ISO 8601 datetime | UTC |

**Photo object structure**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| imageUrl | string | Full-size blob URL |
| thumbnailUrl | string | 400px thumbnail URL |
| displayOrder | int | 1-based |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure (field-level errors returned) |
| 400 | Photo count < 1 or > 5 |
| 400 | One or more photoIds do not exist |
| 401 | Not authenticated |
| 404 | categoryId does not exist |

---

### POST /api/v1/tools/photos

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated (any verified user)

**Request body**: multipart/form-data
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| file | binary | yes | HEIC, JPEG, PNG, or WebP; max 10MB |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Temp photo ID (not yet linked to tool) |
| imageUrl | string | Full-size image URL |
| thumbnailUrl | string | 400px thumbnail URL |
| expiresAt | ISO 8601 datetime | 1 hour from upload (cleaned if not used) |

**Processing details**:
- HEIC files converted to JPEG server-side
- Images resized to max 1920px width (maintain aspect ratio)
- Thumbnails generated at 400px width
- JPEG compression quality 85
- Stored in blob storage: `tools/temp/{userId}/{photoId}.jpg`

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | File format not supported |
| 400 | File size exceeds 10MB |
| 401 | Not authenticated |
| 500 | Image processing failed (e.g., corrupted HEIC) |

---

### GET /api/v1/tools/{id}

**Auth**: Optional (public endpoint)
**Authorization**: None

**Path parameters**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Tool ID |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| title | string | |
| categoryId | UUID | |
| categoryName | string | Display name (e.g., "Power Tools") |
| description | string | |
| conditionNotes | string | null if empty |
| status | string | Enum value |
| photos | Photo[] | Ordered by displayOrder |
| owner | OwnerSummary | Owner details (privacy-filtered) |
| distance | string | null if viewer not authenticated; otherwise formatted (e.g., "2.5 miles") |
| createdAt | ISO 8601 datetime | |
| updatedAt | ISO 8601 datetime | |
| lastUpdatedNotice | string | null if updated_at <= created_at + 1 hour; otherwise "Last updated: [date]" |

**OwnerSummary object**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | User ID |
| firstName | string | From User entity |
| lastInitial | string | First char of lastName (e.g., "D.") |
| neighborhood | string | From User.neighborhood |
| memberSince | ISO 8601 date | User.created_at (year + month) |
| profilePhotoUrl | string | null if not set |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 404 | Tool ID does not exist or tool deleted |

---

### PUT /api/v1/tools/{id}

**Auth**: Required (Bearer JWT)
**Authorization**: ToolOwner (must be tool.user_id)

**Path parameters**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Tool ID |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| title | string | yes | non-empty, max 100 chars |
| categoryId | UUID | yes | must exist in ToolCategory |
| description | string | yes | non-empty, max 2000 chars |
| conditionNotes | string | no | max 500 chars |
| status | string | yes | Enum: 'Available', 'Currently Borrowed', 'Temporarily Unavailable' |
| photos | PhotoUpdate[] | yes | 1-5 items, ordered by displayOrder |

**PhotoUpdate object**:
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | yes | Must be existing ToolPhoto.id for this tool |
| displayOrder | int | yes | 1-based, must be unique within array |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| title | string | Updated value |
| categoryId | UUID | |
| description | string | |
| conditionNotes | string | |
| status | string | |
| photos | Photo[] | Ordered by new displayOrder |
| updatedAt | ISO 8601 datetime | Updated timestamp |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure |
| 400 | Photo count < 1 or > 5 |
| 400 | Duplicate displayOrder values |
| 400 | photoId does not belong to this tool |
| 401 | Not authenticated |
| 403 | User is not tool owner |
| 404 | Tool ID does not exist |

---

### DELETE /api/v1/tools/{id}

**Auth**: Required (Bearer JWT)
**Authorization**: ToolOwner (must be tool.user_id)

**Path parameters**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Tool ID |

**Success response** `204 No Content`

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Tool status is 'Currently Borrowed' (cannot delete while borrowed) |
| 401 | Not authenticated |
| 403 | User is not tool owner |
| 404 | Tool ID does not exist |

**Side effects**:
- All `ToolPhoto` records CASCADE deleted
- All photo blobs deleted from Azure Storage (image_url and thumbnail_url)
- `BorrowRequest.tool_id` set to NULL where tool_id = {id} (preserves transaction history via snapshots)

---

### GET /api/v1/tools

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated (any verified user)

**Query parameters**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| categoryId | UUID[] | no | Comma-separated; each must exist in ToolCategory |
| radius | int | no | Enum: 1, 5, 10, 25 (miles); default 10 |
| availableOnly | boolean | no | Default true; false shows all statuses |
| page | int | no | Default 1; min 1 |
| pageSize | int | no | Default 24; min 1, max 100 |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| items | ToolSearchResult[] | Ordered by distance ASC, created_at DESC |
| totalCount | int | Total matching tools (for pagination) |
| page | int | Current page |
| pageSize | int | Items per page |

**ToolSearchResult object**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| title | string | |
| categoryName | string | Display name |
| thumbnailUrl | string | Primary photo thumbnail |
| distance | string | Formatted rounded distance (e.g., "2.5 miles") |
| ownerFirstName | string | |
| ownerLastInitial | string | |
| ownerNeighborhood | string | |
| status | string | Only included if availableOnly=false |

**Distance calculation**:
- Uses authenticated user's location (User.location_lat, User.location_lng)
- PostGIS query: `ST_Distance(user_point::geography, tool_point::geography) / 1609.34 AS distance_miles`
- Filtered by radius: `ST_DWithin(tool_point::geography, user_point::geography, radius_meters)`
- Displayed rounded to nearest 0.5 mile (see Business Rules #6)

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid radius value (not 1, 5, 10, or 25) |
| 400 | Invalid categoryId (one or more do not exist) |
| 401 | Not authenticated |

---

### GET /api/v1/users/{userId}/tools

**Auth**: Optional (public endpoint)
**Authorization**: None

**Path parameters**:
| Field | Type | Notes |
|-------|------|-------|
| userId | UUID | User ID |

**Query parameters**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| page | int | no | Default 1; min 1 |
| pageSize | int | no | Default 20; min 1, max 100 |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| items | ToolListItem[] | Ordered by created_at DESC |
| totalCount | int | Total tools for this user |
| page | int | |
| pageSize | int | |

**ToolListItem object**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| title | string | |
| categoryName | string | |
| thumbnailUrl | string | Primary photo thumbnail |
| status | string | Enum value |
| createdAt | ISO 8601 datetime | |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 404 | User ID does not exist |

---

### PATCH /api/v1/tools/{id}/photos/{photoId}

**Auth**: Required (Bearer JWT)
**Authorization**: ToolOwner (must be tool.user_id)

**Path parameters**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Tool ID |
| photoId | UUID | Photo ID to delete |

**Success response** `204 No Content`

**Side effects**:
- Photo blob deleted from Azure Storage (image_url and thumbnail_url)
- ToolPhoto record deleted
- Remaining photos' displayOrder recalculated to fill gap (1, 2, 3...)
- If deleted photo was primary (display_order = 1), next photo promoted to primary (Tool.primary_photo_id updated)

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Cannot delete last photo (must have at least 1) |
| 401 | Not authenticated |
| 403 | User is not tool owner |
| 404 | Tool ID or photo ID does not exist |
| 404 | Photo does not belong to this tool |

---

## Business Rules

1. **Email normalization**: Email addresses are normalized to lowercase before storage and lookup (Foundation rule, inherited).
2. **Photo requirements**: Every tool must have between 1 and 5 photos at all times; the first photo (display_order = 1) is the primary thumbnail.
3. **Status transitions**: Tool status may be changed freely by owner except: status may not be set to 'Currently Borrowed' manually (only set by borrow transaction system in Feature 2); status may not be changed from 'Currently Borrowed' until borrow is marked complete.
4. **Location synchronization**: Tool location coordinates (location_lat, location_lng) always match the owner's User.location_lat and User.location_lng; when user updates profile address, all owned tools update synchronously if user has <50 tools, or via background job if ≥50 tools.
5. **Category immutability**: ToolCategory seed data is immutable in v1; categories cannot be added, renamed, or deleted via API.
6. **Distance rounding**: Distance displayed to users is rounded to nearest 0.5 mile to prevent triangulation attacks; exact distance is used internally for sorting and filtering.
7. **Editing policy**: Users may edit tool listings at any time without restriction; updated_at timestamp is updated on every edit; if updated_at > created_at + 1 hour, "Last updated: [date]" notice is displayed.
8. **Deletion restrictions**: Tools with status 'Currently Borrowed' may not be deleted; deletion must wait until borrow is marked complete and status changed.
9. **Transaction history preservation**: When tool is deleted, BorrowRequest.tool_id is set to NULL but cached snapshot fields (tool_title_snapshot, tool_description_snapshot, tool_primary_photo_url_snapshot, tool_category_snapshot) preserve transaction history.
10. **Photo expiration**: Temporary photos uploaded via POST /api/v1/tools/photos expire after 1 hour if not linked to a tool; expired photos are cleaned by background job.

---

## Validation Rules

| Field | Rule | Error message |
|-------|------|---------------|
| title | Required, max 100 chars | "Title is required" / "Title must be 100 characters or less" |
| categoryId | Required, must exist in ToolCategory | "Category is required" / "Invalid category" |
| description | Required, max 2000 chars | "Description is required" / "Description must be 2000 characters or less" |
| conditionNotes | Max 500 chars | "Condition notes must be 500 characters or less" |
| photoIds | Required, 1-5 items, all must exist | "At least 1 photo is required" / "Maximum 5 photos allowed" / "One or more photos not found" |
| file (upload) | HEIC, JPEG, PNG, or WebP; max 10MB | "File format not supported. Use HEIC, JPEG, PNG, or WebP" / "File size must be under 10MB" |
| status | Enum: 'Available', 'Currently Borrowed', 'Temporarily Unavailable' | "Invalid status value" |
| photos (update) | 1-5 items, unique displayOrder values | "At least 1 photo is required" / "Maximum 5 photos" / "Duplicate display order values" |
| radius | Enum: 1, 5, 10, 25 | "Radius must be 1, 5, 10, or 25 miles" |
| page | Min 1 | "Page must be at least 1" |
| pageSize | Min 1, max 100 | "Page size must be between 1 and 100" |

---

## Authorization

| Action | Required policy | Notes |
|--------|----------------|-------|
| Create tool listing | Authenticated | Any verified user |
| Upload photo | Authenticated | Any verified user; photo not yet linked to tool |
| View tool detail | None (public) | Distance only shown to authenticated users |
| Search tools | Authenticated | Requires user location for distance calculation |
| Edit tool listing | ToolOwner | Must be tool.user_id |
| Delete tool listing | ToolOwner | Must be tool.user_id; blocked if status = 'Currently Borrowed' |
| Delete photo | ToolOwner | Must be tool.user_id |
| View user's tools | None (public) | Public profile page |

**ToolOwner policy implementation**:
```csharp
public class ToolOwnerRequirement : IAuthorizationRequirement { }

public class ToolOwnerHandler : AuthorizationHandler<ToolOwnerRequirement, Tool>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        ToolOwnerRequirement requirement,
        Tool tool)
    {
        var userId = context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        if (userId == tool.UserId.ToString())
            context.Succeed(requirement);
        
        return Task.CompletedTask;
    }
}
```

---

## Acceptance Criteria

- [ ] User can create tool listing with 1-5 photos, title, category, description, and optional condition notes
- [ ] Tool categories are exactly: Power Tools, Hand Tools, Gardening, Ladders & Access, Automotive, Specialty Equipment
- [ ] HEIC photos are accepted and converted to JPEG server-side without user intervention
- [ ] Photo upload resizes images to max 1920px width and generates 400px thumbnails
- [ ] Tool status defaults to "Available" on creation
- [ ] User can edit tool listing at any time, updating title, description, photos, status, or condition notes
- [ ] Editing a tool updates updated_at timestamp; if edited >1 hour after creation, "Last updated: [date]" is displayed
- [ ] User can reorder photos via drag-and-drop in edit mode; first photo becomes primary thumbnail
- [ ] User can delete individual photos; remaining photos shift up in display_order; last photo cannot be deleted
- [ ] User can delete tool listing if status is not "Currently Borrowed"
- [ ] Attempting to delete tool with status "Currently Borrowed" returns 400 error with message "Cannot delete while borrowed"
- [ ] Deleted tools hard-delete Tool and ToolPhoto records; photo blobs are removed from storage
- [ ] Deleted tools set BorrowRequest.tool_id to NULL but preserve cached snapshot fields for transaction history
- [ ] Search returns tools within specified radius (1, 5, 10, or 25 miles) of authenticated user's location
- [ ] Search filters by category (multi-select) and availability status (available only / show all)
- [ ] Search results sorted by distance (nearest first), then creation date (newest first) for ties
- [ ] Distance displayed rounded to nearest 0.5 mile (e.g., "Less than 0.5 miles", "2.5 miles")
- [ ] Distance calculated using PostGIS ST_Distance on geography type
- [ ] Search results show: thumbnail, title, category badge, rounded distance, owner first name + last initial, neighborhood
- [ ] Tool detail page shows: all photos in gallery, full description, condition notes, owner summary, approximate distance, "Request to Borrow" button (if authenticated)
- [ ] Tool detail page displays owner's first name, last initial, and neighborhood; never full address or last name
- [ ] Each tool has unique URL: /tools/{id}
- [ ] User's tools list (profile page) shows all tools paginated at 20 per page, ordered by created_at DESC
- [ ] User can view any public user's tool listings via /users/{userId}/tools
- [ ] When user updates profile address, all tools (<50) update location_lat/location_lng synchronously in same transaction
- [ ] When user with ≥50 tools updates address, warning modal is shown; tools update via background job
- [ ] Temporary uploaded photos expire after 1 hour if not linked to a tool
- [ ] Unauthenticated users can view tool details but do not see distance information
- [ ] Authenticated users without location set cannot use search (returns error prompting to complete profile)

---

## Security Requirements

### Image Upload Security

- **File type validation**: Use magic byte detection (not just file extension) to verify image format; reject files with mismatched MIME types.
- **File size limits**: Enforce 10MB maximum per image to prevent DoS via large file uploads.
- **HEIC processing isolation**: Run ImageSharp HEIC conversion in try-catch with timeout (5 seconds); if conversion fails, return safe error message without exposing server details.
- **Blob storage permissions**: Use SAS tokens with 1-hour expiration for uploaded images; tokens scoped to container only, not account-level.
- **Image metadata stripping**: Strip EXIF metadata during processing to remove GPS coordinates, camera info, and other sensitive data.

### Location Privacy

- **Distance rounding**: Always round displayed distance to nearest 0.5 mile; never expose exact coordinates or unrounded distance to frontend.
- **Neighborhood display**: Show user-provided neighborhood string only; do not reverse-geocode coordinates to derive addresses.
- **Search radius limits**: Cap maximum search radius at 25 miles to prevent nationwide reconnaissance.
- **Rate limiting**: Limit search endpoint to 100 requests per user per hour to prevent scraping.

### Authorization

- **Tool ownership verification**: Verify tool.user_id matches authenticated user ID before allowing edit/delete operations; do not rely on client-side checks.
- **JWT validation**: Require valid JWT on all authenticated endpoints; reject expired tokens (24-hour expiration per Foundation spec).
- **Photo ownership**: Verify uploaded photoIds belong to requesting user before linking to tool (prevent linking other users' photos).

### Input Validation

- **SQL injection prevention**: Use parameterized queries exclusively; Entity Framework Core handles this by default, but verify raw SQL queries are never constructed via string concatenation.
- **XSS prevention**: HTML-encode all user-provided text (title, description, condition_notes) before rendering in frontend; use React's default escaping.
- **Path traversal prevention**: Validate blob storage paths do not allow directory traversal (e.g., reject filenames containing `../`).

---

## Out of Scope

- Test plans (owned by QA spec)
- Implementation code (C#, TypeScript, SQL migrations, Entity Framework configurations)
- UI design mockups and wireframes (owned by product team)
- Infrastructure setup (Docker, Kubernetes, Azure configuration)
- Category management API (categories are seed data only in v1; admin UI for categories is future enhancement)
- Bulk tool import (e.g., CSV upload of tool inventory)
- Tool availability calendar (scheduling future unavailability dates)
- Favorite/bookmark tools feature
- Tool request notifications (email/push when specific tool becomes available)
- Audit log of tool edits (tracking who changed what and when)
- "View Edit History" feature for tools
- Advanced search filters (brand, condition rating, price, etc.)
- User setting for location privacy level (Standard/Enhanced mode)
- Tool views/popularity metrics
- Recommended tools based on search history
- Integration with external tool databases or catalogs
- Mobile app native implementations (this spec targets web API only)