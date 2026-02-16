# Tool Listings - Feature Requirements

**Version**: 1.0  
**Date**: 2025-01-10  
**Status**: Initial - Awaiting Tech Lead Review

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

## Acceptance Criteria

- Users can create tool listings with: title (required, max 100 chars), category (required, from predefined list), description (required, max 2000 chars), photos (1-5 images), condition notes (optional, max 500 chars)
- Tool categories include exactly: Power Tools, Hand Tools, Gardening, Ladders & Access, Automotive, Specialty Equipment
- Users can set tool status to one of: "Available", "Currently Borrowed", "Temporarily Unavailable"
- Search interface provides filters: category (multi-select), distance radius (1, 5, 10, or 25 miles), availability status (show available only / show all)
- Search results display: tool photo thumbnail, title, category badge, distance (e.g., "2.3 miles"), owner's first name + last initial, neighborhood name
- Search results are sorted by distance (nearest first) by default
- Tool detail page shows: all photos in gallery, full description, condition notes, usage guidelines, owner's profile summary, approximate distance, "Request to Borrow" button
- Tool listings display owner's first name and neighborhood designation, but never full address or last name
- Each tool has a unique, shareable URL (e.g., `/tools/abc123`)

---

## Functional Requirements

### Tool Creation Flow

**What**: A form-based workflow for users to add new tools to their inventory.

**Why**: Owners need a simple, guided process to catalog their tools. Lower friction here means more tools listed, which means more borrowing activity.

**Behavior**:
- User clicks "List a Tool" from dashboard or profile
- Multi-step form:
  1. Basic Info: Title, Category dropdown
  2. Description: Rich text area with character counter, optional condition notes
  3. Photos: Drag-and-drop upload, up to 5 images, reorder by dragging, first photo is thumbnail
  4. Availability: Default status "Available", can set to "Temporarily Unavailable" if not ready to share yet
- Draft auto-save every 30 seconds (stored client-side)
- Validation errors shown inline before submission
- Success confirmation shows the new tool listing and prompts "List another tool?"

### Photo Management

**What**: Image upload, storage, and display for tool listings.

**Why**: Photos are essential for trust - borrowers need to see the actual tool's condition, not just read a description.

**Behavior**:
- Accepted formats: JPEG, PNG, WebP (max 10MB per image)
- Images auto-resized to max 1920px width, maintaining aspect ratio
- Thumbnail generated at 400px width for search results
- First uploaded photo becomes the primary thumbnail
- Users can reorder photos by dragging (changes which is primary)
- Users can delete individual photos after upload
- Photo gallery on detail page shows all images with lightbox zoom
- Alt text auto-generated from tool title (accessible)

### Search & Discovery

**What**: The primary interface for borrowers to find tools they need.

**Why**: Users need to quickly find relevant tools nearby without browsing hundreds of irrelevant listings.

**Behavior**:
- Search page loads showing all available tools within default 5-mile radius
- Filter panel on left (desktop) or collapsible (mobile):
  - **Category**: Checkboxes for each category, multi-select enabled
  - **Distance**: Radio buttons for 1, 5, 10, 25 miles
  - **Availability**: Toggle "Available only" (default on) vs "Show all"
- Keyword search box filters by tool title and description (partial match, case-insensitive)
- Results update immediately on filter change (no "Apply" button needed)
- Each result card shows: thumbnail, title, category badge, distance, owner name + neighborhood, availability indicator
- Default sort: distance ascending (nearest first)
- Empty state: "No tools found. Try expanding your search radius or adjusting filters."
- Pagination: 24 tools per page (infinite scroll for v2)

### Tool Detail Page

**What**: Complete information view for a single tool listing.

**Why**: Borrowers need all details to make informed request decisions; owners need a shareable link to their tools.

**Behavior**:
- URL structure: `/tools/{toolId}` (e.g., `/tools/abc123`)
- Layout sections:
  1. **Photo Gallery**: Large primary image with thumbnail strip below, click to cycle
  2. **Tool Information**: Title (h1), category badge, availability status badge
  3. **Description**: Full description text, condition notes in callout box if present
  4. **Usage Guidelines**: Any special instructions from owner
  5. **Owner Profile Summary**: Avatar, first name + last initial, neighborhood, "Member since", rating, "Tools shared: X times"
  6. **Location**: "Approximately 2.3 miles away in [Neighborhood]" - no address shown
  7. **Action Button**: "Request to Borrow" (primary CTA) - disabled if unavailable or if you're the owner
