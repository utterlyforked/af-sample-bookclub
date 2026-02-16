# Tool Listings - Technical Review (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: 2025-01-10

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. All critical questions from Iteration 1 have been answered with clear, specific policies. The PRD now includes comprehensive guidance on editing, deletion, location updates, privacy, sorting, and photo management.

## What's Clear

### Data Model

**Tools Table**:
- `id` (UUID, PK)
- `user_id` (UUID, FK to users, indexed)
- `title` (VARCHAR 100, required)
- `category_id` (VARCHAR 50, required, from predefined list: Power Tools, Hand Tools, Gardening, Ladders & Access, Automotive, Specialty Equipment)
- `description` (TEXT 2000, required)
- `condition_notes` (VARCHAR 500, optional)
- `status` (ENUM: Available, Currently Borrowed, Temporarily Unavailable)
- `location_lat` (DECIMAL, mirrors user profile)
- `location_lng` (DECIMAL, mirrors user profile)
- `primary_photo_id` (UUID, FK to tool_photos)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**ToolPhotos Table**:
- `id` (UUID, PK)
- `tool_id` (UUID, FK to tools ON DELETE CASCADE)
- `image_url` (VARCHAR 500, full-size image)
- `thumbnail_url` (VARCHAR 400px width thumbnail)
- `display_order` (INT, determines primary photo and gallery order)
- `uploaded_at` (TIMESTAMP)
- Index: `(tool_id, display_order)`

**BorrowRequests Table (snapshot fields for Feature 2)**:
- `tool_id` (UUID, FK to tools ON DELETE SET NULL)
- `tool_title_snapshot` (VARCHAR 100)
- `tool_description_snapshot` (TEXT)
- `tool_primary_photo_url_snapshot` (VARCHAR 500)
- `tool_category_snapshot` (VARCHAR 50)

### Business Logic

**Tool Editing**:
- Unrestricted editing at any time (no lock checks)
- All fields editable: title, description, category, photos, condition notes, status
- Show warning banner if editing while status = "Currently Borrowed"
- Display "Last updated: [date]" if `updated_at > created_at + 1 hour`
- Updates do NOT affect past transaction snapshots

**Tool Deletion**:
- **Allowed**: If status = Available or Temporarily Unavailable
- **Blocked**: If status = Currently Borrowed (show error modal)
- Confirmation modal required before deletion
- Physical deletion: DELETE from `tools` and `tool_photos`, DELETE blobs from Azure Storage
- Foreign key: `borrow_requests.tool_id` SET NULL (not CASCADE)
- Past transactions preserve snapshots, display "(no longer listed)" indicator
- Profile counter ("Tools shared: X times") counts transactions, not current listings

**Location Updates**:
- Synchronous update for users with <50 tools (single transaction)
- Async background job for users with ≥50 tools (show warning modal)
- SQL: `UPDATE tools SET location_lat = $1, location_lng = $2 WHERE user_id = $3`
- Profile address is single source of truth (no manual tool location editing)
- Mid-borrow location changes are acceptable edge case (no special handling in v1)

**Photo Management**:
- Accept formats: HEIC, JPEG, PNG, WebP (max 10MB per image)
- Server-side HEIC conversion to JPEG using ImageSharp
- Resize: max 1920px width full-size, 400px width thumbnail
- JPEG quality 85 compression
- Storage: Azure Blob Storage at `tools/{toolId}/{photoId}.jpg`
- Drag-and-drop reordering in edit mode (updates `display_order`)
- Minimum 1 photo required, maximum 5 photos per tool
- Photo deletion removes blob and database record, shifts remaining photos

### API Design

**Endpoints** (following `/api/v1/` prefix):

**POST /api/v1/tools**
- Request: `{ title, categoryId, description, conditionNotes?, status, photoIds[] }`
- Response: `{ id, title, category, status, primaryPhotoUrl, createdAt }`
- Authorization: Authenticated users only

**GET /api/v1/tools/search**
- Query params: `?category[]=Power+Tools&radius=5&lat=47.6062&lng=-122.3321&availableOnly=true&page=1`
- Response: `{ tools: [], totalCount, page, pageSize }`
- Sort: distance ASC, created_at DESC
- Distance calculated via PostGIS, rounded to 0.5 mile for display

**GET /api/v1/tools/:id**
- Response: `{ id, title, category, description, conditionNotes, photos: [{url, thumbnailUrl, displayOrder}], owner: {firstName, lastInitial, neighborhood}, approximateDistance, status, createdAt, updatedAt }`
- Authorization: Public (any user)

**PUT /api/v1/tools/:id**
- Request: `{ title?, description?, categoryId?, conditionNotes?, status?, photos: [{id, displayOrder}]? }`
- Response: `{ id, updatedAt }`
- Authorization: Owner only
- Validation: Block if `updated_at` mismatch (optimistic concurrency)

