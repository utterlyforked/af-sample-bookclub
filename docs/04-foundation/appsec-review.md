# AppSec Review

**Date**: December 19, 2024
**Scope**: Foundation + 5 features (Tool Listing & Discovery, Borrowing Request & Communication, User Profiles & Community Verification, Loan Tracking & Management, Neighborhood-Based Communities)
**Risk Level**: **High**

---

## Executive Summary

This is a community tool-sharing platform where strangers lend valuable personal equipment to each other based on postal code proximity. The primary attack surface includes user authentication, location-based search, file uploads, and message exchange between users. The application handles PII (full addresses, names), facilitates trust-based transactions, and creates opportunities for fraud, harassment, and property loss if security controls fail.

Overall risk posture is **High** due to the trust-based model between strangers, handling of home addresses, and potential for coordinated abuse (fake accounts, harassment campaigns, location stalking). Critical controls around authentication, authorization, input validation, and data exposure must be airtight before launch.

---

## Critical Requirements

Must be implemented before launch. Failure here is a showstopper.

### AUTH-01: Password Storage & Complexity

**Risk**: Weak password hashing allows credential stuffing attacks. Users reuse passwords across sites; if this database leaks, attackers gain access to user accounts and can view home addresses, active loans, and messaging history.

**Requirement**: 
- Passwords MUST be hashed using bcrypt with a minimum cost factor of 12
- No other hashing algorithm is acceptable (not SHA-256, not PBKDF2)
- Cost factor MUST be configurable via appsettings.json for future increases
- Plaintext passwords MUST NEVER be logged, stored, or transmitted except during the single HTTPS POST to registration/login endpoints
- Password minimum requirements: 8 characters minimum, no maximum below 128 characters

**Applies to**: Foundation - User registration and authentication system

---

### AUTH-02: Session Management & Token Security

**Risk**: Stolen or leaked JWT tokens allow attackers to impersonate users, access home addresses, send messages as victims, approve/decline borrowing requests, and view loan history.

**Requirement**:
- JWTs MUST use HS256 or RS256 signing algorithm (no "none" algorithm)
- JWT signing secret MUST be 256+ bits of cryptographic randomness, stored in environment variables/key vault (never in appsettings.json committed to version control)
- Access tokens MUST expire after 24 hours maximum
- Refresh tokens MUST expire after 30 days and be rotated on use (single-use tokens)
- JWTs MUST be stored in HttpOnly, Secure, SameSite=Strict cookies
- No JWTs in localStorage, sessionStorage, or accessible to JavaScript
- Token validation MUST verify signature, expiration, issuer, and audience on every request

**Applies to**: Foundation - API authentication middleware

---

### AUTH-03: Brute Force Protection on Authentication Endpoints

**Risk**: Attackers can brute force user passwords or flood registration with bot accounts. This enables account takeover, database bloat with fake users, and community spam.

**Requirement**:
- `POST /api/v1/auth/login` MUST be rate-limited to 5 attempts per IP address per 15-minute window
- `POST /api/v1/auth/register` MUST be rate-limited to 3 attempts per IP address per hour
- `POST /api/v1/auth/forgot-password` MUST be rate-limited to 3 attempts per email per hour
- Exceeding rate limit MUST return HTTP 429 with Retry-After header
- Failed login attempts MUST NOT reveal whether email exists ("Invalid email or password" for both cases)
- Account lockout after 10 failed login attempts from any IP within 24 hours; unlock via email link only

**Applies to**: Foundation - Authentication endpoints

---

### AUTHZ-01: Horizontal Privilege Escalation Prevention

**Risk**: Users can access other users' data by changing IDs in API requests. This exposes home addresses, message threads, loan history, and borrowing requests.

