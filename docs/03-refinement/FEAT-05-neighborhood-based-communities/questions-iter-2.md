# Neighborhood-Based Communities - Technical Review (Iteration 2)

**Status**: ✅ READY FOR IMPLEMENTATION
**Iteration**: 2
**Date**: December 19, 2024

---

## Summary

This feature specification is sufficiently detailed to proceed with implementation. All critical questions from the previous iteration have been answered clearly with specific technical guidance.

## What's Clear

### Data Model
- **Community entity**: Name, center coordinates (lat/lng), postal code, radius (1.5 miles), creation date
- **User-Community relationship**: Each user belongs to exactly one primary community
- **Address validation**: Postal code + street name required, updates limited to once per 365 days
- **Geographic calculations**: Distance-based using coordinate math (center-to-center distances)

### Business Logic
- **Community creation**: Automated when no existing community within 3-mile radius
- **Boundary definition**: Fixed 1.5-mile radius from postal code centroid
- **Adjacent community discovery**: Communities within 5-mile radius of user's home community
- **Activity tracking**: Tools shared + borrowing requests (not just logins)
- **Stats refresh**: Daily batch job updates cached community statistics

### API Design
- **Community assignment**: Automatic during user signup based on postal code
- **Tool discovery**: Default shows home community, optional toggle for 5-mile radius
- **Address updates**: Rate-limited to once per year with full re-verification
- **Community stats**: Cached data served from daily calculations

### UI/UX
- **Default tool view**: User's home community only
- **Discovery expansion**: Toggle to "Include nearby areas" shows 5-mile radius
- **Distance display**: Show distance in search results ("Drill - 0.3 miles")
- **Community dashboard**: Member count, activity stats, popular tool categories
- **Guidelines management**: Structured categories with member voting interface

### Edge Cases
- **Large postal codes**: User gets 1.5-mile community (may be smaller than postal code)
- **Multiple nearby communities**: User joins closest by center-to-center distance
- **Invalid postal codes**: Block signup until valid postal code entered
- **Community health**: 60-day inactivity triggers member email nudges
- **Small communities**: <3 members skip voting requirements for guidelines

## Implementation Notes

**Database**:
- Communities table with (postal_code, center_lat, center_lng, radius_miles, created_at)
- Users table with (community_id, address_last_updated) foreign key
- Unique constraint on postal_code in Communities
- Spatial indexing on community coordinates for distance queries

**Authorization**:
- Community membership required for tool discovery within that community
- Any community member can propose guideline changes
- 3+ member approval needed for guideline updates (except communities <3 members)

**Validation**:
- Postal code format validation (country-specific)
- Street name required (non-empty string)
- Address update rate limit: 1 per 365 days per user
- Guideline text fields: 500 character maximum

**Key Decisions**:
- Fixed 1.5-mile radius for all communities (not adaptive)
- 3-mile minimum gap between community centers
- 5-mile radius for adjacent community discovery
- Daily stats updates (not real-time)
- Tool sharing activity (not login activity) for community health metrics

**Geographic Logic**:
- Use postal code geocoding service for center coordinates
- Haversine formula for distance calculations
- Cache distance calculations where possible
- Default tool discovery to home community only

**Performance Considerations**:
- Community stats pre-calculated and cached daily
- Spatial queries optimized with proper indexing
- Adjacent community lookup cached per user

## Recommended Next Steps

1. Create engineering specification with detailed implementation plan
2. Set up postal code geocoding service integration
3. Design spatial database schema with appropriate indexing

---

**This feature is ready for detailed engineering specification.**