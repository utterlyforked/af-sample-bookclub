# Tool Listings - Technical Questions (Iteration 1)

**Status**: NEEDS CLARIFICATION
**Iteration**: 1
**Date**: 2025-01-10

---

## Summary

After reviewing the specification, I've identified **8** areas that need clarification before implementation can begin. These questions address:
- Tool listing mutability and version control
- Photo storage and processing
- Search result pagination and performance
- Location data handling and privacy
- Status transition workflows
- Data deletion policies

The spec is quite detailed overall, but these gaps would block implementation or lead to inconsistent decisions during development.

---

## CRITICAL Questions

These block core implementation and must be answered first.

### Q1: Can users edit tool listings after they've been borrowed (even once)?

**Context**: The PRD states users can edit tools and mentions "If tool is currently borrowed, show warning" but doesn't address the scenario where a tool has *completed* borrows with ratings/reviews. This affects:
- Data integrity for historical borrow records
- Whether we need version history/audit trails
- Trust implications (can someone change a "Great condition" drill to "Fair condition" after someone rated it 5 stars based on the original description?)

**Options**:

- **Option A: Unrestricted editing forever**
  - Impact: Simple implementation, no version tracking needed
  - Trade-offs: Owner could change description after negative review, making review context invalid
  - Database: Just `updated_at` timestamp
  
- **Option B: Lock after first completed borrow**
  - Impact: Tool listing becomes immutable after first successful return
  - Trade-offs: Prevents legitimate updates (tool condition degrades, accessories lost), forces delete/recreate
  - Database: Add `first_borrowed_at` timestamp, check before allowing edits
  
- **Option C: Edit with version history**
  - Impact: Track versions, show "(edited)" indicator, link historical versions to transactions
  - Trade-offs: More complex, but maintains context for reviews
  - Database: Add `ToolVersion` table with snapshots, or audit log

- **Option D: Allow edits but preserve original for past transactions**
  - Impact: Past transaction records cache tool details at time of borrow
  - Trade-offs: Data duplication, but clean separation of current vs historical
  - Database: Transaction table stores snapshot of title/description/photos at borrow time

**Recommendation for MVP**: Option D. When a borrow is created, cache the tool's current title, description, and primary photo URL in the transaction record. Allow unrestricted editing going forward. Simpler than full version history, but maintains review context.

---

### Q2: What happens when a user deletes a tool that has past completed borrows?

**Context**: The PRD says "Past transaction records reference deleted tools by cached name/ID, not foreign key" and "hard delete from database." Need clarification on data retention:
- Do we show the tool details on past transaction history?
- Can users still see ratings/reviews for deleted tools?
- Does "Tools shared: X times" counter on profile include deleted tools?

**Options**:

- **Option A: Hard delete everything, transactions reference null**
  - Impact: Transaction records exist but show "[Deleted Tool]" placeholder
  - Trade-offs: Clean deletion, but loses historical context for lender reputation
  - Database: Transaction.tool_id becomes nullable, tool data gone
  
- **Option B: Soft delete with is_deleted flag**
  - Impact: Tool records remain in database, marked deleted, hidden from search
  - Trade-offs: Violates "hard delete" in PRD, accumulates dead data
  - Database: Add `is_deleted` boolean, filter in all queries
  
- **Option C: Hard delete tool, preserve cached snapshot in transactions**
  - Impact: Delete Tool and ToolPhoto records, but Transaction table has columns for tool_title_snapshot, tool_photo_snapshot
  - Trade-offs: Data duplication at transaction creation, but complete history preserved
  - Database: Add snapshot columns to Transaction/BorrowRequest tables

- **Option D: Prevent deletion if tool has any transaction history**
  - Impact: User can only "Archive" tool to hide it, not delete
  - Trade-offs: Forces inactive listings to stay in database forever
  - Database: Add `archived` status, prevent DELETE if transactions exist

