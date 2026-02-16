# Foundation Infrastructure — Engineering Spec

**Type**: foundation  
**Component**: foundation-infrastructure  
**Dependencies**: None (this is the base layer)  
**Status**: Ready for Implementation

---

## Overview

This specification defines the shared infrastructure that all features depend on: authentication system, core database entities, API patterns, frontend shell, shared services (email, image storage, geocoding), and background job infrastructure. It establishes the technical contracts for User, Community, Tool, and Photo entities, plus the authentication/authorization framework that protects all endpoints. This foundation must be complete before any feature development can begin.

---

## Data Model

### User

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | ASP.NET Identity GUID |
| email | string(256) | unique, not null, indexed | Normalized to lowercase |
| userName | string(256) | unique, not null | Same as email for ASP.NET Identity |
| passwordHash | string(512) | not null | Hashed via ASP.NET Identity (PBKDF2) |
| fullName | string(200) | not null | Display name |
| postalCode | string(10) | not null, indexed | User's location |
| streetName | string(200) | not null | For community assignment (no house number) |
| communityId | UUID | FK, not null, indexed | Assigned based on postal code |
| createdAt | datetime | not null | UTC timestamp |
| lastActiveAt | datetime | not null | Updated on each authenticated request |
| emailNotificationsEnabled | boolean | not null, default true | User preference for email alerts |
| addressLastUpdatedAt | datetime | nullable | Tracks last address change for rate limiting |
| emailConfirmed | boolean | not null, default false | ASP.NET Identity field |
| securityStamp | string(512) | not null | ASP.NET Identity security token |
| concurrencyStamp | string(512) | not null | ASP.NET Identity optimistic concurrency |

**Indexes**:
- `(email)` unique
- `(userName)` unique
- `(postalCode)` non-unique
- `(communityId)` non-unique

**Relationships**:
- Belongs to one `Community` via `communityId`
- Has many `Tool` (as owner) - cascade delete
- Has many `BorrowingRequest` (as borrower)
- Has many `BorrowingRequest` (as lender via tool ownership)
- Has many `Rating` (as rater)
- Has many `Rating` (as ratee)

**Business Rules**:
- Email is normalized to lowercase before storage and all lookups
- UserName must equal Email (ASP.NET Identity requirement)
- Address (postalCode + streetName) can only be updated once per year
- CommunityId is assigned automatically on registration based on postal code

---

### Community

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| name | string(200) | not null | Display name (e.g., "M5V Downtown Toronto") |
| postalCode | string(10) | not null, indexed | Primary postal code for this community |
| centerLatitude | decimal(9,6) | not null, indexed | Geocoded center point |
| centerLongitude | decimal(9,6) | not null, indexed | Geocoded center point |
| radiusMiles | decimal(4,2) | not null, default 1.5 | Search radius for "nearby" tools |
| memberCount | integer | not null, default 0 | Cached count, updated by background job |
| lastActivityAt | datetime | nullable | Most recent tool listing or loan activity |
| createdAt | datetime | not null | UTC timestamp |

**Indexes**:
- `(postalCode)` non-unique
- `(centerLatitude, centerLongitude)` composite for geospatial queries

**Relationships**:
- Has many `User` - no cascade (prevent accidental deletion)
- Has many `Tool` (via users)

**Business Rules**:
- CenterLatitude/CenterLongitude are calculated via geocoding service during community creation
- MemberCount is updated by background job (hourly), not on every user action
- RadiusMiles default is 1.5 but can be adjusted per community
- LastActivityAt updates when any member lists a tool or completes a loan

---