- If user owns this tool: show "Edit" and "Delete" buttons instead of request button
- Social share: Generate Open Graph meta tags for nice previews when shared

### Tool Status Management

**What**: Owners control when their tools are available for borrowing.

**Why**: Owners need flexibility to temporarily make tools unavailable (seasonal storage, personal use, repairs) without deleting listings.

**Behavior**:
- Status options:
  - **Available**: Green badge, shows in search by default, can be requested
  - **Currently Borrowed**: Yellow badge, shows borrower name and return date to owner only, not requestable, optionally hidden from search
  - **Temporarily Unavailable**: Gray badge, shows in search but grayed out with "Not available", not requestable
- Owner can change status from:
  - Tool detail page (dropdown in owner view)
  - Dashboard "My Tools" list (quick status toggle)
- Status change to "Currently Borrowed" happens automatically when a borrow request is approved and pickup confirmed (handled by Feature 2)
- Status auto-reverts to "Available" when borrow is marked returned and confirmed (handled by Feature 4)

### Tool Editing & Deletion

**What**: Owners can modify or remove their tool listings after creation.

**Why**: Tool conditions change, details need updates, or users stop wanting to share certain items.

**Behavior**:
- **Edit**:
  - Same form as creation, pre-populated with existing data
  - Can modify everything except: creation date, times borrowed count
  - If tool is currently borrowed, show warning: "This tool is currently borrowed. Changes will be visible to the borrower."
  - Save updates with timestamp "Last updated: [date]"
- **Delete**:
  - If tool status is "Available" or "Temporarily Unavailable": immediate deletion with confirmation modal
  - If tool status is "Currently Borrowed": prevent deletion with error message "Cannot delete while borrowed. Wait for return or contact support."
  - Confirmation modal: "Delete [Tool Name]? This will remove the listing and all its photos. Past borrow history will be preserved in transaction records. This cannot be undone."
  - Deletion is permanent (hard delete from database)
  - Past transaction records reference deleted tools by cached name/ID, not foreign key

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:

- **Tool**: Core entity representing a tool listing
  - Attributes: id, userId (owner), title, categoryId, description, conditionNotes, status, createdAt, updatedAt, location (lat/long), timesShared (counter)
  
- **ToolCategory**: Predefined categories for tool classification
  - Attributes: id, name, displayOrder
  - Seeded data: Power Tools, Hand Tools, Gardening, Ladders & Access, Automotive, Specialty Equipment
  
- **ToolPhoto**: Images associated with a tool
  - Attributes: id, toolId, imageUrl, thumbnailUrl, displayOrder, uploadedAt
  
- **User**: Referenced for ownership (defined in Feature 3, but needed here)
  - This feature needs: id, firstName, lastName, neighborhood, location (lat/long)

**Key Relationships**:
- Tool belongs to one User (owner)
- Tool has many ToolPhotos (1-5)
- Tool belongs to one ToolCategory
- Tool location stores owner's geocoded coordinates for distance calculation (but owner's full address never exposed)

**Indexing Considerations**:
- Tool.status (for filtering available tools)
- Tool.categoryId (for category filtering)
- Tool.location (geospatial index for distance queries)
- Tool.userId (for "My Tools" owner queries)

---

## User Experience Flow

**Tool Owner - Creating a Listing**:

1. User clicks "List a Tool" from dashboard
2. Form step 1: enters title "DeWalt 20V Cordless Drill" and selects "Power Tools" category
3. Form step 2: writes description "Barely used cordless drill with two batteries and charger. Great for hanging pictures or light construction." and notes condition "Excellent - like new"
4. Form step 3: uploads 3 photos from phone (drill, batteries, case)
5. Form step 4: confirms status "Available" 
6. Clicks "Publish Tool Listing"
7. Success message appears, redirected to tool detail page
8. Prompt: "Want to list another tool?"

**Borrower - Finding a Tool**:

1. User navigates to "Find Tools" search page
2. Page loads showing available tools within 5 miles (default)
3. User selects "Ladders & Access" category filter
4. Results update to show 8 ladders nearby
5. User clicks on "8ft Aluminum Step Ladder" result card
6. Tool detail page loads with photos, description, owner info
7. User sees "2.3 miles away in Maplewood" and owner "John D. (rated 4.8★, shared 12 times)"
8. User decides this meets their needs and clicks "Request to Borrow" button
9. [Flow continues in Feature 2: Borrowing Requests]

