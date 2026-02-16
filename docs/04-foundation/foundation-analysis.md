# Foundation Analysis & Build Plan

**Date**: 2025-01-14  
**Status**: Ready for Engineering Specification  
**Features Analyzed**: 5 features (Tool Listings, Borrowing Requests, User Profiles & Trust System, Borrow Tracking & Returns, Community & Location-Based Discovery)

---

## Executive Summary

After analyzing 5 features, I've identified **12 foundation elements** that must be built before feature development can begin. The foundation blocks all features and establishes the core infrastructure for authentication, data models, API patterns, and shared services.

Features can then be built in **3 phases**:
- **Phase 1** (2 features): Tool Listings and User Profiles can build in parallel after foundation completion
- **Phase 2** (2 features): Borrowing Requests and Community Discovery depend on Phase 1
- **Phase 3** (1 feature): Borrow Tracking depends on Phase 2

The critical path runs through Phase 2 (Borrowing Requests) before reaching the full transaction lifecycle in Phase 3.

---

## Foundation Elements

These are shared components used by multiple features.

### 1. Core Entities

**User**
- Purpose: Authentication, identity, and location for all platform interactions
- Used by: All features
- Properties: Id, Email, PasswordHash, DisplayName (FirstName + LastName), Neighborhood, Latitude, Longitude, LocationAccuracy ('precise' or 'postal_code'), ProfilePhotoUrl, Bio (max 300 chars), PhoneNumber, PhoneVerified, EmailVerified, AddressVerified, MemberSince, CreatedAt, UpdatedAt
- Relationships: Creates many Tools, Creates many BorrowRequests (as borrower), Receives many BorrowRequests (as owner), Has many UserFollows (as follower and followed), Has many Ratings (given and received)
- Cached Statistics: CachedToolsOwned, CachedToolsShared, CachedCurrentBorrows, CachedAverageRating, CachedRatingCount, StatsLastUpdated
- Timezone: UserTimezone (IANA format, e.g., "America/Los_Angeles") for reminder scheduling

**Tool**
- Purpose: Inventory of shareable tools
- Used by: Tool Listings (FEAT-01), Borrowing Requests (FEAT-02), Borrow Tracking (FEAT-04), Community Discovery (FEAT-05)
- Properties: Id, OwnerId (FK to User), Title (max 100 chars), Category (enum), Description (max 2000 chars), ConditionNotes (max 500 chars), Status (enum: Draft, Published, Borrowed, Unavailable), LocationLat, LocationLng, PrimaryPhotoId (FK to ToolPhoto), CreatedAt, UpdatedAt, PublishedAt
- Relationships: Belongs to User (owner), Has many ToolPhotos, Has many BorrowRequests, Referenced by many ActivityEvents
- Note: Location coordinates mirror owner's location (automatically synced)

**ToolPhoto**
- Purpose: Visual documentation of tool condition
- Used by: Tool Listings (FEAT-01)
- Properties: Id, ToolId (FK), ImageUrl, ThumbnailUrl, DisplayOrder, UploadedAt
- Relationships: Belongs to Tool
- Constraints: Max 5 photos per tool, HEIC/JPEG/PNG/WebP formats

**BorrowRequest**
- Purpose: Represents both request phase and active borrow phase (single entity lifecycle)
- Used by: Borrowing Requests (FEAT-02), Borrow Tracking (FEAT-04), User Profiles (FEAT-03)
- Properties: Id, ToolId (FK), BorrowerUserId (FK), OwnerUserId (FK), RequestedStartDate, RequestedEndDate, OriginalDueDate, CurrentDueDate, ProjectDescription (50-500 chars), Status (enum: Pending, Approved, Declined, Cancelled, Withdrawn, PickedUp, Returned, Completed), OwnerMessage (max 500 chars), DeclineReason (20-500 chars), WithdrawReason (20-500 chars), CreatedAt, RespondedAt, PickedUpAt, ReturnedAt, ConfirmedAt, RatingWindowClosesAt, OwnerTimezone
- Relationships: Belongs to Tool, Borrower (User), Owner (User); Has many RequestMessages, Has many ExtensionRequests, Has one ReturnConfirmation, Has many BorrowNotes
- Cached Snapshots: ToolTitleSnapshot, ToolDescriptionSnapshot, ToolPrimaryPhotoUrlSnapshot, ToolCategorySnapshot (preserved for transaction history)
- Constraints: Exclusion constraint on (ToolId, DateRange) WHERE Status = 'Approved' (prevents double-booking)

