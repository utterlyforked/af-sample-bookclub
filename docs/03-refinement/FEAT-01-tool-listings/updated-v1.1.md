# Tool Listings - Feature Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification (2025-01-10)
- v1.1 - Iteration 1 clarifications (2025-01-10) - Added: editing policies, deletion behavior, location updates, privacy specifications, search sorting, photo management

---

## Feature Overview

Tool Listings is the foundational feature that allows users to catalog their tools and make them discoverable to neighbors. This feature creates the inventory that powers the entire ToolShare platform - without tools listed, there's nothing to borrow.

Tool owners photograph and describe their tools once, then make them available for community borrowing. Each listing includes essential details: what the tool is, its condition, any special usage notes, and current availability status. Borrowers can search this community inventory by category and location to find exactly what they need for their projects.

This feature sits at the heart of the user experience: it's the first thing new users do after signing up (list their first tool) and the primary way borrowers discover what's available in their neighborhood. The quality and completeness of tool listings directly impacts trust and successful matches between lenders and borrowers.

---

## User Stories

**Tool Owner Stories**:
- As a tool owner, I want to list my tools with photos and descriptions so that neighbors know what I have available
- As a tool owner, I want to mark items as available or currently borrowed so that people know what they can request
- As a tool owner, I want to edit my tool listings after creation so that I can update condition notes or photos
- As a tool owner, I want to delete tool listings so that I can remove tools I no longer want to share

**Borrower Stories**:
- As a borrower, I want to search for tools by category and location so that I can find what I need nearby
- As a borrower, I want to see tool details (brand, condition, usage notes) so that I can determine if it meets my project needs
- As a borrower, I want to see the owner's neighborhood and distance so that I can judge convenience without seeing their exact address
- As a borrower, I want to see photos of the actual tool so that I know its condition before requesting

---

## Acceptance Criteria (UPDATED v1.1)

- Users can create tool listings with: title (required, max 100 chars), category (required, from predefined list), description (required, max 2000 chars), photos (1-5 images, HEIC/JPEG/PNG/WebP), condition notes (optional, max 500 chars)
- Tool categories include exactly: Power Tools, Hand Tools, Gardening, Ladders & Access, Automotive, Specialty Equipment
- Users can set tool status to one of: "Available", "Currently Borrowed", "Temporarily Unavailable"
- Search interface provides filters: category (multi-select), distance radius (1, 5, 10, or 25 miles), availability status (show available only / show all)
- Search results display: tool photo thumbnail, title, category badge, **rounded distance** (e.g., "2.5 miles"), owner's first name + last initial, neighborhood name
- Search results are sorted by distance (nearest first), then creation date (newest first) for ties
- Tool detail page shows: all photos in gallery (reorderable by owner), full description, condition notes, usage guidelines, owner's profile summary, approximate distance, "Request to Borrow" button
- Tool listings display owner's first name and neighborhood designation, but never full address or last name
- Each tool has a unique, shareable URL (e.g., `/tools/abc123`)
- **Tool editing allowed at any time; tool details are cached in transaction records to preserve historical context**
- **Tool deletion creates snapshot in past transaction records; physical tool/photo records are hard deleted**
- **Distance displayed rounded to nearest 0.5 mile for privacy (prevents triangulation)**
- **Photo reordering supported in edit mode without re-uploading**

---

## Detailed Specifications (UPDATED v1.1)

### Tool Editing Policy

**Decision**: Users can edit tool listings at any time, including after the tool has been borrowed multiple times. There are no restrictions on editing.

**Rationale**: Tool conditions change over time - tools degrade, accessories get lost, usage notes need updates. Locking listings after first use would force users to delete and recreate listings, losing their borrow history and reviews. Instead, we preserve context by caching tool details in transaction records at the moment of each borrow.

**Implementation**:
- Edit button always available to tool owner (no lock checks)
- All fields editable: title, description, category, photos, condition notes, status
- When user saves edits, update `updated_at` timestamp
- Show "Last updated: [date]" on tool detail page if `updated_at > created_at + 1 hour` (grace period for initial corrections)
- If tool currently has status "Currently Borrowed", show warning banner: "⚠️ This tool is currently borrowed. Changes will be visible to the borrower and reflected in your listing immediately."

