# AppSec Review

**Date**: 2025-01-14  
**Scope**: Foundation + 5 features  
**Risk Level**: **High**

---

## Executive Summary

ToolShare is a peer-to-peer tool lending platform enabling users to list tools, request borrowing, track active borrows, and discover community inventory through location-based search. The primary attack surface includes user authentication, tool/borrow transaction workflows, location data handling, image uploads, and real-time messaging. 

The overall risk posture is **High** due to: (1) complex multi-party transaction state machines with race condition potential, (2) personal identifiable information (PII) including precise geolocation and home addresses shared post-approval, (3) user-generated content (photos, reviews, messages) requiring strict validation, and (4) scheduled background jobs handling sensitive operations like auto-confirmations and reminders.

Critical security requirements focus on authentication hardening, input validation across all user-facing forms, authorization enforcement on every endpoint, and protection against double-booking race conditions in the borrow approval workflow.

---

## Critical Requirements

Must be implemented before launch. Failure here is a showstopper.

### AUTH-01: Password Storage and Authentication

**Risk**: Weak password hashing enables credential compromise. Plaintext or weak hashes (MD5, SHA1) allow attackers to reverse passwords from database breaches.

**Requirement**: 
- Passwords MUST be hashed using ASP.NET Core Identity's default password hasher (PBKDF2-SHA256 with at least 10,000 iterations)
- Password hasher configuration MUST NOT be weakened (accept defaults or increase iterations)
- Plaintext passwords MUST NEVER be stored or logged
- Password reset tokens MUST be single-use, cryptographically random (256-bit), and expire after 1 hour
- Password reset URLs MUST be delivered only via email (no SMS or in-app display)

**Applies to**: Foundation - ASP.NET Core Identity integration

---

### AUTH-02: JWT Token Security

**Risk**: Token theft or manipulation allows account takeover. localStorage storage exposes tokens to XSS. Weak signing enables token forgery.

**Requirement**:
- JWTs MUST be signed with HMAC-SHA256 or RS256 (minimum 256-bit key)
- JWT secret key MUST be stored in Azure Key Vault or environment variable (never in appsettings.json checked into source control)
- JWTs MUST expire after 24 hours maximum
- JWTs MUST be delivered via HttpOnly, Secure, SameSite=Strict cookies (never in response body or localStorage)
- Refresh tokens MUST expire after 30 days and rotate on use (new token issued, old token invalidated)
- Token refresh endpoint (`POST /api/v1/auth/refresh`) MUST be rate-limited to 10 requests per 15 minutes per user

**Applies to**: Foundation - Authentication system

---

### AUTH-03: Rate Limiting on Authentication Endpoints

**Risk**: Brute force attacks against login and password reset endpoints enable credential stuffing and account enumeration.

**Requirement**:
- `POST /api/v1/auth/login` MUST be rate-limited to 5 attempts per IP per 15-minute window
- `POST /api/v1/auth/register` MUST be rate-limited to 3 attempts per IP per hour
- `POST /api/v1/auth/password-reset` MUST be rate-limited to 3 requests per email per hour
- `POST /api/v1/auth/verify-email` MUST be rate-limited to 5 attempts per token per hour
- Rate limit exceeded responses MUST return HTTP 429 with `Retry-After` header
- Rate limiting MUST use Redis for distributed tracking (not in-memory)

**Applies to**: Foundation - API infrastructure

---

### AUTH-04: Authorization on Every Protected Endpoint