**Rating**
- Purpose: Trust system feedback after completed borrows
- Used by: User Profiles (FEAT-03), Borrow Tracking (FEAT-04)
- Properties: Id, TransactionId (FK to BorrowRequest where Status=Completed), RaterUserId (FK), RatedUserId (FK), Stars (1-5), ReviewText (max 500 chars), Visible (boolean, false until mutual rating or 7 days), CreatedAt
- Relationships: Belongs to BorrowRequest (transaction), Rater (User), Rated (User)
- Constraints: Unique index on (TransactionId, RaterUserId) prevents duplicate ratings

**UserFollow**
- Purpose: Social network for prioritizing tools from trusted neighbors
- Used by: Community Discovery (FEAT-05)
- Properties: Id, FollowerUserId (FK to User), FollowedUserId (FK to User), CreatedAt
- Relationships: Both FKs reference User table
- Constraints: Unique index on (FollowerUserId, FollowedUserId), check constraint prevents self-follows

### 2. Authentication & Authorization

**Required Capabilities**:
- User registration (email + password with ASP.NET Core Identity)
- Login with JWT token generation (HttpOnly cookies)
- Email verification flow (send verification email, confirm token)
- Password reset flow (request reset, email link, set new password)
- Session management (token refresh, logout)

**Authorization Policies Needed**:
- `Authenticated` - Any logged-in user (all protected endpoints)
- `ToolOwner` - User owns the specific tool being accessed
- `BorrowParticipant` - User is either borrower or owner in specific transaction
- `ProfileOwner` - User accessing their own profile data

**Used by**: All features

**Key Security Requirements**:
- Nullable reference types enabled (prevent null reference exceptions)
- JWT tokens in HttpOnly cookies (no localStorage exposure)
- HTTPS enforcement in production
- CORS properly configured for SPA
- Rate limiting on auth endpoints (prevent brute force)

### 3. API Infrastructure

**Required**:
- Base API structure (`/api/v1/...`)
- Global error handling with RFC 7807 ProblemDetails format
- CORS configuration for React SPA origin
- Request/response logging (Application Insights or Serilog)
- Rate limiting middleware (auth endpoints, mutation endpoints)
- OpenAPI/Swagger documentation generation

**Used by**: All features

**Standards**:
- RESTful conventions: GET (read), POST (create), PUT (replace), PATCH (partial update), DELETE (remove)
- Controller naming: `[Resource]Controller` (e.g., `ToolsController`, `BorrowRequestsController`)
- Action results: `ActionResult<T>` with explicit status codes (200, 201, 400, 403, 404, 409, 500)
- Async/await everywhere (no `.Result` or `.Wait()`)
- Validation with FluentValidation or DataAnnotations

### 4. Frontend Infrastructure

**Required**:
- React 18+ with TypeScript, Vite build tool
- Authentication state management (TanStack Query for user context)
- Protected route wrapper (redirect to login if not authenticated)
- API client with auth token injection (axios or fetch with interceptors)
- Common layout components (Header with notification bell, Navigation, Footer)
- Error boundaries for graceful failure handling
- Loading states (skeleton screens, spinners)
- Toast notification system for success/error feedback

**Used by**: All features

**Patterns**:
- Functional components only (no class components)
- TypeScript strict mode enabled (no `any` types)
- TanStack Query for server state (caching, refetching, pagination)
- React Context for UI state (auth user, theme, notification count)
- Tailwind CSS utility classes only (no custom CSS files)

### 5. Database Schema Foundation

**Tables in Foundation**:
- `Users` (ASP.NET Identity tables: AspNetUsers, AspNetRoles, AspNetUserRoles, AspNetUserClaims, AspNetUserLogins, AspNetUserTokens)
- `Tools`
- `ToolPhotos`
- `BorrowRequests` (covers entire transaction lifecycle)
- `Ratings`
- `UserFollows`

