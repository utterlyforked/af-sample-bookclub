# User Profiles & Community Verification - Feature Requirements

**Version**: 1.0  
**Date**: December 19, 2024  
**Status**: Initial - Awaiting Tech Lead Review

---

## Feature Overview

The User Profiles & Community Verification feature creates trust and accountability within the toolsharing community by providing transparent user profiles, a rating system, and neighborhood verification. This feature is critical for building confidence between strangers who are lending valuable equipment to each other.

Users can view detailed profiles showing borrowing/lending history, community ratings, and verified neighborhood status before deciding whether to lend or borrow. The verification system ensures users are legitimate local residents, while the rating system creates accountability and helps identify reliable community members. This feature transforms anonymous interactions into trusted community exchanges.

---

## User Stories

- As a tool owner, I want to see borrower profiles and ratings so that I can make informed decisions about lending my equipment
- As a borrower, I want to see lender ratings and responsiveness so that I can choose reliable people to borrow from  
- As any user, I want to verify my neighborhood residency so that the community knows I'm a legitimate local resident

---

## Acceptance Criteria

- User profiles show name, neighborhood, member since date, borrowing/lending history summary, and average rating
- Simple rating system (1-5 stars) for both borrowers and lenders after each completed exchange
- Basic community verification through address confirmation (postal code + street name verification)
- Users can write brief reviews about borrowing/lending experiences

---

## Functional Requirements

### Profile Creation & Management

**What**: Complete user profile system with personal information, community standing, and activity history

**Why**: Users need to see who they're dealing with to build trust for lending expensive tools

**Behavior**:
- New users must complete profile setup during onboarding (name, neighborhood, profile photo optional)
- Profiles display: full name, neighborhood (e.g., "Downtown", "Riverside"), member since date, profile photo, bio (optional, 200 chars max)
- Activity summary shows: total tools lent, total tools borrowed, active loans count, completed exchanges count
- Users can edit their own profile information but cannot change their verified neighborhood
- Profile completeness indicator encourages users to add photo and bio

### Community Verification System

**What**: Address verification to confirm users are legitimate neighborhood residents

**Why**: Prevents fake accounts and ensures tools stay within genuine local communities

**Behavior**:
- During signup, users enter full address (street number, street name, postal/zip code)
- System verifies postal code matches claimed neighborhood community
- Users receive "Verified Resident" badge on profile after confirmation
- Verification status visible to all community members (verified/unverified)
- Re-verification required if user changes neighborhood
- Unverified users can browse but cannot send borrowing requests until verified

### Rating & Review System

**What**: Bidirectional rating system where both borrowers and lenders rate each other after completed exchanges

**Why**: Creates accountability and helps users identify reliable community members

**Behavior**:
- After tool return confirmation, both parties receive rating prompts (email + in-app notification)
- 5-star rating scale with optional written review (500 character limit)
- Ratings appear within 48 hours of submission (prevents immediate retaliation)
- Profile shows average rating with total number of ratings (e.g., "4.8 stars (23 ratings)")
- Recent reviews display on profile (last 5 reviews shown, older ones in "See More")
- Users cannot rate the same person multiple times for the same loan
- No editing or deleting ratings once submitted (prevents manipulation)

### Trust Indicators & Community Standing

**What**: Visual indicators and metrics that help users assess trustworthiness

**Why**: Quick visual cues help users make lending decisions without reading full profiles

**Behavior**:
- Profile badges: "Verified Resident", "5-Star Member" (4.8+ rating), "Active Lender" (5+ tools listed), "Reliable Borrower" (10+ completed borrows)
- Response time indicator: "Usually responds within 2 hours" based on historical message response times
- Community tenure: "Member since [month/year]" prominently displayed
- Loan completion rate: percentage of started loans that ended with confirmed returns
- Recent activity indicator: "Active this week" vs "Last seen 2 weeks ago"

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:
- User: Core user information, verification status, calculated ratings
- UserProfile: Extended profile information, bio, preferences
- Rating: Individual rating records between users for specific loans
- Review: Written review content associated with ratings
- VerificationRequest: Tracking address verification process

**Key Relationships**:
- User has one UserProfile (1:1)
- User can have many Ratings as both rater and ratee (1:many bidirectional)
- Rating optionally has one Review (1:1)
- User has many VerificationRequests for audit trail (1:many)

[Note: This is preliminary - Tech Lead will ask questions to clarify]

---

## User Experience Flow

1. **Profile Setup**: New user completes profile during onboarding (name, address for verification, optional photo/bio)
2. **Verification Process**: System validates postal code, user receives "Verified Resident" status
3. **Profile Viewing**: When browsing tools, user clicks on tool owner's name to view full profile
4. **Trust Assessment**: User sees ratings, badges, response time, and recent reviews to make lending decision
5. **Post-Exchange Rating**: After tool return, both parties receive rating prompts and submit ratings/reviews
6. **Profile Updates**: Ratings appear on profiles, badges update based on new activity milestones

---

## Edge Cases & Constraints

- **New users with no ratings**: Display "New Member" badge and encourage first exchanges with highly-rated users
- **Very low ratings (<3.0)**: Profile shows warning indicator, but users can still participate (community self-regulates)
- **Fake/spam reviews**: Basic profanity filter, but no advanced moderation in v1 (rely on community reporting)
- **Address changes**: Users moving must re-verify with new address, previous ratings carry over
- **Privacy concerns**: Only show neighborhood level location, never full addresses
- **Rating disputes**: No dispute resolution system in v1 (accept that some ratings may be unfair)

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- Advanced identity verification (driver's license, background checks)
- Dispute resolution or rating appeal process  
- Social features (following, friending, messaging beyond loan coordination)
- Integration with external identity providers
- Business/organization profiles (individuals only)
- Detailed activity tracking beyond basic loan statistics

---

## Dependencies

**Depends On**: Basic user authentication system, neighborhood/community assignment system

**Enables**: Tool Listing & Discovery (profile viewing), Borrowing Request System (trust-based decision making), Loan Tracking (rating prompts after returns)

---

## Open Questions for Tech Lead

- Should we implement soft delete for ratings/reviews or hard delete if absolutely necessary?
- What's the best approach for calculating and caching average ratings (real-time vs batch updates)?
- How should we handle profile photo upload, storage, and resizing?
- Should address verification be automatic via postal service APIs or manual admin approval?