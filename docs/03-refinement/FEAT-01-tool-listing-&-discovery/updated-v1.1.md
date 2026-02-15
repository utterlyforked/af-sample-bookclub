# Tool Listing & Discovery - Feature Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: validation rules, search behavior, photo handling, location implementation)

---

## Feature Overview

The Tool Listing & Discovery feature is the core marketplace functionality that enables tool owners to advertise their available equipment and allows borrowers to find exactly what they need within their local community. This feature serves as the primary entry point for most user interactions with the platform.

Tool owners can create detailed listings with photos, descriptions, and availability status, making their unused equipment discoverable to neighbors. Borrowers can search and filter through available tools using various criteria including distance, category, and current availability. This creates a dynamic, searchable inventory of community tools that updates in real-time as items are borrowed and returned.

This feature is essential because it solves the discovery problem - connecting tool supply with demand in a neighborhood context where pickup logistics are practical.

---

## User Stories

- As a tool owner, I want to create listings for my available tools so that neighbors can discover and request to borrow them
- As someone needing a tool, I want to search for specific tools in my area so that I can find borrowing options without buying
- As a user, I want to see photos and details about tools so that I can verify they meet my project needs
- As a tool owner, I want to mark tools as unavailable when they're being used or need maintenance so that I don't get requests I can't fulfill
- As a borrower, I want to see how far away tools are located so that I can choose options within convenient pickup distance

---

## Acceptance Criteria (UPDATED v1.1)

