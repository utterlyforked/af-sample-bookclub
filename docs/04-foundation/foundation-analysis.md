# Foundation Analysis & Build Plan

**Date**: December 19, 2024
**Status**: Ready for Engineering Specification
**Features Analyzed**: 5 features (Tool Listing & Discovery, Borrowing Request & Communication, User Profiles & Community Verification, Loan Tracking & Management, Neighborhood-Based Communities)

---

## Executive Summary

After analyzing 5 features for the neighborhood tool sharing platform, I've identified 7 foundation elements that must be built before feature development can begin. The foundation blocks all features and will take approximately 2 weeks to complete.

Features can then be built in 3 phases:
- **Phase 1** (2 features): Can build in parallel after foundation
- **Phase 2** (2 features): Depend on Phase 1 entities
- **Phase 3** (1 feature): Depends on Phase 2 completion

Total estimated timeline: 2 weeks foundation + 6-8 weeks feature development = 8-10 weeks to MVP.

---

## Foundation Elements

These are shared components used by multiple features.

### 1. Core Entities

**User**
- **Purpose**: Authentication, identity, and platform participation
- **Used by**: All 5 features
- **Properties**: Id, Email, PasswordHash, FullName, PostalCode, StreetName, CreatedAt, LastActiveAt, EmailNotificationsEnabled, AddressLastUpdatedAt
- **Relationships**: 
  - Belongs to one Community
  - Creates many Tools (as owner)
  - Creates many BorrowingRequests (as borrower)
  - Receives many BorrowingRequests (as lender)
  - Gives many Ratings (as rater)
  - Receives many Ratings (as ratee)

**Community**
- **Purpose**: Geographic organization of users for local tool sharing
- **Used by**: Neighborhood-Based Communities (primary), Tool Listing & Discovery (filtering), User Profiles (display)
- **Properties**: Id, Name, PostalCode, CenterLatitude, CenterLongitude, RadiusMiles (default 1.5), MemberCount (cached), LastActivityAt, CreatedAt
- **Relationships**: 
  - Has many Users
  - Has many Tools (through users)
  - Has community guidelines (polymorphic)

**Tool**
- **Purpose**: Inventory items available for borrowing
- **Used by**: Tool Listing & Discovery (primary), Borrowing Requests (target), Loan Tracking (subject)
- **Properties**: Id, OwnerId, Title, Description, Category, Brand, SpecialInstructions, ConditionNotes, AvailabilityStatus, PostalCode, LastUpdatedAt, CreatedAt
- **Relationships**: 
  - Belongs to one User (owner)
  - Has many ToolPhotos
  - Has many BorrowingRequests
  - Has many Loans

### 2. Authentication & Authorization

**Required Capabilities**:
- User registration (email + password with address verification)
- Login with JWT token generation (HttpOnly cookies)
- Password reset flow via email
- Session management with rolling expiration
- Email verification for new accounts

**Authorization Policies Needed**:
- `Authenticated` - Any logged-in user
- `ToolOwner` - User owns the specific tool
- `CommunityMember` - User belongs to specific community
- `LoanParticipant` - User is either borrower or lender in specific loan
- `RequestParticipant` - User is either requester or tool owner in specific request

**Used by**: All features

**Technical Implementation**:
- ASP.NET Core Identity for user management
- JWT tokens stored in HttpOnly cookies
- Policy-based authorization using `[Authorize(Policy = "...")]`
- Custom authorization handlers for resource-based policies

### 3. API Infrastructure

**Required**:
- Base API structure (`/api/v1/...`)
- Global error handling (RFC 7807 ProblemDetails)
- CORS configuration for React frontend
- Request/response logging with Application Insights
- Rate limiting on authentication and mutation endpoints
- Model validation with FluentValidation
- Common response wrapper for consistent API shape

**Used by**: All features

**Technical Standards**:
- RESTful conventions with plural resource names
- HTTP status codes: 200 (success), 201 (created), 400 (validation), 401 (auth), 403 (forbidden), 404 (not found), 500 (server error)
- Consistent error format: `{ "type": "...", "title": "...", "status": 400, "detail": "...", "errors": {} }`
- Pagination parameters: `?page=1&pageSize=20`

