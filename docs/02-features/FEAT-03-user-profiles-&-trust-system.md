# User Profiles & Trust System - Feature Requirements

**Version**: 1.0  
**Date**: 2025-01-10  
**Status**: Initial - Awaiting Tech Lead Review

---

## Feature Overview

The User Profiles & Trust System is the foundation for building confidence within the ToolShare community. It enables users to establish their identity, showcase their sharing history, and assess the trustworthiness of others before entering into lending relationships.

This feature addresses the core challenge of peer-to-peer tool sharing: trusting strangers with valuable equipment. By providing transparent profile information, verified credentials, and community ratings, we create an environment where tool owners feel confident lending and borrowers can prove their reliability.

The trust system is bidirectional - both borrowers and lenders can rate each other after transactions complete, creating accountability and recognizing good community members. Over time, users build reputation through successful transactions, making it easier to borrow from and lend to more community members.

This feature integrates deeply with borrowing requests (FEAT-02) - profiles are viewed during request review, and ratings are collected after borrow tracking (FEAT-04) completes a transaction cycle.

---

## User Stories

- As a new user, I want to create a profile with my neighborhood and introduction so that others know who I am
- As a tool owner, I want to see a borrower's history and ratings so that I can assess trustworthiness before approving a request
- As a borrower, I want to rate my experience after returning a tool so that good owners are recognized and future borrowers can make informed decisions
- As any user, I want verification badges to identify trusted community members so that I can lend and borrow with confidence
- As a tool owner reviewing a request, I want to quickly see key trust indicators (rating, completed borrows, member duration) so I can make fast approval decisions
- As a user with a good track record, I want my profile to showcase my reliability so that I can access more tools from the community

---

## Acceptance Criteria

- Users can create and edit profiles containing: full name, neighborhood, profile photo, and bio (max 300 characters)
- Profile displays key statistics: number of tools owned, total successful borrows as lender, current items borrowed, and average rating (5-star scale)
- Both borrowers and lenders can submit 5-star ratings with optional written reviews (max 500 characters) after transaction completion
- Ratings are mutual - both parties rate each other independently after a borrow is marked complete
- Profile shows verification badges: email verified (required at signup), phone verified (optional), address verified (optional)
- Full street address is never displayed publicly - only neighborhood name and city are shown
- Approved borrowers receive full address only after request approval for pickup coordination
- Profile displays transaction history showing completed borrows with dates, ratings received, and reviews
- Users cannot rate the same transaction twice or edit ratings after submission
- Average rating calculation excludes transactions without ratings and displays as "New User" until at least 3 rated transactions complete

---

## Functional Requirements

### Profile Creation & Editing

**What**: Users establish their identity through a public profile viewable by community members.

**Why**: Transparency builds trust. Knowing who you're dealing with (name, neighborhood, member duration) reduces anxiety about lending valuable tools to strangers.

**Behavior**:
- During signup, users must provide: full name (first + last), email (verified), physical address (geocoded for location), and neighborhood designation
- Neighborhood defaults to postal code area but users can customize (e.g., "Green Valley", "Downtown Historic District")
- Profile photo is optional at signup but encouraged - default avatar shows user's initials
- Bio field accepts plain text only (no rich formatting), max 300 characters
- Profile edit allows changing: profile photo, bio, neighborhood name, password, and contact preferences
- Email change requires verification of new email before switch completes
- Address changes require re-geocoding and may trigger address verification badge removal
- Name changes are allowed but logged (prevents abuse/impersonation)

---

### Profile Viewing & Privacy

**What**: Other users can view profiles to assess trustworthiness, but sensitive information remains protected.

**Why**: Balance transparency (needed for trust) with privacy (needed for safety). Users should feel comfortable sharing enough to build confidence without exposing themselves to harassment or security risks.