**Transaction Context Preservation**:
- When a borrow request is created (Feature 2), cache these fields in `BorrowRequest` table:
  - `tool_title_snapshot` (varchar 100)
  - `tool_description_snapshot` (text)
  - `tool_primary_photo_url_snapshot` (varchar 500)
  - `tool_category_snapshot` (varchar 50)
- These snapshots are immutable - never updated even if tool is edited later
- User's borrowing history displays the tool as it appeared when they borrowed it
- Reviews and ratings remain contextually accurate to the tool state at time of borrow

**Examples**:
- User lists "DeWalt Drill - Excellent condition, includes 2 batteries"
- Tool is borrowed, returned, rated 5 stars for "excellent condition as described"
- Six months later, one battery dies. Owner edits to "DeWalt Drill - Good condition, includes 1 battery (second battery no longer functional)"
- Future borrowers see the updated description
- Past borrower's transaction history still shows "includes 2 batteries" and their 5-star review makes sense in that context

**Edge Cases**:
- If owner changes category (Power Tool → Hand Tool), cached category in old transactions remains unchanged
- If primary photo changes, old transactions still reference the original photo URL (may 404 if deleted - see deletion policy)
- No audit log of changes in v1 (future enhancement: "View Edit History" link)

---

### Tool Deletion Policy

**Decision**: Physical deletion of Tool and ToolPhoto records from database, but transaction records preserve snapshots of deleted tools.

**Rationale**: Users should be able to fully remove tools they no longer want to share, without "soft delete" flags cluttering the database. However, borrowing history must remain intact for reputation/rating context. Solution: cache tool details in transactions, then allow true deletion.

**Deletion Rules**:

**If tool status is "Available" or "Temporarily Unavailable"**:
- Allow immediate deletion
- Show confirmation modal: 
  ```
  Delete [Tool Name]?
  
  This will permanently remove the listing and all its photos. 
  
  Your past borrow history will be preserved - borrowers who used 
  this tool can still see their transaction records, but the listing 
  will no longer be searchable or requestable.
  
  This action cannot be undone.
  
  [Cancel] [Delete Tool]
  ```
- On confirmation:
  1. DELETE all rows from `ToolPhoto` WHERE `tool_id = X`
  2. DELETE all photo blobs from Azure Storage (file deletion)
  3. DELETE row from `Tool` WHERE `id = X`
  4. Redirect to "My Tools" dashboard
  5. Show success toast: "Tool deleted successfully"

**If tool status is "Currently Borrowed"**:
- Prevent deletion entirely
- Show error modal:
  ```
  Cannot Delete While Borrowed
  
  [Tool Name] is currently borrowed by [Borrower First Name] 
  until [Return Date].
  
  You can delete this tool after it's been returned and marked 
  complete, or you can contact support if you need to remove it urgently.
  
  [Contact Support] [Close]
  ```
- DELETE button disabled/grayed in UI when status is "Currently Borrowed"

**Transaction Record Handling**:
- Past `BorrowRequest` records have `tool_id` as foreign key, but:
  - Foreign key set to `ON DELETE SET NULL` (not `CASCADE`)
  - When tool deleted, `tool_id` becomes `NULL` in past transactions
  - Display fields use cached snapshots: `tool_title_snapshot`, `tool_primary_photo_url_snapshot`
- User's borrowing history page shows:
  ```
  [Cached photo thumbnail]
  DeWalt Cordless Drill (no longer listed)
  Borrowed: Dec 1-5, 2024
  Rated: ⭐⭐⭐⭐⭐
  ```
- Link to `/tools/{id}` returns 404, UI handles gracefully with "(no longer listed)" indicator

**Profile Counter Behavior**:
- "Tools shared: 12 times" counter on user profile counts transactions, not current tool listings
- Deleting a tool does NOT decrement this counter
- Query: `SELECT COUNT(*) FROM BorrowRequest WHERE lender_id = X AND status = 'Completed'`