### 4. Frontend Infrastructure

**Required**:
- Authentication state management (current user, login status)
- Protected route wrapper component
- API client with auth token injection
- Common layout components (Header with nav, Footer)
- Error boundaries for graceful failure handling
- Loading states and skeleton screens
- Toast notifications for user feedback
- Form validation patterns

**Used by**: All features

**Technical Patterns**:
- TanStack Query for server state management
- React Context for auth state
- Custom hooks for common operations (useAuth, useApi, useToast)
- Tailwind CSS utility classes only (no custom CSS)

### 5. Shared Services

**Email Service**
- **Purpose**: Send transactional emails
- **Used by**: 
  - User registration (welcome + verification)
  - Password reset flow
  - Borrowing requests (new request, approval, decline)
  - Loan reminders (due soon, overdue)
  - Community activity notifications
- **Integration**: SendGrid or AWS SES (per tech stack)
- **Features**: Template management, email queueing, retry logic

**Image Service**
- **Purpose**: Upload, resize, store tool photos
- **Used by**: Tool Listing & Discovery (tool photos), User Profiles (optional profile photo)
- **Integration**: Azure Blob Storage / S3 (per tech stack)
- **Features**: 
  - Upload validation (JPEG/PNG, 5MB max)
  - Automatic generation of 3 sizes (150x150, 400x300, 1200x900)
  - Compression (85% quality)
  - CDN integration for fast delivery

**Geocoding Service**
- **Purpose**: Convert postal codes to coordinates for distance calculations
- **Used by**: Neighborhood-Based Communities (community creation), Tool Listing & Discovery (search)
- **Integration**: Third-party geocoding API or static postal code database
- **Features**: Postal code validation, center point calculation, adjacent area lookup

### 6. Database Schema Foundation

**Core Tables**:
- `Users` (ASP.NET Identity tables)
- `Communities` 
- `Tools`
- `ToolPhotos`
- `BorrowingRequests` (foundation for Phase 2)
- `Loans` (foundation for Phase 2)
- `Ratings` (foundation for Phase 2)
- `Messages` (foundation for Phase 2)

**Critical Indexes**:
- `Users.Email` (unique, for login)
- `Users.PostalCode` (for community assignment)
- `Communities.CenterLatLng` (geospatial index for distance queries)
- `Tools.OwnerId` (foreign key)
- `Tools.Category` (for filtering)
- `Tools.PostalCode` (for location-based search)
- `ToolPhotos.ToolId` (foreign key)

**Migration Strategy**:
- Code-first with Entity Framework Core
- One migration per logical feature set
- Seed data for categories and initial communities

### 7. Background Job Infrastructure

**Purpose**: Handle scheduled tasks and async operations
**Used by**: Loan Tracking (reminders, overdue notifications), Community Management (stats updates), Email Service (delivery queue)

**Technical Implementation**:
- Hangfire for job scheduling
- Recurring jobs for daily/hourly tasks
- Fire-and-forget jobs for email sending
- Job dashboard for monitoring (admin only)

**Scheduled Jobs Needed**:
- Daily: Update community activity statistics
- Hourly: Check for due/overdue loans and send reminders
- Hourly: Check for auto-decline timers on pending requests
- Daily: Check for auto-confirm timers on pending returns

---

## Feature Dependency Analysis

### Feature: Tool Listing & Discovery (FEAT-01)

**Foundation Dependencies**:
- ✅ User entity (tool owners, created_at timestamps)
- ✅ Community entity (location-based search, postal code areas)
- ✅ Tool entity (the core feature entity)
- ✅ ToolPhoto entity (images)
- ✅ Authentication system (protected endpoints)
- ✅ API infrastructure (search, filtering)
- ✅ Image service (photo upload and processing)
- ✅ Geocoding service (distance calculations)

**Feature Dependencies**:
- None (can build immediately after foundation)

**Build Phase**: Phase 1

**Rationale**: Independent feature that only needs foundation elements. Creates the Tool entity and associated data that other features depend on. Natural starting point for feature development.