**Behavior**:
- Any logged-in user can view any other user's profile via direct link or from tool listings
- Public profile displays: full name, neighborhood + city, profile photo, member since date, bio, statistics, verification badges, ratings summary, and recent reviews
- Address privacy: full street address NEVER shown on public profile
- After request approval, requester sees full address in request details and confirmation email only
- Email and phone never displayed publicly - communication happens through in-app messaging
- Profile photos are moderated - inappropriate images can be reported and removed
- Users cannot hide their profiles or make them private - participation requires transparency
- Deleted/deactivated accounts show as "[User Unavailable]" in historical transactions

---

### Trust Statistics

**What**: Quantifiable metrics that indicate a user's experience and reliability within the community.

**Why**: Numbers provide quick assessment. "12 successful borrows, 4.8-star rating, member for 8 months" tells a story of trustworthiness at a glance.

**Behavior**:
- **Tools Owned**: Count of active tool listings (not including "Temporarily Unavailable" or deleted tools)
- **Tools Shared**: Total count of completed successful borrows where this user was the lender
- **Current Borrows**: Count of tools this user currently has borrowed (due date not yet passed)
- **Average Rating**: Mean of all ratings received across all transactions, displayed to 1 decimal place
- **Member Since**: Account creation date displayed as "Member since [Month Year]"
- Statistics update in real-time as transactions complete and ratings are submitted
- New users (< 3 ratings) display "New User" instead of numeric rating
- Users with overdue items show warning indicator on profile: "⚠️ Has overdue items" (visible to others)

---

### Verification System

**What**: Optional badges that confirm identity elements, increasing trust for high-value tool sharing.

**Why**: Verification reduces risk of fraud and increases confidence in lending expensive equipment. Users can gauge risk based on verification level.

**Behavior**:
- **Email Verified** (required): Automatically achieved during signup via confirmation link; badge always present
- **Phone Verified** (optional): User enters phone number, receives SMS code, enters code to confirm; badge added to profile
- **Address Verified** (optional): User requests verification → admin manually reviews (checks utility bill or ID) → approves/denies → badge added if approved
- Verification badges display as colored icons on profile: ✓ Email (green), ✓ Phone (blue), ✓ Address (gold)
- Users can remove phone verification (removes badge) but cannot remove email verification
- Failed verification attempts are rate-limited (3 attempts per method per 24 hours) to prevent spam
- Address verification is optional for v1 due to manual admin work - consider automated options in v2

---

### Rating & Review System

**What**: After a borrow completes, both parties rate each other on a 5-star scale with optional written feedback.

**Why**: Public ratings create accountability and incentivize good behavior. Borrowers treat tools carefully to maintain good ratings; lenders provide quality tools and clear communication to earn positive reviews.

**Behavior**:
- Rating opportunity triggers when borrow status changes to "Returned - Confirmed" by the lender
- Both parties receive notification: "Rate your experience with [Name]"
- Rating submission includes:
  - Star rating: 1-5 stars (required)
  - Written review: 0-500 characters (optional)
  - Review is about the transaction, not just the person (e.g., "Tool was exactly as described, pickup was easy")
- Ratings are mutual and independent - borrower rates lender, lender rates borrower
- Neither party sees the other's rating until both submit OR 7 days pass (whichever comes first)
- After 7 days, window closes - unsubmitted ratings are forfeited and transaction shows as "Not Rated"
- Users cannot edit ratings after submission - finality creates authentic feedback
- Users can report inappropriate reviews (profanity, personal attacks) for admin moderation
- Star ratings always visible; written reviews can be flagged as hidden by admin if inappropriate

---

### Profile Display in Borrowing Flow

**What**: Integration touchpoints where profile information appears during the borrowing request and approval process.

**Why**: Trust assessment happens at decision points. Lenders need profile info when reviewing requests; borrowers see lender profiles when browsing tools.

**Behavior**:
- **Tool Listing Pages**: Show lender's name, neighborhood, profile photo thumbnail, and average rating
- **Request Review Screen**: Full profile preview embedded in request details: stats, verification badges, rating summary, recent reviews
- **Request Approval Notification**: Includes profile link for both parties to review each other before pickup
- **Transaction History**: Each historical borrow links to the other party's profile
- One-click access to profile from anywhere a username appears in the interface