**Indexes Required**:
- `Users.Email` (unique, for login)
- `Users.LocationGeo` (GiST index for spatial queries: `CREATE INDEX idx_users_location ON users USING GIST (ll_to_earth(latitude, longitude))`)
- `Tools.OwnerId` (for "My Tools" queries)
- `Tools.LocationGeo` (GiST index for radius search)
- `BorrowRequests.BorrowerUserId` (for "I'm Borrowing" dashboard)
- `BorrowRequests.OwnerUserId` (for "I'm Lending" dashboard)
- `BorrowRequests.(ToolId, Status)` (for tool availability checks)
- `BorrowRequests.Exclusion` (GiST exclusion constraint for double-booking prevention)
- `Ratings.(RatedUserId, Visible)` (for profile rating calculations)
- `UserFollows.(FollowerUserId, FollowedUserId)` (unique, for follow relationship checks)

**Migrations Strategy**:
- Code-first with Entity Framework Core migrations
- No stored procedures (business logic in application layer)
- Migration naming: `YYYYMMDDHHMMSS_DescriptiveName.cs`
- Down migrations required for rollback capability

### 6. Geocoding & Location Service

**Purpose**: Convert addresses to lat/long coordinates for distance calculations

**Used by**: User Profiles (FEAT-03 - profile address), Tool Listings (FEAT-01 - tool location sync), Community Discovery (FEAT-05 - radius search)

**Integration**: Azure Maps API or Google Geocoding API (configurable via appsettings.json)

**Functionality**:
- Geocode address string to (latitude, longitude)
- Return accuracy level: 'precise' (address-level) or 'postal_code' (fallback if address fails)
- Store accuracy level in User.LocationAccuracy for UI warnings
- Reverse geocoding (lat/lng → neighborhood name) for "unknown" neighborhoods

**Error Handling**:
- If geocoding API fails, fall back to postal code geocoding
- If postal code fails, reject address with error: "Unable to verify address. Please check and try again."
- Log all geocoding failures for monitoring

**Caching**:
- Cache geocoding results in Redis for 30 days (key: `geocode:{address_hash}`)
- Reduces API costs and latency for duplicate addresses

### 7. Image Processing Service

**Purpose**: Upload, resize, compress, and store tool photos

**Used by**: Tool Listings (FEAT-01 - tool photos), User Profiles (FEAT-03 - profile photo), Borrow Tracking (FEAT-04 - damage report photos)

**Integration**: Azure Blob Storage or AWS S3 (configurable)

**Functionality**:
- Accept HEIC/JPEG/PNG/WebP formats (max 10MB per image)
- Convert HEIC to JPEG server-side using ImageSharp library
- Resize full image to max 1920px width (maintain aspect ratio)
- Generate thumbnail at 400px width
- Compress JPEG to quality 85
- Upload both versions to blob storage: `{container}/{entityType}/{entityId}/{photoId}.jpg` and `{photoId}_thumb.jpg`
- Return URLs for both versions

**Security**:
- Validate file signatures (magic bytes) to prevent disguised executables
- Scan for embedded scripts in image metadata
- Rate limit uploads (max 20 per user per hour)

**Storage Structure**:
```
toolshare-images/
  tools/
    {toolId}/
      {photoId}.jpg
      {photoId}_thumb.jpg
  users/
    {userId}/
      profile.jpg
      profile_thumb.jpg
  damage-reports/
    {returnConfirmationId}/
      {photoId}.jpg
```

### 8. Email Service

**Purpose**: Send transactional emails (auth, notifications, reminders)

**Used by**: Authentication (verification, password reset), Borrowing Requests (FEAT-02 - request notifications), Borrow Tracking (FEAT-04 - due date reminders), User Profiles (FEAT-03 - rating reminders)

**Integration**: SendGrid or Azure Communication Services (configurable)

**Email Types**:
- Welcome email (after registration)
- Email verification with token link
- Password reset with secure token link
- Borrow request notifications (immediate)
- Extension request notifications (immediate)
- Return marked notifications (immediate)
- Due date reminders (9:00 AM owner timezone, scheduled)
- Overdue reminders (daily at 9:00 AM, scheduled)
- Rating window reminders (Day 5 of 7-day window)
- Message digest notifications (2 hours after first unread)

**Template System**:
- HTML email templates with inline CSS (for email client compatibility)
- Razor views or Handlebars templates
- Variables: `{{userName}}`, `{{toolName}}`, `{{dueDate}}`, `{{actionUrl}}`
- All emails include unsubscribe link (footer)