**Requirement**:
- ALL endpoints returning user-specific data MUST verify the authenticated user matches the resource owner
- Authorization checks MUST happen in authorization handlers, not controllers
- Tool endpoints: Only tool owner can edit/delete tools (policy: `ToolOwner`)
- Borrowing request endpoints: Only borrower or lender can view request details (policy: `RequestParticipant`)
- Message endpoints: Only conversation participants can view messages (policy: `ConversationParticipant`)
- Loan endpoints: Only borrower or lender can view loan details (policy: `LoanParticipant`)
- Profile endpoints: Any authenticated user can view profiles (public), but only profile owner can edit (policy: `ProfileOwner`)
- Failed authorization MUST return HTTP 403 Forbidden (not 404)

**Applies to**: Foundation + all features

---

### INPUT-01: SQL Injection Prevention

**Risk**: User-supplied input in search queries, filters, and form submissions could allow SQL injection attacks that dump the entire database including home addresses, passwords hashes, and message content.

**Requirement**:
- ALL database queries MUST use parameterized queries via Entity Framework Core LINQ
- Raw SQL queries (`.FromSqlRaw()`, `.ExecuteSqlRaw()`) are FORBIDDEN unless explicitly reviewed and approved
- Dynamic LINQ expressions MUST NOT concatenate user input into query strings
- Search functionality MUST use parameterized full-text search or LINQ `.Contains()` with proper escaping
- No string concatenation or interpolation in SQL contexts

**Applies to**: Foundation + all features (especially Tool Listing search and filtering)

---

### INPUT-02: Mass Assignment Protection

**Risk**: Users can modify fields they shouldn't control by adding extra properties to JSON payloads. This allows privilege escalation (setting admin flags), data corruption (modifying other users' IDs), or bypassing business logic (changing loan due dates).

**Requirement**:
- ALL API endpoints accepting JSON input MUST use explicit DTOs with only allowed fields
- DTOs MUST NOT bind directly to entity models
- Controllers MUST manually map DTO fields to entity properties (no AutoMapper wildcards without explicit configuration)
- Entity IDs MUST come from route parameters and authenticated user context, never from request body
- Timestamps (CreatedAt, UpdatedAt) MUST be set server-side, never accepted from client
- Example forbidden: `[FromBody] Tool tool` → Example required: `[FromBody] CreateToolDto dto`

**Applies to**: Foundation + all features

---

### INPUT-03: File Upload Restrictions

**Risk**: Malicious file uploads can execute code on the server, store malware that's served to other users, or fill storage with junk files. Uploaded files might contain EXIF data with GPS coordinates, creating privacy leaks.

**Requirement**:
- File uploads MUST be restricted to JPEG and PNG only (check magic bytes, not just extension)
- Maximum file size MUST be 5MB per upload
- Uploaded files MUST be stored outside the webroot with randomized UUIDs as filenames (never use user-supplied names)
- Uploaded files MUST be scanned for malware if budget allows; otherwise accept risk and implement user reporting
- EXIF metadata MUST be stripped from all uploaded images before storage
- Image processing MUST use safe libraries (System.Drawing or ImageSharp) with exception handling for corrupt files
- Upload endpoint MUST be rate-limited to 20 uploads per user per hour
- File content-type validation MUST check magic bytes: JPEG (FF D8 FF), PNG (89 50 4E 47)

**Applies to**: Foundation (Image Service) + Tool Listing & Discovery (tool photos) + User Profiles (profile photos)

---

### DATA-01: PII Exposure in API Responses

**Risk**: API responses leak sensitive data that shouldn't be public. Full addresses, password hashes, internal IDs, and email addresses could enable stalking, credential attacks, or enumeration attacks.