**Tool Owner - Managing Status**:

1. Owner going on vacation for 2 weeks
2. Opens "My Tools" dashboard
3. Sees list of 5 tools currently marked "Available"
4. Clicks status dropdown next to "Chainsaw" 
5. Selects "Temporarily Unavailable"
6. Tool immediately grayed out in search results
7. Returns from vacation, reopens dashboard
8. Toggles chainsaw back to "Available"
9. Tool reappears in active search results

---

## Edge Cases & Constraints

- **No photos uploaded**: First photo is required (validation error if user tries to publish without at least one photo)
- **Duplicate tool listings**: Allow - same user might own multiple of the same tool (e.g., two drills); no deduplication logic needed
- **Tool title profanity**: Run automated check on title and description, flag for admin review if profanity detected (auto-publish anyway, remove later if confirmed inappropriate)
- **Location privacy**: Tool location uses owner's address coordinates for distance calculation but NEVER displays full address publicly; detail page shows only neighborhood name and approximate distance
- **User moves to new address**: When user updates their profile address (Feature 3), all their tool listings' locations update automatically; existing search results for those tools recalculate distance
- **Category selection**: Users must pick exactly one category (no multi-category or "Other" option for v1); if tool genuinely doesn't fit, user picks closest match
- **Tool in multiple states**: Tool can only have ONE status at a time; status "Currently Borrowed" is managed automatically by Features 2 & 4, owner shouldn't manually set this
- **Deleted tool with active borrow**: Cannot delete; enforce at application level and database level (foreign key constraint prevents deletion while borrow record exists)
- **Search with no location**: Users must have address set in profile before accessing search; redirect to profile completion if location missing
- **Distance calculation accuracy**: Use haversine formula for lat/long distance (accounts for earth curvature); display distance rounded to one decimal place

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- **Advanced search**: No filtering by brand, model, power source, year purchased - basic keyword and category only (possible v2 enhancement)
- **Tool availability calendar**: No calendar showing future reserved dates; only current status is tracked (v2: integrate with borrow dates)
- **Tool value/replacement cost**: No insurance value field; kept simple to avoid deterring sharing
- **Tool manuals or guides**: No PDF uploads or links to instruction manuals (v2: add document attachments)
- **Tool maintenance history**: No service records or maintenance reminders (separate v2 feature)
- **Consumables**: No support for listing nails, screws, paint - durable tools only
- **Tool sets/bundles**: Each tool listed individually; no "drill with bit set" as single listing (v2: could add "related tools" grouping)
- **Tool ratings separate from transaction**: Tools don't have their own ratings; only users rate the overall borrow transaction (Feature 4 handles rating)
- **Map view**: Listed in Feature 5 (Community & Discovery); this feature provides the data, F5 provides map UI
- **Favorites/Wishlist**: Not in v1; users can only request tools, not save them for later
- **Automated image enhancement**: Photos uploaded as-is; no AI upscaling or background removal (keep implementation simple)

---

## Open Questions for Tech Lead

1. **Photo storage strategy**: Should we use Azure Blob Storage (per tech stack doc) or is there a preference for AWS S3? Need to confirm blob storage configuration.

2. **Geospatial queries**: PostgreSQL supports PostGIS extension for location queries. Should we enable this extension, or use a simpler haversine formula in application code? Trade-off: PostGIS is faster for large datasets but adds infrastructure complexity.

3. **Image processing**: Do we have existing image resizing infrastructure, or should we integrate a service like Cloudinary/ImageKit? Need consistent thumbnail generation.

4. **Search performance**: At what scale (number of tools) should we consider full-text search (PostgreSQL tsvector) vs. simple LIKE queries? Suggest simple LIKE for MVP, optimize later.

5. **Status transition validation**: Should status changes be event-sourced for audit trail, or is simple field update sufficient for v1?

---

## Dependencies

**Depends On**: 
- Feature 3 (User Profiles) - partially: needs User entity with location, firstName, neighborhood fields defined. Users must complete profile with address before listing tools.

**Enables**: 
- Feature 2 (Borrowing Requests) - requires tool listings to exist before requests can be made
- Feature 5 (Community & Discovery) - uses tool listing data for map view and discovery feed

**Technical Dependencies**:
- Authentication system (user must be logged in to list tools)
- Geolocation service (geocode user addresses to lat/long)
- Image upload/storage infrastructure
- PostgreSQL with spatial query capability