**Delivery Tracking**:
- Log all sent emails to `EmailDeliveryLog` table
- Track bounces and failures from webhook callbacks
- Retry failed sends once after 5 minutes (then give up)

### 9. Background Job Infrastructure

**Purpose**: Scheduled and recurring tasks for reminders, stats updates, auto-confirmations

**Used by**: Borrow Tracking (FEAT-04 - reminders, auto-confirm), User Profiles (FEAT-03 - stats caching), Community Discovery (FEAT-05 - activity feed)

**Integration**: Hangfire with SQL Server storage (or Redis storage for higher performance)

**Job Types**:
- **Recurring Jobs** (cron-scheduled):
  - `UpdateUserStatistics` - every 1 minute (profile stats caching)
  - `SendDueDateReminders` - hourly (9:00 AM in each timezone)
  - `AutoConfirmReturns` - daily at 2:00 AM UTC (7-day rule)
  - `ExpireExtensionRequests` - daily at 2:00 AM UTC (72-hour timeout)
- **Fire-and-Forget Jobs** (triggered by events):
  - `SendEmailNotification` - triggered on borrow request approval
  - `UpdateToolLocations` - triggered when user changes address (if 50+ tools)
- **Delayed Jobs** (scheduled for future execution):
  - `SendMessageDigest` - 2 hours after first unread message

**Dashboard**:
- Hangfire web dashboard at `/hangfire` (admin-only access)
- Monitor job success/failure rates
- Retry failed jobs manually

### 10. Notification System

**Purpose**: Dual-channel delivery (email + in-app) for all user notifications

**Used by**: Borrowing Requests (FEAT-02), Borrow Tracking (FEAT-04), User Profiles (FEAT-03)

**Components**:
- **In-App Notification Center**:
  - Bell icon in header with unread count badge
  - Dropdown showing last 10 notifications
  - Full notification center page (`/notifications`)
  - Mark as read (individual or bulk)
  - Filter by type (Reminders, Returns, Extensions, Ratings)
- **Email Notifications**:
  - All critical notifications sent via email service
  - HTML templates matching in-app notification content
  - Action links (e.g., "View Request", "Confirm Return")
- **Notification Table** (`Notification`):
  - UserId, Type, Title, Content, ActionUrl, Read, CreatedAt, ReadAt
  - Frontend polls every 60 seconds or uses WebSocket for real-time updates

**Notification Types**:
- `Reminder_DueSoon` (1 day before due date)
- `Reminder_DueToday` (on due date)
- `Reminder_Overdue` (1, 3, 7+ days overdue)
- `Return_Marked` (borrower marked tool returned)
- `Return_Confirmed` (owner confirmed return)
- `Extension_Requested` (borrower requests extension)
- `Extension_Approved` (owner approves extension)
- `Extension_Denied` (owner denies extension)
- `Extension_TimedOut` (72-hour expiration)
- `Damage_Reported` (owner reports issue)
- `Rebuttal_Added` (borrower disputes damage)
- `Rating_Reminder` (Day 5 of rating window)
- `Rating_Mutual` (both parties rated, now visible)

### 11. Spatial Query Support (PostGIS)

**Purpose**: Efficient distance-based queries for tool discovery

**Used by**: Tool Listings (FEAT-01 - search by distance), Community Discovery (FEAT-05 - radius search, map view, stats)

**Setup**:
- Install PostGIS extension in PostgreSQL: `CREATE EXTENSION postgis;`
- Use `GEOGRAPHY` type for accurate earth-surface distance calculations
- Helper functions:
  - `ST_Distance(geography1, geography2)` - returns meters between two points
  - `ST_DWithin(geography, geography, meters)` - boolean check if within radius
  - `ST_MakePoint(longitude, latitude)::geography` - convert coords to geography type

**Example Query**:
```sql
-- Find tools within 5 miles (8046.72 meters)
SELECT 
  t.id,
  t.title,
  ST_Distance(
    ST_MakePoint(t.location_lng, t.location_lat)::geography,
    ST_MakePoint($user_lng, $user_lat)::geography
  ) / 1609.34 AS distance_miles
FROM tools t
WHERE ST_DWithin(
  ST_MakePoint(t.location_lng, t.location_lat)::geography,
  ST_MakePoint($user_lng, $user_lat)::geography,
  8046.72  -- 5 miles in meters
)
AND t.status = 'Published'
ORDER BY distance_miles ASC
LIMIT 20 OFFSET 0;
```