**Requirement**:
- API responses MUST use explicit DTOs with only approved fields (no `return entity` from controllers)
- User entities returned to clients MUST exclude: `PasswordHash`, `Email` (except in profile owner's own data), `StreetName`, `CenterLatitude`, `CenterLongitude`
- User responses MUST include only: `Id`, `FullName`, `PostalCode` (first 3 digits only, e.g., "946xx"), `CommunityId`, `AverageRating`, `MemberSince`
- Tool owner addresses MUST show only postal code area (e.g., "Oakland 94610 area"), never street names
- Community responses MUST exclude exact `CenterLatitude`/`CenterLongitude`; show only radius and postal code
- Error messages MUST NOT leak stack traces, database field names, or internal paths in production
- Logging MUST NOT include password fields, full addresses, or email content

**Applies to**: Foundation + all features

---

### DATA-02: Message Content Privacy

**Risk**: Message history is exposed to unauthorized users or stored insecurely, enabling harassment evidence collection by abusers, competitive intelligence gathering, or privacy violations.

**Requirement**:
- Message threads MUST be accessible only to the borrower and lender in that specific request
- Message list endpoints MUST filter by authenticated user participation (cannot query all messages)
- Message detail endpoint MUST verify authenticated user is a participant before returning content
- Messages MUST NOT be included in tool listing responses or user profile responses
- Database queries for messages MUST always include `.Where(m => m.BorrowerUserId == currentUserId || m.LenderUserId == currentUserId)`
- Admin access to messages requires explicit audit logging with justification

**Applies to**: Borrowing Request & Communication

---

### INFRA-01: HTTPS Enforcement

**Risk**: Transmitting authentication tokens, passwords, home addresses, or messages over HTTP allows network attackers to intercept sensitive data.

**Requirement**:
- ALL traffic MUST be served over HTTPS in production (TLS 1.2 minimum, TLS 1.3 preferred)
- HTTP requests MUST redirect to HTTPS with HTTP 301
- HSTS header MUST be set: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- Cookies MUST have `Secure` flag set in production
- ASP.NET Core HTTPS redirection middleware MUST be enabled

**Applies to**: Foundation - API infrastructure

---

### INFRA-02: CORS Configuration

**Risk**: Misconfigured CORS allows malicious websites to make authenticated requests on behalf of users, stealing data or performing actions without consent.

**Requirement**:
- CORS MUST be configured with explicit allowed origins (no `*` wildcard with credentials)
- Allowed origin for development: `http://localhost:5173` (Vite default)
- Allowed origin for production: `https://[yourdomain.com]` (single domain only)
- `Access-Control-Allow-Credentials: true` MUST be set
- Allowed methods: `GET, POST, PUT, DELETE, OPTIONS` (explicit list)
- Allowed headers: `Content-Type, Authorization` (explicit list, no `*`)
- Preflight requests cached for 1 hour maximum

**Applies to**: Foundation - API infrastructure

---

## High Priority Requirements

Should be implemented in the first release. Deferring increases risk significantly.

### SEC-01: Email Verification for New Accounts

**Risk**: Without email verification, attackers create fake accounts with disposable emails to spam users, inflate community stats, or perform reconnaissance on neighborhoods.

**Requirement**:
- User accounts MUST require email verification before full platform access
- Unverified users MUST be able to log in but restricted to read-only access (cannot create tools, send requests, or message)
- Verification token MUST be cryptographically random (32+ bytes), single-use, expiring in 24 hours
- Verification link MUST be sent immediately after registration
- Users MUST be able to request new verification email (rate-limited to 1 per hour)
- Verification tokens MUST be hashed before database storage

**Applies to**: Foundation - User registration

---

### SEC-02: Rate Limiting on Mutation Endpoints

**Risk**: Attackers can flood the system with tool listings, borrowing requests, or messages, degrading performance and creating moderation burden.

**Requirement**:
- Tool creation: 10 per user per day
- Borrowing requests: 20 per user per day (in addition to 10 pending limit)
- Messages: 100 per user per day
- Profile updates: 5 per user per day
- Extension requests: 10 per user per day
- Rate limits MUST return HTTP 429 with clear message: "You have exceeded the daily limit for this action. Try again tomorrow."
- Rate limit counters MUST reset at midnight UTC

**Applies to**: All features

---

### SEC-03: Input Validation with Size Limits

**Risk**: Oversized inputs cause database bloat, UI rendering issues, or denial-of-service through memory exhaustion.

**Requirement**:
- Tool title: 100 characters max, alphanumeric + spaces + hyphens + parentheses only
- Tool description: 1000 characters max, allow full Unicode
- User full name: 100 characters max
- Message content: 2000 characters max
- Review text: 500 characters max
- Bio: 200 characters max
- All text inputs MUST be trimmed of leading/trailing whitespace
- Empty or whitespace-only fields MUST be rejected with HTTP 400
- Validation errors MUST be specific: "Tool title cannot exceed 100 characters (currently 147)"

**Applies to**: All features

---

### SEC-04: Postal Code Validation

**Risk**: Invalid postal codes allow users to join non-existent communities, break distance calculations, or probe for system behavior with injection payloads.

**Requirement**:
- Postal codes MUST be validated against a known list of valid codes for the supported country (US ZIP codes for MVP)
- Format validation: US ZIP codes MUST match regex `^\d{5}(-\d{4})?$`
- Postal codes in search queries MUST be sanitized (allow only digits and hyphens)
- Invalid postal codes MUST return HTTP 400: "Invalid postal code format"
- Database MUST store postal codes as strings (not integers) to preserve leading zeros

**Applies to**: Foundation (user registration), Neighborhood-Based Communities, Tool Listing & Discovery

---

### SEC-05: Secure Password Reset Flow

**Risk**: Insecure password reset allows account takeover through token prediction, token reuse, or timing attacks.

**Requirement**:
- Reset tokens MUST be cryptographically random (32+ bytes)
- Reset tokens MUST expire after 1 hour
- Reset tokens MUST be single-use (invalidated on first use or manual cancellation)
- Reset tokens MUST be hashed before database storage
- Password reset endpoint MUST NOT reveal whether email exists in system
- New password MUST meet same complexity requirements as registration
- Successful password reset MUST invalidate all existing sessions for that user

**Applies to**: Foundation - Authentication

---

### SEC-06: Audit Logging for Sensitive Actions

**Risk**: Without audit logs, investigating security incidents, abuse reports, or disputes is impossible. Attackers can cover their tracks.

**Requirement**:
- MUST log to persistent storage (Application Insights or file logs):
  - All authentication events (login, logout, failed attempts, password reset)
  - Account creation and deletion
  - Tool creation, update, deletion
  - Borrowing request approval/decline
  - Loan status changes
  - Message reporting
  - Admin actions
- Log entries MUST include: timestamp, user ID, action type, resource ID, IP address
- Logs MUST NOT include: passwords, message content (only metadata), full addresses
- Logs MUST be retained for 90 days minimum

**Applies to**: Foundation + all features

---

### SEC-07: Content Security Policy

**Risk**: XSS attacks inject malicious scripts that steal tokens, phish credentials, or perform actions on behalf of users.

**Requirement**:
- CSP header MUST be set: `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'`
- Inline scripts MUST use nonce or be eliminated
- Eval and similar dynamic code execution MUST be disabled
- Frame ancestors MUST be restricted: `frame-ancestors 'none'`
- Report-URI should be configured for CSP violation monitoring

**Applies to**: Foundation - Frontend infrastructure

---

### SEC-08: Admin Action Authorization

**Risk**: Regular users can access admin functionality, escalate privileges, or view sensitive platform-wide data.

**Requirement**:
- Admin role MUST be implemented with explicit `IsAdmin` flag on User entity
- Admin flag MUST be set manually via direct database access (no API endpoint to grant admin)
- Admin endpoints MUST require `[Authorize(Policy = "Admin")]` policy
- Admin actions include: viewing all messages, banning users, modifying communities, accessing Hangfire dashboard
- Admin actions MUST be logged with detailed audit trail

**Applies to**: Foundation - Authorization system

---

## Medium Priority Requirements

Best practice; address before going to production with real users.

### SEC-09: Account Lockout Duration

**Risk**: Permanent account lockouts after failed login attempts create denial-of-service vector. Attackers can lock out legitimate users.

**Requirement**:
- Account lockout SHOULD last 1 hour (not permanent)
- Lockout SHOULD be based on account email (not IP) to prevent IP-based DoS
- Unlock email SHOULD be sent to account owner
- Alternative: Implement CAPTCHA after 3 failed attempts instead of lockout

**Applies to**: Foundation - Authentication

---

### SEC-10: Security Headers

**Risk**: Missing security headers increase attack surface for clickjacking, MIME sniffing, and information leakage.

**Requirement**:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block` (defense-in-depth, even though deprecated)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

**Applies to**: Foundation - API infrastructure

---

### SEC-11: Secrets Management

**Risk**: Hardcoded secrets in source code or configuration files leak when repositories are exposed or developers' machines are compromised.

**Requirement**:
- JWT signing keys MUST be stored in environment variables or Azure Key Vault (not appsettings.json)
- Database connection strings MUST use environment variables in production
- SendGrid/SES API keys MUST be stored in environment variables
- Azure Blob Storage connection strings MUST use managed identity or environment variables
- `.env` files MUST be in `.gitignore`
- Development secrets MUST use .NET User Secrets

**Applies to**: Foundation - Configuration management

---

### SEC-12: Denial of Service Protection

**Risk**: Resource-intensive operations can be abused to degrade performance or crash the application.

**Requirement**:
- Search endpoints SHOULD limit results to 50 items per request
- Pagination SHOULD enforce maximum page size of 100 items
- Tool photo batch upload SHOULD be limited to 5 files per request
- Database queries SHOULD have default timeouts (5 seconds)
- Background jobs SHOULD have retry limits (3 attempts max)

**Applies to**: All features

---

## Feature-Specific Notes

### Tool Listing & Discovery

- **Search injection**: User search terms must be parameterized; do not concatenate into SQL
- **Distance calculation**: Ensure PostGIS queries are parameterized; malformed coordinates could cause SQL injection
- **Image URLs**: Return CDN URLs, not direct blob storage URLs with SAS tokens (if using Azure)
- **Tool availability**: Concurrent request checks must use database transactions to prevent race conditions

### Borrowing Request & Communication

- **Message HTML**: All message content must be HTML-escaped before rendering to prevent XSS
- **Profanity filter bypass**: Users will try `@$$hole` variations; accept that automated filtering is imperfect
- **Request spam**: 10 pending request limit is enforced at application level; ensure database constraints also exist
- **Auto-decline timing**: Use Hangfire scheduled jobs; ensure job idempotency (don't double-decline)

### User Profiles & Community Verification

- **Address updates**: One per year limit must be enforced with database check (not just application logic)
- **Rating manipulation**: Multiple ratings from same user pair is acceptable per design; monitor for artificial inflation
- **Profile enumeration**: User ID enumeration is acceptable (profiles are semi-public); don't expose email addresses
- **EXIF data**: Strip GPS coordinates from uploaded profile photos

### Loan Tracking & Management

- **Due date manipulation**: Loan due dates must be validated server-side; don't trust client timestamps
- **Return confirmation**: Race condition possible if both parties confirm simultaneously; use optimistic locking
- **Overdue notifications**: Ensure Hangfire jobs don't send duplicate emails if job retries

### Neighborhood-Based Communities

- **Community creation race**: Two users in same postal code could create duplicate communities; use database unique constraint on postal code
- **Postal code injection**: Search by postal code must sanitize input (digits and hyphens only)
- **Location privacy**: Never expose exact latitude/longitude; always show postal code area only
- **Address verification**: Street name validation is loose by design; accept some fake addresses in favor of UX

---

## What the Engineering Spec Must Include

A checklist of security requirements the engineering spec agent must address in each component:

**Foundation**:
- [x] Password hashing algorithm specified (bcrypt, cost factor 12)
- [x] JWT signing algorithm, expiry, and refresh policy defined (HS256/RS256, 24hr access, 30-day refresh with rotation)
- [x] Rate limiting rules for auth endpoints specified (login 5/15min, register 3/hour, password reset 3/hour)
- [x] CORS policy explicitly defined with allowed origins, methods, headers (no wildcards with credentials)
- [x] HTTPS enforcement and HSTS configuration
- [x] HttpOnly, Secure, SameSite cookie flags for JWT storage
- [x] Email verification flow with token expiry and single-use enforcement
- [x] Authorization policies named for each resource type (ToolOwner, RequestParticipant, LoanParticipant, ProfileOwner, Admin)
- [x] Audit logging configuration for authentication events

**All authenticated endpoints**:
- [x] Authorization policy explicitly applied with `[Authorize(Policy = "...")]`
- [x] Behavior on unauthorized access documented (403 for authz failure, 401 for missing auth)
- [x] User context extraction from JWT documented

**Any endpoint accepting user input**:
- [x] Input validation rules with character limits specified per field
- [x] Content-type restrictions defined for file uploads (JPEG/PNG only, magic byte validation)
- [x] DTO classes with explicit field lists (no entity binding)
- [x] Rate limiting rules per endpoint type (mutations, searches, uploads)
- [x] SQL injection prevention approach confirmed (EF Core LINQ, no raw SQL)

**Any endpoint returning user data**:
- [x] Response DTO explicitly defined with approved field list only
- [x] Sensitive fields exclusion documented (PasswordHash, Email, full addresses, exact coordinates)
- [x] PII handling rules for logging (what can/cannot be logged)

**File upload endpoints**:
- [x] File type validation approach (magic bytes, not extension)
- [x] File size limits specified (5MB per file)
- [x] Storage location outside webroot with randomized filenames
- [x] EXIF metadata stripping confirmed
- [x] Upload rate limiting specified (20 per user per hour)

**Message/communication endpoints**:
- [x] Access control for message threads (participant verification)
- [x] XSS prevention for message display (HTML escaping)
- [x] Message content size limits (2000 characters)
- [x] Reporting mechanism implementation

**Background jobs**:
- [x] Job idempotency guarantees (no duplicate actions on retry)
- [x] Retry limits specified (3 attempts max)
- [x] Error handling and logging approach

**Database**:
- [x] Parameterized query usage confirmed
- [x] Index strategy for performance
- [x] Unique constraints for business rules (prevent duplicate communities, etc.)
- [x] Audit columns (CreatedAt, UpdatedAt) set server-side only

---

## Out of Scope

- Penetration testing (will be scheduled post-MVP launch)
- Infrastructure security (hosting environment, network segmentation, CI/CD pipeline) - assumed to follow platform best practices
- Compliance certifications (GDPR, SOC 2, CCPA) - flagged for future consideration:
  - **GDPR**: Platform collects home addresses (PII); must implement data export and deletion on request
  - **CCPA**: California users (likely many given tool-sharing urban focus) have data rights
  - **Recommendation**: Add user data export endpoint and account deletion flow in Phase 2
- DDoS mitigation at network layer (Cloudflare/CDN responsibility)
- Third-party service security (SendGrid, Azure, geocoding API) - assumed secure
- Physical security of development machines
- Social engineering attacks (outside platform controls)

---

## Quality Checklist

- [x] All critical requirements are specific and testable
- [x] Each requirement names the component it applies to
- [x] Priority levels are justified (Critical = launch blocker)
- [x] Feature-specific risks are called out
- [x] Engineering spec checklist is complete
- [x] No vague advice ("be secure", "validate input")
- [x] No implementation code