### Tool

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| ownerId | UUID | FK, not null, indexed | References User.id |
| title | string(100) | not null | Tool name/headline |
| description | string(2000) | not null | Full description |
| category | string(50) | not null, indexed | From predefined list (see seed data) |
| brand | string(100) | nullable | Manufacturer/brand name |
| specialInstructions | string(1000) | nullable | Usage notes for borrowers |
| conditionNotes | string(500) | nullable | Current condition/wear details |
| availabilityStatus | string(20) | not null, default 'Available' | Enum: Available, Borrowed, Unlisted |
| postalCode | string(10) | not null, indexed | Tool location (owner's postal code) |
| lastUpdatedAt | datetime | not null | UTC timestamp, updated on any edit |
| createdAt | datetime | not null | UTC timestamp |

**Indexes**:
- `(ownerId)` non-unique
- `(category)` non-unique
- `(postalCode)` non-unique
- `(availabilityStatus)` non-unique

**Relationships**:
- Belongs to one `User` via `ownerId` - cascade delete
- Has many `ToolPhoto` - cascade delete
- Has many `BorrowingRequest`
- Has many `Loan`

**Business Rules**:
- AvailabilityStatus changes to 'Borrowed' when a loan becomes active
- AvailabilityStatus returns to 'Available' when loan completes
- AvailabilityStatus set to 'Unlisted' when owner wants to hide (soft delete)
- PostalCode must match owner's postal code (validated on creation and updates)
- Maximum 5 photos per tool (enforced at application level)

---

### ToolPhoto

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| toolId | UUID | FK, not null, indexed | References Tool.id |
| displayOrder | integer | not null | Sort order (1-5) |
| thumbnailUrl | string(500) | not null | 150x150px image URL |
| mediumUrl | string(500) | not null | 400x300px image URL |
| fullUrl | string(500) | not null | 1200x900px image URL |
| uploadedAt | datetime | not null | UTC timestamp |

**Indexes**:
- `(toolId, displayOrder)` composite, unique

**Relationships**:
- Belongs to one `Tool` via `toolId` - cascade delete

**Business Rules**:
- DisplayOrder must be between 1 and 5
- Maximum 5 photos per tool (enforced at Tool entity level)
- All three sizes are generated on upload (thumbnail, medium, full)
- Images are stored in Azure Blob Storage / S3 with CDN caching

---

### Seed Data

**Tool Categories** (inserted during initial migration):
```
- Power Tools
- Hand Tools
- Lawn & Garden
- Ladders & Scaffolding
- Painting Supplies
- Plumbing Tools
- Electrical Tools
- Automotive Tools
- Cleaning Equipment
- Moving & Lifting
- Seasonal Equipment
- Other
```

**Initial Communities** (optional - can be created on-demand):
- Seeded based on postal code database or created dynamically when first user in area registers

---

## API Endpoints

### POST /api/v1/auth/register

**Auth**: None (public endpoint)  
**Authorization**: N/A

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| email | string | yes | Valid email format, max 256 chars, unique |
| password | string | yes | Min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit |
| fullName | string | yes | Non-empty, max 200 chars |
| postalCode | string | yes | Valid postal code format (region-specific), max 10 chars |
| streetName | string | yes | Non-empty, max 200 chars, no house numbers allowed |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | User ID |
| email | string | Normalized to lowercase |
| fullName | string | |
| communityId | UUID | Auto-assigned based on postal code |
| communityName | string | Community display name |
| emailConfirmed | boolean | Always false on registration |

**Response headers**:
- Location: `/api/v1/users/{id}`

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure — returns field-level errors |
| 409 | Email already registered |
| 503 | Geocoding service unavailable (cannot assign community) |

**Side effects**:
- Sends email verification link to provided email address
- Creates new Community if postal code area has no existing community
- Sets `addressLastUpdatedAt` to registration time
- Sets `emailConfirmed` to false (requires verification)

---

### POST /api/v1/auth/login

**Auth**: None (public endpoint)  
**Authorization**: N/A

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| email | string | yes | Valid email format |
| password | string | yes | Non-empty |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | User ID |
| email | string | |
| fullName | string | |
| communityId | UUID | |
| communityName | string | |
| emailNotificationsEnabled | boolean | |

**Response headers**:
- Set-Cookie: `auth_token={JWT}; HttpOnly; Secure; SameSite=Strict; Max-Age=86400`

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Invalid email or password |
| 403 | Email not verified (emailConfirmed = false) |
| 429 | Rate limit exceeded (10 attempts per IP per hour) |

**Side effects**:
- Updates `lastActiveAt` to current timestamp
- JWT token issued with 24-hour expiration

---

### POST /api/v1/auth/logout

**Auth**: Required (Bearer JWT or cookie)  
**Authorization**: Authenticated

**Request body**: Empty

**Success response** `204 No Content`

**Response headers**:
- Set-Cookie: `auth_token=; HttpOnly; Secure; SameSite=Strict; Max-Age=0` (clears cookie)

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |

---

### POST /api/v1/auth/forgot-password

**Auth**: None (public endpoint)  
**Authorization**: N/A

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| email | string | yes | Valid email format |

**Success response** `204 No Content`

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid email format |
| 429 | Rate limit exceeded (3 requests per IP per hour) |

**Side effects**:
- Sends password reset email with time-limited token if email exists
- Returns 204 even if email not found (security - no user enumeration)

---

### POST /api/v1/auth/reset-password

**Auth**: None (public endpoint)  
**Authorization**: N/A (token in request body provides authorization)

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| email | string | yes | Valid email format |
| token | string | yes | Password reset token from email |
| newPassword | string | yes | Min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit |

**Success response** `204 No Content`

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure or invalid/expired token |
| 404 | Email not found |
| 429 | Rate limit exceeded (5 attempts per IP per hour) |

**Side effects**:
- Updates passwordHash
- Invalidates all existing JWT tokens via securityStamp update
- Sends confirmation email

---

### POST /api/v1/auth/verify-email

**Auth**: None (public endpoint)  
**Authorization**: N/A (token in request body provides authorization)

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| userId | UUID | yes | Valid UUID |
| token | string | yes | Email verification token from email |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| message | string | "Email verified successfully" |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid or expired token |
| 404 | User not found |
| 409 | Email already verified |

**Side effects**:
- Sets `emailConfirmed` to true
- Sends welcome email

---

### GET /api/v1/users/{id}

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated (own profile) OR CommunityMember (same community)

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| id | UUID | Valid UUID |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| email | string | Only if own profile |
| fullName | string | |
| postalCode | string | First 3 characters only if not own profile |
| streetName | string | Only if own profile |
| communityId | UUID | |
| communityName | string | |
| createdAt | ISO 8601 datetime | UTC |
| emailNotificationsEnabled | boolean | Only if own profile |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | Not authorized to view this profile |
| 404 | User not found |

---

### PUT /api/v1/users/{id}

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated (own profile only)

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| id | UUID | Valid UUID, must match authenticated user |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| fullName | string | yes | Non-empty, max 200 chars |
| postalCode | string | no | Valid postal code format, max 10 chars |
| streetName | string | no | Required if postalCode provided, max 200 chars |
| emailNotificationsEnabled | boolean | yes | true or false |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| email | string | |
| fullName | string | |
| postalCode | string | |
| streetName | string | |
| communityId | UUID | May change if address updated |
| communityName | string | |
| emailNotificationsEnabled | boolean | |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure |
| 401 | Not authenticated |
| 403 | Attempting to update another user's profile |
| 404 | User not found |
| 409 | Address updated within past year (rate limit) |
| 503 | Geocoding service unavailable (cannot reassign community) |

**Side effects**:
- If address changes, `communityId` is recalculated via geocoding service
- If address changes, `addressLastUpdatedAt` is set to current timestamp
- `lastUpdatedAt` is updated

---

### GET /api/v1/communities

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated

**Query parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|-----------|
| postalCode | string | no | Valid postal code format |
| page | integer | no | Min 1, default 1 |
| pageSize | integer | no | Min 1, max 50, default 20 |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| items | array | Array of Community objects |
| totalCount | integer | Total communities matching filter |
| page | integer | Current page |
| pageSize | integer | Items per page |

**Community object**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| name | string | |
| postalCode | string | |
| memberCount | integer | Cached count |
| radiusMiles | decimal | |
| lastActivityAt | ISO 8601 datetime | UTC, nullable |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 400 | Invalid pagination parameters |

---

### GET /api/v1/communities/{id}

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated

**Path parameters**:
| Parameter | Type | Validation |
|-----------|------|-----------|
| id | UUID | Valid UUID |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| name | string | |
| postalCode | string | |
| centerLatitude | decimal | |
| centerLongitude | decimal | |
| radiusMiles | decimal | |
| memberCount | integer | |
| lastActivityAt | ISO 8601 datetime | UTC, nullable |
| createdAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 404 | Community not found |

---

### POST /api/v1/images/upload

**Auth**: Required (Bearer JWT)  
**Authorization**: Authenticated

**Request body**: `multipart/form-data`
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| file | file | yes | JPEG or PNG, max 5MB |
| purpose | string | yes | Enum: 'tool_photo', 'profile_photo' |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| thumbnailUrl | string | 150x150px CDN URL |
| mediumUrl | string | 400x300px CDN URL |
| fullUrl | string | 1200x900px CDN URL |
| uploadedAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid file type or size exceeds 5MB |
| 401 | Not authenticated |
| 503 | Image processing service unavailable |

**Side effects**:
- Generates 3 sizes (thumbnail, medium, full)
- Compresses images to 85% quality
- Stores in Azure Blob Storage / S3
- Returns CDN URLs for immediate use
- Images are not associated with Tool or User until subsequent API call links them

---

## Business Rules

1. **Email normalization**: All email addresses are converted to lowercase before storage and all lookups (case-insensitive matching).

2. **Address update rate limit**: Users may update their address (postalCode + streetName) at most once per 365 days. The first update is allowed immediately after registration.

3. **Community assignment**: On registration or address update, users are automatically assigned to a Community based on their postal code via geocoding service. If no Community exists for that postal code, a new Community is created.

4. **Email verification requirement**: Users must verify their email address before they can log in. Attempting to log in with `emailConfirmed = false` returns 403.

5. **JWT token expiration**: All JWT tokens expire after 24 hours. Clients must implement token refresh or require re-login.

6. **Password hashing**: All passwords are hashed using ASP.NET Identity's default algorithm (PBKDF2 with 10,000 iterations minimum).

7. **Tool availability status**: When a loan becomes active, Tool.availabilityStatus automatically changes to 'Borrowed'. When loan completes, status returns to 'Available'.

8. **Tool location constraint**: Tool.postalCode must match the owner's User.postalCode at all times. If owner changes address, all owned tools must have their postalCode updated automatically.

9. **Photo count limit**: Each Tool may have at most 5 photos. Attempting to upload a 6th photo returns 400 error.

10. **Photo size generation**: All uploaded images generate 3 sizes automatically (150x150 thumbnail, 400x300 medium, 1200x900 full). Original files are not retained.

11. **Community member count caching**: Community.memberCount is updated by background job (hourly) rather than real-time to avoid database contention.

12. **Community activity tracking**: Community.lastActivityAt updates when any member lists a new tool OR completes a loan (return confirmed).

13. **Security stamp invalidation**: When a user changes their password, their ASP.NET Identity `securityStamp` is updated, invalidating all existing JWT tokens.

14. **Rate limiting**: Authentication endpoints are rate-limited per IP address:
    - Login: 10 attempts per hour
    - Registration: 10 attempts per hour
    - Password reset request: 3 attempts per hour
    - Password reset submission: 5 attempts per hour

---

## Validation Rules

| Field | Rule | Error message |
|-------|------|---------------|
| email | Required, valid email format, max 256 chars, unique | "Email is required" / "Invalid email format" / "Email too long" / "Email already registered" |
| password | Required, min 8 chars, at least 1 uppercase, 1 lowercase, 1 digit | "Password is required" / "Password must be at least 8 characters and contain uppercase, lowercase, and digit" |
| fullName | Required, non-empty, max 200 chars | "Full name is required" / "Full name too long" |
| postalCode | Required, valid postal code format (region-specific regex), max 10 chars | "Postal code is required" / "Invalid postal code format" / "Postal code too long" |
| streetName | Required, non-empty, max 200 chars, must not contain digits | "Street name is required" / "Street name too long" / "Street name must not contain house numbers" |
| tool.title | Required, non-empty, max 100 chars | "Tool name is required" / "Tool name too long" |
| tool.description | Required, non-empty, max 2000 chars | "Description is required" / "Description too long" |
| tool.category | Required, must match predefined category list | "Category is required" / "Invalid category" |
| tool.brand | Optional, max 100 chars | "Brand name too long" |
| tool.specialInstructions | Optional, max 1000 chars | "Special instructions too long" |
| tool.conditionNotes | Optional, max 500 chars | "Condition notes too long" |
| image.file | Required, JPEG or PNG, max 5MB | "Image file is required" / "Invalid image format (JPEG or PNG only)" / "Image file too large (max 5MB)" |
| image.purpose | Required, enum: 'tool_photo' or 'profile_photo' | "Image purpose is required" / "Invalid image purpose" |

---

## Authorization

| Action | Required policy | Notes |
|--------|----------------|-------|
| Register | None (public) | |
| Login | None (public) | |
| Logout | Authenticated | |
| Forgot password | None (public) | Rate-limited |
| Reset password | None (public) | Token-based authorization |
| Verify email | None (public) | Token-based authorization |
| Get own profile | Authenticated | User ID in JWT matches path parameter |
| Get other user profile | CommunityMember | Both users in same community |
| Update profile | Authenticated | User ID in JWT matches path parameter |
| List communities | Authenticated | |
| Get community details | Authenticated | |
| Upload image | Authenticated | |

**Authorization Policies** (for implementation):

```csharp
// Policy: Authenticated
// Requirement: Valid JWT token present

// Policy: CommunityMember
// Requirement: Authenticated AND user.communityId matches resource owner's communityId

// Policy: ToolOwner (used in future features)
// Requirement: Authenticated AND user.id matches tool.ownerId

// Policy: LoanParticipant (used in future features)
// Requirement: Authenticated AND (user.id matches loan.borrowerId OR user.id matches loan.lenderId)
```

---

## Acceptance Criteria

- [ ] User can register with valid email, password, full name, postal code, and street name
- [ ] Registration automatically assigns user to existing Community or creates new Community if none exists for postal code
- [ ] Duplicate email registration returns 409 with error message "Email already registered"
- [ ] Password validation enforces minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 digit
- [ ] Registration sends email verification link to provided email address
- [ ] User cannot log in until email is verified (emailConfirmed = true)
- [ ] Login with valid credentials returns 200 and sets HttpOnly cookie with JWT token
- [ ] Login with invalid credentials returns 401 with generic error message (no user enumeration)
- [ ] Login with unverified email returns 403 with message "Please verify your email address"
- [ ] JWT token expires after 24 hours
- [ ] JWT token includes user ID, email, and communityId claims
- [ ] Logout clears authentication cookie
- [ ] Forgot password sends reset email if user exists, returns 204 regardless (no user enumeration)
- [ ] Password reset with valid token updates password and invalidates existing JWT tokens
- [ ] Password reset with expired token returns 400 with message "Invalid or expired reset token"
- [ ] Email verification with valid token sets emailConfirmed to true and sends welcome email
- [ ] User can view own profile with all fields visible (email, full address, notification settings)
- [ ] User can view profile of user in same community with limited fields (partial postal code, no email)
- [ ] User cannot view profile of user in different community (returns 403)
- [ ] User can update own full name and email notification preference
- [ ] User can update own address (postal code + street name) if not updated in past year
- [ ] Address update within 365 days of last change returns 409 with message "Address can only be updated once per year"
- [ ] Address update recalculates communityId via geocoding service
- [ ] Address update fails with 503 if geocoding service is unavailable
- [ ] Geocoding service unavailable during registration returns 503 with retry message
- [ ] Community list endpoint returns paginated results with default pageSize 20
- [ ] Community list filtered by postal code returns only communities matching that postal code
- [ ] Community detail endpoint returns all community fields including member count
- [ ] Image upload with valid JPEG or PNG (under 5MB) returns 3 URLs (thumbnail, medium, full)
- [ ] Image upload with invalid file type returns 400 with message "Invalid image format (JPEG or PNG only)"
- [ ] Image upload exceeding 5MB returns 400 with message "Image file too large (max 5MB)"
- [ ] Uploaded images are compressed to 85% quality
- [ ] Uploaded images generate exactly 3 sizes: 150x150, 400x300, 1200x900
- [ ] Image URLs are served from CDN with proper caching headers
- [ ] Login endpoint is rate-limited to 10 attempts per IP per hour
- [ ] Registration endpoint is rate-limited to 10 attempts per IP per hour
- [ ] Forgot password endpoint is rate-limited to 3 requests per IP per hour
- [ ] Password reset endpoint is rate-limited to 5 attempts per IP per hour
- [ ] Rate limit exceeded returns 429 with Retry-After header
- [ ] All datetime fields are stored and returned in UTC with ISO 8601 format
- [ ] All validation errors return 400 with RFC 7807 ProblemDetails format including field-level errors
- [ ] All endpoints return appropriate HTTP status codes (200, 201, 204, 400, 401, 403, 404, 409, 429, 503)
- [ ] All protected endpoints return 401 if no JWT token provided
- [ ] All endpoints log requests and responses to Application Insights
- [ ] Background job updates Community.memberCount hourly for all communities
- [ ] Background job runs successfully and logs completion status

---

## Security Requirements

**Password Storage**:
- Passwords must be hashed using ASP.NET Identity's default algorithm (PBKDF2 with at least 10,000 iterations)
- Never log or expose password hashes in API responses
- Never return passwords in any API response

**JWT Token Security**:
- Tokens stored in HttpOnly cookies (not accessible via JavaScript)
- Cookies use Secure flag (HTTPS only)
- Cookies use SameSite=Strict to prevent CSRF
- Tokens expire after 24 hours (no refresh tokens in MVP)
- Token signature uses HS256 with 256-bit secret key
- Secret key stored in environment variable, never in code

**Rate Limiting**:
- All authentication endpoints rate-limited per IP address (see Business Rules #14)
- Rate limit state stored in Redis with sliding expiration
- Exceeded rate limits return 429 with Retry-After header in seconds

**Email Verification**:
- Email verification tokens are single-use and expire after 24 hours
- Token format: cryptographically random 32-byte base64-encoded string
- Tokens stored hashed in database (never plain text)

**Password Reset**:
- Password reset tokens are single-use and expire after 1 hour
- Token format: cryptographically random 32-byte base64-encoded string
- Tokens stored hashed in database (never plain text)
- Password reset requests do not reveal whether email exists (return 204 regardless)

**Authorization**:
- All endpoints except registration, login, password reset, email verification require authentication
- Resource-based authorization uses policy handlers (e.g., ToolOwner, CommunityMember)
- Attempting to access unauthorized resource returns 403 with generic message (no details about why)

**Input Validation**:
- All user input validated on server side (client-side validation is UX only)
- File uploads restricted to JPEG and PNG (validate via magic bytes, not extension)
- Maximum file size enforced at middleware level (5MB)
- All string inputs trimmed and sanitized for HTML/SQL injection

**CORS**:
- CORS configured to allow only frontend origin (no wildcards)
- Credentials (cookies) allowed only from configured origin
- Preflight cache set to 1 hour

**API Security Headers**:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000; includeSubDomains

**Logging**:
- Never log passwords, tokens, or password hashes
- Log authentication failures with IP address (for monitoring brute force)
- Log all authorization failures with user ID and resource ID
- Log all rate limit violations with IP address

**Database Security**:
- Database connection uses TLS 1.2+
- Database credentials stored in Azure Key Vault / AWS Secrets Manager
- Application uses least-privilege database account (no DDL permissions in production)

**Image Upload Security**:
- Validate image format via magic bytes (JPEG: FF D8 FF, PNG: 89 50 4E 47)
- Strip EXIF metadata from uploaded images (prevent GPS leakage)
- Generate unique random filenames (prevent path traversal)
- Store images