**Indexing**:
- GiST index on geography column: `CREATE INDEX idx_tools_location ON tools USING GIST (ST_MakePoint(location_lng, location_lat)::geography);`
- Dramatically speeds up radius queries (100x+ faster for large datasets)

### 12. Message Threading System

**Purpose**: In-app messaging between borrowers and owners about specific requests/borrows

**Used by**: Borrowing Requests (FEAT-02 - request coordination)

**Components**:
- **RequestMessage Table**:
  - Id, BorrowRequestId (FK), SenderUserId (FK), RecipientUserId (FK), MessageText (max 1000 chars), ReadAt, CreatedAt
- **UI**:
  - Message thread view on borrow request detail page
  - Text input with character counter
  - "Send" button (disabled if empty)
  - Read/unread indicators (gray/bold text)
- **Notifications**:
  - In-app notification when message received
  - Email digest 2 hours after first unread message (batched)
- **Message Retention**:
  - Permanent (no auto-deletion)
  - Read-only after transaction completes (no new messages)

**Constraints**:
- Messages only visible to borrower and owner (privacy)
- Cannot message before request approved (use request note instead)
- Messages remain accessible in transaction history indefinitely

---

## Feature Dependency Analysis

### Feature: Tool Listings (FEAT-01)

**Foundation Dependencies**:
- ✅ User entity (tool ownership)
- ✅ Tool entity (core data model)
- ✅ ToolPhoto entity (photo gallery)
- ✅ Authentication system (protect tool creation)
- ✅ Authorization (only owner can edit/delete)
- ✅ API infrastructure
- ✅ Frontend shell (protected routes, layouts)
- ✅ Image processing service (photo upload, HEIC conversion)
- ✅ Geocoding service (tool location from owner address)
- ✅ Spatial query support (distance calculations)

**Feature Dependencies**:
- None (can build immediately after foundation)

**Build Phase**: Phase 1

**Rationale**: Independent of other features - creates the inventory that other features consume. Only needs foundation infrastructure and services. Can build in parallel with User Profiles.

---

### Feature: User Profiles & Trust System (FEAT-03)

**Foundation Dependencies**:
- ✅ User entity (profile data)
- ✅ Authentication system (profile access control)
- ✅ Authorization (only owner can edit profile)
- ✅ API infrastructure
- ✅ Frontend shell
- ✅ Image processing service (profile photo upload)
- ✅ Geocoding service (address to lat/lng)
- ✅ Email service (verification emails)
- ✅ Background jobs (stats caching every 1 minute)

**Feature Dependencies**:
- Partial: Rating entity defined in foundation, but rating submission workflow depends on BorrowRequest.Status = 'Completed' (from FEAT-04)
- Can build profile view, edit, verification badges in Phase 1
- Rating submission UI built in Phase 3 (after Borrow Tracking creates completed transactions)

**Build Phase**: Phase 1 (profile management), Phase 3 (rating submission)

**Rationale**: Profile management (view, edit, verification) is independent and foundational for other features. Rating submission is deferred until Phase 3 when completed transactions exist to rate. Split implementation is acceptable - core profile functionality doesn't block Phase 2 features.

---

### Feature: Borrowing Requests (FEAT-02)

**Foundation Dependencies**:
- ✅ User entity
- ✅ Tool entity
- ✅ BorrowRequest entity
- ✅ RequestMessage entity
- ✅ Authentication system
- ✅ Authorization policies (BorrowParticipant)
- ✅ API infrastructure
- ✅ Frontend shell
- ✅ Email service (request notifications)
- ✅ Notification system (dual-channel delivery)
- ✅ Message threading system

**Feature Dependencies**:
- **Requires**: Tool Listings (FEAT-01) - users must be able to browse and view tools before requesting them
- **Requires**: User Profiles (FEAT-03 - Phase 1) - owners review borrower profiles when approving requests
- Tool.Status must be 'Published' and CurrentBorrowId must be null to allow requests

**Build Phase**: Phase 2

**Rationale**: Depends on Tool Listings for tool inventory and User Profiles for trust signals. Creates approved BorrowRequests that Borrow Tracking (Phase 3) transitions through active borrow states.

---

### Feature: Borrow Tracking & Returns (FEAT-04)

