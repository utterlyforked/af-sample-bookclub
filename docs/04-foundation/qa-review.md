# QA Test Plan

**Date**: December 19, 2024
**Scope**: Foundation + 5 features (Tool Listing & Discovery, Borrowing Request & Communication, User Profiles & Community Verification, Loan Tracking & Management, Neighborhood-Based Communities)
**Risk Level**: Medium-High

---

## Test Strategy

This test plan prioritizes integration and E2E testing for cross-entity workflows (borrowing requests, loan lifecycle) while using unit tests for business rules and validation logic. The geographic features (postal code boundaries, adjacent communities) require special integration testing to verify distance calculations are accurate. Authentication and authorization policies need thorough coverage given the multi-role nature of the platform (tool owners, borrowers, community members).

**Test pyramid**:
- Unit tests: Business rule validation (date conflicts, loan limits, request limits), postal code validation, rating eligibility rules, extension limits, duplicate detection algorithms
- Integration tests: Database operations with relationships (users → communities → tools → requests → loans), email notifications, background job execution, image processing pipeline
- E2E tests: Critical user journeys only (register → list tool → request tool → approve → return → rate)

---

## Foundation Test Plan

### Authentication

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Register — valid data | email: test@example.com, password: Pass123!@#, fullName: John Smith, postalCode: 94610, streetName: Main Street | User created, 201 response, verification email sent |
| Register — duplicate email | Existing email: test@example.com, other valid fields | 409 Conflict with error: "Email already registered" |
| Register — weak password | password: pass123 (no special char, no uppercase) | 400, field error: "Password must contain uppercase, lowercase, number, and special character" |
| Register — missing address | Valid email/password, missing postalCode or streetName | 400, field errors: "Postal code is required", "Street name is required" |
| Register — invalid postal code | postalCode: 00000 (not in database) | 400, error: "Please enter a valid postal code" |
| Login — valid credentials | email: test@example.com, password: Pass123!@# | 200, JWT token in HttpOnly cookie, user object returned |
| Login — wrong password | email: test@example.com, password: WrongPass123! | 401, error: "Invalid email or password" |
| Login — unknown email | email: nonexistent@test.com, password: anything | 401, error: "Invalid email or password" (same as wrong password) |
| Login — unverified email | Valid credentials, email not verified | 401, error: "Please verify your email address" |
| Password reset — valid email | email: test@example.com | 200, reset email sent (don't reveal if email exists) |
| Password reset — unknown email | email: nonexistent@test.com | 200, no email sent (don't reveal if email exists) |
| Token validation — expired token | JWT with exp timestamp in past | 401, error: "Token expired" |
| Token validation — tampered token | JWT with modified payload | 401, error: "Invalid token" |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Full registration flow | POST /api/v1/auth/register → check database → check email queue | User in database, password hashed with bcrypt, verification email queued, user assigned to community based on postal code |
| Email verification flow | Register → get verification token from email → POST /api/v1/auth/verify-email | User.EmailVerified = true, can now login |
| Protected endpoint access | Login → use JWT token on GET /api/v1/tools | 200, tools returned |
| Expired token rejection | Login → wait for token expiry → use token | 401, must login again |
| Logout | POST /api/v1/auth/logout | Cookie cleared, subsequent requests with old token fail with 401 |

---

### Authorization Policies

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| ToolOwner policy — user owns tool | userId: 123, toolOwnerId: 123 | Policy succeeds |
| ToolOwner policy — user doesn't own tool | userId: 123, toolOwnerId: 456 | Policy fails, 403 Forbidden |
| CommunityMember policy — user in community | userId: 123, userCommunityId: abc, targetCommunityId: abc | Policy succeeds |
| CommunityMember policy — user not in community | userId: 123, userCommunityId: abc, targetCommunityId: xyz | Policy fails, 403 Forbidden |
| LoanParticipant policy — user is borrower | userId: 123, loan.borrowerId: 123 | Policy succeeds |
| LoanParticipant policy — user is lender | userId: 123, loan.tool.ownerId: 123 | Policy succeeds |
| LoanParticipant policy — user is neither | userId: 123, loan involves userId 456 and 789 | Policy fails, 403 Forbidden |
| RequestParticipant policy — user is requester | userId: 123, request.borrowerId: 123 | Policy succeeds |
| RequestParticipant policy — user is tool owner | userId: 123, request.tool.ownerId: 123 | Policy succeeds |
| RequestParticipant policy — user is neither | userId: 123, request involves userId 456 and 789 | Policy fails, 403 Forbidden |

---

### API Infrastructure

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Global error handler — validation error | FluentValidation exception with 2 field errors | 400, RFC 7807 format: `{ "type": "...", "title": "Validation Failed", "status": 400, "errors": { "Field1": ["Error 1"], "Field2": ["Error 2"] } }` |
| Global error handler — not found | EntityNotFoundException | 404, RFC 7807 format with "Resource not found" title |
| Global error handler — unauthorized | UnauthorizedAccessException | 401, RFC 7807 format |
| Global error handler — unhandled exception | Generic Exception | 500, RFC 7807 format, error details logged but not exposed to client |
| Rate limiting — within limit | 5 requests in 1 minute to /api/v1/auth/login | All succeed with 200 |
| Rate limiting — exceeds limit | 11 requests in 1 minute to /api/v1/auth/login (limit: 10) | First 10 succeed, 11th returns 429 Too Many Requests with Retry-After header |
| CORS — allowed origin | Request from configured frontend URL | CORS headers present, request succeeds |
| CORS — disallowed origin | Request from random domain | CORS error, request blocked |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Request logging | Make API request → check Application Insights logs | Request logged with method, path, status code, duration |
| Model validation | POST /api/v1/tools with invalid data → check response | 400, field-level errors in RFC 7807 format |
| Pagination | GET /api/v1/tools?page=2&pageSize=20 | Returns items 21-40, includes pagination metadata: `{ "page": 2, "pageSize": 20, "totalItems": 100, "totalPages": 5 }` |

---

### Database Schema & Migrations

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| User → Community relationship | Create user with communityId → query user with include | User.Community navigation property populated |
| User → Tools relationship | Create user → create 3 tools for user → query user.Tools | Collection contains 3 tools |
| Tool → ToolPhotos relationship | Create tool → upload 5 photos → query tool.Photos | Collection contains 5 photos in displayOrder |
| BorrowingRequest → Messages relationship | Create request → send 3 messages → query request.Messages | Collection contains 3 messages ordered by timestamp |
| Loan → Ratings relationship | Complete loan → submit 2 ratings → query loan.Ratings | Collection contains 2 ratings (borrower and lender) |
| Index performance — Users.Email | Query user by email 1000 times | Average query time < 5ms |
| Index performance — Tools.PostalCode | Query tools by postal code 1000 times | Average query time < 10ms |
| Index performance — Communities geospatial | Find communities within 5 miles of point, 1000 times | Average query time < 20ms |
| Cascade delete — User deletion | Delete user with 5 tools → check database | Tools deleted, ToolPhotos deleted, BorrowingRequests marked as cancelled |
| Migration rollback | Apply migration → rollback | Schema reverts cleanly, no orphaned tables/columns |

---

### Email Service

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Welcome email template | User object with name, email, verification token | HTML email with personalized greeting, verification link, proper formatting |
| Request notification template | BorrowingRequest object, tool name, borrower name | Email with project details, dates, link to request |
| Reminder email template | Loan object, tool name, due date | Email with tool name, due date, return instructions |
| Email validation — invalid recipient | to: "not-an-email" | Validation error, email not queued |
| Email validation — missing template variables | Template requires {userName}, data has no userName | Error: "Missing required template variable: userName" |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Email queueing | Trigger email send → check database | Email record in queue with status "Pending" |
| Email delivery via SendGrid | Process email queue → check SendGrid logs | Email sent, status updated to "Sent", SendGrid message ID recorded |
| Email retry on failure | Simulate SendGrid failure → wait for retry job | Email retried 3 times with exponential backoff (1min, 5min, 15min) |
| Email failure after max retries | Simulate 3 failed attempts → check final status | Email status = "Failed", error logged, admin notification sent |

---

### Image Service

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Upload validation — valid JPEG | 2MB JPEG file | Validation passes |
| Upload validation — valid PNG | 3MB PNG file | Validation passes |
| Upload validation — invalid file type | 1MB GIF file | 400, error: "Only JPEG and PNG images are allowed" |
| Upload validation — file too large | 6MB JPEG file | 400, error: "Image must be less than 5MB" |
| Upload validation — corrupted file | Corrupted JPEG header | 400, error: "Invalid or corrupted image file" |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Image upload and processing | Upload 4MB JPEG → wait for processing | 3 sizes generated (150x150, 400x300, 1200x900), all stored in blob storage, URLs returned |
| Image compression | Upload 4MB uncompressed PNG → check output size | Compressed to ~1MB total across 3 sizes (85% quality) |
| Thumbnail cropping | Upload 1200x800 image → check thumbnail | 150x150 thumbnail is center-cropped square |
| CDN integration | Upload image → request via CDN URL | Image served with proper caching headers (max-age=31536000) |
| Delete cleanup | Delete tool with 5 photos → check blob storage | All 15 blob files deleted (5 photos × 3 sizes) |

---

### Geocoding Service

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Valid postal code lookup | postalCode: 94610 | Returns { latitude: 37.8044, longitude: -122.2712, city: "Oakland", state: "CA" } |
| Invalid postal code | postalCode: 00000 | Returns null or error: "Postal code not found" |
| Distance calculation | point1: (37.8044, -122.2712), point2: (37.8144, -122.2812) | Distance: ~0.8 miles (using Haversine formula) |
| Adjacent postal codes | postalCode: 94610, radiusMiles: 5 | Returns array of postal codes within 5 miles: [94611, 94609, 94618, ...] |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Postal code caching | Look up 94610 → look up 94610 again → check cache | Second lookup hits cache, no external API call |
| Community boundary calculation | Create community for 94610 → calculate boundary points | 1.5-mile radius circle with 8 boundary points stored |

---

### Background Jobs

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Hangfire job scheduling | Schedule recurring job "UpdateCommunityStats" | Job appears in Hangfire dashboard, executes on schedule |
| Job retry on failure | Job throws exception → check Hangfire | Job retried 3 times with exponential backoff, then marked failed |
| Fire-and-forget job | Queue email send job → check execution | Job executes once, completes, removed from queue |
| Recurring job execution | Create daily job → advance system clock 24 hours | Job executes exactly once in 24-hour period |
| Job dashboard access | Login as admin → visit /hangfire | Dashboard loads, shows active/failed/scheduled jobs |
| Job dashboard — non-admin | Login as regular user → visit /hangfire | 403 Forbidden |

---

## Feature Test Plans

### Feature: Tool Listing & Discovery (FEAT-01)

**Risk areas**: Duplicate detection algorithm may have false positives, search ranking could produce unexpected results, postal code distance calculations must be accurate for trust

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Create tool — valid data | title: "Cordless Drill", description: "18V Makita", category: "Power Tools", 1 photo | Tool created, 201, owner assigned to current user |
| Create tool — title too long | title: 101 character string | 400, error: "Tool name cannot exceed 100 characters" |
| Create tool — description too long | description: 1001 character string | 400, error: "Description cannot exceed 1000 characters" |
| Create tool — missing photo | title, description, category, 0 photos | 400, error: "At least one photo is required" |
| Create tool — too many photos | 6 photos uploaded | 400, error: "Maximum 5 photos allowed per tool" |
| Create tool — invalid category | category: "Cooking Tools" (not in list) | 400, error: "Invalid category" |
| Create tool — emoji in title | title: "Drill 🔧" | Tool created successfully, emoji counted as 1 character |
| Update tool — owner updates own tool | toolId, ownerId match current user | 200, tool updated |
| Update tool — non-owner attempts update | toolId, ownerId ≠ current user | 403, error: "You can only update your own tools" |
| Delete tool — owner deletes tool | toolId, ownerId match current user | 204, tool soft-deleted, photos deleted from blob storage |
| Delete tool — tool has active loan | toolId with active loan status | 400, error: "Cannot delete tool with active loans" |
| Search tools — text match scoring | query: "drill", 3 tools: "Drill" (exact), "Cordless Power Drill" (partial), "Tool set" (no match) | Results ordered: exact title match, partial match, no match excluded |
| Search tools — distance scoring | Same postal code: 100pts, 1 area away: 95pts, 2 areas away: 90pts | Tools ordered by score descending |
| Search tools — recently updated bonus | Tool updated 5 days ago vs 30 days ago | Recent tool gets +5 point bonus |
| Filter tools — by category | category: "Power Tools", 10 total tools (5 power tools) | Returns 5 power tools only |
| Filter tools — by availability | availabilityStatus: "Available", 10 tools (7 available) | Returns 7 available tools |
| Filter tools — by distance | postalCode: 94610, maxDistance: 1 area | Returns only tools in same postal code area |
| Duplicate detection — similar title | Existing tool: "Drill", new tool: "Dril" (typo) | Warning shown: "Similar listing found: Drill" with option to proceed or edit |
| Duplicate detection — 75% similarity threshold | Existing: "Cordless Drill", new: "Cordless Power Drill" | Warning triggered (82% similar) |
| Duplicate detection — below threshold | Existing: "Drill", new: "Saw" | No warning, proceeds normally |
| Inactive listing indicator — 30 days | Owner last active 31 days ago | Listing shows "Last active 1 month ago" in gray text |
| Inactive listing indicator — 90+ days | Owner last active 95 days ago | Listing shows "Last active 3+ months ago" with warning icon |
| Photo reordering | Upload 5 photos, drag photo 5 to position 1 | displayOrder updated: new order [5,1,2,3,4] |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Full tool creation flow | Login → POST /api/v1/tools with data → upload 3 photos → query database | Tool in database, 3 ToolPhoto records created with URLs, tool assigned to user's postal code |
| Tool with community assignment | Create tool → check tool.postalCode matches user.postalCode | Tool postal code = user postal code, searchable in user's community |
| Search by postal code + adjacent | Search from 94610 → check results | Returns tools from 94610 + adjacent codes (94611, 94609, 94618) |
| Photo deletion | Tool with 5 photos → delete photo 3 → check database and blob storage | ToolPhoto record deleted, 3 blob files removed (thumb, medium, full), other photos remain |
| Tool availability during loan | Tool approved for loan → check tool.availabilityStatus | Status = "On Loan", search excludes tool from available results |
| Tool availability after return | Loan completed → check tool.availabilityStatus | Status = "Available", tool appears in search again |

#### Edge Cases

| Case | Why it matters | Expected behaviour |
|------|---------------|-------------------|
| Empty tool list for new user | First-time visitor to community | Empty array response with message "No tools in your area yet. Be the first to share!", not 404 |
| Maximum photos (5) uploaded | User tries to add 6th photo | 400 error before upload starts, clear message: "Maximum 5 photos. Delete one to add another." |
| Concurrent tool updates | Two users (owner + viewer) load tool page, owner updates title | Viewer sees stale data until page refresh, no data corruption (optimistic concurrency not required for MVP) |
| Search with special characters | query: "drill & saw" | Search handles & as separator, matches either "drill" or "saw" |
| Very long tool title (exactly 100 chars) | User enters max length title | Accepted, displays fully on tool page, truncated with ellipsis in search results |
| Postal code with no adjacent codes | Rural postal code 99999 with no neighbors in database | Search returns only tools from 99999, no adjacent results |
| Tool category "Other Tools" | Generic category selected | Requires more detailed description (validation: description must be >100 chars for "Other Tools") |

---

### Feature: Borrowing Request & Communication (FEAT-02)

**Risk areas**: Date conflict detection must be bulletproof to prevent double-booking, auto-decline timing must be precise, message notification spam could overwhelm users

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Create request — valid data | toolId, dates: "2024-06-01 to 2024-06-05", projectDescription: "Building deck" | Request created, 201, owner notified via email |
| Create request — 10 pending limit reached | User has 10 pending requests, creates 11th | 400, error: "You have reached the maximum of 10 pending requests. Cancel existing requests first." |
| Create request — date conflict (overlap) | Tool approved for June 1-5, new request June 3-7 | 400, error: "Tool not available June 3-5. Available again starting June 6." |
| Create request — date conflict (same start) | Tool approved for June 1-5, new request June 1-3 | 400, error: "Tool not available June 1-3. Available again starting June 6." |
| Create request — date conflict (encompassing) | Tool approved for June 2-4, new request June 1-5 | 400, error: "Tool not available June 2-4. Available again starting June 5." |
| Create request — same day return/pickup | Tool return June 5, new request pickup June 5 | Request allowed (no conflict) |
| Create request — duplicate request for same tool | User has pending request for tool #123, creates another | 400, error: "You already have a pending request for this tool. Cancel it to submit new dates." |
| Approve request | toolOwnerId = currentUserId, requestId, optional message | Request status = "Approved", borrower notified, loan created with status "Active" |
| Decline request | toolOwnerId = currentUserId, requestId, reason message | Request status = "Declined", borrower notified with reason |
| Auto-decline trigger — exactly 48 hours | Request created Monday 2:00 PM, checked Wednesday 2:00 PM | Status changes to "Declined", reason: "No response within 48 hours", borrower notified |
| Auto-decline trigger — owner responded | Request created Monday 2 PM, owner sends message Tuesday 10 AM, checked Wednesday 2 PM | Auto-decline timer resets, request still "Pending" |
| Return initiation — borrower only | Borrower clicks "Mark as Returned", adds note | Loan status = "PendingReturn", owner notified to confirm |
| Return confirmation — owner confirms | Owner confirms return within 24 hours | Loan status = "Returned", both parties can rate |
| Return auto-confirm — no owner response | Borrower marks returned, owner doesn't respond for 24 hours | Loan status = "Returned" with note "Auto-confirmed", both can rate |
| Message sending | requestId, senderId (borrower or lender), message text | Message saved, recipient notified via email immediately |
| Message notification — user disabled | User.EmailNotificationsEnabled = false, receives message | In-app notification only, no email sent |
| Message reporting | User reports message, provides reason | Admin email sent with full context (reporter, reported user, message, request) |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Full request approval flow | Create request → owner approves → check database | Request status = "Approved", Loan created with status "Active", tool availability = "On Loan", both parties notified |
| Request with messaging | Create request → borrower sends question → owner replies → owner approves | 2 messages in thread, both parties received email notifications, request approved |
| Multiple requests for different tools | User creates 5 pending requests for 5 different tools | All succeed, user can still create 5 more (limit: 10) |
| Request limit enforcement | User at 10 pending requests → oldest request declined → user creates new request | New request succeeds (now 10 pending again) |
| Date conflict across requests | Tool approved June 1-10, request for June 5-8 blocked | Conflict detected, error shows available date: "June 11+" |
| Auto-decline background job | Create request → run auto-decline job 48 hours later | Request status = "Declined", borrower receives email |
| Return confirmation flow | Loan active → borrower marks returned → owner confirms → check ratings eligibility | Loan status = "Returned", both users can rate each other, rating deadline 48 hours from now |
| Return auto-confirm job | Mark returned → wait 24 hours → run auto-confirm job | Loan status = "Returned" with auto-confirm note |

#### Edge Cases

| Case | Why it matters | Expected behaviour |
|------|---------------|-------------------|
| Request for unavailable tool | Tool status = "On Loan" or "Unavailable" | 400 error: "This tool is not available for requests" (shouldn't happen if UI hides request button) |
| Owner approves then immediately changes mind | Owner clicks approve, request creates loan, owner wants to undo | No undo feature in MVP - owner must message borrower and resolve manually |
| Borrower deletes account with pending requests | User deletion with 3 pending requests | Requests cancelled with status "Borrower unavailable", owners notified |
| Message thread after request declined | Request declined, borrower sends follow-up message | Message allowed - enables clarification/discussion about future requests |
| Two owners respond to same request | Edge case: admin testing, impersonating owner | Only true owner (tool.ownerId) can approve/decline, others get 403 |
| Request dates in the past | User submits request with startDate: yesterday | 400 validation error: "Start date must be in the future" |
| Very long project description | 1000 character description (at limit) | Accepted, displays fully on request page |

---

### Feature: User Profiles & Community Verification (FEAT-03)

**Risk areas**: Rating system must prevent gaming/retaliation, profile privacy must protect addresses, verification must prevent fake accounts without being too restrictive

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Profile view — own profile | GET /api/v1/users/me | Returns full profile including private fields (email, full address) |
| Profile view — other user profile | GET /api/v1/users/{userId} | Returns public profile only (name, neighborhood, rating, history summary) |
| Address verification — valid | postalCode: 94610, streetName: "Main Street" | Verification passes, user assigned to community "Oakland 94610" |
| Address verification — invalid postal code | postalCode: 00000, streetName: anything | 400, error: "Please enter a valid postal code" |
| Address verification — postal code mismatch | Community: "Oakland", postalCode: 90210 (Los Angeles) | 400, error: "Postal code doesn't match selected neighborhood area" |
| Address update — within 1 year | User registered 6 months ago, attempts address change | 400, error: "Address can only be updated once per year. Last updated: [date]" |
| Address update — after 1 year | User registered 13 months ago, updates address | 200, address updated, community reassigned if needed, verification re-run |
| Profile completion percentage | User with name, address, no photo, no bio | Shows "60% complete - Add photo and bio" |
| Rating submission — loan completed | Loan status = "Returned", rater is borrower or lender | Rating saved with 48-hour display delay |
| Rating submission — not eligible | Loan status = "Active", user attempts to rate | 400, error: "You can only rate after the loan is completed" |
| Rating submission — already rated | User already submitted rating for loan #123 | 400, error: "You have already rated this loan" |
| Rating submission — rate self | User attempts to rate themselves | 400, error: "You cannot rate yourself" |
| Rating display — before 48 hours | Rating submitted Monday 2 PM, checked Tuesday 10 AM | Rating not visible yet, profile shows previous average |
| Rating display — after 48 hours | Rating submitted Monday 2 PM, checked Wednesday 3 PM | Rating now visible, profile average updated |
| Multiple ratings from same users | Alice and Bob complete 3 loans together | 3 separate ratings from Alice on Bob's profile, all visible with dates |
| Average rating calculation | User has ratings: 5, 4, 5, 3, 4 | Average: 4.2 stars, displayed as "4.2 ⭐ (5 ratings)" |
| Response time — quick responder | 10 messages, avg response time: 2 hours | Shows "Usually responds quickly" |
| Response time — slow responder | 15 messages, avg response time: 20 hours | Shows "Usually responds within a day" |
| Response time — insufficient data | 2 messages | No response time indicator shown |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Full verification flow | Register with address → system validates → check database | User.IsVerified = true, User.CommunityId assigned based on postal code |
| Profile with borrowing history | User completes 5 loans as borrower → view profile | Shows "5 tools borrowed" with dates and tool names |
| Profile with lending history | User completes 8 loans as lender → view profile | Shows "8 tools lent" with dates and borrower names |
| Profile with mixed history | User completes 3 loans borrowing, 5 lending → view profile | Shows both summaries accurately |
| Rating submission after loan | Complete loan → submit rating 5 stars + review → wait 48 hours | Rating appears on recipient's profile after delay |
| Multiple ratings update average | User has 4.0 avg from 5 ratings → receives new 5-star rating → check average | Average updates to 4.2 after 48-hour delay |
| Address update triggers community change | User in Oakland 94610 → moves to SF 94102 → updates address | User reassigned to SF community, tools postal code updated |

#### Edge Cases

| Case | Why it matters | Expected behaviour |
|------|---------------|-------------------|
| User with no completed loans | Brand new user views profile | Shows "No borrowing history yet" and "No lending history yet", not errors |
| User with only cancelled loans | 3 loans all cancelled before pickup | History shows cancelled status, no ratings allowed |
| Boundary postal code verification | Postal code 94610 is border between Oakland and Berkeley communities | Accept in either community (err on inclusion) |
| Rating retaliation | Alice rates Bob 1 star, Bob immediately rates Alice 1 star | Both ratings allowed - community will notice pattern in reviews |
| User changes name | Profile update changes fullName | Name updated immediately, visible on all future interactions, past loans show new name |
| Very long review text | 500 character review (at limit) | Accepted, displays fully on profile, truncated with "read more" in loan history |
| User attempts HTML in bio | bio: "<script>alert('xss')</script>" | HTML escaped, displays as plain text |
| Profanity filter false positive | bio: "I live in Scunthorpe" (contains profanity substring) | Overly aggressive filter acceptable for MVP - user can contact support |

---

### Feature: Loan Tracking & Management (FEAT-04)

**Risk areas**: Due date calculations and timezone handling, extension limit enforcement, overdue notification timing, auto-confirmation timing

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Loan activation — request approved | BorrowingRequest approved, startDate: June 1, endDate: June 5 | Loan created with status "Active", tool availability = "On Loan", reminders scheduled |
| Loan creation — set due date | endDate: "2024-06-15" | Loan.dueDate = "2024-06-15 23:59:59" in user's timezone |
| Due date reminder — 1 day before | Loan due June 15, check June 14 at 9 AM | Reminder email sent: "Your borrowed [tool] is due tomorrow" |
| Due date reminder — on due date | Loan due June 15, check June 15 at 9 AM | Reminder email sent: "Your borrowed [tool] is due today" |
| Overdue notification — 1 day | Loan due June 15, check June 16 at 9 AM | Email sent: "Your borrowed [tool] was due yesterday. Please return or contact lender." |
| Overdue notification — 3 days | Loan due June 15, check June 18 at 9 AM | Email sent: "Your borrowed [tool] is now 3 days overdue. This may affect your rating." |
| Overdue notification — no more after day 3 | Loan due June 15, check June 20 | No additional automated emails (day 5 overdue) |
| Extension request — first request | Loan active, 0 extensions, borrower requests 3 more days | Extension request created, owner notified |