**Examples**:
- User lists drill, it's borrowed 5 times over a year, then user sells the drill and deletes listing
- Those 5 borrowers can still see "DeWalt Drill" in their history with cached photos/descriptions
- User's profile still shows "Tools shared: 5 times" (includes deleted tool)
- Drill no longer appears in search results or user's "My Tools" dashboard

**Database Implementation**:
```sql
-- Foreign key configuration
ALTER TABLE borrow_requests 
ADD CONSTRAINT fk_tool 
FOREIGN KEY (tool_id) 
REFERENCES tools(id) 
ON DELETE SET NULL;

-- Snapshot columns (added to borrow_requests table)
tool_title_snapshot VARCHAR(100) NOT NULL,
tool_description_snapshot TEXT,
tool_primary_photo_url_snapshot VARCHAR(500),
tool_category_snapshot VARCHAR(50) NOT NULL
```

---

### Location Update Behavior

**Decision**: Synchronous update of all tool locations when user changes profile address, with async fallback for users with 50+ tools.

**Rationale**: Most users will have <10 tools listed (expected pattern for home tool sharing). Synchronous update keeps the system simple and immediately consistent. For edge case power users with large inventories, async prevents UI blocking.

**Standard Flow (< 50 tools)**:
1. User saves new address in Profile Settings (Feature 3)
2. Backend geocodes new address to lat/long
3. Same database transaction:
   - UPDATE user profile with new address/coordinates
   - UPDATE all tools: `UPDATE tools SET location_lat = $1, location_lng = $2, updated_at = NOW() WHERE user_id = $3`
4. Profile save returns success
5. Next search results immediately reflect new distances

**SQL Example**:
```sql
BEGIN TRANSACTION;
  UPDATE users 
  SET address = '123 New St', 
      location_lat = 47.6062, 
      location_lng = -122.3321 
  WHERE id = 'user123';
  
  UPDATE tools 
  SET location_lat = 47.6062, 
      location_lng = -122.3321,
      updated_at = NOW()
  WHERE user_id = 'user123';
COMMIT;
```

**Performance**: Single UPDATE query, indexed on `user_id`, affects <50 rows typical - completes in <100ms.

**Power User Flow (≥ 50 tools)**:
1. User saves new address
2. Backend detects tool count: `SELECT COUNT(*) FROM tools WHERE user_id = X` ≥ 50
3. Show warning modal before save:
   ```
   Update Location for 73 Tools?
   
   You have 73 tools listed. Updating their locations may take 
   a moment. Your profile will save immediately, and tool locations 
   will update in the background.
   
   [Cancel] [Update Address]
   ```
4. On confirmation:
   - UPDATE user profile immediately, return success
   - Queue Hangfire background job: `UpdateToolLocationsJob(userId)`
   - Show toast: "Address updated. Tool locations are updating in the background (73 tools)."
5. Background job runs within ~30 seconds, updates all tools
6. During update window, search results may show old distances (acceptable brief inconsistency)

**Mid-Borrow Edge Case**:
- **Scenario**: User lists drill as "2 miles away", borrower requests it, then mid-borrow user moves 50 miles away
- **Behavior**: Tool location updates immediately, but borrow continues normally
  - Active BorrowRequest already has pickup/return arrangements made
  - Borrower sees tool location on detail page, but already has pickup scheduled
  - After return, future borrowers see new 50-mile distance
- **Acceptable Trade-off**: This is rare (user moving during active borrow) and doesn't break the transaction. Borrower already knows pickup location from messages/coordination. Document as known edge case, no special handling needed for v1.
- **Future Enhancement (v2)**: Cache pickup location in BorrowRequest at time of approval, show "Pickup was at: [old neighborhood]" in transaction history

**No User Action Required**:
- User does NOT manually update each tool listing
- Profile address is single source of truth for all tool locations
- "Edit Tool" page does not show location fields (automatically inherited)

---

### Distance Display & Privacy

**Decision**: Display distance rounded to nearest 0.5 mile, combined with real neighborhood name.