---

### Feature: Neighborhood-Based Communities (FEAT-05)

**Foundation Dependencies**:
- ✅ User entity (community membership)
- ✅ Community entity (the core feature entity)
- ✅ Authentication system (protected community pages)
- ✅ API infrastructure (community endpoints)
- ✅ Geocoding service (boundary calculations, adjacent communities)
- ✅ Background jobs (activity statistics updates)

**Feature Dependencies**:
- None (can build immediately after foundation)

**Build Phase**: Phase 1

**Rationale**: While Community entity is in foundation, the feature-specific functionality (guidelines, activity tracking, discovery mechanics) can be built in parallel with Tool Listing. These two features are completely independent.

---

### Feature: User Profiles & Community Verification (FEAT-03)

**Foundation Dependencies**:
- ✅ User entity (profile data)
- ✅ Community entity (neighborhood display)
- ✅ Authentication system (profile access control)
- ✅ API infrastructure (profile endpoints)
- ✅ Image service (profile photos)
- ✅ Rating entity (from foundation)

**Feature Dependencies**:
- Requires: Tool Listing & Discovery (needs Tool entity for "tools owned" display)
- Requires: Loan data (for "borrowing history" and "lending history" summaries)

**Build Phase**: Phase 2

**Rationale**: Profile pages need to display user's tools and loan history. Must wait for Tool entity (Phase 1) and loan-related entities to be created.

---

### Feature: Borrowing Request & Communication (FEAT-02)

**Foundation Dependencies**:
- ✅ User entity (request participants)
- ✅ Tool entity (request target)
- ✅ BorrowingRequest entity (from foundation)
- ✅ Message entity (from foundation)
- ✅ Authentication system (request access control)
- ✅ API infrastructure (request/message endpoints)
- ✅ Email service (request notifications)
- ✅ Background jobs (auto-decline timers)

**Feature Dependencies**:
- Requires: Tool Listing & Discovery (needs Tool entity and availability status)
- Optional: User Profiles (nice to show profiles when reviewing requests, but not blocking)

**Build Phase**: Phase 2

**Rationale**: Requests are made against Tools, so Tool entity must exist first. BorrowingRequest and Message entities can be in foundation schema, but feature implementation (request flow, messaging UI, conflict detection) waits for Tool Listing completion.

---

### Feature: Loan Tracking & Management (FEAT-04)

**Foundation Dependencies**:
- ✅ User entity (loan participants)
- ✅ Tool entity (loan subject)
- ✅ Loan entity (from foundation)
- ✅ BorrowingRequest entity (loans are activated requests)
- ✅ Authentication system (loan access control)
- ✅ API infrastructure (loan endpoints)
- ✅ Email service (reminders, overdue notifications)
- ✅ Background jobs (due date checks, auto-confirmations)

**Feature Dependencies**:
- Requires: Borrowing Request & Communication (loans are created from approved requests)
- Requires: Tool Listing & Discovery (loan subjects are tools)
- Optional: User Profiles (for displaying loan participants, but not blocking)

**Build Phase**: Phase 3

**Rationale**: Loans are a natural extension of approved borrowing requests. The loan lifecycle (active, return confirmation, completion) depends on the request system being functional. Must wait for Phase 2 completion.

---

## Build Phases

### Phase 0: Foundation (Blocks Everything)

**Duration Estimate**: 2 weeks

**Scope**:

**Database Layer**:
- Core entity definitions (User, Community, Tool, ToolPhoto, BorrowingRequest, Loan, Rating, Message)
- Database schema and migrations
- Entity relationships and navigation properties
- Critical indexes for performance
- Seed data for tool categories and initial communities

**Authentication System**:
- User registration with email verification
- Login with JWT (HttpOnly cookies)
- Password reset flow
- ASP.NET Core Identity configuration
- Authorization policies (ToolOwner, CommunityMember, etc.)

**API Infrastructure**:
- Base API structure (`/api/v1/`)
- Global error handling (RFC 7807 ProblemDetails)
- CORS configuration
- Request/response logging
- Rate limiting middleware
- Model validation with FluentValidation
- OpenAPI/Swagger documentation

