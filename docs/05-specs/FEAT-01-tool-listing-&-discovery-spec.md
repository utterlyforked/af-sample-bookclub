# Tool Listing & Discovery — Engineering Spec

**Type**: feature
**Component**: tool-listing-discovery
**Dependencies**: foundation-spec
**Status**: Ready for Implementation

---

## Overview

This component provides the public-facing catalog of AI tools, enabling unauthenticated users to browse, search, filter, and view details of tools submitted by vendors and approved by admins. It owns the read-only display layer for tools, categories, and pricing tiers, while the underlying Tool, Category, and PricingTier entities are defined in the foundation spec. This feature does not handle tool submission, approval workflows, or vendor management.

---

## Data Model

> **Note**: This spec owns no new entities. All data model entities (Tool, Category, PricingTier, Vendor, ToolCategory) are defined in the Foundation Spec and referenced here by name only.

**Entities referenced from Foundation**:
- `Tool` (id, name, slug, tagline, description, website, logo_url, status, vendor_id, created_at, updated_at)
- `Category` (id, name, slug, description, display_order)
- `PricingTier` (id, tool_id, name, price_monthly, price_annual, features, display_order)
- `Vendor` (id, name, logo_url)
- `ToolCategory` (tool_id, category_id)

**Additional indexes required for this feature**:
- `Tool(status, created_at DESC)` — for listing published tools
- `Tool(slug)` unique — for canonical URLs
- `ToolCategory(category_id, tool_id)` — for category filtering
- `Category(display_order, name)` — for ordered category lists

---

## API Endpoints

### GET /api/v1/tools

**Auth**: None (public)  
**Authorization**: None

**Query parameters**:
| Parameter | Type | Required | Validation | Notes |
|-----------|------|----------|------------|-------|
| category | string | no | Must match existing category slug | Filter by single category |
| search | string | no | Max 100 chars | Full-text search across name, tagline, description |
| page | integer | no | Min 1, default 1 | Pagination |
| limit | integer | no | Min 1, max 100, default 20 | Items per page |
| sort | string | no | Enum: `newest`, `name`, default `newest` | Sort order |