**Rationale**: Borrowers need enough precision to judge convenience ("Is it worth a 10-minute drive?") but exact distances enable triangulation attacks. Three searches from different locations could pinpoint owner's address within ~50 feet. Rounding to 0.5-mile increments provides useful proximity information while making triangulation impractical.

**Display Format**:
- **Search Results**: "2.5 miles away in Maplewood"
- **Tool Detail Page**: "Approximately 2.5 miles away in Maplewood"
- **Profile Page** (owner's tools list): No distance shown (unnecessary, it's your own stuff)

**Rounding Logic**:
```
Actual Distance → Displayed Distance
0.0 - 0.24 mi   → "Less than 0.5 miles"
0.25 - 0.74 mi  → "0.5 miles"
0.75 - 1.24 mi  → "1.0 mile"
1.25 - 1.74 mi  → "1.5 miles"
1.75 - 2.24 mi  → "2.0 miles"
2.25 - 2.74 mi  → "2.5 miles"
... and so on
```

**Backend Implementation**:
```csharp
public static string FormatDistance(double miles)
{
    if (miles < 0.25)
        return "Less than 0.5 miles";
    
    double rounded = Math.Round(miles * 2) / 2; // Round to nearest 0.5
    
    if (rounded == 1.0)
        return "1.0 mile"; // Singular
    
    return $"{rounded:F1} miles"; // e.g., "2.5 miles"
}
```

**Database Query**:
- Calculate exact distance in SQL using PostGIS:
  ```sql
  ST_Distance(
    ST_MakePoint(user_lng, user_lat)::geography,
    ST_MakePoint(tool_lng, tool_lat)::geography
  ) / 1609.34 AS distance_miles  -- Convert meters to miles
  ```
- Sort by exact `distance_miles` ASC
- Format for display in application layer (not SQL)

**Privacy Analysis**:

**With exact distance** (2.34 miles):
- Search from 3 locations → 3 circles intersect at precise point → owner's address compromised
- Effort: ~15 minutes of driving + mapping, feasible for motivated bad actor

**With 0.5-mile rounding** (2.5 miles):
- Search from 3 locations → 3 circles with ~0.5-mile radius variance → intersection area ~0.8 square miles
- Effort: Cannot pinpoint specific address, only general area already revealed by neighborhood
- Acceptable: Neighborhood name already narrows to ~1-2 square miles, distance rounding doesn't meaningfully add risk

**Neighborhood Name**:
- Display real neighborhood as entered in user profile (e.g., "Maplewood", "Downtown", "Capitol Hill")
- No obfuscation needed - neighborhood is public info user chose to share
- Provides important context for borrowers ("Is this in my neighborhood or across town?")

**Example Displays**:
```
[Search Results Card]
┌─────────────────────────────────────┐
│ [Photo]  DeWalt Cordless Drill      │
│          Power Tools                │
│          2.5 miles away in Maplewood│
│          John D. · Member since 2024│
└─────────────────────────────────────┘

[Tool Detail Page]
📍 Location: Approximately 2.5 miles away in Maplewood
   (Exact address shared after pickup is confirmed)
```

**Future Enhancement (v2)**:
- Option for users to hide neighborhood ("2.5 miles away in [City Name]") if they prefer more privacy
- User setting: "Privacy Level: Standard / Enhanced"

---

### Search Result Sorting

**Decision**: Primary sort by distance (nearest first), secondary sort by creation date (newest first).

**Rationale**: Distance is the most important factor for borrowers - nearby tools are more convenient. When multiple tools are equidistant (common in apartment buildings or same neighborhood), newest listings appear first. This gives recently added tools a small visibility boost and encourages active listing.

**Sort Order**:
1. **Distance** (ASC) - nearest to farthest (rounded for display, but sorted by exact distance)
2. **Created At** (DESC) - newest to oldest

**SQL Query Example**:
```sql
SELECT 
  t.id,
  t.title,
  t.category_id,
  ST_Distance(
    ST_MakePoint($user_lng, $user_lat)::geography,
    ST_MakePoint(t.location_lng, t.location_lat)::geography
  ) / 1609.34 AS distance_miles
FROM tools t
WHERE t.status = 'Available'
  AND ST_DWithin(
    ST_MakePoint(t.location_lng, t.location_lat)::geography,
    ST_MakePoint($user_lng, $user_lat)::geography,
    $radius_meters
  )
ORDER BY distance_miles ASC, t.created_at DESC
LIMIT 24 OFFSET $page_offset;
```