**Frontend Shell**:
- React app structure with Vite
- Routing with React Router v6
- Authentication context and protected routes
- API client with TanStack Query
- Common layout components (Header, Footer)
- Error boundaries
- Loading states and skeletons
- Toast notification system
- Form components and validation patterns

**Shared Services**:
- Email service with template management (SendGrid/SES integration)
- Image upload service (Azure Blob / S3 integration)
  - Upload validation
  - Image processing (3 sizes)
  - CDN configuration
- Geocoding service (postal code to coordinates)
- Background job infrastructure (Hangfire setup)

**Deliverable**: Working app with:
- User registration/login functional
- Empty authenticated dashboard
- Basic infrastructure ready for features
- Image upload working
- Email sending functional
- Background jobs schedulable

**Success Criteria**:
- Can create account, verify email, login
- Can upload test images and see 3 sizes generated
- API returns consistent error format
- Frontend shows loading states properly
- Background job dashboard accessible to admins

---

### Phase 1: Independent Features (Parallel Development)

**Duration Estimate**: 3 weeks

**Features**:
- **Tool Listing & Discovery (FEAT-01)**: Full implementation of tool creation, photo management, search, filtering, and display
- **Neighborhood-Based Communities (FEAT-05)**: Community pages, guidelines, activity tracking, adjacent community discovery

**Why These Can Build in Parallel**:
- Tool Listing works with User, Community, Tool entities (all in foundation)
- Communities feature works with User, Community entities (all in foundation)
- No interdependencies between these two features
- Different UI areas (tools vs. communities)
- Different backend controllers and services

**Deliverable**: 
- Users can list tools with photos
- Users can search/filter tools by location and category
- Users can view community pages and activity
- Community guidelines are manageable
- Adjacent community discovery works

**Success Criteria**:
- Can create tool listing with 5 photos
- Search returns relevant results within 1.5-mile radius
- Can toggle "include nearby areas" and see expanded results
- Community page shows accurate member count and activity
- Tool listings show owner's postal code area

---

### Phase 2: Request & Profile Features

**Duration Estimate**: 2-3 weeks

**Features**:
- **Borrowing Request & Communication (FEAT-02)**: Request submission, approval/decline, messaging, date conflict detection
- **User Profiles & Community Verification (FEAT-03)**: Profile pages, rating display, borrowing/lending history

**Why Phase 2**:
- Both features need Tool entity from Phase 1
- Profiles need loan history data (basic structure in foundation, but display logic here)
- Requests operate on Tools, so tools must exist first
- Can build these two features in parallel (different UI areas)

**Deliverable**: 
- Users can send borrowing requests with project details
- Tool owners can approve/decline requests
- Built-in messaging works with email notifications
- User profiles show tools owned and loan history
- Rating system displays properly (submission comes in Phase 3)

**Success Criteria**:
- Can request tool and receive approval
- Auto-decline triggers after 48 hours
- Date conflicts are blocked appropriately
- Profile shows accurate tool count and community membership
- Messages send immediate email notifications

---

### Phase 3: Loan Lifecycle Management

**Duration Estimate**: 2 weeks

**Features**:
- **Loan Tracking & Management (FEAT-04)**: Loan activation, reminders, return confirmation, overdue handling, rating submission

**Why Phase 3**:
- Depends on approved BorrowingRequests from Phase 2
- Loan lifecycle is extension of request approval
- Rating submission happens after loan completion
- Most complex business logic (reminders, auto-confirmations, extensions)

**Deliverable**: Full MVP complete
- Loans activate when requests are approved
- Automated reminders for due dates
- Return confirmation workflow functional
- Overdue notifications sent appropriately
- Rating system allows mutual feedback after returns
- Extension requests work (2 maximum per loan)

**Success Criteria**:
- Loan appears in dashboard when request approved
- Reminder emails sent 1 day before due date
- Can mark tool as returned and owner confirms
- Auto-confirm triggers after 24 hours if owner doesn't respond
- Both parties can rate after completion (48-hour delay displays correctly)
- Loan history shows all statuses correctly

---

## Dependency Graph