- Users can create tool listings with title (100 chars max), description (1000 chars max), category, photos, and availability status
- Search functionality works by tool name, category, and postal code area (user's postal code + adjacent ones)
- Tool listings display owner's postal code area, availability status, and basic condition notes
- Users can filter results by distance, tool category, and availability
- Photo uploads support JPEG/PNG, max 5MB per image, up to 5 images per listing with automatic thumbnails (150x150, 400x300, 1200x900)
- Tool listings can be edited and deleted by their owners
- Search results are ordered by text match score first, then distance
- Users can view detailed tool pages with all information and owner contact options
- System prevents duplicate listings by warning users about similar tool names with option to proceed
- Listings show "last active" indicators when owners haven't responded to requests in 30+ days

---

## Detailed Specifications (UPDATED v1.1)

**Tool Listing Validation & Constraints**

**Decision**: Conservative validation limits with clear boundaries

**Rationale**: Clear limits prevent edge cases and abuse while ensuring good UI display. Users can always use direct contact for additional details that don't fit in descriptions.

**Validation Rules**:
- Tool name: 100 characters maximum, alphanumeric + basic punctuation (periods, hyphens, spaces, parentheses)
- Description: 1000 characters maximum, full text allowed including line breaks
- Category: Must select from predefined flat category list
- At least one photo required, maximum 5 photos per listing
- Special instructions: 500 characters maximum (optional field)
- Brand/model: 100 characters maximum (optional field)

**Edge Cases**:
- Empty or whitespace-only fields rejected with clear error messages
- Emoji in text fields are allowed and count as 1 character each
- Form preserves user input during validation errors

---

**Location-Based Search Implementation**

**Decision**: Postal code based search with adjacent area inclusion

**Rationale**: Provides good balance of precision and privacy without requiring GPS coordinates. Postal codes are familiar to users and provide natural neighborhood boundaries.

**Behavior**:
- Users provide postal code during registration (validated against known postal code list)
- Search includes user's postal code + all adjacent postal codes (determined by postal code adjacency database)
- Tool listings display postal code area publicly (e.g., "Oakland 94610 area")
- No exact addresses ever displayed or stored in searchable form
- Distance shown as postal code area ("Same area" vs "1 area away" vs "2 areas away")

**Examples**:
- User in 94610 sees tools from 94610, 94611, 94609, 94618 (adjacent codes)
- Results show "Oakland 94610 area" not street addresses
- Search radius approximately 3-5 miles depending on postal code density

**Edge Cases**:
- Invalid postal codes during search show "No tools in that area" message
- Users can manually search other postal code areas beyond their default

---

**Photo Upload & Content Handling**

**Decision**: Basic technical validation with community reporting mechanism

**Rationale**: Focus on technical reliability for MVP while allowing community self-moderation. Automated content screening can be added later if abuse becomes problematic.

**Photo Processing**:
- Upload validation: JPEG/PNG only, max 5MB per file, max 5 files per listing
- Automatic generation of 3 sizes: thumbnail (150x150 crop), medium (400x300 scale), full (1200x900 scale)
- Fixed cropping/scaling with no user control (users can retake photos if cropping looks poor)
- Images compressed to 85% quality for web optimization
- Alt text auto-generated from tool name + photo number

**Content Policy**:
- Technical validation only during upload (file type, size, corruption check)
- Users can report inappropriate images via "Report Image" link
- Reported images flagged for manual review within 24 hours
- Clear photo guidelines provided: "Show the tool clearly, no people, no inappropriate content"

**Error Handling**:
- Upload failures preserve form data and show specific error (file too large, wrong type, etc.)
- Retry mechanism for temporary network issues
- Progress indicators for uploads over 1MB

---

**Search Results Ranking & Behavior**

**Decision**: Simple text match + distance scoring with predictable results

**Rationale**: Users understand "best match, closest first" intuitively. Predictable ranking helps users learn how to search effectively.

**Ranking Algorithm**:
- Exact title match: 100 points
- Partial title match: 50 points
- Description match: 25 points
- Category match: 15 points
- Subtract postal area distance: -5 points per area away
- Recently updated bonus: +5 points if updated within 7 days

**Search Behavior**:
- Text search is case-insensitive and matches partial words
- Results limited to 50 items per search to ensure performance
- "No results" page suggests: broader keywords, different category, expand to more postal areas
- Search highlights matching terms in results

**Examples**:
- Search "drill": Exact title "Drill" (100pts, same area) ranks above "Cordless Power Drill" (50pts, same area)
- "Makita drill" prioritizes title match over description mention of brand

---

**Duplicate Listing Prevention**

**Decision**: Similar listing detection with warning and override option

**Rationale**: Prevents obvious duplicates while allowing legitimate cases (user owns two identical tools). Guides users toward good behavior without being restrictive.

**Duplicate Detection**:
- Check for similar tool names using fuzzy string matching (75% similarity threshold)
- Show warning: "You have a similar listing: [existing tool name]. Are you listing a different tool?"
- Options: "Yes, this is different" (proceed) or "Edit existing listing" (redirect)
- No prevention of exact duplicates - users might legitimately own multiple identical tools

**Examples**:
- Creating "Cordless Drill" when "Drill (Cordless)" exists triggers warning
- Creating "Drill #2" when "Drill" exists triggers warning
- User can always proceed after seeing warning

---

**Inactive Listing Management**

**Decision**: Track activity and show "potentially inactive" indicators

**Rationale**: Improves borrower experience by helping identify responsive owners without automatically changing user data. Provides foundation for future automated features.

**Activity Tracking**:
- Track "last owner activity" timestamp when owner: logs in, responds to requests, updates listings
- Show "Last active: [timeframe]" on listings when owner hasn't been active for 30+ days
- Timeframe display: "Last active 1 month ago", "Last active 3 months ago", etc.
- No automatic changes to listing availability

**Display Rules**:
- Active within 30 days: No indicator shown
- 30-90 days inactive: "Last active 2 months ago" in gray text
- 90+ days inactive: "Last active 3+ months ago" in orange text with warning icon

**Future Foundation**:
- Data structure supports future features like auto-disable or owner re-engagement emails
- Borrowers can make informed decisions about which tools to request

---

**Photo Display & Management**

**Decision**: Fixed thumbnail sizes with automatic cropping, no user control initially

**Rationale**: Ensures consistent UI and predictable performance. Users can retake photos if automatic cropping doesn't work well. User cropping can be added in v2 if feedback indicates it's needed.

**Photo Sizes**:
- Thumbnail: 150x150 pixels (cropped to square, used in search results)
- Medium: 400x300 pixels (scaled to fit, used in tool detail pages)
- Full: 1200x900 pixels max (scaled down if larger, used in lightbox/zoom)

**Display Behavior**:
- Primary photo (first uploaded) shown in search results and as main image
- Gallery thumbnails show all photos on tool detail page
- Click any photo to open full-size lightbox
- Photos display tool name + owner username in alt text for accessibility

**Management Features**:
- Owners can reorder photos by drag-and-drop (primary photo = first position)
- Delete individual photos (minimum 1 photo must remain)
- Replace photos by uploading new ones

---

**Tool Categories Structure**

**Decision**: Flat category list with ~15 well-chosen categories

**Rationale**: Simple UI and search implementation. Easier for users to choose the right category. Can add subcategories later when data shows which categories become too large.

**Category List**:
- Power Tools
- Hand Tools  
- Garden Tools
- Lawn Care
- Automotive Tools
- Plumbing Tools
- Electrical Tools
- Painting Supplies
- Construction Tools
- Measuring Tools
- Safety Equipment
- Cleaning Equipment
- Moving Equipment
- Outdoor/Camping
- Other Tools

**Category Behavior**:
- Single selection required (no multi-category listings)
- Filter sidebar shows category names with tool counts
- "Other Tools" category requires more detailed description
- Categories can be added/renamed based on usage data

---

## Q&A History

### Iteration 1 - December 19, 2024

**Q1: What are the exact validation rules for tool listings?**  
**A**: Conservative limits - tool name 100 chars max (alphanumeric + basic punctuation), description 1000 chars max (full text), prevents abuse while ensuring good UI display.

**Q2: How should location-based search work exactly?**  
**A**: Postal code based - users provide postal code, search includes their code + adjacent ones, displays "area" publicly not addresses, good balance of precision and privacy.

**Q3: What happens when users upload invalid or inappropriate photos?**  
**A**: Basic technical validation only (file type, size, format) with community reporting mechanism, manual review of flagged content within 24 hours.

**Q4: How should search results be ranked when multiple tools match?**  
**A**: Simple text match scoring (exact title 100pts, partial 50pts, description 25pts) minus distance penalty, predictable and intuitive for users.

**Q5: What should happen when tool owners don't respond to requests?**  
**A**: Track owner activity and show "last active" indicators on listings after 30+ days of inactivity, helps borrowers choose responsive owners.

**Q6: How should we handle duplicate tool listings from the same user?**  
**A**: Detect similar titles (75% similarity), show warning with option to proceed or edit existing listing, allows legitimate duplicates while preventing obvious mistakes.

**Q7: What photo features are needed beyond basic upload?**  
**A**: Fixed thumbnail sizes (150x150, 400x300, 1200x900) with automatic cropping/scaling, no user control initially, consistent UI and performance.

**Q8: Should tool categories be hierarchical or flat?**  
**A**: Flat list of ~15 categories for simplicity, can add subcategories later when usage data shows which categories need subdivision.

---

## Product Rationale

**Why postal code based location?**  
Provides natural neighborhood boundaries users understand while maintaining privacy. No GPS permissions needed, easier to implement than coordinate calculations, and postal codes align with how people think about "their area."

**Why conservative validation limits?**  
Prevents edge cases in UI rendering and reduces potential for spam/abuse. 100 character tool names cover 99% of real tools, and 1000 character descriptions are sufficient for detailed explanations. Users can always contact directly for additional information.

**Why no automated content moderation initially?**  
Technical validation handles the majority of issues (wrong file types, corrupted uploads) while community reporting provides escalation path. Automated screening adds complexity and cost that may not be justified until we see actual abuse patterns.

**Why simple search ranking?**  
"Best match, closest" is intuitive to users and creates predictable results. Complex algorithms with multiple weighted factors are harder to debug and users can't learn how to search effectively. Can enhance later based on actual usage patterns.

**Why flat categories instead of hierarchy?**  
Reduces decision paralysis and UI complexity. Users don't have to navigate through multiple levels or guess which subcategory their tool belongs in. With only 15 categories, the list remains scannable and manageable.