**Foundation Dependencies**:
- ✅ BorrowRequest entity (entire transaction lifecycle)
- ✅ ExtensionRequest entity
- ✅ ReturnConfirmation entity
- ✅ BorrowNote entity
- ✅ BorrowReminder entity
- ✅ Rating entity (submission workflow)
- ✅ Authentication system
- ✅ Authorization policies (BorrowParticipant)
- ✅ API infrastructure
- ✅ Frontend shell
- ✅ Email service (reminders, notifications)
- ✅ Notification system
- ✅ Background jobs (reminders, auto-confirm)
- ✅ Image processing service (damage report photos)

**Feature Dependencies**:
- **Requires**: Borrowing Requests (FEAT-02) - creates approved BorrowRequests that this feature manages
- **Requires**: User Profiles (FEAT-03 - Phase 1) - displays borrower/owner info on tracking dashboard
- BorrowRequest.Status must be 'Approved' before tracking begins

**Build Phase**: Phase 3

**Rationale**: Depends on Borrowing Requests creating approved transactions. Completes the transaction lifecycle (Active → Returned → Completed). Enables rating submission (User Profiles Phase 3 component).

---

### Feature: Community & Location-Based Discovery (FEAT-05)

**Foundation Dependencies**:
- ✅ User entity (location data)
- ✅ Tool entity
- ✅ UserFollow entity
- ✅ ActivityEvent entity (not yet mentioned - see below)
- ✅ Authentication system
- ✅ API infrastructure
- ✅ Frontend shell
- ✅ Spatial query support (radius search)
- ✅ Geocoding service (neighborhood names)

**New Foundation Entity Required** (missed in initial analysis):
- **ActivityEvent**: Represents community activity feed events
  - Id, EventType (enum: NewToolListed, SuccessfulBorrow), ToolId, ToolName, ToolCategory, Neighborhood, CreatedAt
  - Used by: Community Discovery (FEAT-05)
  - Created when: Tool.Status transitions to 'Published' (NewToolListed), BorrowRequest.Status transitions to 'Completed' (SuccessfulBorrow)

**Feature Dependencies**:
- **Requires**: Tool Listings (FEAT-01) - tools must exist to show on map and search results
- **Requires**: User Profiles (FEAT-03 - Phase 1) - follow system requires profiles, stats require cached statistics
- Tool.Status = 'Published' for discovery visibility
- UserFollow relationships for "My Network" view

**Build Phase**: Phase 2

**Rationale**: Depends on Tool Listings for inventory and User Profiles for social features (following, stats). Can build in parallel with Borrowing Requests - both consume Phase 1 outputs without depending on each other. Map view, search, and follow system are independent of request/borrow workflows.

---

## Build Phases

### Phase 0: Foundation (Blocks Everything)

**Duration Estimate**: 2-3 weeks (2 backend engineers + 1 frontend engineer)

**Scope**:

**Backend**:
- Database schema with all foundation tables (Users, Tools, ToolPhotos, BorrowRequests, Ratings, UserFollows, RequestMessages, ExtensionRequests, ReturnConfirmations, BorrowNotes, BorrowReminders, Notifications, EmailDeliveryLog, ActivityEvents)
- EF Core code-first models and migrations
- PostGIS setup and spatial query helpers
- ASP.NET Core Identity integration (registration, login, JWT cookies)
- Authorization policies (Authenticated, ToolOwner, BorrowParticipant, ProfileOwner)
- Base API controllers (UsersController, placeholder for others)
- Global error handling middleware (ProblemDetails)
- CORS configuration
- Rate limiting middleware
- Geocoding service integration (Azure Maps or Google)
- Image processing service (ImageSharp + Azure Blob Storage)
- Email service integration (SendGrid or Azure Communication Services)
- Hangfire setup (recurring job infrastructure)
- Notification service (create Notification records, send emails)

**Frontend**:
- React + TypeScript + Vite project setup
- Tailwind CSS configuration
- Authentication context (TanStack Query for user state)
- Protected route wrapper
- API client with auth token interceptor (axios)
- Common layout components (Header with logo/nav/notifications bell, Footer)
- Error boundary
- Toast notification system (react-hot-toast or similar)
- Loading skeleton components
- Empty state components
- Login/Register pages (functional, not styled heavily)
- Basic home page shell ("Welcome to ToolShare - Add your first tool!")