```
Foundation (Phase 0)
    ├─► Tool Listing & Discovery (Phase 1) ────┐
    │                                           ├─► Borrowing Requests (Phase 2) ──┐
    │                                           │                                   │
    └─► Neighborhood Communities (Phase 1) ────┘                                   ├─► Loan Tracking (Phase 3)
                                                                                    │
        User Profiles & Verification (Phase 2) ─────────────────────────────────────┘
```

**Build Order Rules**:
1. Foundation must complete before any features
2. Phase 1 features (Tool Listing, Communities) can build in parallel
3. Phase 2 features (Requests, Profiles) wait for Tool Listing completion
4. Phase 2 features can build in parallel with each other
5. Phase 3 (Loan Tracking) waits for Request system completion
6. Rating submission is part of Phase 3 (after loan completion)

---

## Foundation Scope Definition

### What IS in Foundation

✅ **Entities used by 2+ features**
- User (used by all 5 features)
- Community (used by 3 features: Communities, Tool Listing, Profiles)
- Tool (used by 4 features: Tool Listing, Requests, Profiles, Loan Tracking)
- ToolPhoto (used by Tool Listing, Profiles)
- BorrowingRequest (schema only - used by Requests, Loan Tracking)
- Loan (schema only - used by Loan Tracking, Profiles)
- Rating (schema only - used by Profiles, Loan Tracking)
- Message (schema only - used by Requests)

✅ **Authentication/Authorization** (used by all features)

✅ **API patterns** that all features follow
- RESTful conventions
- Error handling format
- Validation approach
- Response wrappers

✅ **Frontend shell** that all pages use
- Layout components
- Authentication state
- Protected routing
- Error boundaries

✅ **Services** needed by multiple features
- Email service (Requests, Loan Tracking, Communities, Auth)
- Image service (Tool Listing, Profiles)
- Geocoding service (Communities, Tool Listing)

✅ **Background job infrastructure** (used by Loan Tracking, Communities)

### What is NOT in Foundation

❌ **Feature-specific business logic**
- Tool search ranking algorithm → Build in Tool Listing feature
- Request approval workflow → Build in Borrowing Requests feature
- Return confirmation logic → Build in Loan Tracking feature
- Rating display calculations → Build in Profiles feature
- Community guideline voting → Build in Communities feature

❌ **Feature-specific UI components**
- Tool listing cards → Build with Tool Listing
- Request form → Build with Borrowing Requests
- Loan dashboard widgets → Build with Loan Tracking
- Profile statistics displays → Build with Profiles
- Community activity feed → Build with Communities

❌ **Feature-specific validations**
- Tool title similarity detection → Build with Tool Listing
- Request date conflict checking → Build with Borrowing Requests
- Loan extension limit enforcement → Build with Loan Tracking
- Address update rate limiting → Build with Profiles

❌ **One-off integrations**
- Specific tool category list → Build with Tool Listing
- Postal code adjacency logic → Build with Communities
- Response time calculation → Build with Profiles

---

## Technical Decisions

### Database Design

**Approach**: Code-first migrations with Entity Framework Core

**Why**: Better version control, easier refactoring, team collaboration through C# code rather than SQL scripts.

**Shared Tables**:

