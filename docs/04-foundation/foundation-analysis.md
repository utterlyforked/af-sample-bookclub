# Foundation Analysis & Build Plan

**Date**: February 15, 2025
**Status**: Ready for Engineering Specification
**Features Analyzed**: Tool Inventory Management, Tool Discovery & Search, Borrowing Request System, Loan Tracking & Returns

---

## Executive Summary

After analyzing 4 features, I've identified 7 foundation elements that must be built before feature development can begin. The foundation will take approximately 85 hours and blocks all features.

Features can then be built in 2 phases, with Phase 1 features buildable in parallel after foundation completion.

---

## Foundation Elements

These are shared components used by multiple features.

### 1. Core Entities

**User**
- Purpose: Authentication and identity for all platform interactions
- Used by: All features (tool ownership, borrowing, communications)
- Properties: Id, Email, Name, PhotoUrl, PasswordHash, CreatedAt, Location (neighborhood-level coordinates), IsActive
- Relationships: Owns many Tools, Creates many BorrowRequests, Participates in many Loans

**Tool**
- Purpose: Central inventory item that can be borrowed
- Used by: Tool Inventory (creation/management), Tool Discovery (search), Borrowing Request (target), Loan Tracking (what's borrowed)
- Properties: Id, OwnerId, Title, Description, Brand, Model, Category, EstimatedValue, YearPurchased, Condition, IsAvailable, IsDeleted, CreatedAt, UpdatedAt
- Relationships: Belongs to User (owner), Has many ToolPhotos, Target of many BorrowRequests, Subject of many Loans

**ToolPhoto**
- Purpose: Visual documentation of tools for discovery and condition tracking
- Used by: Tool Inventory (management), Tool Discovery (display), Loan Tracking (condition comparison)
- Properties: Id, ToolId, PhotoUrl, PhotoOrder, UploadedAt, IsDeleted
- Relationships: Belongs to Tool

### 2. Authentication & Authorization

**Required Capabilities**:
- User registration (email + password)
- Login with JWT token generation via HttpOnly cookies
- Password reset flow with email verification
- Session management and token refresh

**Authorization Policies Needed**:
- `Authenticated` - Any logged-in user
- `ToolOwner` - User owns the specific tool
- `LoanParticipant` - User is either borrower or owner in specific loan
- `RequestParticipant` - User is either requestor or tool owner in specific borrow request

**Used by**: All features require authentication and resource-specific authorization

### 3. API Infrastructure

**Required**:
- Base API structure (`/api/v1/...`)
- Global error handling (RFC 7807 ProblemDetails)
- CORS configuration for React frontend
- Request/response logging with Application Insights
- Rate limiting (authentication endpoints and file uploads)
- JWT authentication middleware
- Authorization policy framework

**Used by**: All features require consistent API patterns and error handling

### 4. Frontend Infrastructure

**Required**:
- Authentication state management (current user, login status)
- Protected route wrapper for authenticated pages
- API client with automatic auth token handling
- Common layout components (Header, Navigation, Footer)
- Error boundaries for graceful failure handling
- Loading states and spinners
- Toast notifications for user feedback

**Used by**: All features need authentication context and common UI patterns

### 5. Photo Upload & Storage Service

**Purpose**: Handle image uploads, processing, and storage for tools and loan documentation
**Used by**: Tool Inventory (tool photos), Loan Tracking (condition photos), Borrowing Request (message attachments)
**Integration**: Azure Blob Storage with synchronous resize/compress processing
**Capabilities**: 
- Upload validation (file types, size limits)
- Automatic resize to 1200px max width
- Compression for web optimization
- Secure URL generation with expiration
- Cleanup of deleted images

### 6. Email Service

**Purpose**: Send transactional emails for notifications and workflows
**Used by**: User registration (welcome emails), Password reset, Borrowing Request (notifications), Loan Tracking (reminders, overdue notifications)
**Integration**: SendGrid or AWS SES (per tech stack standards)
**Capabilities**:
- Template-based email generation
- Retry logic for failed deliveries
- Delivery tracking and monitoring
- Unsubscribe management (for non-critical emails)

### 7. Background Job Processing

**Purpose**: Handle time-based operations and automated state transitions
**Used by**: Loan Tracking (status transitions, reminder scheduling), Tool Discovery (search index updates), general cleanup tasks
**Integration**: Hangfire with Redis backing store
**Capabilities**:
- Scheduled job execution (daily, weekly)
- Recurring job management
- Job retry and failure handling
- Monitoring dashboard for job status

---

## Feature Dependency Analysis

### Feature: Tool Inventory Management

**Foundation Dependencies**:
- ✅ User entity (tool ownership)
- ✅ Tool entity and ToolPhoto (core functionality)
- ✅ Authentication system (protect tool management)
- ✅ API infrastructure (CRUD operations)
- ✅ Photo upload service (tool documentation)

**Feature Dependencies**:
- None (can build immediately after foundation)

**Build Phase**: Phase 1

**Rationale**: Independent feature that creates the supply side. Only needs foundation elements, no interdependencies with other features.

---

### Feature: Tool Discovery & Search

**Foundation Dependencies**:
- ✅ Tool entity and ToolPhoto (search targets)
- ✅ User entity (location-based search)
- ✅ Authentication system (personalized search)
- ✅ API infrastructure (search endpoints)

**Feature Dependencies**:
- Requires: Tool Inventory Management (needs tools to exist in database)

**Build Phase**: Phase 1

**Rationale**: Can build in parallel with Tool Inventory. Uses same Tool entity but focuses on read operations. Search functionality enables tool discovery once inventory exists.

---

### Feature: Borrowing Request System

**Foundation Dependencies**:
- ✅ User entity (borrower and owner)
- ✅ Tool entity (request target)
- ✅ Authentication system (protect requests)
- ✅ API infrastructure (request workflow)
- ✅ Email service (notifications)
- ✅ Photo upload service (message attachments)

**Feature Dependencies**:
- Requires: Tool Inventory Management (needs tools to request)
- Requires: Tool Discovery & Search (users find tools before requesting)

**Build Phase**: Phase 2

**Rationale**: Depends on tools existing and being discoverable. Creates new entities (BorrowRequest, RequestMessage) but builds on foundation tools.

---

### Feature: Loan Tracking & Returns

**Foundation Dependencies**:
- ✅ User entity (loan participants)
- ✅ Tool entity (loaned item)
- ✅ Authentication system (protect loan data)
- ✅ API infrastructure (loan management)
- ✅ Email service (reminders and notifications)
- ✅ Photo upload service (condition documentation)
- ✅ Background jobs (automated reminders and state transitions)

**Feature Dependencies**:
- Requires: Borrowing Request System (loans created from approved requests)

**Build Phase**: Phase 2

**Rationale**: Loans are created from approved borrow requests. Needs the BorrowRequest→LoanAgreement workflow to exist first.

---

## Build Phases

### Phase 0: Foundation (Blocks Everything)

**Scope**:
- Core entity definitions (User, Tool, ToolPhoto)
- Database schema and migrations with proper indexes
- Authentication system (register, login, JWT, password reset)
- Authorization policies and middleware
- API infrastructure (base controllers, error handling, CORS, logging)
- Frontend shell (routing, auth context, layout, common components)
- Photo upload service (validation, processing, storage)
- Email service integration (templates, delivery, monitoring)
- Background job infrastructure (Hangfire setup, Redis configuration)

**Effort Estimate**: ~85 hours
- Backend: 55 hours (DB design, auth, API patterns, services)
- Frontend: 25 hours (shell, auth flow, common components)
- Infrastructure: 5 hours (deployment, monitoring setup)

**Team**: 2 engineers (1 backend, 1 frontend) = 2.5 weeks

**Deliverable**: Working app with user registration/login, empty dashboard, photo upload capability, email notifications, basic job processing

---

### Phase 1: Core Features

Features that only depend on foundation (can build in parallel).

**Features**:
- Tool Inventory Management
- Tool Discovery & Search

**Effort Estimate**: ~75 hours total
- Tool Inventory Management: 45 hours (CRUD, photo management, validation)
- Tool Discovery & Search: 30 hours (search API, filtering, results display)

**Team**: 2 engineers can work in parallel (1 per feature)

**Timeline**: 2 weeks parallel development

**Deliverable**: Users can add tools and search/find available tools

---

### Phase 2: Transaction Features

Features that depend on Phase 1 features.

**Features**:
- Borrowing Request System (depends on Tool Inventory + Discovery)
- Loan Tracking & Returns (depends on Borrowing Request System)

**Effort Estimate**: ~85 hours total
- Borrowing Request System: 50 hours (request workflow, messaging, notifications)
- Loan Tracking & Returns: 35 hours (loan lifecycle, photo comparison, reminders)

**Team**: Can work in sequence or with 1-week overlap

**Timeline**: 2.5 weeks (or 3 weeks with overlap)

**Deliverable**: Full borrowing workflow from discovery to return

---

## Dependency Graph

```
Foundation (Phase 0)
    ├─► Tool Inventory (Phase 1) ────┐
    │                                ├─► Borrowing Requests (Phase 2) ─► Loan Tracking (Phase 2)
    └─► Tool Discovery (Phase 1) ────┘
```

**Build Order Rules**:
1. Foundation must complete before any features
2. Phase 1 features can build in parallel (both use Tool entity independently)
3. Borrowing Requests waits for both Phase 1 features (needs tools to exist and be discoverable)
4. Loan Tracking waits for Borrowing Requests (loans created from approved requests)

---

## Foundation Scope Definition

### What IS in Foundation

✅ **Entities used by 2+ features**
- User (used by all 4 features)
- Tool, ToolPhoto (used by all 4 features)

✅ **Authentication/Authorization** (used by all features)
- User registration, login, password reset
- JWT token management
- Authorization policies for resource access

✅ **Services needed by multiple features**
- Photo upload/storage (Tool Inventory, Loan Tracking, Borrowing Requests)
- Email notifications (User auth, Borrowing Requests, Loan Tracking)
- Background jobs (Loan Tracking, general maintenance)

✅ **API and frontend infrastructure** (used by all features)

### What is NOT in Foundation

❌ **Feature-specific entities**
- BorrowRequest (only for Borrowing Request System)
- LoanAgreement, LoanPhoto (only for Loan Tracking)
- RequestMessage (only for Borrowing Request System)

❌ **Feature-specific business logic**
- Search algorithms and filtering logic
- Request approval workflows
- Loan state machine transitions

❌ **Feature-specific UI components**
- Tool inventory forms
- Search results display
- Request messaging interface

---

## Technical Decisions

### Database Design

**Approach**: Code-first migrations with Entity Framework Core

**Shared Tables**:
- Users (with ASP.NET Identity integration)
- Tools (with soft delete via IsDeleted flag)
- ToolPhotos (with foreign key to Tools)

**Critical Indexes**:
- Users.Email (unique, for login)
- Tools.OwnerId (for inventory queries)
- Tools.Category + IsAvailable + IsDeleted (for search performance)
- Tools.Location fields (for geospatial search - using PostGIS extension)
- ToolPhotos.ToolId (for photo retrieval)

### API Patterns

**Convention**: RESTful with `/api/v1/[resource]` structure

**Error Handling**: All errors return RFC 7807 ProblemDetails format

**Authorization**: Policy-based using `[Authorize(Policy = "PolicyName")]` attributes

**Validation**: FluentValidation with consistent error response format

### Frontend Architecture

**Routing**: React Router v6 with protected route wrappers

**State Management**:
- Server state: TanStack Query for caching and synchronization
- UI state: React Context for authentication and global UI state
- No Redux (per tech stack standards)

**Styling**: Tailwind CSS utility classes with custom component library

### Photo Storage Strategy

**Processing**: Synchronous upload with immediate resize/compress

**Storage**: Azure Blob Storage with CDN for fast delivery

**Security**: Signed URLs with expiration for private tool photos

---

## Risks & Considerations

### Potential Issues

**1. Foundation Scope Creep**
- Risk: Adding feature-specific logic to foundation for convenience
- Mitigation: Strict rule - foundation only contains shared elements used by 2+ features

**2. Photo Storage Costs**
- Risk: Unlimited photo uploads could drive storage costs high
- Mitigation: Implement 5MB per photo limit, photo cleanup policies, monitoring dashboards

**3. Search Performance**
- Risk: Full-text search might not scale with large tool inventory
- Mitigation: Start with PostgreSQL full-text search, plan migration to dedicated search service if needed

**4. Email Delivery Reliability**
- Risk: Critical notifications (overdue tools) might not reach users
- Mitigation: Use reliable service (SendGrid/SES), implement retry logic, monitor delivery rates

### Open Questions

**Q: Should we implement real-time notifications for borrowing requests?**
- Recommendation: Start with email-only, add push notifications in v2 based on user feedback

**Q: How should we handle user location privacy vs search accuracy?**
- Recommendation: Use ZIP+4 level precision (already specified in requirements), allows ~0.1 mile accuracy

---

## Effort Summary

| Component | Hours | Calendar Time |
|-----------|-------|---------------|
| Foundation | 85h | 2.5 weeks (2 engineers) |
| Phase 1 Features | 75h | 2 weeks (parallel) |
| Phase 2 Features | 85h | 2.5 weeks (sequential) |
| **Total** | **245h** | **7 weeks** |

**Assumptions**:
- 2 engineers (1 backend-focused, 1 frontend-focused)
- Standard working hours (40h/week per person)
- No major technical blockers
- Requirements are clear from refined PRDs
- Testing time included in estimates

---

## Recommended Next Steps

1. **Review this analysis** - Product and Engineering alignment on foundation scope and build phases
2. **Create Foundation Engineering Spec** - Detailed technical implementation plan with database schema, API contracts, component architecture
3. **Set up development environment** - CI/CD pipeline, staging environment, monitoring tools
4. **Build Foundation** - 2.5 week sprint focused on shared infrastructure
5. **Create Phase 1 Engineering Specs** - Detailed specs for Tool Inventory and Tool Discovery while foundation builds
6. **Build Phase 1 Features** - Parallel development of inventory and search capabilities
7. **Build Phase 2 Features** - Sequential development of borrowing and loan tracking

---

## Appendix: Feature Requirements Matrix

| Feature | User | Tool | Auth | Photo Service | Email | Jobs | Phase |
|---------|------|------|------|---------------|-------|------|-------|
| Tool Inventory | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | 1 |
| Tool Discovery | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | 1 |
| Borrowing Requests | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | 2 |
| Loan Tracking | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 2 |

✅ = Required by feature  
❌ = Not used by feature

**Key Insights**:
- All features require User, Tool, and Auth (confirms these belong in foundation)
- Photo service needed by 3 of 4 features (foundation candidate)
- Email service needed by 2 features (foundation candidate)
- Background jobs only needed by loan tracking, but justified in foundation for future scalability
- Clear separation between Phase 1 (simpler dependencies) and Phase 2 (complex workflows)