**Deliverable**: Working app with:
- Users can register, verify email, log in, log out
- Authenticated users see empty dashboard ("No tools yet - list your first one!")
- Protected routes redirect to login if not authenticated
- API returns proper error responses (ProblemDetails format)
- Background job dashboard accessible at `/hangfire` (admin only)
- Database schema deployed with all tables and indexes
- All shared services functional (geocoding, image upload, email, notifications)

**Acceptance Criteria**:
- New user can register with address, system geocodes to lat/lng
- Email verification link works (token validation, user.EmailVerified set to true)
- Login returns JWT in HttpOnly cookie, subsequent API calls authenticated
- Password reset flow works end-to-end
- Image upload endpoint accepts HEIC, converts to JPEG, returns URLs
- Geocoding service converts address to coordinates and returns accuracy level
- Email service sends test email successfully
- Hangfire job can be scheduled and executed

---

### Phase 1: Core Inventory & Profiles (Parallel Development)

**Duration Estimate**: 2-3 weeks (can overlap with Foundation final week)

**Features**:
- **Tool Listings (FEAT-01)**: Full implementation
- **User Profiles (FEAT-03 - Part 1)**: Profile view, edit, verification badges, statistics display (no rating submission yet)

**Deliverable**: 
- Users can list tools with photos, search for tools by distance, view tool details
- Users can view/edit profiles, verify phone, see trust badges, view transaction history (empty until Phase 3)
- Foundation infrastructure validated through real feature usage

**Why These Two**:
- Both are foundational for Phase 2 features (requests depend on tool inventory and profile trust signals)
- Independent of each other (no shared business logic beyond foundation entities)
- Can be built by separate engineers in parallel
- Validates foundation architecture under real feature load

**Critical Path Items**:
- Tool search pagination and distance sorting (tests spatial query performance)
- Image upload flow with HEIC conversion (tests image service under load)
- Profile statistics caching (tests background job infrastructure)
- Phone verification SMS limits (tests rate limiting and tracking)

---

### Phase 2: Transactions & Discovery (Parallel Development)

**Duration Estimate**: 3-4 weeks

**Features**:
- **Borrowing Requests (FEAT-02)**: Full implementation
- **Community Discovery (FEAT-05)**: Full implementation

**Deliverable**:
- Users can request tools, owners can approve/decline, messaging works, notifications sent
- Users can browse map view, follow others, see activity feed, view community stats
- Approved BorrowRequests exist in database ready for Phase 3 tracking

**Why These Two**:
- Both depend on Phase 1 completions (tools inventory + profiles)
- Independent of each other (requests don't need map view, discovery doesn't need borrow workflow)
- Can be built by separate engineers in parallel
- Creates approved transactions that Phase 3 will manage

**Critical Path Items**:
- Double-booking prevention (tests exclusion constraint under concurrent approvals)
- Extension request timeout (tests scheduled job execution)
- Message digest batching (tests delayed job infrastructure)
- Auto-decline on date conflicts (tests database constraint error handling)
- Map pin clustering (tests frontend performance with 100+ pins)
- Activity event creation on tool publish (tests cross-feature integration)

---

### Phase 3: Transaction Lifecycle & Ratings (Sequential)

**Duration Estimate**: 3-4 weeks

**Features**:
- **Borrow Tracking & Returns (FEAT-04)**: Full implementation
- **User Profiles (FEAT-03 - Part 2)**: Rating submission UI, mutual rating reveal workflow

**Deliverable**:
- Full transaction lifecycle: Approved → PickedUp → Returned → Completed
- Due date reminders sent on schedule
- Return confirmation with damage reports
- Extension requests with 72-hour timeout
- Auto-confirmation after 7 days
- Rating submission after completion
- Rating visibility logic (mutual reveal or 7-day window)
- Complete platform with all features functional

**Why Sequential**:
- Borrow Tracking must be completed first to create Status='Completed' transactions that can be rated
- Rating submission UI depends on completed transaction data structure
- Phase 3 builds on Phase 2 outputs (approved BorrowRequests)
- No parallelization possible without artificial mocking

**Critical Path Items**:
- Timezone-aware reminder scheduling (tests hourly job finding correct timezone users)
- Auto-confirmation trigger (tests daily job finding expired returns)
- Rating window calculation (tests UTC timestamp math)
- Damage report rebuttal flow (tests cross