**Risk**: Missing authorization checks allow horizontal privilege escalation (User A accesses User B's data). Vertical escalation allows non-owners to edit/delete resources.

**Requirement**:
- ALL endpoints returning user-specific data MUST enforce authorization (no public access to personal dashboards, messages, transaction history)
- Tool edit/delete endpoints (`PUT /api/v1/tools/{id}`, `DELETE /api/v1/tools/{id}`) MUST verify `tool.OwnerId == currentUserId` BEFORE allowing operation
- BorrowRequest endpoints MUST verify `request.BorrowerId == currentUserId OR request.OwnerId == currentUserId` (only participants access transaction)
- Profile edit endpoint (`PUT /api/v1/users/{id}`) MUST verify `id == currentUserId` (users only edit their own profile)
- Authorization failures MUST return HTTP 403 Forbidden (not 404) when resource exists but user lacks permission
- Authorization policies MUST be defined in `Program.cs` and enforced via `[Authorize(Policy = "...")]` attribute (not inline code checks)

**Applies to**: All features - every authenticated endpoint

---

### INPUT-01: Tool Listing Input Validation

**Risk**: XSS via unsanitized tool descriptions. SQL injection if ORM bypassed. Mass assignment overwrites protected fields.

**Requirement**:
- `POST /api/v1/tools` and `PUT /api/v1/tools/{id}` MUST accept ONLY these fields: Title (max 100 chars), Category (enum validation), Description (max 2000 chars), ConditionNotes (max 500 chars), Status (enum)
- Title, Description, ConditionNotes MUST be HTML-stripped on backend (regex: `/<.*?>/g` removed)
- Category MUST be validated against enum: PowerTools, HandTools, Gardening, Ladders, Automotive, Specialty (reject others with 400)
- Status MUST be validated against enum: Draft, Published, Borrowed, Unavailable (reject others with 400)
- Tool location (lat/lng) MUST NEVER be user-submitted (automatically populated from owner's profile coordinates)
- OwnerId MUST be set to `currentUserId` server-side (never accepted from request body)
- `PrimaryPhotoId` MUST reference a ToolPhoto with matching `ToolId` (prevent reference to other users' photos)

**Applies to**: FEAT-01 Tool Listings

---

### INPUT-02: BorrowRequest Input Validation

**Risk**: Logic flaws via invalid date ranges enable overbooking. XSS in project descriptions. Mass assignment corrupts transaction state.

**Requirement**:
- `POST /api/v1/borrow-requests` MUST validate:
  - `RequestedStartDate >= today` (UTC)
  - `RequestedEndDate > RequestedStartDate`
  - `RequestedEndDate <= RequestedStartDate + 14 days`
  - `ProjectDescription` length 50-500 characters, HTML-stripped
- `BorrowerId` MUST be set to `currentUserId` server-side (never from request body)
- `OwnerId` MUST be looked up from `Tool.OwnerId` (never from request body)
- `Status` MUST be set to `Pending` on creation (never from request body)
- Approval endpoint (`POST /api/v1/borrow-requests/{id}/approve`) MUST validate `request.OwnerId == currentUserId` BEFORE database commit
- OwnerMessage (max 500 chars) and DeclineReason (min 20, max 500 chars) MUST be HTML-stripped
- No endpoint MUST allow setting `PickedUpAt`, `ReturnedAt`, or `ConfirmedAt` directly (only state transition methods set these)

**Applies to**: FEAT-02 Borrowing Requests, FEAT-04 Borrow Tracking

---

### INPUT-03: User Profile Input Validation

**Risk**: XSS in bio/review fields. Phone number enumeration. Address injection for location spoofing.

**Requirement**:
- `PUT /api/v1/users/{id}` MUST validate:
  - `DisplayName` max 100 characters, HTML-stripped, no leading/trailing whitespace
  - `Bio` max 300 characters, HTML-stripped, max 2 consecutive line breaks
  - `PhoneNumber` MUST be normalized to E.164 format (`+1XXXXXXXXXX`) server-side, max 15 characters
  - `Address` MUST be geocoded via Azure Maps/Google Geocoding API before save (reject if geocoding fails)
  - `Neighborhood` max 50 characters, HTML-stripped
- Rating submission (`POST /api/v1/ratings`) MUST validate:
  - `Stars` integer 1-5 only
  - `ReviewText` max 500 characters, HTML-stripped
  - `TransactionId` MUST reference a BorrowRequest where `Status = Completed` and requester is participant
  - Unique constraint enforced: one rating per user per transaction
- Review text MUST NOT allow embedded URLs to be clickable (display as plain text)

**Applies to**: FEAT-03 User Profiles & Trust System

---

### INPUT-04: Image Upload Validation

**Risk**: Malicious file uploads (executable disguised as image). XXE attacks via SVG. Storage exhaustion from large files.

**Requirement**:
- Image upload endpoints (`POST /api/v1/tools/photos`, `POST /api/v1/users/profile-photo`) MUST validate:
  - File size max 10MB per image
  - MIME type MUST be `image/jpeg`, `image/png`, `image/heic`, or `image/webp` (reject others with 400)
  - File signature (magic bytes) MUST match MIME type (hex signature validation: JPEG `FF D8 FF`, PNG `89 50 4E 47`)
  - SVG format MUST be rejected (XML parsing risk)
- Images MUST be processed with ImageSharp library (convert HEIC to JPEG, resize, re-encode) to strip metadata and sanitize
- Processed images MUST be uploaded to isolated blob storage container (not web-accessible root)
- Original uploaded files MUST be deleted after processing (never stored permanently)
- Blob URLs MUST use time-limited SAS tokens if storage is private (or public-read with non-guessable filenames)

**Applies to**: Foundation - Image Processing Service, FEAT-01 Tool Listings, FEAT-03 User Profiles, FEAT-04 Damage Reports

---

### RACE-01: Double-Booking Prevention

**Risk**: Race condition in borrow approval allows two users to book same tool for overlapping dates, causing conflicts and reputation damage.

**Requirement**:
- PostgreSQL exclusion constraint MUST be defined on BorrowRequests table:
  ```sql
  ALTER TABLE BorrowRequests 
  ADD CONSTRAINT no_overlapping_approved_borrows 
  EXCLUDE USING GIST (
    ToolId WITH =, 
    daterange(RequestedStartDate, RequestedEndDate, '[]') WITH &&
  ) 
  WHERE (Status = 'Approved');
  ```
- Approval operation MUST be wrapped in database transaction (EF Core `SaveChangesAsync` handles this)
- Constraint violation (HTTP 409 from database) MUST be caught and handled:
  - Decline the conflicting request automatically
  - Notify owner: "Someone else was approved for overlapping dates. This request has been auto-declined."
  - Log event for monitoring
- NO application-level locking (database constraint is authoritative)

**Applies to**: FEAT-02 Borrowing Requests - approval workflow

---

### DATA-01: Address and Location Privacy

**Risk**: Exposing full addresses enables stalking, harassment, or theft. Precise coordinates allow triangulation attacks.

**Requirement**:
- Full street address MUST NEVER appear in:
  - Tool detail pages (public)
  - Search result listings
  - User profile pages (even when authenticated)
  - API responses for `GET /api/v1/tools` or `GET /api/v1/users/{id}`
- Full address MUST be revealed ONLY:
  - In email notification after borrow request approval (to borrower only)
  - In `GET /api/v1/borrow-requests/{id}` response when `Status = Approved` and `currentUserId` is borrower or owner
- Distance in search results MUST be rounded to nearest 0.5 mile (format: "2.5 miles away in Maplewood")
- Exact coordinates (lat/lng) MUST NEVER be returned in API responses (only used server-side for distance calculations)
- Map pins MUST show tools within radius but NOT exact coordinates (cluster pins at neighborhood centroid with ±200m random jitter)

**Applies to**: FEAT-01 Tool Listings, FEAT-05 Community Discovery, Foundation - Geocoding Service

---

### DATA-02: Message Thread Privacy

**Risk**: Unauthorized access to private messages exposes coordination details (pickup times, addresses, personal info).

**Requirement**:
- `GET /api/v1/borrow-requests/{id}/messages` MUST verify `currentUserId == request.BorrowerId OR currentUserId == request.OwnerId` BEFORE returning messages
- Message creation (`POST /api/v1/borrow-requests/{id}/messages`) MUST verify same ownership
- Messages MUST be retained permanently (no deletion endpoint in v1) to preserve dispute evidence
- Message endpoints MUST NOT be accessible via public/unauthenticated requests (return 401)
- Message content MUST be HTML-stripped on save (max 1000 characters)

**Applies to**: FEAT-02 Borrowing Requests - messaging system

---

### DATA-03: Transaction History Privacy

**Risk**: Public transaction history exposes borrowing patterns (e.g., "Alice borrows power tools every weekend" enables targeted theft timing).

**Requirement**:
- `GET /api/v1/users/{id}/transactions` MUST verify `id == currentUserId` (users ONLY see their own history, return 403 otherwise)
- Transaction detail endpoint (`GET /api/v1/borrow-requests/{id}`) MUST verify requester is borrower or owner
- Public profile pages MUST show ONLY aggregated statistics (total tools shared, average rating) NOT individual transaction details
- Rating reviews MUST be public ONLY after mutual rating or 7-day window expires (controlled by `Rating.Visible` boolean)

**Applies to**: FEAT-04 Borrow Tracking - transaction history

---

## High Priority Requirements

Should be implemented in the first release. Deferring increases risk significantly.

### SEC-01: HTTPS Enforcement

**Risk**: Man-in-the-middle attacks capture credentials and tokens over unencrypted HTTP. Session hijacking via network sniffing.

**Requirement**:
- Production environment MUST enforce HTTPS on all endpoints (HTTP requests redirect to HTTPS 301)
- Configure in `Program.cs`:
  ```csharp
  app.UseHttpsRedirection();
  app.UseHsts(); // HTTP Strict Transport Security
  ```
- HSTS header MUST be set: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- Development environment MAY use HTTP for localhost (acceptable trade-off for dev velocity)

**Applies to**: Foundation - API infrastructure

---

### SEC-02: CORS Policy

**Risk**: Overly permissive CORS (`Access-Control-Allow-Origin: *`) allows malicious sites to make authenticated requests on behalf of users.

**Requirement**:
- CORS MUST be configured with explicit allowed origins (NO wildcards in production):
  ```csharp
  builder.Services.AddCors(options =>
  {
      options.AddDefaultPolicy(policy =>
      {
          policy.WithOrigins("https://toolshare.com", "https://www.toolshare.com")
                .AllowCredentials()
                .AllowAnyHeader()
                .WithMethods("GET", "POST", "PUT", "PATCH", "DELETE");
      });
  });
  ```
- `AllowCredentials()` MUST be enabled (required for HttpOnly cookies)
- Development environment MAY allow `http://localhost:5173` (Vite default port)

**Applies to**: Foundation - API infrastructure

---

### SEC-03: SQL Injection Prevention

**Risk**: Raw SQL queries with string concatenation enable database compromise, data exfiltration, or deletion.

**Requirement**:
- ALL database queries MUST use Entity Framework Core parameterized queries (LINQ or `FromSqlRaw` with parameters)
- NO raw SQL string concatenation (e.g., `$"SELECT * FROM Tools WHERE Id = {id}"`)
- If `FromSqlRaw` is unavoidable, MUST use parameterized syntax:
  ```csharp
  context.Tools.FromSqlRaw(
      "SELECT * FROM Tools WHERE OwnerId = {0} AND Status = {1}", 
      userId, 
      status
  )
  ```
- Stored procedures MUST NOT be used (business logic in application code per tech stack standards)

**Applies to**: All features - database access layer

---

### SEC-04: Email Verification Enforcement

**Risk**: Unverified email addresses enable spam, fake accounts, and inability to recover accounts. Attackers register with others' emails.

**Requirement**:
- Email verification MUST be required before users can create tool listings or submit borrow requests
- Unverified users MUST be redirected to "Verify your email" page when attempting protected actions
- Verification tokens MUST be cryptographically random (256-bit), single-use, and expire after 24 hours
- Verification link format: `https://toolshare.com/verify-email?token={token}&email={urlEncodedEmail}`
- Email change MUST trigger re-verification (old email loses verified status immediately)

**Applies to**: Foundation - Authentication system

---

### SEC-05: Phone Verification Rate Limiting

**Risk**: SMS verification abuse enables toll fraud (attackers generate thousands of SMS to premium numbers). Credential stuffing via phone number enumeration.

**Requirement**:
- Phone verification SMS sends MUST be limited to 5 per phone number per 24 hours (tracked in `User.PhoneVerificationAttempts` JSONB field)
- Incorrect code attempts MUST be limited to 3 per phone number per 24 hours
- After limits exceeded, phone number MUST be locked for 24 hours (no new codes sent)
- Verification codes MUST be 6 digits, cryptographically random, expire after 10 minutes
- Previous codes MUST be invalidated when new code is sent
- Background job MUST clear `PhoneVerificationAttempts` older than 24 hours hourly

**Applies to**: FEAT-03 User Profiles - phone verification

---

### SEC-06: Geocoding API Key Protection

**Risk**: Exposed API keys enable quota exhaustion attacks (attacker spams geocoding endpoint, racks up $1000s in API charges). Key theft for use in other projects.

**Requirement**:
- Geocoding API keys (Azure Maps or Google) MUST be stored in Azure Key Vault or environment variables (never in appsettings.json committed to Git)
- Geocoding service MUST implement retry logic with exponential backoff (prevent rate limit violations)
- Geocoding responses MUST be cached in Redis for 30 days (key: `geocode:{sha256(address)}`)
- Geocoding endpoint MUST NOT be exposed to frontend (only backend internal calls)

**Applies to**: Foundation - Geocoding service

---

### SEC-07: Background Job Authorization

**Risk**: Unauthenticated Hangfire dashboard allows attackers to view sensitive job data, cancel jobs, or execute arbitrary code.

**Requirement**:
- Hangfire dashboard (`/hangfire`) MUST be protected by authorization:
  ```csharp
  app.UseHangfireDashboard("/hangfire", new DashboardOptions
  {
      Authorization = new[] { new HangfireAuthorizationFilter() }
  });
  ```
- `HangfireAuthorizationFilter` MUST verify user is authenticated and has Admin role
- Dashboard MUST NOT be accessible in production without authentication
- Background jobs MUST NOT log sensitive data (passwords, tokens, full addresses) in job arguments or results

**Applies to**: Foundation - Background job infrastructure

---

### SEC-08: Error Message Information Disclosure

**Risk**: Detailed error messages leak stack traces, connection strings, or internal paths to attackers, enabling targeted attacks.

**Requirement**:
- Production environment MUST return generic error messages for 500 errors:
  - Client sees: `{ "error": "An unexpected error occurred. Please try again." }`
  - Detailed error logged to Application Insights (not returned to client)
- Development environment MAY return detailed errors for debugging
- Configure in `Program.cs`:
  ```csharp
  if (app.Environment.IsDevelopment())
  {
      app.UseDeveloperExceptionPage();
  }
  else
  {
      app.UseExceptionHandler("/error");
      app.UseHsts();
  }
  ```
- Database constraint violations MUST return user-friendly messages (not raw SQL error text)

**Applies to**: Foundation - Global error handling

---

### SEC-09: Session Timeout and Logout

**Risk**: Abandoned sessions on shared computers allow account takeover. Long-lived tokens increase compromise window.

**Requirement**:
- JWT tokens MUST expire after 24 hours (no extension, user must re-login)
- Refresh tokens MUST expire after 30 days and rotate on use
- Logout endpoint (`POST /api/v1/auth/logout`) MUST invalidate refresh token (add to blacklist in Redis with TTL = token expiry)
- Frontend MUST clear auth cookies and redirect to login on 401 responses
- Idle timeout warning SHOULD be shown at 23 hours (optional UX enhancement)

**Applies to**: Foundation - Authentication system

---

### SEC-10: Notification Email Spoofing Prevention

**Risk**: Attackers send phishing emails appearing to be from ToolShare. SPF/DKIM misconfiguration allows domain spoofing.

**Requirement**:
- Email sending domain MUST have SPF record configured:
  - `v=spf1 include:sendgrid.net ~all` (for SendGrid)
  - `v=spf1 include:_spf.google.com ~all` (for Google SMTP)
- DKIM signing MUST be enabled in SendGrid/Azure Communication Services
- DMARC policy MUST be configured (minimum: `v=DMARC1; p=quarantine; rua=mailto:security@toolshare.com`)
- Email templates MUST include sender verification text: "This email was sent from ToolShare. If you didn't expect it, ignore it or contact support@toolshare.com"

**Applies to**: Foundation - Email service

---

## Medium Priority Requirements

Best practice; address before going to production with real users.

### SEC-11: Content Security Policy (CSP)

**Risk**: XSS attacks via injected scripts. Clickjacking via iframe embedding.

**Requirement**:
- CSP header SHOULD be set in API responses:
  ```
  Content-Security-Policy: 
    default-src 'self'; 
    script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; 
    style-src 'self' 'unsafe-inline'; 
    img-src 'self' data: https:; 
    font-src 'self' data:;
    frame-ancestors 'none';
  ```
- `X-Frame-Options: DENY` SHOULD be set (prevent clickjacking)
- `X-Content-Type-Options: nosniff` SHOULD be set (prevent MIME sniffing)

**Applies to**: Foundation - API infrastructure

---

### SEC-12: Activity Feed Rate Limiting

**Risk**: Rapid tool creation/deletion spam pollutes activity feed. Reputation manipulation via fake activity.

**Requirement**:
- Tool creation SHOULD be rate-limited to 10 per user per hour
- Tool publish (draft → published) SHOULD be rate-limited to 5 per user per hour
- Activity event queries SHOULD be cached for 5 minutes (reduce database load)

**Applies to**: FEAT-01 Tool Listings, FEAT-05 Community Discovery

---

### SEC-13: Borrow Extension Abuse Prevention

**Risk**: Users spam extension requests to harass owners. Malicious owners deny all extensions to sabotage borrowers.

**Requirement**:
- Extension requests SHOULD be rate-limited to 3 per borrow per 24 hours
- Users with >5 timed-out extension requests SHOULD trigger review flag (logged, not auto-restricted)
- Extension request timeout (72 hours) SHOULD be enforced via background job (no manual circumvention)

**Applies to**: FEAT-04 Borrow Tracking - extension workflow

---

### SEC-14: Password Strength Requirements

**Risk**: Weak passwords (e.g., "password123") enable credential stuffing attacks.

**Requirement**:
- Password SHOULD meet minimum requirements:
  - At least 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character
- Configure ASP.NET Identity password policy in `Program.cs`:
  ```csharp
  builder.Services.Configure<IdentityOptions>(options =>
  {
      options.Password.RequiredLength = 8;
      options.Password.RequireUppercase = true;
      options.Password.RequireLowercase = true;
      options.Password.RequireDigit = true;
      options.Password.RequireNonAlphanumeric = true;
  });
  ```

**Applies to**: Foundation - Authentication system

---

### SEC-15: Audit Logging for Sensitive Operations

**Risk**: Account compromise or insider threats go undetected without audit trail.

**Requirement**:
- The following actions SHOULD be logged to audit table:
  - User login/logout (IP address, timestamp, user agent)
  - Password changes (timestamp only, not old/new passwords)
  - Email address changes
  - Tool deletion (tool ID, user ID, timestamp)
  - Borrow approval/decline (transaction ID, decision, timestamp)
  - Rating submission (rater, rated, transaction, stars)
- Logs SHOULD be retained for 90 days minimum
- Logs SHOULD be write-only (no user-facing deletion)

**Applies to**: All features - audit infrastructure

---

## Feature-Specific Notes

### Tool Listings (FEAT-01)

- Tool photo URLs stored in database MUST be validated as blob storage URLs (regex: `^https://[account].blob.core.windows.net/toolshare-images/tools/\d+/\d+(_thumb)?\.(jpg|png)$`)
- Tool deletion MUST cascade delete ToolPhoto records AND delete blobs from storage (prevent orphaned files)
- Tool location update background job (50+ tools async) MUST not expose location changes mid-update (eventual consistency acceptable)

### Borrowing Requests (FEAT-02)

- RequestMessage table MUST have `CreatedAt` index for pagination performance
- Auto-decline on tool unavailability MUST use database transaction (decline all pending requests atomically)
- Withdrawal reason MUST be HTML-stripped and logged for abuse pattern detection

### User Profiles & Trust System (FEAT-03)

- Profile statistics caching MUST handle race conditions (last-write-wins acceptable, eventual consistency)
- Rating visibility flip (mutual reveal) MUST be atomic (both ratings visible or both hidden, no partial state)
- Phone number changes MUST invalidate previous verification status immediately

### Borrow Tracking & Returns (FEAT-04)

- Auto-confirmation after 7 days MUST be idempotent (running job twice doesn't create duplicate confirmations)
- Damage report photos MUST be uploaded to separate blob container (`damage-reports/` not `tools/`) to prevent borrower from deleting evidence
- Rebuttal submission MUST check 30-day deadline server-side (not just frontend validation)

### Community Discovery (FEAT-05)

- Map pin clustering MUST not expose exact coordinates (cluster centroid with jitter)
- Follow relationship MUST prevent self-follows (database constraint: `CHECK (FollowerUserId != FollowedUserId)`)
- Activity event queries MUST be read-only (no DELETE or UPDATE allowed via API)

---

## What the Engineering Spec Must Include

A checklist of security requirements the engineering spec agent must address in each component:

**Foundation**:
- [ ] Password hashing algorithm confirmed as ASP.NET Identity default (PBKDF2-SHA256, 10K+ iterations)
- [ ] JWT signing algorithm specified (HMAC-SHA256 or RS256) with key rotation policy
- [ ] JWT expiry set to 24 hours, refresh token expiry 30 days with rotation
- [ ] Refresh token blacklist implemented in Redis
- [ ] Rate limiting rules for auth endpoints: login 5/15min, register 3/hour, password-reset 3/hour per email
- [ ] CORS policy explicitly defined with exact origins (NO `*` wildcard)
- [ ] HTTPS enforcement in production (`UseHttpsRedirection`, HSTS header)
- [ ] Global error handler returns generic messages in production (no stack traces)
- [ ] Hangfire dashboard protected with admin authorization filter
- [ ] Image upload validation: file size, MIME type, magic byte signature check, ImageSharp re-encoding

**All authenticated endpoints**:
- [ ] Authorization policy named and enforced via `[Authorize(Policy = "...")]` attribute
- [ ] 403 Forbidden returned when user lacks permission (not 404)
- [ ] Current user ID retrieved from JWT claims, never from request parameters

**Tool CRUD endpoints** (`/api/v1/tools`):
- [ ] Input validation: Title max 100 chars, Description max 2000, ConditionNotes max 500, HTML-stripped
- [ ] Category and Status validated against enum
- [ ] OwnerId set to currentUserId server-side (never from request body)
- [ ] Tool location (lat/lng) auto-populated from owner profile (never user-submitted)
- [ ] Authorization check: PUT/DELETE only allowed if `tool.OwnerId == currentUserId`

**BorrowRequest endpoints** (`/api/v1/borrow-requests`):
- [ ] Input validation: dates, description length, HTML-stripping
- [ ] BorrowerId set to currentUserId server-side
- [ ] OwnerId looked up from Tool, never from request
- [ ] Status enum validated, never directly settable by user
- [ ] Approval endpoint wrapped in database transaction
- [ ] PostgreSQL exclusion constraint defined for double-booking prevention
- [ ] Constraint violation caught, auto-decline triggered, owner notified
- [ ] Authorization: only participants (borrower or owner) access transaction details

**User profile endpoints** (`/api/v1/users/{id}`):
- [ ] Authorization: PUT only allowed if `id == currentUserId`
- [ ] Input validation: DisplayName max 100, Bio max 300, PhoneNumber E.164 normalization
- [ ] Address geocoded server-side, reject if geocoding fails
- [ ] Phone verification rate limits: 5 SMS sends, 3 incorrect codes per 24 hours
- [ ] Full address NEVER returned in public profile responses
- [ ] Transaction history endpoint verifies `id == currentUserId` (403 otherwise)

**Rating endpoints** (`POST /api/v1/ratings`):
- [ ] Input validation: Stars 1-5, ReviewText max 500 chars, HTML-stripped
- [ ] Unique constraint enforced: one rating per user per transaction
- [ ] TransactionId must reference completed transaction where user is participant
- [ ] Rating visibility logic implemented (mutual reveal or 7-day window)

**Image upload endpoints**:
- [ ] File size max 10MB enforced
- [ ] MIME type validated (JPEG, PNG, HEIC, WebP only)
- [ ] Magic byte signature verified (prevent disguised executables)
- [ ] SVG rejected (XML parsing risk)
- [ ] ImageSharp used for re-encoding (strips metadata, sanitizes)
- [ ] Original uploads deleted after processing
- [ ] Blob URLs use time-limited SAS tokens or non-guessable filenames

**Message endpoints** (`/api/v1/borrow-requests/{id}/messages`):
- [ ] Authorization: only borrower or owner access messages
- [ ] Content HTML-stripped, max 1000 chars
- [ ] No deletion endpoint (messages retained permanently)

**Map and discovery endpoints**:
- [ ] Exact coordinates (lat/lng) NEVER returned in API responses
- [ ] Distance rounded to nearest 0.5 mile in responses
- [ ] Address shown only post-approval (in borrow request detail for participants)
- [ ] Map pin validation API (`/tools/{id}/availability`) checks status before popup

**Background jobs**:
- [ ] Auto-confirmation job (7 days) is idempotent
- [ ] Extension timeout job (72 hours) is idempotent
- [ ] Jobs do not log sensitive data (passwords, tokens, full addresses)
- [ ] Statistics update job handles race conditions gracefully

**Email notifications**:
- [ ] SPF record configured for sending domain
- [ ] DKIM signing enabled
- [ ]