---

### Transaction History

**What**: Chronological record of completed borrows displayed on user profiles, showing both lending and borrowing activity.

**Why**: History demonstrates experience and reveals patterns. A user with 30 successful borrows and 4.9 stars is clearly reliable. A new user with 2 borrows deserves a chance but might warrant caution with expensive tools.

**Behavior**:
- Profile shows two tabs: "As Lender" and "As Borrower"
- Each transaction entry displays:
  - Tool name (linked to tool listing if still active)
  - Other party's name (linked to their profile)
  - Borrow dates: "May 15-18, 2025"
  - Rating received: Star display + written review if provided
  - Rating given: Star display + written review if provided
- Transactions sorted by completion date (most recent first)
- Unrated transactions show as "Not Rated" but still appear in history
- Transactions with reported issues show warning icon + issue description if lender marked return as having problems
- History paginated at 20 transactions per page
- Filter options: "All", "Last 30 Days", "Last 6 Months", "Last Year"

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:

- **User**: Core identity entity containing name, email, password_hash, address (geocoded), neighborhood, bio, profile_photo_url, created_at, phone (optional), phone_verified, address_verified, account_status
- **Rating**: Represents one user's rating of another after a transaction; links to Transaction, includes: rater_id, rated_user_id, transaction_id, stars (1-5), review_text, created_at, status (active/flagged/hidden)
- **VerificationEvent**: Audit log of verification attempts/successes: user_id, verification_type (email/phone/address), status, verified_at, verified_by (for manual address verification)

**Key Relationships**:

- User has_many Ratings (as both rater and rated_user)
- Transaction (from FEAT-04) belongs_to borrower (User) and lender (User)
- Rating belongs_to Transaction (each transaction can have up to 2 ratings - one from each party)
- User has_many VerificationEvents
- User profile statistics are computed from related entities: tool count from Tool table, borrows from Transaction table, ratings from Rating table

**Notes**: 
- Average rating should be computed property or cached value updated when new ratings added
- Consider soft-delete for Users to preserve transaction history integrity
- Profile photo storage needs URL-based reference to blob storage

---

## User Experience Flow

### New User Profile Creation (Signup)

1. User enters email and password on signup form
2. User enters full name, physical address, optional neighborhood name
3. User optionally uploads profile photo
4. User optionally enters bio (max 300 chars)
5. System geocodes address to lat/long for proximity calculations
6. System sends email verification link
7. User clicks link in email, account becomes active
8. User redirected to profile page showing "New User" status, empty statistics, and prompt to list first tool or browse community

### Tool Owner Reviewing a Request

1. Owner receives notification: "John Smith wants to borrow your Circular Saw"
2. Owner clicks notification, lands on request review page
3. Request shows embedded profile preview: John's photo, neighborhood, "Member since March 2025", 8 completed borrows, 4.7-star rating
4. Owner clicks "View Full Profile"
5. Profile page shows John's statistics, verification badges (Email ✓, Phone ✓), and recent reviews from other lenders
6. Owner reads review: "Returned drill in perfect condition, communicated clearly about pickup - great borrower!"
7. Owner feels confident, returns to request, clicks "Approve"

### Submitting a Rating After Borrow

1. Borrower marks tool as returned in "My Borrows" dashboard
2. Lender receives notification, confirms return (or reports issue)
3. Both parties receive notification: "Rate your experience with [Name]"
4. User clicks notification, lands on rating page showing:
   - Other party's name and profile photo
   - Tool name and borrow dates
   - Star selector (1-5)
   - Optional text box: "Share your experience (optional)"
5. User selects 5 stars, types: "Great tool, worked perfectly for my deck project. Quick and friendly pickup. Highly recommend!"
6. User clicks "Submit Rating"
7. Confirmation: "Thanks for your feedback! Your rating will be visible after both parties rate or in 7 days."
8. Rating appears on rated user's profile after conditions met

---

## Edge Cases & Constraints

