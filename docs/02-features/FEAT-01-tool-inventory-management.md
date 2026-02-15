# Tool Inventory Management - Feature Requirements

**Version**: 1.0  
**Date**: February 15, 2025  
**Status**: Initial - Awaiting Tech Lead Review

---

## Feature Overview

Tool Inventory Management allows community members to catalog and manage their personal tools that they're willing to share with neighbors. This is the foundation feature that creates the supply side of the sharing economy - without tools listed, there's nothing to share.

This feature enables tool owners to create detailed profiles for each tool, including photos, descriptions, condition notes, and sharing preferences. Owners maintain full control over their inventory, setting availability periods, loan restrictions, and pickup preferences. The feature transforms a casual "I have a drill" into a structured, searchable, and trustworthy tool listing that neighbors can discover and request.

This is a supply-side feature that directly enables the core value proposition: making neighborhood tools discoverable and available for sharing in a structured, safe way.

---

## User Stories

- As a tool owner, I want to create a profile for each tool I'm willing to share so that neighbors can see what's available
- As a tool owner, I want to add photos, descriptions, and usage instructions so borrowers know exactly what they're getting
- As a tool owner, I want to set availability periods and restrictions so I can control when my tools can be borrowed
- As a tool owner, I want to mark tools as temporarily unavailable so I can use my own tools without removing the listing
- As a tool owner, I want to update tool condition and details over time so listings stay accurate
- As a tool owner, I want to see which of my tools are most popular so I can understand what my community needs

---

## Acceptance Criteria

- Users can add tools with title, description, category, photos (up to 5), and condition notes
- Users can mark tools as "Available", "Temporarily Unavailable", or "On Loan" 
- Users can set lending preferences (max loan duration, deposit required, pickup vs delivery)
- Tool listings show estimated value, age, and any special instructions
- Users can edit tool details and photos at any time
- Users can delete tools from their inventory (with warnings if currently on loan)
- Tool photos are automatically compressed and optimized for mobile viewing
- Tool categories follow a standardized list (Power Tools, Garden Tools, Hand Tools, etc.)

---

## Functional Requirements

### Tool Creation & Editing

**What**: Complete tool profile creation with all necessary details for safe sharing

**Why**: Detailed listings build trust and set clear expectations, reducing conflicts and damaged tools

**Behavior**:
- Required fields: title, category, condition, description (min 20 chars)
- Optional fields: brand, model, year purchased, estimated value, special instructions
- Photo upload supports JPEG/PNG, max 5MB per photo, auto-resized to 1200px max width
- Categories are pre-defined dropdown: Power Tools, Garden Tools, Hand Tools, Outdoor Equipment, Specialty Tools
- Condition options: Excellent, Good, Fair, Poor (with guidance text for each)

### Availability Management  

**What**: Dynamic control over when tools can be borrowed

**Why**: Owners need flexibility to use their own tools while maintaining long-term sharing

**Behavior**:
- Three states: Available, Temporarily Unavailable, On Loan (system-managed)
- "Temporarily Unavailable" shows estimated return to availability (optional)
- Owners can set blackout periods (e.g., "Not available June 1-15")
- Calendar view shows tool availability for next 60 days

### Lending Preferences

**What**: Owner-defined rules for how their tools can be borrowed

**Why**: Different tools have different risk profiles and usage requirements

**Behavior**:
- Max loan duration: 1 day, 3 days, 1 week, 2 weeks, 1 month
- Pickup preference: "Must pick up", "I can deliver within 1 mile", "Either works"
- Deposit requirement: None, $25, $50, $100, Custom amount
- Experience level required: Anyone, Some DIY experience, Experienced users only
- Special requirements free-text field (e.g., "Please bring extension cord")

### Tool Organization

**What**: Personal dashboard for managing tool inventory

**Why**: Owners need clear oversight of their shared tools and lending activity

**Behavior**:
- Grid/list view toggle with tool photos, titles, and current status
- Filter by category, availability status, or popularity
- Sort by date added, alphabetical, most requested, or currently on loan
- Bulk actions: mark multiple tools unavailable, update categories
- Quick stats: total tools, currently loaned, total loans completed

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:
- Tool: Core tool information, photos, preferences
- ToolCategory: Standardized categorization system  
- ToolPhoto: Multiple photos per tool with ordering
- User: Tool owner information and contact preferences

**Key Relationships**:
- User has many Tools (one-to-many)
- Tool belongs to one ToolCategory (many-to-one)
- Tool has many ToolPhotos (one-to-many, ordered)

[Note: This is preliminary - Tech Lead will ask questions to clarify]

---

## User Experience Flow

1. User clicks "Add Tool" from dashboard
2. System presents tool creation form with required/optional fields
3. User fills title, selects category from dropdown, adds description
4. User uploads 1-5 photos (with drag-and-drop or file picker)
5. System shows photo previews with reorder/delete options
6. User sets condition level and estimated value
7. User configures lending preferences (duration, pickup, deposit)
8. User adds any special instructions or requirements
9. User clicks "List Tool" - system validates and saves
10. System shows confirmation and returns to inventory dashboard
11. New tool appears in "Available" status, visible to community

**For editing**: Click tool from dashboard → same form pre-populated → save updates → return to dashboard

---

## Edge Cases & Constraints

- **Photo upload failures**: Show clear error messages, allow retry, save other fields
- **Duplicate tool names**: Allow duplicates (someone might have multiple drills)
- **Very long descriptions**: 2000 character limit with counter shown
- **Invalid estimated values**: Accept $0-$10,000, warn if unusually high/low
- **Tool deletion with active loans**: Block deletion, show "Return first" message
- **Category changes**: Allow category changes even with loan history
- **Inactive users**: Tools from users inactive >90 days marked "Owner Inactive"

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- Barcode scanning or automated tool identification
- Integration with tool manufacturer databases  
- Automatic value estimation or depreciation tracking
- Tool maintenance reminders or service history
- Batch import from spreadsheets or other apps
- Tool insurance or damage protection plans
- Monetization features (rental pricing, transaction fees)

---

## Open Questions for Tech Lead

- Should we implement soft deletes for tools to preserve loan history, or hard deletes with orphaned loan records?
- What's the preferred approach for photo storage and CDN integration?
- Should tool availability status changes trigger notifications to users who previously requested that tool?

---

## Dependencies

**Depends On**: User authentication and profile system

**Enables**: Tool Discovery & Search, Borrowing Request System (tools must exist before they can be found or requested)