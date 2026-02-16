# User Profiles & Community Verification — Engineering Spec

**Type**: feature
**Component**: user-profiles-verification
**Dependencies**: foundation-spec (User, Group, GroupMember entities)
**Status**: Ready for Implementation

---

## Overview

This component extends the foundation User entity with profile data and implements a community-based verification system. Users can add profile information (bio, location, social links, avatar) which is stored in a UserProfile entity. Community verification is managed through a VerificationNomination entity where group members can nominate users for a verified badge. When a user receives 3+ nominations from distinct groups, they are automatically marked as verified. This spec owns UserProfile and VerificationNomination entities; it reads from foundation User, Group, and GroupMember entities.

---

## Data Model

### UserProfile

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| user_id | UUID | FK, unique, not null | References User.id |
| bio | string(500) | nullable | Plain text, no HTML |
| location | string(100) | nullable | Free-form text |
| website_url | string(2048) | nullable | Must be valid URL if provided |
| twitter_handle | string(15) | nullable | Without @ symbol, alphanumeric + underscore only |
| github_username | string(39) | nullable | GitHub username format |
| linkedin_url | string(2048) | nullable | Must be valid LinkedIn URL if provided |
| avatar_url | string(2048) | nullable | HTTPS only, links to blob storage |
| created_at | datetime | not null | UTC, set on insert |
| updated_at | datetime | not null | UTC, updated on every modification |

**Indexes**:
- `(user_id)` unique

**Relationships**:
- Belongs to `User` via `user_id` (cascade delete)

### VerificationNomination

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on insert |
| nominee_user_id | UUID | FK, not null | References User.id - the person being nominated |
| nominator_user_id | UUID | FK, not null | References User.id - the person nominating |
| group_id | UUID | FK, not null | References Group.id - the group context |
| reason | string(500) | nullable | Optional explanation |
| created_at | datetime | not null | UTC, set on insert |

**Indexes**:
- `(nominee_user_id, group_id)` unique — one nomination per user per group
- `(nominee_user_id, created_at)` — for counting nominations
- `(group_id, created_at)` — for group activity queries

**Relationships**:
- References `User` via `nominee_user_id` (cascade delete)
- References `User` via `nominator_user_id` (cascade delete)
- References `Group` via `group_id` (cascade delete)

> **Note**: This spec owns only UserProfile and VerificationNomination entities. The User entity (which includes the `is_verified` boolean field) is defined in the Foundation Spec and is referenced here by name.

---

## API Endpoints

### GET /api/v1/users/{userId}/profile

**Auth**: None (public read)
**Authorization**: None

**Path parameters**:
| Field | Type | Validation |
|-------|------|------------|
| userId | UUID | Valid UUID format |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | UserProfile.id |
| userId | UUID | |
| bio | string | null | Max 500 chars |
| location | string | null | Max 100 chars |
| websiteUrl | string | null | |
| twitterHandle | string | null | Without @ symbol |
| githubUsername | string | null | |
| linkedinUrl | string | null | |
| avatarUrl | string | null | |
| isVerified | boolean | From User.is_verified |
| verificationCount | integer | Count of distinct groups that nominated this user |
| createdAt | ISO 8601 datetime | UTC |
| updatedAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 404 | User not found or has no profile (return empty profile with userId and isVerified=false) |
| 400 | Invalid userId format |

---

### PUT /api/v1/users/{userId}/profile

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated user must match userId

**Path parameters**:
| Field | Type | Validation |
|-------|------|------------|
| userId | UUID | Valid UUID format |

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| bio | string | null | no | Max 500 chars, plain text only |
| location | string | null | no | Max 100 chars |
| websiteUrl | string | null | no | Valid URL format, max 2048 chars |
| twitterHandle | string | null | no | Alphanumeric + underscore only, max 15 chars, strip leading @ if present |
| githubUsername | string | null | no | GitHub username format, max 39 chars |
| linkedinUrl | string | null | no | Valid URL format, must contain "linkedin.com", max 2048 chars |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| userId | UUID | |
| bio | string | null | |
| location | string | null | |
| websiteUrl | string | null | |
| twitterHandle | string | null | |
| githubUsername | string | null | |
| linkedinUrl | string | null | |
| avatarUrl | string | null | Not updated by this endpoint |
| isVerified | boolean | |
| verificationCount | integer | |
| createdAt | ISO 8601 datetime | UTC |
| updatedAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure — returns field-level errors |
| 401 | Not authenticated |
| 403 | userId does not match authenticated user |
| 404 | User not found |