**Behavior Examples**:

**Scenario 1: Tools at different distances**
```
1. Ladder (0.3 miles) - created Jan 1
2. Drill (0.8 miles) - created Jan 15  
3. Saw (1.2 miles) - created Jan 10
→ Sort by distance only, creation date irrelevant
```

**Scenario 2: Tools equidistant (same building)**
```
All three tools are 0.5 miles away:
1. Drill (created Jan 15) ← newest first
2. Saw (created Jan 10)
3. Sander (created Jan 5) ← oldest last
```

**Scenario 3: Mixed distances with ties**
```
1. Ladder (0.3 miles, Jan 1)
2. Drill (0.5 miles, Jan 20) ← 0.5mi tie, newest
3. Saw (0.5 miles, Jan 10)   ← 0.5mi tie, older
4. Sander (1.0 miles, Jan 15)
```

**User-Controlled Sorting (Future v2)**:
- Add dropdown: "Sort by: Nearest (default) | Newest | Most Borrowed"
- For v1, fixed sorting is sufficient - keep it simple

**Performance**:
- `distance_miles` calculated in SQL, indexed query
- `created_at` indexed on tools table
- Compound index not needed (distance filter narrows result set to <1000 rows typical, sort is fast)

---

### Maximum Tools Per User

**Decision**: No hard limit enforced. Optimize UI and queries for <10 tools per typical user.

**Rationale**: The expected use case is homeowners sharing personal tool collections (5-15 tools typical). Enforcing an arbitrary cap (like 50) risks frustrating legitimate users (contractors, workshop owners, maker spaces) without solving any real problem. Instead, design for the common case and monitor actual usage.

**UI Implementation**:

**"My Tools" Dashboard (Owner View)**:
- Display all tools in a single paginated list (simple for small collections)
- Pagination: 20 tools per page (only adds pagination UI if user has >20)
- Each row shows: thumbnail, title, category, status toggle, edit/delete buttons
- No search/filter in v1 (add if users actually hit >50 tools)

**Example Layout**:
```
My Tools (8)                                    [+ List a Tool]

┌────────────────────────────────────────────────────────────┐
│ [Photo] DeWalt Drill           Available ▼   [Edit] [Delete]│
│ [Photo] Ladder 8ft             Available ▼   [Edit] [Delete]│
│ [Photo] Circular Saw           Borrowed      [Edit] [Delete]│
│ ... (5 more tools)                                           │
└────────────────────────────────────────────────────────────┘
```

**Query Performance**:
- `SELECT * FROM tools WHERE user_id = $1 ORDER BY created_at DESC LIMIT 20 OFFSET $offset`
- Indexed on `user_id`, fast even with 100+ tools
- No special optimization needed for v1

**Monitoring**:
- Track 95th percentile tool count per user in analytics
- Alert if median user has >15 tools (indicates different usage pattern than expected)
- If 95th percentile exceeds 50 tools, consider adding:
  - Search bar on "My Tools" page
  - Category filter dropdown
  - Bulk actions (e.g., "Mark all as Unavailable")

**Power User Considerations**:
- **Scenario**: Workshop with 200 tools
- **v1 Behavior**: All 200 load in paginated list (10 pages of 20)
- **Acceptable**: Rare edge case, pagination handles it, no performance issue
- **v2 Enhancement**: Add search/filter if this becomes common

**No Artificial Cap**:
- No validation error "Maximum 50 tools reached"
- No warning messages
- Keep it simple: users list what they want to share

---

### Photo Upload & HEIC Support

**Decision**: Accept HEIC format, convert server-side to JPEG before storage.

**Rationale**: iPhones default to HEIC format. Rejecting it creates massive friction - users don't know how to convert images, support requests spike, tool listings don't get created. Server-side conversion solves this transparently.

**Accepted Formats**:
- HEIC (Apple iPhone default)
- JPEG / JPG
- PNG
- WebP