**DELETE /api/v1/tools/:id**
- Response: 204 No Content
- Authorization: Owner only
- Validation: Block if status = "Currently Borrowed"

**POST /api/v1/tools/photos**
- Request: multipart/form-data with image file
- Response: `{ id, imageUrl, thumbnailUrl }`
- Processing: HEIC conversion, resize, compress, upload to blob storage
- Authorization: Authenticated users only

**DELETE /api/v1/tools/photos/:id**
- Response: 204 No Content
- Authorization: Owner of parent tool only
- Side effect: DELETE blob from storage

### UI/UX

**Tool Listing Form**:
- Required fields: title (100 char limit), category (dropdown), description (2000 char limit), 1-5 photos
- Optional fields: condition notes (500 char limit)
- Default status: "Available"
- Photo upload: drag-and-drop zone, file input fallback, progress bars
- HEIC support: transparent server-side conversion, error handling for unsupported formats
- Validation: real-time character count, file size check (max 10MB), format check

**Search Interface**:
- Filters: category (multi-select checkboxes), distance radius (1/5/10/25 miles radio buttons), availability (checkbox "Show available only")
- Results display: thumbnail, title, category badge, "X.X miles away in [Neighborhood]", owner "FirstName L.", "Request to Borrow" button
- Pagination: 24 results per page
- Empty state: "No tools found. Try expanding your search radius or removing filters."

**Tool Detail Page**:
- Photo gallery: primary photo large, thumbnails below (click to expand)
- Metadata: category, condition notes, description, "Last updated: [date]" if edited
- Location: "Approximately X.X miles away in [Neighborhood]"
- Owner profile: avatar, "FirstName L.", "Member since [year]", "Tools shared: X times"
- Action: "Request to Borrow" button (if Available), "Currently Borrowed" banner (if borrowed)
- Shareable URL: `/tools/{uuid}`

**Edit Tool Page** (owner only):
- All fields editable in-place
- Photo section: existing photos with drag handles, delete buttons, "+ Add Photo" button
- Reorder via drag-and-drop (no re-upload)
- Warning banner if status = "Currently Borrowed": "⚠️ This tool is currently borrowed. Changes will be visible immediately."
- Save button: "Save Changes"

**My Tools Dashboard** (owner view):
- List view: thumbnail, title, category, status dropdown (inline toggle), "Edit" and "Delete" buttons
- Pagination: 20 per page
- No distance shown (own tools)
- Empty state: "You haven't listed any tools yet. [+ List Your First Tool]"

**Delete Confirmation Modal**:
- If Available/Unavailable: "Delete [Tool Name]? This will permanently remove the listing and all photos. Past borrow history will be preserved. This action cannot be undone. [Cancel] [Delete Tool]"
- If Currently Borrowed: "Cannot Delete While Borrowed. [Tool Name] is currently borrowed by [FirstName] until [ReturnDate]. [Contact Support] [Close]"

### Edge Cases

**Editing while borrowed**:
- Allow editing (show warning banner)
- Changes visible immediately to borrower
- Snapshots in BorrowRequest preserve original state for history

**Deleting tool with past borrows**:
- Tool record deleted, tool_id SET NULL in past transactions
- Borrowing history shows "(no longer listed)" with cached snapshots
- Profile counter unchanged (counts transactions, not active tools)

**User moves during active borrow**:
- Tool location updates immediately
- Active borrow continues normally (pickup already coordinated)
- Future searches show new distance
- Document as known edge case (no special handling in v1)

**HEIC conversion failure**:
- Show error: "We couldn't process this HEIC image. Try converting it to JPEG using your Photos app."
- Allow retry or alternative file upload

**Photo reordering + deletion**:
- Remaining photos shift display_order (gaps removed)
- If primary photo deleted, promote next photo (display_order = 1)
- Prevent deleting last photo (validation error)

**Distance ties in search**:
- Secondary sort by created_at DESC (newest first)
- Consistent, predictable ordering

**Power user with 50+ tools**:
- Location update shows warning modal, runs async background job
- "My Tools" dashboard paginated (20 per page)
- No search/filter in v1 (add if usage patterns warrant)

### Authorization

**Create Tool**:
- Authenticated users only
- Must have verified profile address (location required for search)

**Edit Tool**:
- Owner only (`tool.user_id == current_user.id`)
- No restrictions on what can be edited or when

**Delete Tool**:
- Owner only
- Block if status = "Currently Borrowed"

**View Tool Detail**:
- Public (any authenticated user)
- Show "Request to Borrow" only if viewer ≠ owner

**Upload Photo**:
- Authenticated users only
- Photos orphaned if tool creation abandoned (cleanup job: delete photos >24 hours old with no tool_id)

### Validation

