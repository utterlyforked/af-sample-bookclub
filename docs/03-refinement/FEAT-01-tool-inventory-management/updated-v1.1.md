# Tool Inventory Management - Feature Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: field validation rules, photo storage approach, ownership model, deletion behavior, availability management, uniqueness handling, value field specs, category change behavior)

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

## Acceptance Criteria (UPDATED v1.1)

- Users can add tools with title (5-150 chars), description (20-2000 chars), category, photos (up to 5), and condition notes
- Users can mark tools as "Available", "Temporarily Unavailable", or "On Loan" 
- Users can set lending preferences (max loan duration, deposit required, pickup vs delivery)
- Tool listings show estimated value (integer $1-$10,000), age, and any special instructions
- Users can edit tool details and photos at any time
- Users can delete tools from their inventory (soft delete preserves loan history)
- Tool photos are processed synchronously with immediate resize/compress to 1200px max width
- Tool categories follow a standardized list (Power Tools, Garden Tools, Hand Tools, etc.)
- Each user has individual tool ownership (no co-ownership in v1)
- System suggests unique tool names but allows duplicates with user confirmation

---

## Detailed Specifications (UPDATED v1.1)

**Field Validation & Constraints**

**Decision**: Moderate validation constraints that encourage quality without being overly restrictive

**Rationale**: Balance between data quality and user friction. Too strict constraints might discourage tool listings, while too loose allows poor quality data that hurts search and trust.

**Examples**:
- Title: "Cordless Drill", "Lawn Mower - Electric", "Socket Set 1/4 inch" (5-150 chars)
- Description: "18V cordless drill with two batteries. Great for home projects. Please return with both batteries charged." (20-2000 chars minimum)
- Brand/Model: Optional fields, 50 chars each if provided
- Estimated Value: $25, $150, $800 (integer only, $1-$10,000 range)
- Year Purchased: 1950 to current year validation

**Edge Cases**:
- Values under $10 or over $1,000 show warning: "This seems unusually low/high for this category - is this correct?"
- Special characters in title/description are allowed but HTML is stripped for security

---

**Photo Storage & Processing**

**Decision**: Simple synchronous processing with immediate resize and compress on upload

**Rationale**: MVP needs to work reliably without complex background job infrastructure. Users get immediate feedback on photo processing. Can enhance with async processing in v2 if upload times become problematic.

**Examples**:
- User selects 3.2MB JPEG → system resizes to 1200px max width → compressed to ~400KB → stored in blob storage
- Upload progress shows: "Processing photo 2 of 3..." during resize operation
- Failed uploads show clear error: "Photo too large (8MB). Maximum size is 5MB per photo."

**Edge Cases**:
- Upload timeout after 30 seconds with retry option
- Corrupt image files rejected with helpful error message
- When tool is deleted, photos are marked for cleanup but preserved for 30 days (in case of accidental deletion)

---

**Tool Ownership Model** 

**Decision**: Single ownership only - one user owns each tool

**Rationale**: Keeps authorization simple and maintains clear responsibility. The vast majority of shared tools have single owners. Co-ownership can be added in v2 if users request it, but adds significant complexity for minimal v1 benefit.

**Examples**:
- Sarah owns "Circular Saw" - only Sarah can edit, delete, or manage availability
- If roommates want to share a tool, they decide which person lists it under their account
- Tool history shows "Owned by Sarah Johnson" clearly in tool details

**Edge Cases**:
- If user account is deactivated, their tools are marked "Owner Inactive" and hidden from discovery
- Account deletion requires either deleting all tools or transferring ownership (to be designed in user management)

---

**Tool Deletion & History Preservation**

**Decision**: Soft delete that preserves loan history and analytics data

**Rationale**: Sharing history is valuable for community trust building and platform analytics. Hard deleting tools would lose this data. Soft delete keeps database integrity while removing from active listings.

**Examples**:
- User clicks delete on "Power Drill" → System shows "This tool has been borrowed 5 times. Delete anyway?" → Tool marked deleted but data preserved
- Deleted tools don't appear in search or user inventory but loan history still shows "Power Drill (no longer available)"
- Analytics can still count "tools deleted after X loans" for platform insights

**Edge Cases**:
- Tools currently on loan cannot be deleted: "Cannot delete - Tool is currently borrowed by John until March 15"
- Deleted tools can be "undeleted" within 30 days from user settings
- After 30 days, deleted tools are marked for archival (remove from active queries but preserve data)

---

**Temporary Unavailability Management**

**Decision**: Manual-only management with display-only estimated return date

**Rationale**: Keep v1 simple without background jobs or automated status changes. Most temporary unavailability is short-term and owners will remember to update. Automatic changes could make tools available when owner still needs them.

**Examples**:
- Owner marks drill "Temporarily Unavailable" with note "Using for bathroom renovation, back ~March 20"
- Status remains until owner manually changes back to "Available"
- Other users see "Temporarily unavailable (expected back around March 20)"

**Edge Cases**:
- No automatic expiration - tools can stay unavailable indefinitely until owner updates
- Future enhancement: system could send reminders "Tool has been unavailable for 2 weeks - still need it?"
- If owner becomes inactive while tool is unavailable, tool shows "Owner inactive" instead

---

**Tool Name Uniqueness**