**Upload Flow**:
1. User selects photos (file input or drag-and-drop)
2. Frontend validates file size: max 10MB per image
3. Frontend uploads to backend endpoint: `POST /api/v1/tools/photos`
4. Backend processes each image:
   - Detect format via magic bytes, not extension
   - If HEIC: convert to JPEG using ImageSharp + HEIC plugin
   - If JPEG/PNG/WebP: use as-is
   - Resize to max 1920px width (maintain aspect ratio)
   - Generate thumbnail at 400px width
   - Compress JPEG to quality 85
5. Upload both versions to Azure Blob Storage:
   - Full size: `tools/{toolId}/{photoId}.jpg`
   - Thumbnail: `tools/{toolId}/{photoId}_thumb.jpg`
6. Save URLs to database: `ToolPhoto` table with `image_url` and `thumbnail_url`
7. Return URLs to frontend for preview

**Backend Implementation** (C# example):
```csharp
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Formats.Jpeg;

public async Task<PhotoUploadResult> ProcessPhoto(IFormFile file)
{
    using var image = await Image.LoadAsync(file.OpenReadStream());
    
    // Resize full image if too large
    if (image.Width > 1920)
        image.Mutate(x => x.Resize(1920, 0));
    
    // Generate thumbnail
    var thumbnail = image.Clone(x => x.Resize(400, 0));
    
    // Save to blob storage
    var fullUrl = await SaveToBlob(image, JpegFormat);
    var thumbUrl = await SaveToBlob(thumbnail, JpegFormat);
    
    return new PhotoUploadResult(fullUrl, thumbUrl);
}
```

**HEIC Conversion**:
- Use `SixLabors.ImageSharp` with `ImageSharp.Formats.Heif` package
- Fallback: If HEIC decode fails, return error "Unable to process this image format. Please try converting to JPEG first."
- Processing time: ~1-3 seconds per HEIC image (acceptable, async upload)

**Alternate Option (if HEIC too complex)**:
- Use Cloudinary or ImageKit API for all image processing
- Pros: Handles HEIC, auto-optimization, CDN delivery
- Cons: External dependency, monthly cost ($25+/month)
- Decision: Try ImageSharp first (open source, no cost), fall back to service if HEIC proves unreliable

**Client-Side Validation**:
- Check file extension: `.heic, .jpg, .jpeg, .png, .webp`
- Check MIME type: `image/heic, image/jpeg, image/png, image/webp`
- Check file size: max 10MB
- Show upload progress bar (async upload, don't block UI)

**Error Handling**:
- Unsupported format: "This file format is not supported. Please upload JPEG, PNG, WebP, or HEIC images."
- File too large: "Image must be under 10MB. Yours is 14MB. Try compressing it first."
- HEIC conversion failed: "We couldn't process this HEIC image. Try converting it to JPEG using your Photos app."

---

### Photo Reordering in Edit Mode

**Decision**: Users can reorder existing photos in edit mode without re-uploading.

**Rationale**: Users make mistakes - they upload 3 photos and realize photo #3 should be the primary thumbnail. Forcing delete + re-upload is poor UX. Drag-to-reorder is a standard pattern, low implementation cost for high user satisfaction.

**Implementation**:

**Edit Tool Page - Photo Section**:
```
Photos (3 of 5)

┌─────────────────────────────────────────────────────┐
│ [1. Photo]  [2. Photo]  [3. Photo]   [+ Add Photo]  │
│   Primary    (drag to reorder)                      │
│  [Delete]    [Delete]    [Delete]                   │
└─────────────────────────────────────────────────────┘

Drag photos to reorder. The first photo is your primary thumbnail.
```

**Drag-and-Drop Behavior**:
- User grabs photo #3, drags left
- Drop between photo #1 and #2
- Order updates: [3, 1, 2]
- Display order numbers update: "1. Primary", "2.", "3."
- No save required yet - order persists on "Save Tool" click

**Database Schema**:
```sql
CREATE TABLE tool_photos (
  id UUID PRIMARY KEY,
  tool_id UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
  image_url VARCHAR(500) NOT NULL,
  thumbnail_url VARCHAR(500) NOT NULL,
  display_order INT NOT NULL,
  uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Index for ordering
CREATE INDEX idx_tool_photos_order 
ON tool_photos(tool_id, display_order);
```

**Save Behavior**:
- User clicks "Save Tool"
- Frontend sends updated `display_order` values:
  ```json
  {
    "toolId": "abc123",
    "photos": [
      { "id": "photo3", "displayOrder": 1 },
      { "id": "photo1", "displayOrder": 2 },
      { "id": "photo2", "displayOrder": 3 }
    ]
  }
  ```
- Backend updates: `UPDATE tool_photos SET display_order = $1 WHERE id = $2`
- Primary thumbnail (display_order = 1) updates in `tools` table: `UPDATE tools SET primary_photo_id = 'photo3'`

**Frontend Library**:
- Use `@dnd-kit/core` (React drag-and-drop)
- Lightweight, accessible, touch-friendly
- Example: https://docs.dndkit.com/presets/sortable

**Photo Deletion in Edit Mode**:
- Click "Delete" under photo
- Confirmation: "Delete this photo? It will be removed from the listing immediately."
- On confirm:
  - DELETE blob from Azure Storage
  - DELETE row from `tool_photos` table
  - Remaining photos shift up (display_order recalculated: 1, 2, 3...)
  - If deleted photo was primary (order 1), promote next photo to primary

**Edge Cases**:
- Deleting last photo: Prevent with validation "You must have at least 1 photo. Upload a new photo before deleting this one."
- Reordering + adding new photos: New photos append at end (max display_order + 1), then user can reorder all
- Reordering during upload: Disable drag-and-drop on photos with upload spinner (wait for upload to complete)

---

## Q&A History

### Iteration 1 - 2025-01-10

**Q1: Can users edit tool listings after they've been borrowed (even once)?**

**A**: Yes, unrestricted editing is allowed at any time. Tool details (title, description, photos, category) are cached in the `BorrowRequest` table at the moment each borrow is created. This preserves historical context for reviews and ratings while allowing owners to update their listings as tool conditions change. See "Tool Editing Policy" section above for implementation details.

---

**Q2: What happens when a user deletes a tool that has past completed borrows?**

**A**: Physical deletion (hard delete) of the `Tool` and `ToolPhoto` records occurs, but transaction records preserve snapshots. The `BorrowRequest.tool_id` foreign key is set to NULL, and cached fields (`tool_title_snapshot`, `tool_description_snapshot`, `tool_primary_photo_url_snapshot`) display in borrowing history. The user's "Tools shared" counter includes deleted tools since it counts transactions, not active listings. See "Tool Deletion Policy" section for full details.

---

**Q3: How do we handle tool location when user updates their profile address?**

**A**: Synchronous update for most users (<50 tools): profile save transaction includes updating all tool coordinates in the same database commit. For power users with 50+ tools, show a warning modal and queue an async background job. Tool locations always mirror the user's current profile address automatically - no manual tool-by-tool editing required. Mid-borrow location changes are acceptable edge cases (rare, doesn't break transaction). See "Location Update Behavior" section.

---

**Q4: What does "approximately 2.3 miles" mean for privacy?**

**A**: Distance is rounded to the nearest 0.5 mile for display (e.g., "2.5 miles") to prevent triangulation attacks. Exact distance is calculated and used for sorting, but the displayed value is fuzzy. Combined with real neighborhood name (which user chose to share), this provides sufficient proximity information for convenience judgments without enabling precise location discovery. See "Distance Display & Privacy" section.

---

**Q5: How do search results handle ties in distance sorting?**

**A**: Primary sort is distance (nearest first), secondary sort is creation date (newest first). When multiple tools are equidistant, recently listed tools appear higher. This gives new listings a small visibility boost and keeps the sort order predictable and consistent. See "Search Result Sorting" section.

---

**Q6: What's the expected maximum number of tools per user?**

**A**: No hard limit enforced. Expected typical user has <10 tools. "My Tools" dashboard designed as simple paginated list (20 per page). Monitor 95th percentile