---

### POST /api/v1/users/{userId}/profile/avatar

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated user must match userId

**Path parameters**:
| Field | Type | Validation |
|-------|------|------------|
| userId | UUID | Valid UUID format |

**Request body**: `multipart/form-data`
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| file | binary | yes | Image file (JPEG, PNG, GIF, WebP), max 5MB, min 100x100px, max 2048x2048px |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| avatarUrl | string | HTTPS URL to uploaded image in blob storage |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Invalid file format, size, or dimensions |
| 401 | Not authenticated |
| 403 | userId does not match authenticated user |
| 404 | User not found |
| 413 | File exceeds 5MB |

---

### POST /api/v1/verification/nominations

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated user must be a GroupMember in the specified group

**Request body**:
| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| nomineeUserId | UUID | yes | Valid UUID, user must exist |
| groupId | UUID | yes | Valid UUID, group must exist, nominator must be member |
| reason | string | no | Max 500 chars |

**Success response** `201 Created`:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| nomineeUserId | UUID | |
| nominatorUserId | UUID | Authenticated user |
| groupId | UUID | |
| reason | string | null | |
| createdAt | ISO 8601 datetime | UTC |
| nomineeIsNowVerified | boolean | True if this nomination pushed nominee to 3+ groups |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 400 | Validation failure |
| 401 | Not authenticated |
| 403 | Nominator is not a member of the specified group |
| 404 | Nominee user or group not found |
| 409 | Nomination already exists for this user in this group |
| 422 | Nominator cannot nominate themselves |

---

### GET /api/v1/verification/nominations/{userId}

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated user must match userId OR be a GroupMember in any group that nominated this user

**Path parameters**:
| Field | Type | Validation |
|-------|------|------------|
| userId | UUID | Valid UUID format |

**Success response** `200 OK`:
| Field | Type | Notes |
|-------|------|-------|
| nomineeUserId | UUID | |
| isVerified | boolean | From User.is_verified |
| totalNominations | integer | Count of VerificationNomination records |
| distinctGroupCount | integer | Count of distinct group_id values |
| nominations | array | List of nomination details |

**nominations array item**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| groupId | UUID | |
| groupName | string | From Group.name |
| nominatorUserId | UUID | |
| nominatorName | string | From User.name |
| reason | string | null | |
| createdAt | ISO 8601 datetime | UTC |

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is not authorized to view this data |
| 404 | User not found |

---

### DELETE /api/v1/verification/nominations/{nominationId}

**Auth**: Required (Bearer JWT)
**Authorization**: Authenticated user must be the original nominator OR a group admin of the nomination's group

**Path parameters**:
| Field | Type | Validation |
|-------|------|------------|
| nominationId | UUID | Valid UUID format |

**Success response** `204 No Content`:
(Empty body)

**Error responses**:
| Status | Condition |
|--------|-----------|
| 401 | Not authenticated |
| 403 | User is not authorized to delete this nomination |
| 404 | Nomination not found |

---

## Business Rules

1. UserProfile is created automatically when a user first updates their profile; it does not exist on User creation.
2. Avatar files are stored in blob storage with path pattern `avatars/{userId}/{timestamp}.{extension}`.
3. Avatar URLs must use HTTPS only.
4. A user becomes verified (User.is_verified = true) when they have nominations from 3 or more distinct groups.
5. A user loses verified status (User.is_verified = false) if their distinct group nomination count drops below 3 (e.g., via nomination deletion or group deletion).
6. A user may only be nominated once per group (uniqueness enforced at database level).
7. A user cannot nominate themselves (validation enforced at API level).
8. Only current GroupMembers of a group can nominate users on behalf of that group.
9. Twitter handles are stored without the leading @ symbol; API must strip it if provided.
10. When a nomination is deleted, the system must recalculate the nominee's is_verified status.
11. When a group is deleted, all associated nominations are cascade deleted and affected users' verification status is recalculated.
12. The verificationCount field in profile responses reflects the count of distinct groups, not total nominations.

---

## Validation Rules