**Tool Creation**:
- Title: required, max 100 chars
- Category: required, must match predefined list (validate against enum)
- Description: required, max 2000 chars
- Condition notes: optional, max 500 chars
- Photos: minimum 1, maximum 5
- Status: defaults to "Available"
- Location: inherited from user profile (must exist)

**Photo Upload**:
- File size: max 10MB
- Format: HEIC, JPEG, PNG, WebP only (check MIME type and magic bytes)
- Image dimensions: no minimum, max 1920px width after resize
- Virus scan: optional (recommend ClamAV integration for production)

**Tool Editing**:
- Same validation as creation
- Optimistic concurrency: check `updated_at` matches (409 Conflict if stale)

**Tool Deletion**:
- Status must NOT be "Currently Borrowed" (422 Unprocessable Entity)

**Search**:
- Radius: 1, 5, 10, or 25 miles (400 Bad Request if invalid)
- Latitude: -90 to 90, Longitude: -180 to 180
- Category: must match predefined list (ignore invalid)
- Page: minimum 1 (default 1)

---

## Implementation Notes

### Database

**Tables**:
- `tools` with columns as specified above
- `tool_photos` with `ON DELETE CASCADE` to tools, indexed on `(tool_id, display_order)`
- `borrow_requests` (Feature 2) with snapshot columns, `tool_id ON DELETE SET NULL`

**Indexes**:
- `tools(user_id)` for "My Tools" dashboard queries
- `tools(status)` for availability filtering
- `tools(created_at)` for secondary sort
- PostGIS spatial index on `tools(location_lat, location_lng)` for distance queries
- `tool_photos(tool_id, display_order)` for gallery ordering

**Constraints**:
- `tools.status` CHECK IN ('Available', 'Currently Borrowed', 'Temporarily Unavailable')
- `tools.category_id` CHECK IN (list of 6 categories)
- `tool_photos.display_order` UNIQUE per tool_id (prevent duplicates)

### Authorization

**Policy-based authorization** (ASP.NET Core):
- `IsToolOwner` policy: check `tool.user_id == current_user.id`
- `IsAuthenticated` policy: JWT token valid
- Apply policies at controller action level

### Validation

**FluentValidation** for request DTOs:
- `CreateToolRequestValidator`: title/category/description required, length checks, photo count 1-5
- `UpdateToolRequestValidator`: same as create, all fields optional
- `SearchToolsRequestValidator`: radius enum check, lat/lng range check

### Key Decisions

**Distance Privacy**:
- Round to 0.5 mile for display (prevent triangulation)
- Sort by exact distance (precision needed for correct ordering)
- Display format: "Approximately X.X miles away in [Neighborhood]"

**Editing Policy**:
- Unrestricted editing preserves UX flexibility
- Snapshots preserve historical accuracy for reviews
- No version tracking in v1 (future enhancement)

**Deletion Policy**:
- Hard delete (not soft delete) keeps database clean
- Snapshot preservation maintains transaction history
- Block deletion during active borrow (reasonable constraint)

**Photo Handling**:
- Server-side HEIC conversion removes user friction (iPhones default to HEIC)
- ImageSharp library (open source, no recurring cost)
- Fallback: error message if conversion fails (acceptable for v1)

**Location Updates**:
- Synchronous for typical users (<50 tools) keeps system simple
- Async for power users prevents UI blocking
- Single source of truth (profile address) avoids desync issues

**Search Sorting**:
- Distance primary (most important to borrowers)
- Creation date secondary (small boost for new listings)
- No user-configurable sorting in v1 (keep simple)

---

## Recommended Next Steps

1. **Create engineering specification** with:
   - Database migration scripts (EF Core)
   - Service layer interfaces (`IToolService`, `IPhotoService`)
   - Controller endpoints with request/response DTOs
   - Background job definitions (Hangfire: `UpdateToolLocationsJob`)
   - Azure Blob Storage configuration

2. **Set up PostGIS extension** in PostgreSQL:
   - `CREATE EXTENSION postgis;`
   - Spatial index on tools table
   - Distance calculation functions

3. **Configure ImageSharp** with HEIC support:
   - NuGet: `SixLabors.ImageSharp` + `ImageSharp.Formats.Heif`
   - Resize/compression pipeline
   - Error handling for unsupported formats

4. **Implement snapshot preservation** for borrow requests:
   - Add snapshot columns to BorrowRequests table
   - Populate on request creation (Feature 2 integration point)

5. **Build frontend components**:
   - Tool listing form with photo upload
   - Search interface with filters
   - Tool detail page with gallery
   - Edit mode with drag-and-drop reordering
   - My Tools dashboard with pagination

6. **Write tests**:
   - Unit tests: distance calculation, rounding logic, snapshot population
   - Integration tests: CRUD operations, photo upload/conversion, search queries
   - E2E tests: full listing creation flow, edit flow, deletion flow

---

**This feature is ready for detailed engineering specification and implementation.**