```csharp
// Users - ASP.NET Identity extended
public class User : IdentityUser
{
    public string FullName { get; set; }
    public string PostalCode { get; set; }
    public string StreetName { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime LastActiveAt { get; set; }
    public bool EmailNotificationsEnabled { get; set; } = true;
    public DateTime? AddressLastUpdatedAt { get; set; }
    
    public Guid CommunityId { get; set; }
    public Community Community { get; set; }
    
    public ICollection<Tool> Tools { get; set; }
    public ICollection<BorrowingRequest> RequestsAsBorrower { get; set; }
    public ICollection<BorrowingRequest> RequestsAsLender { get; set; }
}

// Communities
public class Community
{
    public Guid Id { get; set; }
    public string Name { get; set; }
    public string PostalCode { get; set; }
    public double CenterLatitude { get; set; }
    public double CenterLongitude { get; set; }
    public double RadiusMiles { get; set; } = 1.5;
    public int MemberCount { get; set; } // cached
    public DateTime? LastActivityAt { get; set; }
    public DateTime CreatedAt { get; set; }
    
    public ICollection<User> Members { get; set; }
}

// Tools
public class Tool
{
    public Guid Id { get; set; }
    public Guid OwnerId { get; set; }
    public string Title { get; set; }
    public string Description { get; set; }
    public string Category { get; set; }
    public string? Brand { get; set; }
    public string? SpecialInstructions { get; set; }
    public string? ConditionNotes { get; set; }
    public ToolAvailabilityStatus AvailabilityStatus { get; set; }
    public string PostalCode { get; set; }
    public DateTime LastUpdatedAt { get; set; }
    public DateTime CreatedAt { get; set; }
    
    public User Owner { get; set; }
    public ICollection<ToolPhoto> Photos { get; set; }
    public ICollection<BorrowingRequest> BorrowingRequests { get; set; }
}

// ToolPhotos
public class ToolPhoto
{
    public Guid Id { get; set; }
    public Guid ToolId { get; set; }
    public int DisplayOrder { get; set; }
    public string ThumbnailUrl { get; set; }
    public string MediumUrl { get; set; }
    public string FullUrl { get; set; }
    public DateTime UploadedAt { get; set; }
    
    public Tool Tool { get; set; }
}
```

**Indexes**:
```csharp
// In DbContext.OnModelCreating()
builder.Entity<User>()
    .HasIndex(u => u.Email)
    .IsUnique();

builder.Entity<User>()
    .HasIndex(u => u.PostalCode);

builder.Entity<Community>()
    .HasIndex(c => new { c.CenterLatitude, c.CenterLongitude });

builder.Entity<Tool>()
    .HasIndex(t => t.OwnerId);

builder.Entity<Tool>()
    .HasIndex(t => t.Category);

builder.Entity<Tool>()
    .HasIndex(t => t.PostalCode);

builder.Entity<ToolPhoto>()
    .HasIndex(p => p.ToolId);
```

**Migration Strategy**:
- Foundation migration: Core entities (User, Community, Tool, ToolPhoto)
- Phase 1 migration: Feature-specific columns if needed
- Phase 2 migration: BorrowingRequest, Message entities
- Phase 3 migration: Loan, Rating entities

---

### API Patterns

**Convention**: RESTful with `/api/v1/[resource]`

**Examples**:
```
GET    /api/v1/tools              // List tools (with search/filter params)
POST   /api/v1/tools              // Create tool
GET    /api/v1/tools/{id}         // Get tool details
PUT    /api/v1/tools/{id}         // Update tool
DELETE /api/v1/tools/{id}         // Delete tool
POST   /api/v1/tools/{id}/photos  // Upload photos

GET    /api/v1/communities        // List communities
GET    /api/v1/communities/{id}   // Community details
PUT    /api/v1/communities/{id}/guidelines  // Update guidelines

POST   /api/v1/auth/register      // User registration
POST   /api/v1/auth/login         // Login
POST   /api/v1/auth/logout        // Logout
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
```

**Error Handling**: All errors return RFC 7807 ProblemDetails

```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "Validation Failed",
  "status": 400,
  "detail": "One or more validation errors occurred",
  "errors": {
    "Title": ["Tool name cannot exceed 100 characters"],
    "Photos": ["Maximum 5 photos allowed per tool"]
  }
}
```

**Authorization**: Policy-based using `[Authorize(Policy = "...")]`

```csharp
[Authorize(Policy = "ToolOwner")]
[HttpPut("api/v1/tools/{id}")]
public async Task<IActionResult> UpdateTool(Guid id, UpdateToolDto dto) { }

[Authorize(Policy = "Authenticated")]
[HttpPost("api/v1/tools")]
public async Task<IActionResult> CreateTool(CreateToolDto dto) { }
```

---

### Frontend Architecture

**Routing**: React Router v6

