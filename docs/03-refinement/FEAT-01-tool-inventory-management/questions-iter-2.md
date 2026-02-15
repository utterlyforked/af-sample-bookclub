# Tool Inventory Management - Technical Review (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: February 15, 2025

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. All critical questions from iteration 1 have been answered clearly with specific validation rules, technical decisions, and implementation guidance provided.

## What's Clear

### Data Model
- **Tool entity** with clear field constraints: Title (5-150 chars), Description (20-2000 chars), Brand/Model (optional, 50 chars each), EstimatedValue (int $1-$10,000), YearPurchased (1950-current)
- **Single ownership model**: One user per tool, clear authorization boundaries
- **Photo storage**: Up to 5 photos per tool, URLs stored in database, blobs in external storage
- **Soft delete pattern**: Preserve loan history and analytics data
- **Status enumeration**: Available, Temporarily Unavailable, On Loan
- **Category system**: Standardized list (Power Tools, Garden Tools, Hand Tools, etc.)

### Business Logic
- **Validation**: Moderate constraints with helpful warnings for edge cases (unusual values, category ranges)
- **Uniqueness handling**: Warning for duplicate titles within user inventory, but allow override
- **Photo processing**: Synchronous resize/compress to 1200px max width during upload
- **Availability management**: Manual-only status changes, no automatic expiration
- **Category changes**: Allowed with user confirmation, no change history tracking

### API Design
- **CRUD operations**: Create, Read, Update, Delete tools with proper authorization
- **Photo upload endpoint**: Handle multipart form data with immediate processing
- **Status management**: Dedicated endpoints for availability state changes
- **Soft delete**: DELETE marks as deleted, preserves data, can undelete within 30 days

### UI/UX
- **Tool creation form**: Clear validation feedback, photo upload with progress indicators
- **Duplicate name warnings**: "You already have a 'Cordless Drill' - consider adding brand/model"
- **Value guidance**: Category-specific range hints ("Hand Tools: $10-$200")
- **Deletion confirmation**: Show loan history count before confirming delete
- **Status indicators**: Clear visual states for Available/Unavailable/On Loan

### Edge Cases
- **Upload failures**: 30-second timeout with retry, clear error messages for oversized/corrupt files
- **Tools on loan**: Cannot be deleted until returned
- **Inactive owners**: Tools hidden when owner account deactivated
- **Value validation**: Warnings for unusual ranges but allow override
- **Photo cleanup**: 30-day retention after tool deletion for recovery

## Implementation Notes

**Database**:
- `Tools` table with UserId foreign key, soft delete flag (IsDeleted, DeletedAt)
- `ToolPhotos` table with ToolId foreign key, URL and display order
- Unique constraint considerations: None enforced at DB level (handled in business logic)
- Status enum: Available = 0, TemporarilyUnavailable = 1, OnLoan = 2

**Authorization**:
- Only tool owner can edit/delete their tools
- All authenticated users can view available tools
- System admin can manage any tool (for moderation)

**Validation**:
- Title: 5-150 characters, required
- Description: 20-2000 characters, required  
- EstimatedValue: Integer 1-10000, required
- YearPurchased: 1950 to DateTime.Now.Year, optional
- Brand/Model: Max 50 chars each, optional
- Photos: Max 5 per tool, 5MB each, common image formats

**Key Decisions**:
- Single ownership model (no co-ownership in v1)
- Synchronous photo processing (resize on upload thread)
- Manual availability management (no background automation)
- Soft delete with 30-day recovery window
- Category-based value guidance (no strict enforcement)
- Gentle duplicate name handling (warn but allow)

## Recommended Next Steps

1. Create engineering specification with detailed implementation plan
2. Set up database schema with Entity Framework migrations
3. Implement photo processing pipeline with resize/compress logic
4. Create API endpoints following RESTful patterns
5. Build React components with TypeScript interfaces

---

**This feature is ready for detailed engineering specification.**