**Decision**: Gentle guidance toward unique names with user override capability

**Rationale**: Encourages better tool organization and easier identification without being overly restrictive. Some users legitimately have multiple similar tools.

**Examples**:
- User enters "Cordless Drill" but already has one → Warning: "You already have a 'Cordless Drill'. Consider adding brand or size to tell them apart."
- User can click "Continue anyway" to create duplicate
- Better approach suggested: "Cordless Drill - Makita 18V" and "Cordless Drill - DeWalt 20V"

**Edge Cases**:
- Warning appears for exact title matches, ignoring case
- No validation on brand/model combinations - focus on title clarity
- Users with legitimately identical tools (e.g., two identical hammers) can proceed with duplicates

---

**Estimated Value Field**

**Decision**: Integer dollars only with smart category-based guidance

**Rationale**: Tool values don't need cent precision, and integer handling is simpler. Category hints help users provide realistic values without complex validation rules.

**Examples**:
- Hand Tools category shows guidance: "Typical range: $10-$200"
- Power Tools category shows: "Typical range: $50-$800" 
- User enters $15 for "Circular Saw" → Warning: "This seems low for power tools - typical range is $50-$800"
- Values stored and displayed as whole dollars: $45, $150, $250

**Edge Cases**:
- $0 value rejected: "Please enter the approximate value if you were to buy this tool today"
- Values over $2,000 get confirmation: "High value tools may require deposits - continue?"
- Invalid entries (negative, non-numeric) show clear error messages

---

**Category Change Handling**

**Decision**: Allow category changes with user confirmation and awareness

**Rationale**: Simple implementation that educates users about the impact without preventing legitimate category corrections. Category changes should be infrequent enough that confirmation step is reasonable.

**Examples**:
- User changes "Socket Set" from "Hand Tools" to "Auto Tools" 
- Confirmation dialog: "Changing category will affect how your tool appears in search results. Continue?"
- After change, tool appears in new category for all future searches
- Historical loans preserve the original category context for analytics

**Edge Cases**:
- No limit on category changes - users can correct mistakes freely
- System doesn't track category change history (keeps data model simple)
- Tools with active loans can have category changed without affecting the current loan

---

## Q&A History

### Iteration 1 - February 15, 2025

**Q1: What are the exact validation rules and constraints for tool fields?**  
**A**: Moderate constraints for MVP: Title 5-150 chars, Description 20-2000 chars, Brand/Model optional 50 chars each, Estimated value integer $1-$10,000 with warnings for unusual values, Year purchased 1950-current year. Balances data quality with user friction.

**Q2: How should we handle tool photos in terms of storage, processing, and deletion?**  
**A**: Simple synchronous processing for MVP: upload → immediate resize/compress to 1200px max → store in blob storage. Photo URLs stored in database. Photos preserved 30 days after tool deletion for accidental deletion recovery.

**Q3: Can multiple users co-own tools, or is ownership always individual?**  
**A**: Single ownership only for v1. One user owns each tool and has full control over editing, deletion, and availability. Keeps authorization simple and maintains clear responsibility. Co-ownership can be added in v2 if requested.

**Q4: What happens when a user tries to delete a tool that has historical loan data?**  
**A**: Soft delete that preserves all loan history and analytics data. Tool is hidden from active listings but historical data remains intact. Shows confirmation dialog mentioning loan history count. Can be undeleted within 30 days.

**Q5: How should "Temporarily Unavailable" work - does it expire automatically or require manual management?**  
**A**: Manual management only for MVP. Owner sets status and must manually change back to Available. Estimated return date is display-only for other users. Keeps implementation simple without background job complexity.

**Q6: Should we enforce uniqueness constraints on tool titles within a user's inventory?**  
**A**: Gentle guidance approach - warn user if creating duplicate title but allow override. Shows: "You already have a 'Cordless Drill' - consider adding brand/model to differentiate" with option to continue anyway. Encourages better organization without being restrictive.

**Q7: How should the estimated value field behave and what validation should it have?**  
**A**: Integer dollars only ($1-$10,000 range) with smart category-based guidance text. Hand tools show "Typical range: $10-$200", Power tools show "$50-$800", etc. Warning for values outside typical ranges but allow override.

**Q8: What should happen when a user changes a tool's category after it has loan history?**  
**A**: Allow changes with confirmation dialog: "Changing category will affect how your tool appears in search results - continue?" Simple update without tracking change history. Loan records preserve context but aren't affected by category changes.

---

## Product Rationale

**Why moderate validation constraints?**  
MVP needs to encourage tool listings while maintaining basic quality. Overly strict validation could discourage sharing, while too loose creates poor search experience. Starting moderate allows tightening based on actual data quality observed.

**Why synchronous photo processing?**  
Immediate user feedback is more important than optimal performance for MVP. Users can see results instantly and retry if needed. Background processing adds complexity that can be added in v2 if upload times become problematic.

**Why soft delete for tools?**  
Community sharing platforms benefit from preserving trust-building data like loan history. Hard deletes would lose valuable analytics about tool popularity and user behavior patterns. 30-day recovery window handles accidental deletions.

**Why manual availability management?**  
Automated status changes could make tools available when owners still need them, creating conflicts. Manual control gives owners full authority over their tools. Can add automation features based on how users actually behave with the manual system.