**Recommendation for MVP**: Option C (aligns with PRD's "cached name/ID" mention). When a borrow request is created, cache the tool title and primary photo URL in the transaction. Hard delete Tool/ToolPhoto records, but user's borrowing history still shows what they borrowed. "Tools shared" counter on profile includes deleted tools (count from transactions, not tool listings).

---

### Q3: How do we handle tool location when user updates their profile address?

**Context**: PRD states "When user updates their profile address (Feature 3), all their tool listings' locations update automatically." Need to clarify:
- Do we recalculate immediately or async/background job?
- What if user moves 50 miles away mid-borrow (borrower thinks tool is close, now it's far)?
- Should we notify active borrowers if lender location changes significantly during a borrow?

**Options**:

- **Option A: Synchronous update on address change**
  - Impact: When user saves new address in profile, all their tools' lat/long update in same transaction
  - Trade-offs: Simple, immediate consistency, but slow if user has 100+ tools
  - Implementation: Single UPDATE query on Tool table WHERE user_id = X

- **Option B: Async background job**
  - Impact: Queue job to update tool locations after profile save returns
  - Trade-offs: Fast user experience, but brief inconsistency (search shows old distances for ~seconds)
  - Implementation: Hangfire background job processes update

- **Option C: Store location reference, not copy**
  - Impact: Tool table has only user_id, no lat/long; join to User for location at query time
  - Trade-offs: Eliminates sync issue entirely, but slower search queries (can't index tool location)
  - Implementation: Every search query JOINs Tool -> User for coordinates

- **Option D: Don't auto-update, require user to manually update each tool**
  - Impact: Profile address change doesn't touch tools; user must edit each listing
  - Trade-offs: No sync issues, but violates PRD requirement and terrible UX
  - Implementation: N/A

**Recommendation for MVP**: Option A (synchronous update). User tool counts will be low in MVP, update will be fast. Add guard: if user has >50 tools, show warning "This will update X tool locations, may take a moment" and use background job for that case. For mid-borrow scenario, document as known edge case (rare, acceptable for v1).

---

### Q4: What does "approximately 2.3 miles" mean for privacy?

**Context**: PRD emphasizes location privacy heavily ("NEVER displays full address publicly"). Need to clarify distance precision:
- Is "2.3 miles" actual calculated distance, or should we fuzzy/round it?
- Do we add random jitter to prevent triangulation (user searches from 3 different spots, calculates owner location)?
- Is neighborhood name alone sufficient, or should we also obscure that?

**Options**:

- **Option A: Exact distance, precise neighborhood**
  - Impact: Show real calculated distance "2.34 miles" and real neighborhood "Maplewood"
  - Trade-offs: Most useful for borrowers, but multiple searches could triangulate owner location
  - Privacy risk: Medium (requires effort but possible)

- **Option B: Rounded distance (0.5 mile increments), real neighborhood**
  - Impact: Show "2.0 miles" or "2.5 miles" (round to nearest half mile), real neighborhood
  - Trade-offs: Slight loss of precision, harder to triangulate
  - Privacy risk: Low-Medium

- **Option C: Distance buckets (1-2 mi, 2-5 mi, 5-10 mi), real neighborhood**
  - Impact: Show "2-5 miles away in Maplewood"
  - Trade-offs: Less precise for borrowers, but good privacy
  - Privacy risk: Low

- **Option D: Exact distance but generalized location ("North Seattle" vs "Maplewood")**
  - Impact: Show "2.3 miles" but obscure neighborhood to larger region
  - Trade-offs: Distance precision preserved, location fuzzed
  - Privacy risk: Low

**Recommendation for MVP**: Option B (round to 0.5 mile increments). Shows "2.5 miles away in Maplewood" - specific enough for convenience judgments, but prevents precise triangulation. Real neighborhood shown because it's already semi-public info (user chose to share it in profile). Can tighten in v2 if users report privacy concerns.

---

## HIGH Priority Questions

These affect major workflows but have reasonable defaults.

### Q5: How do search results handle ties in distance sorting?

**Context**: PRD says "default sort: distance ascending (nearest first)" but doesn't specify secondary sort when multiple tools are equidistant (common in apartment buildings or same neighborhood).

**Options**:

- **Option A: Distance only, database-determined order**
  - Impact: Tools at same distance appear in unpredictable order (likely by ID)
  - Trade-offs: Simple, but inconsistent across page loads
  
- **Option B: Distance, then creation date (newest first)**
  - Impact: Ties broken by showing recently listed tools first
  - Trade-offs: Encourages freshness, simple logic
  
- **Option C: Distance, then alphabetical by title**
  - Impact: Predictable alphabetical secondary sort
  - Trade-offs: Boring, but consistent
  
- **Option D: Distance, then availability (Available before Unavailable), then date**
  - Impact: Available tools bubble up within same distance
  - Trade-offs: Most useful for borrowers, slightly more complex

**Recommendation for MVP**: Option B (distance, then created_at DESC). Newest listings get slight visibility boost when equidistant, encourages active listings.

---

### Q6: What's the expected maximum number of tools per user?

**Context**: Affects UI pagination decisions, query performance, and whether we need "My Tools" management features beyond a simple list.

**Options**:

- **Option A: No limit, expect <10 per typical user**
  - Impact: No artificial cap, optimize for small collections
  - Trade-offs: Simple, but "My Tools" page could get unwieldy for power users
  - Implementation: Show all tools on one page, add pagination later if needed

- **Option B: No limit, expect 10-50 per typical user**
  - Impact: Plan for pagination/filtering on "My Tools" dashboard from day 1
  - Trade-offs: More upfront work, but scalable
  - Implementation: Paginate "My Tools" (20 per page), add category filter

- **Option C: Hard cap at 50 tools per user**
  - Impact: Enforce limit, show warning at 45 tools
  - Trade-offs: Prevents abuse, keeps UI simple, but might frustrate contractors/serious tool collectors
  - Implementation: Validation on tool creation

- **Option D: Hard cap at 100 tools per user**
  - Impact: High limit, essentially unlimited for normal users
  - Trade-offs: Allows power users, might need better "My Tools" management UI
  - Implementation: Validation on tool creation

**Recommendation for MVP**: Option A (no limit, optimize for <10). Most home users won't list >10 tools. Build "My Tools" as simple list with status toggles. Add pagination/search in v2 if users actually hit >20 tools. Monitor 95th percentile tool count in analytics.

---

### Q7: Should photo upload support HEIC (iPhone format)?

**Context**: PRD says "Accepted formats: JPEG, PNG, WebP" but iPhones default to HEIC. This is a major friction point for iOS users.

**Options**:

- **Option A: Accept HEIC, convert server-side to JPEG**
  - Impact: Seamless for iPhone users, requires image processing library that handles HEIC
  - Trade-offs: Best UX, but HEIC decoding adds processing complexity/time
  - Implementation: ImageSharp supports HEIC with extra package

- **Option B: Reject HEIC with helpful error message**
  - Impact: Show error: "HEIC format not supported. Please convert to JPEG in your Photos app first."
  - Trade-offs: Adds friction, but simpler implementation
  - Implementation: Validate file extension/MIME type, reject early

- **Option C: Client-side conversion (JavaScript)**
  - Impact: Convert HEIC to JPEG in browser before upload
  - Trade-offs: No server changes, but requires JS library, slower on older devices
  - Implementation: Use heic2any or similar library

**Recommendation for MVP**: Option A if image processing pipeline can handle it easily (check with ImageSharp or Cloudinary capabilities). Otherwise Option B with clear error message. HEIC is common enough that rejecting it will cause support burden.

---

## MEDIUM Priority Questions

Edge cases and polish items - can have sensible defaults if needed.

### Q8: Can users reorder photos after initial upload without re-uploading?

**Context**: PRD says "Users can reorder photos by dragging (changes which is primary)" but doesn't specify if this works in edit mode or only during initial creation.

**Options**:

- **Option A: Reorder only during creation**
  - Impact: Once tool is published, photo order is locked (except delete/upload new)
  - Trade-offs: Simpler, but user can't fix mistake if they picked wrong primary photo
  
- **Option B: Reorder anytime via edit page**
  - Impact: Edit tool page shows existing photos, allows drag-to-reorder, saves new order
  - Trade-offs: Better UX, requires persisting display_order and update logic
  - Implementation: Store display_order in ToolPhoto table, update on save

**Recommendation for MVP**: Option B. Already storing display_order for creation flow, small additional effort to allow reordering in edit. Saves users from delete/re-upload workaround.

---

## Notes for Product

- **Photo storage question** (Open Question #1 in PRD): Recommend Azure Blob Storage per tech stack doc. We have existing infrastructure. Need container names: `toolshare-tool-photos-prod` and `toolshare-tool-photos-dev`.

- **Geospatial queries** (Open Question #2): Recommend PostGIS for MVP. Distance queries will be frequent (every search), and PostgreSQL PostGIS is mature/reliable. Haversine in application code will become bottleneck quickly.

- **Image processing** (Open Question #3): If no existing service, recommend ImageSharp library (open source, .NET native). Can resize/thumbnail server-side. Avoid third-party services like Cloudinary for MVP (adds cost + external dependency).

- **Search performance** (Open Question #4): Simple LIKE queries for MVP. PostgreSQL performs well for keyword search on <10k records. Add full-text search (tsvector) only if search becomes measurably slow.

- **Status transitions** (Open Question #5): Simple field update for v1. Event sourcing is overkill - status changes aren't complex enough to warrant event log. Add `updated_at` timestamp for basic audit.

---

Once these 8 questions are answered, this feature will be ready for detailed engineering specification. The core structure is solid - these are genuine ambiguities, not missing fundamentals.