```typescript
// App.tsx routing structure
<Routes>
  <Route path="/" element={<Layout />}>
    <Route index element={<HomePage />} />
    <Route path="login" element={<LoginPage />} />
    <Route path="register" element={<RegisterPage />} />
    
    <Route element={<ProtectedRoute />}>
      <Route path="dashboard" element={<DashboardPage />} />
      <Route path="tools">
        <Route index element={<ToolListPage />} />
        <Route path=":id" element={<ToolDetailPage />} />
        <Route path="new" element={<CreateToolPage />} />
      </Route>
      <Route path="communities/:id" element={<CommunityPage />} />
      <Route path="profile/:userId" element={<ProfilePage />} />
    </Route>
  </Route>
</Routes>
```

**State Management**:
- **Server state**: TanStack Query
  ```typescript
  // Example: Fetch tools
  const { data: tools, isLoading, error } = useQuery({
    queryKey: ['tools', searchParams],
    queryFn: () => api.tools.search(searchParams),
  });
  ```

- **UI state**: React Context
  ```typescript
  // Auth context example
  const { user, login, logout, isAuthenticated } = useAuth();
  ```

- **No Redux** (per tech stack standards - TanStack Query handles caching and sync)

**Styling**: Tailwind CSS utility classes only

```tsx
// Component example
export function ToolCard({ tool }: { tool: Tool }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <img 
        src={tool.thumbnailUrl} 
        alt={tool.title}
        className="w-full h-48 object-cover rounded-md mb-3"
      />
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {tool.title}
      </h3>
      <p className="text-sm text-gray-600 line-clamp-2">
        {tool.description}
      </p>
    </div>
  );
}
```

**Common Patterns**:
```typescript
// Custom hooks for repeated logic
export function useToolSearch(initialParams: SearchParams) {
  const [params, setParams] = useState(initialParams);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['tools', params],
    queryFn: () => api.tools.search(params),
  });
  
  return { tools: data?.items, isLoading, error, params, setParams };
}

// Protected route wrapper
function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) return <LoadingSpinner />;
  if (!isAuthenticated) return <Navigate to="/login" />;
  
  return <Outlet />;
}
```

---

## Risks & Considerations

### Potential Issues

**1. Foundation Scope Creep**
- **Risk**: Team adds "nice to have" features to foundation that could wait for feature phases
- **Mitigation**: Strict rule - only shared elements used by 2+ features. Feature-specific logic waits for its phase.
- **Example**: Don't build tool category management UI in foundation - seed basic categories and add admin UI in Tool Listing feature.

**2. Geocoding API Costs**
- **Risk**: Third-party geocoding services charge per request, costs could escalate
- **Mitigation**: 
  - Use static postal code database for MVP (pre-loaded coordinates)
  - Cache postal code lookups aggressively
  - Only geocode on user registration and address updates (max 1/year per user)
- **Alternative**: Build postal code database during foundation using one-time bulk geocoding

**3. Image Storage Costs**
- **Risk**: Generating 3 sizes per photo (5 photos × 3 sizes = 15 files per tool) increases storage costs
- **Mitigation**: 
  - Implement image compression (85% quality saves significant space)
  - Set up CDN with proper caching headers
  - Consider lazy generation (create thumbnails on upload, medium/full on first request)
- **Monitoring**: Track storage usage and implement cleanup of deleted tool photos

**4. Background Job Reliability**
- **Risk**: Critical reminders (loan due dates, overdue notifications) might not send if Hangfire fails
- **Mitigation**:
  - Implement Hangfire with persistent storage (PostgreSQL)
  - Add job retry logic (3 attempts with exponential backoff)
  - Create admin dashboard to monitor failed jobs
  - Add fallback: Daily summary email showing all actions taken
- **Monitoring**: Alert on failed job count exceeding threshold

**5. Phase 2 Parallelization Challenges**
- **Risk**: Profiles and Requests features might have hidden dependencies discovered during development
- **Mitigation**:
  - Clearly define API contracts before starting Phase 2
  - Use feature branches and coordinate on shared endpoints
  - Daily standup to identify coupling issues early
- **Contingency**: If significant dependency discovered, sequence rather than parallelize

**6. Foundation Timeline (2 Weeks)**
- **Risk**: 2 weeks feels long before seeing features, team