# QA Test Plan

**Date**: 2025-01-14  
**Scope**: Foundation + 5 features (Tool Listings, Borrowing Requests, User Profiles & Trust System, Borrow Tracking & Returns, Community & Location-Based Discovery)  
**Risk Level**: High

---

## Test Strategy

This test plan prioritizes unit tests for business logic (60% coverage), integration tests for cross-component workflows (30%), and narrow E2E tests for critical user journeys (10%). Given the social/transactional nature of ToolShare, the highest risk areas are transaction state management, geographic accuracy, and notification delivery - these receive extra coverage through integration and edge case testing.

**Test pyramid**:
- **Unit tests**: Business logic (rating calculations, overdue detection, distance sorting, status transitions), input validation (character limits, date ranges, geocoding results), service methods (geocoding, image processing, email formatting)
- **Integration tests**: Database constraints (double-booking prevention, uniqueness), background job execution (reminders, auto-confirmation, stats updates), API authentication/authorization flows, external service integration (geocoding, blob storage, email delivery)
- **E2E tests**: Complete user journeys only - registration → tool listing → borrow request → approval → tracking → return → rating (one happy path, one with issues reported)

---

## Foundation Test Plan

### Authentication

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Register — valid data | Valid email (test@example.com), strong password (TestPass123!), address (123 Main St, City, 55404) | User created with Status=201, EmailVerified=false, verification email queued |
| Register — duplicate email | Email already in AspNetUsers table | 409 Conflict with error: "An account with this email already exists" |
| Register — weak password | Password = "test" (< 8 chars, no uppercase/number/symbol) | 400 Bad Request with field-level errors: "Password must be at least 8 characters", "Password must contain uppercase letter", "Password must contain number", "Password must contain special character" |
| Register — invalid email format | Email = "notanemail" | 400 Bad Request with error: "Invalid email format" |
| Register — geocoding failure (address) | Address cannot be geocoded to coordinates | 400 Bad Request with error: "Unable to verify address. Please check and try again." |
| Register — geocoding fallback (postal code) | Address fails, postal code succeeds | User created with LocationAccuracy='postal_code', coordinates from postal code centroid |
| Login — valid credentials | Correct email/password | 200 OK, JWT token in HttpOnly cookie, user object in response body |
| Login — wrong password | Incorrect password | 401 Unauthorized with error: "Invalid email or password" (same message as unknown email - don't leak existence) |
| Login — unknown email | Non-existent email | 401 Unauthorized with error: "Invalid email or password" |
| Login — unverified email | User exists but EmailVerified=false | 403 Forbidden with error: "Please verify your email before logging in. Check your inbox for verification link." |
| Token validation — valid token | Valid JWT in cookie, request to protected endpoint | 200 OK with requested resource |
| Token validation — expired token | JWT with exp < NOW() | 401 Unauthorized with error: "Session expired. Please log in again." |
| Token validation — tampered token | JWT with modified signature | 401 Unauthorized with error: "Invalid session token" |
| Token refresh — valid refresh token | Refresh token within validity window | 200 OK with new JWT in cookie |
| Password reset — valid email | Email exists in system | 200 OK (always, don't leak existence), reset email queued if user exists |
| Password reset — token validation | Valid reset token, new password (TestPass456!) | 200 OK, password hash updated, old sessions invalidated |
| Password reset — expired token | Reset token with exp < NOW() | 400 Bad Request with error: "Reset link expired. Please request a new one." |
| Email verification — valid token | Valid verification token | 200 OK, EmailVerified=true, redirect to login |
| Email verification — already verified | Token for already-verified user | 200 OK with message: "Email already verified" |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Full registration flow | POST /api/v1/auth/register with valid data → check database | User row in AspNetUsers with hashed password (bcrypt), EmailVerified=false, coordinates stored, verification email in EmailDeliveryLog with Status=Sent |
| Geocoding address to coordinates | Register with address "123 Main St, Minneapolis, 55404" → geocoding service called | User.Latitude and User.Longitude populated with numeric values, User.LocationAccuracy='precise' |
| Geocoding postal code fallback | Mock address geocoding failure, postal code succeeds → register | User.LocationAccuracy='postal_code', coordinates from postal code centroid, no error returned to user |
| Token validation on protected endpoint | Register → Login → GET /api/v1/tools (protected) with JWT cookie | 200 OK with tools data, no 401 |
| Expired token rejection | Login → manually expire token → GET /api/v1/tools | 401 Unauthorized, cookie cleared |
| Concurrent registration (same email) | Two POST /api/v1/auth/register requests with same email submitted simultaneously | First succeeds (201), second fails (409 Conflict), database has only one user |
| Rate limiting on login endpoint | 10 POST /api/v1/auth/login requests from same IP within 1 minute | First 5 succeed/fail normally, 6th-10th return 429 Too Many Requests |

---

### Authorization Policies

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Authenticated policy — logged in user | Valid JWT, any protected endpoint | Policy passes, request proceeds |
| Authenticated policy — anonymous user | No JWT, protected endpoint | Policy fails, 401 Unauthorized |
| ToolOwner policy — correct owner | UserId=123, Tool.OwnerId=123, PUT /api/v1/tools/{id} | Policy passes, update allowed |
| ToolOwner policy — different owner | UserId=123, Tool.OwnerId=456, PUT /api/v1/tools/{id} | Policy fails, 403 Forbidden |
| BorrowParticipant policy — borrower | UserId=123, BorrowRequest.BorrowerId=123 | Policy passes |
| BorrowParticipant policy — owner | UserId=456, BorrowRequest.OwnerId=456 | Policy passes |
| BorrowParticipant policy — unrelated user | UserId=789, BorrowRequest has different borrower/owner | Policy fails, 403 Forbidden |
| ProfileOwner policy — own profile | UserId=123, GET /api/v1/users/123/settings | Policy passes |
| ProfileOwner policy — other profile | UserId=123, GET /api/v1/users/456/settings | Policy fails, 403 Forbidden |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Tool edit authorization | User A creates tool → User B attempts PUT /api/v1/tools/{id} | 403 Forbidden, tool unchanged in database |
| Borrow request message authorization | User A and B have active borrow → User C attempts POST /api/v1/borrow-requests/{id}/messages | 403 Forbidden, no message created |
| Profile settings authorization | User A attempts PATCH /api/v1/users/{User B's ID}/settings | 403 Forbidden, User B's settings unchanged |

---

### Geocoding Service

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Valid address geocoding | "123 Main St, Minneapolis, MN 55404" | Latitude=44.9778, Longitude=-93.2650, Accuracy='precise' |
| Postal code fallback | Address fails validation, postal code "55404" | Coordinates for postal code centroid, Accuracy='postal_code' |
| Complete geocoding failure | Invalid address, invalid postal code | Error: "Unable to verify address. Please check and try again." |
| Reverse geocoding (neighborhood) | Latitude=44.9778, Longitude=-93.2650 | Neighborhood="Downtown Minneapolis" |
| Reverse geocoding (unknown neighborhood) | Coordinates with no named neighborhood | Neighborhood="55404" (postal code fallback) |
| Cache hit | Address "123 Main St..." geocoded previously (in Redis cache) | Coordinates returned from cache, no API call to Azure Maps |
| Cache miss | Address not in cache | API call made, result cached with 30-day TTL, coordinates returned |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Full geocoding flow with caching | Geocode address → check Redis → geocode same address again | First call makes API request and caches result, second call retrieves from cache (no API call) |
| Azure Maps API timeout | Mock API timeout after 5 seconds | Fallback to postal code geocoding, if that fails return error to user |
| Invalid API key | Mock Azure Maps 401 Unauthorized | Log error, fallback to postal code, return error if postal code also fails |

---

### Image Processing Service

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| HEIC to JPEG conversion | HEIC file (10MB, 4000x3000px) | Full image: JPEG 1920px width, ~800KB; Thumbnail: 400px width, ~80KB; URLs returned |
| JPEG upload (no conversion) | JPEG file (5MB, 2000x1500px) | Full image: Resized to 1920px width if needed; Thumbnail: 400px; URLs returned |
| PNG upload | PNG file (8MB, 3000x2000px) | Converted to JPEG, resized, thumbnail generated, URLs returned |
| WebP upload | WebP file (3MB, 1600x1200px) | Processed as-is (already compressed), thumbnail generated, URLs returned |
| Oversized image | JPEG 5000x4000px | Resized to 1920px width (maintains aspect ratio: 1920x1536), thumbnail 400px width |
| File too large | 15MB image | 400 Bad Request with error: "Image must be under 10MB. Yours is 15MB. Try compressing it first." |
| Invalid file signature | .jpg extension but EXE magic bytes | 400 Bad Request with error: "Invalid image file. Please upload JPEG, PNG, WebP, or HEIC images only." |
| HEIC conversion failure | Corrupted HEIC file | 400 Bad Request with error: "We couldn't process this HEIC image. Try converting it to JPEG using your Photos app." |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Full upload flow to blob storage | Upload HEIC image → process → upload to Azure Blob | Full image at `tools/{toolId}/{photoId}.jpg`, thumbnail at `tools/{toolId}/{photoId}_thumb.jpg`, both URLs returned in response |
| Upload rate limiting | User uploads 21 images within 1 hour | First 20 succeed, 21st returns 429 Too Many Requests with error: "Upload limit reached (20 per hour). Try again later." |
| Blob storage upload failure | Mock Azure Blob 500 error | 500 Internal Server Error, image not saved to database, user sees generic error |

---

### Email Service

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Welcome email formatting | User registered with name="Alice Johnson" | HTML email with subject="Welcome to ToolShare, Alice!", body includes user's name, link to verify email |
| Email verification link | UserId=123, verification token="abc123xyz" | Email contains link: `https://toolshare.com/verify-email?token=abc123xyz&userId=123` |
| Password reset email | User requests reset, token="def456" | Email subject="Reset your ToolShare password", link expires in 1 hour, token in URL |
| Borrow request notification | Borrower="Bob", Tool="Drill", Owner="Alice" | Email to Alice with subject="Bob has requested your Drill", includes borrower profile link, approve/decline actions |
| Due date reminder | Tool="Drill", DueDate=tomorrow | Email subject="Reminder: Drill due back tomorrow", sent at 9:00 AM owner timezone |
| Unsubscribe link presence | Any transactional email | Footer contains: "Unsubscribe from these emails" link to `/settings/notifications` |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Email delivery logging | Send welcome email → check database | Row in EmailDeliveryLog with Status='Sent', SentAt timestamp, RecipientUserId |
| Email bounce handling | Mock SendGrid bounce webhook → receive bounce notification | EmailDeliveryLog updated with Status='Bounced', BouncedAt timestamp, ErrorMessage populated |
| Email retry on failure | Mock SMTP 500 error → wait 5 minutes → check retry | Email retried once, if still fails Status='Failed', no further retries |
| Template rendering | Send email with template variables {{userName}}, {{toolName}} | Rendered email has actual values ("Alice", "Drill"), no template syntax visible |

---

### Background Job Infrastructure (Hangfire)

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Recurring job registration | Register `UpdateUserStatistics` with cron "*/1 * * * *" | Job appears in Hangfire dashboard, Next Execution shows ~1 minute from now |
| Fire-and-forget job enqueue | Enqueue `SendEmailNotification` with userId=123, emailType="BorrowRequestApproved" | Job queued immediately, executed within 10 seconds |
| Delayed job scheduling | Schedule `SendMessageDigest` to run at `DateTime.UtcNow + 2 hours` | Job scheduled for future execution, not executed immediately |
| Job success logging | Job completes successfully | Hangfire dashboard shows "Succeeded" status, SucceededAt timestamp |
| Job failure logging | Job throws exception | Hangfire dashboard shows "Failed" status, exception message visible, job queued for retry |
| Job retry after failure | Job fails with transient error → automatic retry | Job retried up to 3 times with exponential backoff (1 min, 5 min, 15 min), marked Failed after 3rd attempt |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| UpdateUserStatistics recurring job | Create tool, complete borrow → wait for job execution → check cached stats | User.CachedToolsOwned incremented, User.CachedToolsShared incremented, StatsLastUpdated updated |
| SendDueDateReminders hourly job | Create borrow with DueDate=tomorrow → wait for 9:00 AM owner timezone | Email sent at 9:00 AM, BorrowReminder row created with ReminderType='OneDayBefore', SentAt timestamp |
| AutoConfirmReturns daily job | Borrower marks returned 8 days ago, owner never confirms → job runs at 2:00 AM UTC | BorrowRequest.Status='Completed', ReturnConfirmation created with AutoConfirmed=true, both parties notified |
| ExpireExtensionRequests daily job | Extension request created 73 hours ago, Status='Pending' → job runs | ExtensionRequest.Status='TimedOut', borrower notified with message "Extension request expired" |

---

### Notification System

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| In-app notification creation | Create notification with Type='Reminder_DueToday', UserId=123 | Row in Notifications table, Read=false, CreatedAt=NOW() |
| Email + in-app dual delivery | Send notification with DeliveredVia='Both' | Notification row created AND email queued in EmailDeliveryLog |
| Notification read marking | User clicks notification → mark as read | Notification.Read=true, ReadAt=NOW() |
| Bulk mark as read | User clicks "Mark all as read" → 15 unread notifications | All 15 updated to Read=true in single query |
| Unread count calculation | User has 8 unread notifications | GET /api/v1/notifications/unread-count returns `{ count: 8 }` |
| Notification filtering by type | GET /api/v1/notifications?type=Reminders | Returns only notifications with Type starting with "Reminder_" |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Borrow approval notification flow | Owner approves request → check notifications | Borrower receives in-app notification + email, notification contains tool name, approval message, pickup instructions link |
| Extension request notification batching | Borrower requests extension → check email queue | Email queued but not sent immediately, in-app notification sent immediately, unread badge incremented |
| Notification polling (frontend simulation) | Frontend polls GET /api/v1/notifications every 60 seconds | Each poll returns new notifications since last poll, Read=false |

---

### Spatial Query Support (PostGIS)

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Distance calculation (accurate) | Point A (44.9778, -93.2650), Point B (44.9500, -93.2000) | Distance ≈ 2.1 miles (calculated via ST_Distance) |
| Radius query (5 miles) | User location (44.9778, -93.2650), radius=5 miles | Tools within 5-mile radius returned, tools >5 miles excluded |
| Radius query (25 miles) | User location, radius=25 miles | All tools within 25 miles returned, sorted by distance ASC |
| Distance sorting accuracy | 3 tools at 1.2, 3.5, 0.8 miles | Results ordered: 0.8, 1.2, 3.5 miles |
| GiST index usage | EXPLAIN query with ST_DWithin | Query plan shows "Index Scan using idx_tools_location_gist" (not sequential scan) |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Tool search by distance | User at (44.9778, -93.2650) searches 10-mile radius → check results | All returned tools within 10 miles, sorted nearest first, distances displayed rounded to 0.5 mile |
| Map pin population | GET /api/v1/tools/nearby-map?radius=5 → check pin count | Pins for all available tools within 5 miles, includes lat/lng/toolId for clustering |
| Performance with 1000+ tools | Database with 1000 tools across metro → search 5-mile radius | Query completes in <200ms (GiST index optimization) |

---

### Message Threading System

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Message creation | POST /api/v1/borrow-requests/{id}/messages with text="What time for pickup?" | RequestMessage row created, SenderUserId=authenticated user, RecipientUserId=other party, ReadAt=null |
| Message length validation | Message with 1001 characters | 400 Bad Request with error: "Message must be 1000 characters or less (currently 1001)" |
| Message thread retrieval | GET /api/v1/borrow-requests/{id}/messages | Messages returned in chronological order (CreatedAt ASC), includes sender names |
| Read status update | Recipient views message thread → mark as read | All unread messages updated to ReadAt=NOW() |
| Message authorization | User C (not participant) attempts POST /api/v1/borrow-requests/{A-B transaction}/messages | 403 Forbidden |
| Message after completion | Borrow Status='Completed', user attempts to send message | 400 Bad Request with error: "Cannot send messages on completed transactions" |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Full message flow | Borrower sends message → owner receives notification → owner reads and replies → borrower gets notification | 2 RequestMessage rows, 2 in-app notifications, 2 email digests (if 2-hour window passes), messages visible in thread |
| Message digest batching | Borrower sends 3 messages in 5 minutes → wait 2 hours → check email | Owner receives 1 email digest with all 3 messages, subject="[Borrower] sent you messages about [Tool]" |

---

## Feature Test Plans

### Tool Listings (FEAT-01)

**Risk areas**: 
- Double-booking via overlapping edits (not blocked by feature design)
- Geocoding failures leaving tools without location
- Photo upload rate limiting bypass
- Tool deletion with active borrows (should prevent)

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Create tool — valid data | Title="DeWalt Drill", Category="Power Tools", Description="18V cordless", Photo URLs | Tool created with Status='Draft', 201 Created |
| Create tool — missing required field | Title missing | 400 Bad Request with error: "Title is required" |
| Create tool — title too long | Title with 101 characters | 400 Bad Request with error: "Title must be 100 characters or less" |
| Create tool — invalid category | Category="Weapons" (not in enum) | 400 Bad Request with error: "Invalid category. Must be one of: Power Tools, Hand Tools, Gardening, Ladders & Access, Automotive, Specialty Equipment" |
| Publish tool | PUT /api/v1/tools/{id}/publish, Status='Draft' → 'Published' | Tool.Status='Published', PublishedAt=NOW(), ActivityEvent created |
| Edit tool — owner | PUT /api/v1/tools/{id} with new description | Tool updated, UpdatedAt=NOW(), no snapshot creation until borrow |
| Edit tool — borrowed tool warning | Tool.Status='Borrowed', attempt edit | 200 OK with warning flag: "This tool is currently borrowed. Changes visible immediately." |
| Delete tool — available | DELETE /api/v1/tools/{id}, Status='Available' | Tool and ToolPhoto rows deleted, photo blobs deleted from storage, 204 No Content |
| Delete tool — borrowed | DELETE /api/v1/tools/{id}, Status='Borrowed' | 409 Conflict with error: "Cannot delete while borrowed. Please wait until returned." |
| Tool location sync (user address change) | User updates address → geocode → update tools | All user's tools have Location updated to new coordinates |
| Search tools by distance | User location, radius=5 miles, category filter="Power Tools" | Tools filtered by category, within radius, sorted by distance ASC |
| Search result distance rounding | Actual distance=2.34 miles | Displayed distance="2.5 miles" (rounded to nearest 0.5) |
| Photo reordering | PUT /api/v1/tools/{id}/photos with new display_order values | ToolPhoto rows updated, primary photo (display_order=1) reflected in Tool.PrimaryPhotoId |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Full tool creation flow | POST /api/v1/tools with valid data → upload 3 photos → publish | Tool in database with Status='Published', 3 ToolPhoto rows, ActivityEvent with Type='NewToolListed' |
| Tool editing preserves history | Create tool, create borrow request, edit tool title → check BorrowRequest | BorrowRequest.ToolTitleSnapshot contains original title, Tool.Title has new value |
| Tool deletion with past borrows | Create tool, complete borrow, delete tool → check history | BorrowRequest.ToolId=null, BorrowRequest.ToolTitleSnapshot preserved, tool detail page shows "(no longer listed)" |
| Concurrent edits (no locking) | User A and User B edit same tool simultaneously | Last writer wins (no conflict detection), UpdatedAt shows most recent edit timestamp |
| Photo upload rate limiting | User uploads 21 photos in 1 hour | First 20 succeed, 21st returns 429 Too Many Requests |
| HEIC photo conversion | Upload HEIC file → check blob storage | JPEG files created (full + thumbnail), original HEIC not stored |

#### Edge Cases

| Case | Why it matters | Expected behaviour |
|------|---------------|-------------------|
| Tool deleted mid-borrow | User deletes tool while someone has borrowed it | 409 Conflict prevents deletion, tool remains in database until returned |
| Address change during active borrow | Owner moves 50 miles away mid-borrow | Tool location updates immediately, borrower already has pickup location from messages |
| Search with postal-code accuracy + 1-mile radius | User's location is approximate, searches 1 mile | Warning banner shown: "Your location is approximate. Distances may vary." Results still returned. |
| Publish → Unpublish → Publish | User changes mind multiple times | Each publish transition creates new ActivityEvent (potential spam, acceptable for v1) |
| Delete tool with 100+ past borrows | Popular tool with extensive history | All BorrowRequest.ToolId set to null (cascade update), snapshot fields preserved |

---

### Borrowing Requests (FEAT-02)

**Risk areas**:
- Double-booking race conditions (handled by database constraint, must verify)
- Extension timeout edge cases (72-hour window calculation)
- Message digest batching failures (scheduled job reliability)
- Auto-decline notification spam (multiple pending requests)

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Create request — valid dates | StartDate=tomorrow, EndDate=7 days from now, ProjectDescription="Deck repair" | BorrowRequest created with Status='Pending', 201 Created |
| Create request — date validation (end before start) | StartDate=Jan 15, EndDate=Jan 10 | 400 Bad Request with error: "End date must be after start date" |
| Create request — date validation (too long) | StartDate=today, EndDate=15 days from now | 400 Bad Request with error: "Maximum borrow period is 14 days" |
| Create request — project description too short | ProjectDescription="Need it" (8 chars) | 400 Bad Request with error: "Project description must be 50-500 characters" |
| Create request — tool unavailable | Tool.Status='Borrowed' | 400 Bad Request with error: "This tool is not currently available for borrowing" |
| Approve request | PATCH /api/v1/borrow-requests/{id}/approve with OwnerMessage="Pick up after 6pm" | Status='Approved', RespondedAt=NOW(), borrower notified with owner's address/phone |
| Approve with date conflict (constraint violation) | Tool already approved Jan 10-15, attempt approve Jan 12-17 | 409 Conflict, second request auto-declined, owner notified "Someone else was just approved" |
| Decline request | PATCH /api/v1/borrow-requests/{id}/decline with DeclineReason="Tool needs repair" | Status='Declined', borrower notified with reason |
| Withdraw approval | PATCH /api/v1/borrow-requests/{id}/withdraw with WithdrawReason="Family emergency, need tool back" | Status='Withdrawn', borrower notified, tool calendar freed |
| Cancel request (borrower) | PATCH /api/v1/borrow-requests/{id}/cancel, Status='Approved' | Status='Cancelled', owner notified "Tool available again" |
| Send message | POST /api/v1/borrow-requests/{id}/messages with text="Can I pick up at 3pm?" | RequestMessage created, recipient notified immediately in-app, email digest scheduled for 2 hours |
| Extension request — valid | POST /api/v1/borrow-requests/{id}/extensions, NewDueDate=3 days from now, Reason="Project delayed" | ExtensionRequest created with Status='Pending', ExpiresAt=72 hours from now |
| Extension request — while 3+ days overdue | CurrentDueDate=4 days ago, attempt extension | 400 Bad Request with error: "Cannot request extension when 3+ days overdue. Contact owner directly." |

#### Integration Tests

| Scenario | Steps | Expected Result |
|----------|-------|----------------|
| Happy path: request approval | Borrower creates request → owner receives notification (email + in-app) → owner approves → borrower receives approval with address | BorrowRequest.Status='Approved', notifications in Notification table + EmailDeliveryLog, borrower sees owner's full address in notification |
| Double-booking prevention | Approve request A (Jan 10-15) → simultaneously approve request B (Jan 12-17) | First commit succeeds, second violates exclusion constraint, request B auto-declined with system message showing conflicting dates |
| Extension approval | Borrower requests extension → owner approves → check due date | BorrowRequest.CurrentDueDate updated to new date, OriginalDueDate unchanged, overdue flags cleared if applicable |
| Extension timeout | Borrower requests extension → 73 hours pass → background job runs | ExtensionRequest.Status='TimedOut', borrower notified "Request expired - owner didn't respond" |
| Message digest batching | Borrower sends 3 messages within 10 minutes → 2 hours pass → background job | Owner receives 1 email digest with all 3 messages, subject="[Borrower] sent you messages about [Tool]" |
| Auto-decline on tool unavailability | Owner marks tool unavailable → 5 pending requests exist | All 5 requests auto-declined with reason "Owner marked tool unavailable", borrowers notified |
| Withdrawal before pickup | Owner approves request → next day withdraws → check tool availability | Tool.Status back to 'Available', borrower notified with withdrawal reason, tool calendar freed for new requests |

#### Edge Cases

| Case | Why it matters | Expected behaviour |
|------|---------------|-------------------|
| Request submitted during date conflict | Request A approved Jan 10-15, Request B submitted for Jan 12-14 while A still pending | Request B creation succeeds (no blocking), but if owner approves B first, A auto-declines on later approval attempt |
| Extension request counter-offer | Borrower requests 7-day extension, owner counter-offers 3 days | ExtensionRequest with Type='CounterOffer' created, borrower can accept (updates date) or decline (date unchanged) |
| Message sent after cancellation | Borrower cancels request, then sends message | 400 Bad Request with error: "Cannot send messages on cancelled requests" |
| Multiple pending extensions | Borrower submits extension while previous still pending | 400 Bad Request with error: "You already have a pending extension request. Wait for response before requesting again." |
| Owner never responds to request | Request submitted, 30 days pass, no response | Request remains Status='Pending' indefinitely (no auto-expiration in v1) |

---

### User Profiles & Trust System (FEAT-03)

**Risk areas**:
- Rating visibility logic (mutual reveal vs. 7-day window)
- Statistics caching staleness (1-minute job failures)
- Phone verification bypass attempts (SMS limits)
- Timezone-aware rating window calculations

#### Unit Tests

| Test Case | Input | Expected Output |
|-----------|-------|----------------|
| Profile creation | User registers with name="Alice Johnson", neighborhood="Green Valley" | User.DisplayName="Alice Johnson", User.Neighborhood="Green Valley" |
| Profile edit — bio | PATCH /api/v1/users/{id}/profile with Bio="Love woodworking!" (19 chars) | User.Bio updated, 200 OK |
| Profile edit — bio too long | Bio with 301 characters | 400 Bad Request with error: "Bio must be 300 characters or less (currently 301)" |
| Profile edit — emoji support | Bio with "Happy to help! 😊🔨" | Bio saved with emojis intact, character count=19 (emojis=1 char each) |
| Profile photo upload | POST /api/v1/users/{id}/profile-photo with JPEG | Photo resized, thumbnail generated, User.ProfilePhotoUrl updated |
| Phone verification — send code | POST /api/v1/users/{id}/verify-phone with phone="+15035551234" | 6-digit code generated, SMS sent via Twilio, code expires in 10 minutes |
| Phone verification — correct code | POST /api/v1/users/{id}/verify-phone/confirm with correct code | User.PhoneVerified=true, verification badge added, 200 OK |
| Phone verification — wrong code (1st attempt) | POST confirm with incorrect code | 400 Bad Request with error: "Incorrect code. 2 attempts remaining." |
| Phone verification — 3 wrong codes | 3 incorrect