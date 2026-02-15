# Neighborhood-Based Communities - Product Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: geographic boundary logic, community creation rules, discovery mechanics)

---

## Feature Overview

The Neighborhood-Based Communities feature organizes users into geographically-focused groups to ensure tool sharing happens within practical pickup distances. Users join communities based on their postal/zip code, creating local networks where tools remain accessible without long drives.

This feature is foundational to the platform's success - without geographic boundaries, users might find tools too far away to be practical, or tool owners might receive requests from users across the city. By creating neighborhood-focused communities, we ensure the platform delivers on its promise of convenient, local tool sharing while building stronger neighborhood connections.

The feature balances discoverability (finding enough tools nearby) with practicality (not traveling 30 minutes for a hammer) by allowing users to see their primary community plus adjacent ones when needed.

---

## User Stories

- As a new user, I want to join my specific neighborhood community so that I only see tools within reasonable distance
- As any user, I want assurance that borrowing options are within my local area so that pickup is convenient
- As a community member, I want to see how active my local toolsharing network is so that I can gauge participation

---

## Acceptance Criteria (UPDATED v1.1)

- Users join communities based on postal/zip code with 1.5-mile radius from postal code center point
- New communities are created only if no existing community exists within 3 miles
- Tool discovery shows user's home community by default, with option to include communities within 5-mile radius
- Community pages show member count, recent activity stats (updated daily), and most shared tool categories
- Users can update address once per year with re-verification
- Community guidelines use structured categories with simple member voting (3+ approvals)

---

## Detailed Specifications (UPDATED v1.1)

**Geographic Boundaries & Community Creation**

**Decision**: Fixed 1.5-mile radius from postal code centroid for all communities

**Rationale**: Postal codes vary enormously in size (0.2 miles urban to 20+ miles rural). Fixed radius ensures consistent, walkable/bikeable community sizes while keeping implementation simple. Rural users get the same practical distance as urban users.

**Examples**:
- User in postal code 12345 joins community "Riverside 12345" covering 1.5-mile radius from that postal code's center
- All tool discovery, by default, happens within this 1.5-mile circle
- Community boundaries are circular, not following postal code shapes

**Edge Cases**:
- Very large postal codes: Users still get 1.5-mile radius, which might be smaller than their postal code
- Very small postal codes: Community might include multiple postal codes within the 1.5-mile radius

---

**Community Creation Logic**

**Decision**: Create new community only if no existing community center is within 3 miles

**Rationale**: Prevents community fragmentation while ensuring reasonable coverage. A 3-mile gap means communities don't overlap much (1.5-mile radius each = 3-mile diameter), but users aren't left in dead zones.

**Examples**:
- User signs up in postal code 10001. System checks if any community center is within 3 miles.
- If yes: User joins the closest existing community
- If no: New community "Manhattan 10001" is created centered on postal code 10001

**Edge Cases**:
- Multiple existing communities within 3 miles: User joins the closest one by center-to-center distance
- Postal code lookup fails: User must re-enter postal code (no community assignment until valid)

---

**Adjacent Community Discovery**

**Decision**: "Adjacent communities" means any community whose center point is within 5 miles of user's home community center

**Rationale**: Simple distance calculation that's fast to query and predictable for users. 5-mile radius captures meaningful nearby communities without overwhelming users with distant options.

**Examples**:
- User's home community center is at coordinates (40.7128, -74.0060)
- Adjacent communities are all communities with centers within 5 miles of that point
- When user toggles "Include nearby areas", they see tools from home community + all adjacent communities
- Search results show distance: "Drill - 0.3 miles" or "Ladder - 2.1 miles"

**User Control**: Users can toggle adjacent community inclusion on/off. Default is home community only.

---

**Address Verification & Updates**

**Decision**: Require valid postal code + street name during signup, allow address updates once per year with full re-verification

**Rationale**: Balances data quality with user experience. Street name requirement discourages fake addresses but doesn't require slow geocoding APIs. Annual limit prevents location gaming while allowing legitimate moves.

**Examples**:
- Valid signup: "12345, Main Street" → assigns to appropriate community
- Invalid signup: "99999, Oak Road" → error message "Please enter a valid postal code"
- Address update: User can change address once per 365 days, requires re-entering postal code + street name

**Edge Cases**:
- User moves twice in one year: Must contact support for exception
- User typos address: Can immediately retry signup with correct information

---

**Community Activity Stats**

**Decision**: Daily batch job updates cached stats. Activity = tools shared or borrowing requests made (not just logins)