- **Unrated transactions**: If one or both parties don't rate within 7 days, transaction appears in history as "Not Rated" - does not affect average rating calculation
- **First-time users**: Profiles show "New User" instead of star rating until 3+ ratings received - prevents single bad rating from being disproportionately harmful
- **Profile photo moderation**: Users can report inappropriate photos; admin review queue handles reports; inappropriate photos replaced with default avatar
- **Rating disputes**: Users cannot challenge or remove ratings (no back-and-forth arguments); can report reviews for admin review if they contain profanity/harassment
- **Deleted accounts**: When user deletes account, profile shows "[User Unavailable]" in transaction history; ratings and reviews remain visible (anonymized) to preserve trust data for other party
- **Self-rating prevention**: System prevents users from rating themselves (enforced at API level)
- **Duplicate rating prevention**: User cannot submit multiple ratings for same transaction (enforced by unique constraint on [transaction_id, rater_id])
- **Rating window closure**: After 7 days, rating submission form disappears; transaction permanently marked as unrated
- **Overdue items impact**: Users with overdue borrows show warning on profile but rating system is separate - overdue status doesn't automatically lower ratings
- **Address verification bottleneck**: Manual admin review required for address verification; expect delays; communicate 3-5 business day turnaround in UI
- **Privacy vs. transparency tension**: Balance is: show enough info to build trust (name, neighborhood, stats) but protect personal safety (no full address, email, or phone publicly)

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- **Social features**: No friend lists, direct messaging (v1 has basic in-app messaging for active requests only), activity feeds, or social networking elements
- **Badges/gamification**: No achievement badges, leaderboards, or gamified reputation system beyond star ratings
- **Detailed analytics**: No personal dashboards showing "your most borrowed tool" or community comparison stats
- **Profile customization**: No themes, custom layouts, or rich media embeds in bio
- **Blocking/muting users**: No ability to hide specific users or block them from seeing your tools (v2 consideration for safety)
- **Background checks**: No integration with identity verification services, criminal background checks, or credit checks
- **Endorsements/recommendations**: No LinkedIn-style skill endorsements or written recommendations separate from transaction ratings
- **Profile visibility controls**: Profiles are always public to logged-in users - no private/friends-only options
- **Import from social media**: No "Sign in with Facebook" or profile import from other platforms
- **Multi-language profiles**: English only; no language preference or translation

---

## Open Questions for Tech Lead

- **Profile photo storage**: Should we use blob storage (Azure/S3) with CDN for profile photos, or is there a preferred service in our stack? Size limits and image optimization strategy?
- **Rating calculation performance**: Should average rating be computed on-the-fly or cached in User table and updated via trigger/background job when new ratings arrive?
- **Address geocoding service**: What geocoding service should we use for address → lat/long conversion? Google Maps API, Mapbox, or something else in our stack?
- **Email verification flow**: Should we use a third-party service (SendGrid, Mailgun) or built-in email capabilities? What's the standard for our stack?
- **Phone verification**: SMS verification service - should we use Twilio, AWS SNS, or is there an existing service we integrate with?
- **Soft delete strategy**: When users delete accounts, do we soft-delete (set deleted_at flag) or hard-delete? Need to preserve referential integrity for transaction history.
- **Admin moderation tools**: Is there existing admin panel infrastructure for reviewing flagged photos/reviews, or do we build new admin UI for this feature?

---

## Dependencies

**Depends On**: 
- FEAT-01 (Tool Listings) - profiles must link to tools owned; tool listings display lender profiles
- FEAT-02 (Borrowing Requests) - request review screen embeds profile information for trust assessment

**Enables**: 
- FEAT-04 (Borrow Tracking & Returns) - completion of borrows triggers rating opportunities
- FEAT-05 (Community & Discovery) - profiles power the social/community aspects like following users and neighborhood discovery

**Integration Points**:
- Authentication system (signup/login) creates User entity that this feature extends
- Transaction lifecycle (FEAT-04) triggers rating prompts at return confirmation
- Tool listing pages (FEAT-01) display profile preview for lenders