**Success response** `200 OK`:
```json
{
  "tools": [
    {
      "id": "uuid",
      "name": "string",
      "slug": "string",
      "tagline": "string",
      "logoUrl": "string (nullable)",
      "categories": ["string"],
      "vendor": {
        "name": "string",
        "logoUrl": "string (nullable)"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

**Field notes**:
| Field | Type | Notes |
|-------|------|-------|
| tools | array | List of tool summary objects |
| tools[].id | UUID | Tool identifier |
| tools[].name | string | Tool name (max 200 chars) |
| tools[].slug | string | URL-safe identifier |
| tools[].tagline | string | Short description (max 500 chars) |
| tools[].logoUrl | string\|null | Full URL to logo image |
| tools[].categories | string[] | Array of category names |
| tools[].vendor.name | string | Vendor display name |
| tools[].vendor.logoUrl | string\|null | Full URL to vendor logo |
| pagination.page | integer | Current page number |
| pagination.limit | integer | Items per page |
| pagination.total | integer | Total matching tools |
| pagination.totalPages | integer | Calculated: ceil(total / limit) |

**Business rules applied**:
- Only tools with `status = 'published'` are returned
- Search matches against `name`, `tagline`, and `description` fields (case-insensitive)
- Sort `newest` orders by `created_at DESC`
- Sort `name` orders by `name ASC` (case-insensitive)
- Category filter matches tools via `ToolCategory` join

**Error responses**:
| Status | Condition | Response body |
|--------|-----------|---------------|
| 400 | Invalid query parameters | `{ "errors": { "category": ["Category not found"], "limit": ["Must be between 1 and 100"] } }` |

---

### GET /api/v1/tools/{slug}

**Auth**: None (public)  
**Authorization**: None

**Path parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| slug | string | yes | Must match existing tool slug |

**Success response** `200 OK`:
```json
{
  "id": "uuid",
  "name": "string",
  "slug": "string",
  "tagline": "string",
  "description": "string",
  "website": "string",
  "logoUrl": "string (nullable)",
  "categories": [
    {
      "id": "uuid",
      "name": "string",
      "slug": "string"
    }
  ],
  "vendor": {
    "id": "uuid",
    "name": "string",
    "logoUrl": "string (nullable)"
  },
  "pricingTiers": [
    {
      "id": "uuid",
      "name": "string",
      "priceMonthly": "decimal (nullable)",
      "priceAnnual": "decimal (nullable)",
      "features": ["string"]
    }
  ],
  "createdAt": "ISO 8601 datetime",
  "updatedAt": "ISO 8601 datetime"
}
```

**Field notes**:
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Tool identifier |
| name | string | Tool name (max 200 chars) |
| slug | string | URL-safe identifier |
| tagline | string | Short description (max 500 chars) |
| description | string | Full description (max 5000 chars, Markdown allowed) |
| website | string | Full URL to tool website |
| logoUrl | string\|null | Full URL to logo image |
| categories | array | List of associated categories |
| categories[].id | UUID | Category identifier |
| categories[].name | string | Category display name |
| categories[].slug | string | Category URL identifier |
| vendor.id | UUID | Vendor identifier |
| vendor.name | string | Vendor display name |
| vendor.logoUrl | string\|null | Full URL to vendor logo |
| pricingTiers | array | Ordered list of pricing options (by display_order ASC) |
| pricingTiers[].id | UUID | Pricing tier identifier |
| pricingTiers[].name | string | Tier name (e.g., "Free", "Pro") |
| pricingTiers[].priceMonthly | decimal\|null | Monthly price in USD, null if not offered |
| pricingTiers[].priceAnnual | decimal\|null | Annual price in USD, null if not offered |
| pricingTiers[].features | string[] | List of feature descriptions |
| createdAt | ISO 8601 datetime | UTC timestamp |
| updatedAt | ISO 8601 datetime | UTC timestamp |

**Business rules applied**:
- Only tools with `status = 'published'` can be retrieved
- Pricing tiers ordered by `display_order ASC`
- Description field may contain Markdown (sanitized on write, not here)

**Error responses**:
| Status | Condition | Response body |
|--------|-----------|---------------|
| 404 | Slug not found or tool not published | `{ "title": "Tool not found", "status": 404 }` |

---

### GET /api/v1/categories

**Auth**: None (public)  
**Authorization**: None

**Query parameters**: None

**Success response** `200 OK`:
```json
{
  "categories": [
    {
      "id": "uuid",
      "name": "string",
      "slug": "string",
      "description": "string",
      "toolCount": 0
    }
  ]
}
```

**Field notes**:
| Field | Type | Notes |
|-------|------|-------|
| categories | array | All categories ordered by display_order ASC, then name ASC |
| categories[].id | UUID | Category identifier |
| categories[].name | string | Display name (max 100 chars) |
| categories[].slug | string | URL-safe identifier |
| categories[].description | string | Category description (max 1000 chars) |
| categories[].toolCount | integer | Count of published tools in this category |

**Business rules applied**:
- Ordered by `display_order ASC`, then `name ASC` (case-insensitive)
- `toolCount` reflects only tools with `status = 'published'`

**Error responses**: None expected (empty array if no categories exist)

---

### GET /api/v1/categories/{slug}/tools

**Auth**: None (public)  
**Authorization**: None

**Path parameters**:
| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| slug | string | yes | Must match existing category slug |

**Query parameters**:
| Parameter | Type | Required | Validation | Notes |
|-----------|------|----------|------------|-------|
| page | integer | no | Min 1, default 1 | Pagination |
| limit | integer | no | Min 1, max 100, default 20 | Items per page |
| sort | string | no | Enum: `newest`, `name`, default `newest` | Sort order |

**Success response** `200 OK`:
```json
{
  "category": {
    "id": "uuid",
    "name": "string",
    "slug": "string",
    "description": "string"
  },
  "tools": [
    {
      "id": "uuid",
      "name": "string",
      "slug": "string",
      "tagline": "string",
      "logoUrl": "string (nullable)",
      "vendor": {
        "name": "string",
        "logoUrl": "string (nullable)"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "totalPages": 3
  }
}
```

**Field notes**: Same as `GET /api/v1/tools` with addition of `category` object

**Business rules applied**:
- Only tools with `status = 'published'` are returned
- Tools filtered by `ToolCategory` join on `category_id`
- Sort `newest` orders by `created_at DESC`
- Sort `name` orders by `name ASC` (case-insensitive)

**Error responses**:
| Status | Condition | Response body |
|--------|-----------|---------------|
| 404 | Category slug not found | `{ "title": "Category not found", "status": 404 }` |
| 400 | Invalid query parameters | `{ "errors": { "limit": ["Must be between 1 and 100"] } }` |

---

## Business Rules

1. Only tools with `status = 'published'` are visible via any public endpoint.
2. Tool slugs must be unique and immutable once created.
3. Category slugs must be unique and immutable once created.
4. Full-text search is case-insensitive and matches partial words in `name`, `tagline`, and `description`.
5. Pricing tiers are always ordered by `display_order ASC` within a tool's detail view.
6. Categories are always ordered by `display_order ASC`, then alphabetically by name.
7. Pagination `limit` cannot exceed 100 items per page.
8. Category `toolCount` reflects only published tools at query time (not cached).
9. Logo URLs must be absolute URLs (validated at write time, not in this feature).
10. Vendor information is denormalized into tool responses (no separate vendor endpoint in this feature).

---

## Validation Rules

| Field | Rule | Error message |
|-------|------|---------------|
| search (query param) | Max 100 chars | "Search query too long (max 100 characters)" |
| page (query param) | Integer, min 1 | "Page must be 1 or greater" |
| limit (query param) | Integer, min 1, max 100 | "Limit must be between 1 and 100" |
| sort (query param) | Enum: `newest`, `name` | "Invalid sort option (allowed: newest, name)" |
| category (query param) | Must match existing category slug | "Category not found" |
| slug (path param) | Must match existing slug | "Tool not found" / "Category not found" |

---

## Authorization

| Action | Required policy | Notes |
|--------|----------------|-------|
| List tools | None (public) | Anonymous access allowed |
| View tool detail | None (public) | Anonymous access allowed |
| List categories | None (public) | Anonymous access allowed |
| List tools by category | None (public) | Anonymous access allowed |

---

## Acceptance Criteria

- [ ] Unauthenticated user can retrieve paginated list of published tools
- [ ] Tools with `status != 'published'` are never returned in any public endpoint
- [ ] Search query filters tools by name, tagline, and description (case-insensitive)
- [ ] Category filter returns only tools associated with specified category slug
- [ ] Category filter with invalid slug returns 404
- [ ] Tool detail endpoint returns 404 for unpublished or non-existent tools
- [ ] Tool detail includes all pricing tiers ordered by display_order ASC
- [ ] Pagination returns correct `total`, `totalPages`, and `page` metadata
- [ ] Pagination limit exceeding 100 returns 400 error
- [ ] Categories endpoint returns all categories ordered by display_order, then name
- [ ] Category toolCount reflects only published tools
- [ ] Sort by `newest` orders tools by created_at DESC
- [ ] Sort by `name` orders tools alphabetically (case-insensitive)
- [ ] Logo URLs are returned as absolute URLs (or null if not set)
- [ ] Vendor information is included in tool list and detail responses
- [ ] Empty search or category filter returns empty tools array, not an error
- [ ] Response times for tool listing under 200ms for queries returning ≤100 results

---

## Security Requirements

1. **Rate Limiting**: Public endpoints must enforce rate limits to prevent abuse:
   - `GET /api/v1/tools`: 100 requests per IP per minute
   - `GET /api/v1/tools/{slug}`: 200 requests per IP per minute
   - `GET /api/v1/categories`: 50 requests per IP per minute
   - `GET /api/v1/categories/{slug}/tools`: 100 requests per IP per minute

2. **Input Sanitization**: All query parameters must be validated and sanitized to prevent injection attacks (handled by framework validation, not custom code).

3. **CORS Policy**: Public endpoints must allow cross-origin requests from whitelisted domains (configured in appsettings, not hardcoded).

4. **SQL Injection Prevention**: All database queries must use parameterized queries via Entity Framework Core (no raw SQL for user input).

5. **Response Size Limits**: Paginated responses must enforce maximum page size of 100 to prevent memory exhaustion attacks.

6. **Cache-Control Headers**: Responses should include appropriate cache headers:
   - Tool list: `Cache-Control: public, max-age=300` (5 minutes)
   - Tool detail: `Cache-Control: public, max-age=600` (10 minutes)
   - Categories: `Cache-Control: public, max-age=3600` (1 hour)

7. **Error Message Disclosure**: 404 responses must not reveal whether a tool exists but is unpublished (same message for both cases).

---

## Out of Scope

- Tool submission and approval workflows (separate feature)
- Vendor registration and management (separate feature)
- Admin interfaces for managing tools, categories, or pricing tiers (separate feature)
- User accounts, authentication, or saved favorites (separate feature)
- Analytics tracking or view counters (separate feature)
- API versioning strategy beyond `/api/v1/` prefix (foundation concern)
- Caching implementation details (engineering decision)
- CDN configuration for logo images (infrastructure concern)
- SEO meta tags or OpenGraph data (frontend concern)
- A/B testing or feature flags (platform concern)