**Rationale**: Daily updates provide good performance with acceptably fresh data. Tool sharing activity is more meaningful than just user logins for measuring community health.

**Examples**:
- Community dashboard shows: "47 members, 12 active lenders, 89 tools available, 23 loans completed this month"
- Stats refresh every night at midnight
- "Active lender" = someone who has shared at least one tool in the last 30 days
- Recent activity feed: "Someone borrowed a drill 2 days ago", "New tool shared: Pressure washer"

**Performance**: Stats are cached, so community pages load fast even with hundreds of members.

---

**Inactive Community Management**

**Decision**: Communities with no tool sharing activity (tools shared or borrowing requests) for 60+ days get gentle email nudges to members

**Rationale**: Tool sharing activity is the best indicator of community health. 60 days allows for seasonal variation while catching truly dormant communities.

**Examples**:
- Day 60 of no activity: Email to all community members: "Your neighborhood tool sharing has been quiet. Consider sharing a tool to get things started!"
- Day 90 of no activity: Second email with tips for community growth
- No automatic community deletion - manual review only

**Edge Cases**:
- New communities get 90-day grace period before activity tracking starts
- Communities with <3 members get different messaging focused on inviting neighbors

---

**Community Guidelines Management**

**Decision**: Structured guideline categories with simple voting (3+ member approval required)

**Rationale**: Structured approach prevents inappropriate content while allowing meaningful local customization. Simple voting threshold encourages participation without creating bureaucracy.

**Examples**:
- Guideline categories: "Preferred loan duration", "Popular pickup locations", "Special community rules"
- Dropdown options: "1-3 days", "1 week", "2+ weeks" for loan duration
- Text field (500 chars max) for pickup locations: "Community center parking lot, Main Street café"
- Voting: Any member can propose changes, goes live when 3+ members approve

**Edge Cases**:
- Communities with <3 members: Guidelines changes are immediate (no voting required)
- Inappropriate content: Basic profanity filter + manual reporting system

---

## Q&A History

### Iteration 1 - December 19, 2024

**Q1: How do we define community boundaries precisely?**  
**A**: Fixed 1.5-mile radius from postal code centroid. This ensures consistent, practical community sizes regardless of postal code variation. Simple to implement and understand.

**Q2: When exactly are new communities created automatically?**  
**A**: Create new community only if no existing community center is within 3 miles. This prevents fragmentation while ensuring coverage, balancing user density with reasonable access.

**Q3: What defines "adjacent communities" for discovery expansion?**  
**A**: Communities whose center points are within 5 miles of user's home community center. Simple distance calculation that's predictable and performant.

**Q4: What are the exact validation rules for address during signup?**  
**A**: Require valid postal code + street name, no geocoding verification. Good balance of data quality and user experience for MVP.

**Q5: How should community stats be calculated and updated?**  
**A**: Daily batch job updates cached stats. Provides good performance with acceptably fresh data for community dashboards.

**Q6: What's the minimum viable threshold for community activity warnings?**  
**A**: Activity = tools shared or borrowing requests made. 60+ days of no activity triggers gentle email nudges. Focuses on actual tool sharing rather than just logins.

**Q7: How should we handle users who move to different neighborhoods?**  
**A**: Allow address updates once per year with full re-verification. Prevents gaming while handling legitimate moves.

**Q8: Should community guidelines have character limits and approval process?**  
**A**: Structured guideline categories with 3+ member approval voting. Safer for MVP with good community input while preventing abuse.

---

## Product Rationale

**Why fixed 1.5-mile radius instead of adaptive sizing?**  
User experience consistency is more important than perfect geographic matching for MVP. Users can predict their community size, and the distance is practical for most tool pickup scenarios. Can enhance with density-based logic in v2 if needed.

**Why 3-mile gap for new community creation?**  
Prevents community fragmentation (too many tiny communities) while ensuring no user is more than ~2.25 miles from their community center (3-mile gap minus 1.5-mile radius = 1.5-mile maximum distance, but typically less).

**Why daily stats updates instead of real-time?**  
Community stats are "nice to know" not "need to know" information. Daily updates provide excellent performance for page loads while keeping stats reasonably current. Real-time updates would add complexity for minimal user benefit.

**Why structured guidelines instead of free-form text?**  
Reduces moderation burden and ensures consistent information format. Free-form text risks inappropriate content, inconsistent formatting, and unclear information. Can add free-form sections in v2 if users request more flexibility.

**Why tool sharing activity (not logins) for community health?**  
Logins don't indicate actual platform value - users might log in, see no tools, and leave disappointed. Tool sharing activity indicates the community is actually functional for its intended purpose.