| Field | Rule | Error message |
|-------|------|---------------|
| bio | Max 500 chars | "Bio must not exceed 500 characters" |
| location | Max 100 chars | "Location must not exceed 100 characters" |
| websiteUrl | Valid URL format, HTTPS or HTTP, max 2048 chars | "Website URL must be a valid URL" / "Website URL must not exceed 2048 characters" |
| twitterHandle | Alphanumeric + underscore only, max 15 chars | "Twitter handle must contain only letters, numbers, and underscores" / "Twitter handle must not exceed 15 characters" |
| githubUsername | Valid GitHub username format (alphanumeric + hyphen, cannot start/end with hyphen), max 39 chars | "GitHub username format is invalid" / "GitHub username must not exceed 39 characters" |
| linkedinUrl | Valid URL format, must contain "linkedin.com", max 2048 chars | "LinkedIn URL must be a valid LinkedIn profile URL" / "LinkedIn URL must not exceed 2048 characters" |
| avatar file | Must be image type (JPEG, PNG, GIF, WebP), max 5MB, min 100x100px, max 2048x2048px | "File must be an image" / "File must not exceed 5MB" / "Image must be at least 100x100 pixels" / "Image must not exceed 2048x2048 pixels" |
| nomineeUserId | Valid UUID, user must exist, cannot be self | "Nominee user not found" / "You cannot nominate yourself" |
| groupId | Valid UUID, group must exist, nominator must be member | "Group not found" / "You must be a member of this group to nominate" |
| reason | Max 500 chars | "Reason must not exceed 500 characters" |

---

## Authorization

| Action | Required policy | Notes |
|--------|----------------|-------|
| View profile | None | Public read |
| Update profile | Authenticated | Own profile only (userId must match JWT sub claim) |
| Upload avatar | Authenticated | Own profile only |
| Create nomination | GroupMember | Must be member of the group specified in nomination |
| View nominations | Authenticated | Own nominations OR shared group membership with nominee |
| Delete nomination | Authenticated | Must be original nominator OR group admin of nomination's group |

---

## Acceptance Criteria

- [ ] User can view any profile without authentication
- [ ] User can update their own profile with valid bio, location, and social links
- [ ] User cannot update another user's profile (returns 403)
- [ ] Twitter handle with leading @ is automatically stripped before storage
- [ ] Invalid URL formats for websiteUrl or linkedinUrl return 400 with field error
- [ ] User can upload avatar image and receive HTTPS URL in response
- [ ] Avatar upload rejects files over 5MB with 413 status
- [ ] Avatar upload rejects images smaller than 100x100px with 400 status
- [ ] Avatar upload rejects non-image files with 400 status
- [ ] GroupMember can nominate another user in their group
- [ ] User cannot nominate themselves (returns 422)
- [ ] User cannot nominate same person twice in same group (returns 409)
- [ ] Non-member cannot nominate user on behalf of group (returns 403)
- [ ] User becomes verified when reaching 3 distinct group nominations
- [ ] User's is_verified field is updated immediately upon 3rd group nomination
- [ ] GET profile returns verificationCount matching distinct group count
- [ ] GET nominations returns list of all nominations with group and nominator details
- [ ] User can view nominations only if authorized (self or shared group)
- [ ] Nominator can delete their own nomination
- [ ] Group admin can delete any nomination in their group
- [ ] Deleting nomination recalculates is_verified status if drops below 3 groups
- [ ] Deleting a group cascade deletes all its nominations and recalculates affected users' verification
- [ ] Profile created_at and updated_at timestamps are in UTC ISO 8601 format

---

## Security Requirements

**From AppSec Review:**

- Avatar uploads must validate image content (not just extension) to prevent malicious file execution
- Uploaded avatars must be served from a separate domain (blob storage CDN) to prevent XSS
- Avatar filenames must be sanitized and not include user input to prevent path traversal
- Rate limit avatar uploads to 5 per user per hour to prevent storage abuse
- Profile update endpoints must validate content length before processing to prevent DoS
- Social media URLs must be validated as legitimate external links (no javascript: or data: schemes)
- Nomination endpoints must verify group membership server-side (never trust client-provided group context)
- The is_verified calculation must happen server-side in a transaction to prevent race conditions
- Nomination deletion must verify authorization before calculating verification status changes

**Additional Requirements:**

- All blob storage URLs must be HTTPS only
- Avatar image processing must strip EXIF metadata to protect user privacy
- Rate limit: max 10 profile updates per user per hour
- Rate limit: max 20 nominations per user per day (to prevent badge farming)

---

## Out of Scope

- Email notifications for verification badge awarded (future feature)
- Profile privacy settings (all profiles are public in v1)
- Bulk nomination imports
- Verification badge revocation by admins
- Profile visit analytics
- Custom badge icons or tiers
- Nomination voting or weighting by user reputation
- Test plans (owned by QA spec)
- Implementation code (engineer's responsibility)