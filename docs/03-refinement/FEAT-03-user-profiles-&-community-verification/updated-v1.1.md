# User Profiles & Community Verification - Product Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: completed exchange definition, verification process, rating system behavior, profile requirements)

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

## Acceptance Criteria (UPDATED v1.1)

- User profiles show name, neighborhood, member since date, borrowing/lending history summary, and average rating
- Simple rating system (1-5 stars) for both borrowers and lenders after each completed exchange
- Basic community verification through address confirmation (postal code + street name verification)
- Users can write brief reviews about borrowing/lending experiences
- Completed exchanges are triggered when borrowers self-report tool return
- Required profile information: full name and complete address for verification
- Rating eligibility occurs once per loan between users (multiple loans = multiple ratings)
- All ratings display 48 hours after individual submission

---

## Detailed Specifications (UPDATED v1.1)

**Completed Exchange Definition**

**Decision**: A completed exchange occurs when the borrower marks the tool as "returned" (self-reported)

**Rationale**: Simplest trigger mechanism that enables immediate rating workflow without complex confirmation loops. Borrowers have direct incentive to mark returns promptly (security deposit release, ability to borrow again). Tool owners maintain ultimate control through the rating system - they can rate poorly if tools weren't actually returned properly.

**Examples**:
- Borrower clicks "Mark as Returned" button in their active loans → both parties receive rating prompts within 5 minutes
- If borrower never marks as returned, loan remains "active" indefinitely and no ratings are triggered

**Edge Cases**:
- Lost/broken tools: Borrower should still mark as "returned" to close the loop, then tool owner rates accordingly
- Disputed returns: Tool owner uses rating/review to document the issue

---

**Neighborhood Verification Process**

**Decision**: Instant verification with loose postal code validation - users select neighborhood from dropdown, system validates postal code is in the same city/region

**Rationale**: Prevents obviously fake addresses (someone in New York can't claim to be in Los Angeles neighborhood) without requiring detailed neighborhood boundary mapping. Keeps verification simple and scalable as new communities join. Community self-policing handles edge cases.

**Examples**:
- User selects "Downtown" neighborhood, enters postal code 90210 → if 90210 is valid for that city, verification passes immediately
- User selects "Riverside" neighborhood, enters postal code from different city → verification fails with message "Postal code doesn't match selected neighborhood area"

**Edge Cases**:
- Boundary postal codes: Accept them (err on side of inclusion rather than exclusion)
- New developments: May have postal codes not yet in our validation - these auto-verify and can be refined later

---

**Profile Setup Requirements**

**Decision**: Required fields are full real name and complete address (street number, street name, city, postal code). Optional fields are profile photo and bio.

**Rationale**: Tool lending involves valuable personal property between strangers - trust is paramount. Real names and verified addresses create accountability. Users unwilling to provide this information likely aren't serious about community participation. Higher friction is acceptable for better safety.

**Examples**:
- Cannot complete signup with just "Mike" as name - must provide "Mike Johnson"
- Cannot skip address fields - all required for verification process
- Can proceed without photo or bio, but profile shows completion percentage to encourage adding them

**Edge Cases**:
- Users concerned about privacy: Explain that full address is only used for verification - public profile shows neighborhood level only
- Users with unique names: Accept any reasonable name format, no restrictions on cultural naming conventions

---

**Multi-Loan Rating System**

**Decision**: Users can rate each other once per completed loan. Multiple loans between the same users generate multiple rating opportunities.

**Rationale**: People change over time - someone might improve their communication or tool care practices. Multiple ratings reflect ongoing relationship development. Also prevents single bad experience from permanently damaging someone's reputation if they improve.

**Examples**:
- Alice lends drill to Bob → both can rate after return
- Two months later, Alice lends saw to Bob → both can rate again after this return
- Bob's profile shows both ratings from Alice, contributing to overall average

**Edge Cases**:
- Rating retaliation across loans: Accept this risk - community members will notice patterns in reviews
- Artificial rating inflation through multiple small loans: Limit of one rating per loan prevents gaming

---

**Rating Display Timing**

**Decision**: Each rating appears exactly 48 hours after individual submission, regardless of whether the other party has rated.

**Rationale**: Consistent, predictable behavior that users can understand. Prevents immediate retaliation because there's always a 48-hour cooling-off period. Simple implementation without complex coordination between paired ratings.

**Examples**:
- Alice submits rating Monday 2pm → appears on Bob's profile Wednesday 2pm
- Bob submits his rating Tuesday 10am → appears on Alice's profile Thursday 10am
- Timing is independent - Alice's rating doesn't wait for Bob's

**Edge Cases**:
- Only one person rates: Their rating still appears after 48 hours (other person missed their opportunity)
- Both rate within minutes: Both will appear 48 hours after their respective submission times

---

**Content Guidelines**

**Decision**: Plain text only for bios (200 chars max) and reviews (500 chars max). Basic profanity filter applied, no formatting or links allowed.

**Rationale**: Keep it simple and safe. Avoid XSS risks from HTML/markdown. Focus on genuine content rather than formatting. Profanity filter maintains community standards without heavy moderation.

**Examples**:
- Bio: "Long-time resident who loves DIY projects. Happy to share tools with neighbors!"
- Review: "Borrowed hedge trimmer. Tool was clean and worked perfectly. Great communication and flexible pickup time. Would lend to again."

**Edge Cases**:
- Profanity filter false positives: Accept some over-filtering rather than risk offensive content
- Users trying to include contact info: Filter removes phone numbers and emails automatically

---

**Response Time Calculation**

**Decision**: Simple categories based on message response patterns: "Usually responds quickly" (<4 hours average), "Usually responds within a day" (<24 hours average), or no indicator if insufficient data.

**Rationale**: Easy to understand categories are more useful than precise timing. New users aren't penalized with poor indicators. Gives useful guidance without creating pressure for immediate responses.

**Examples**:
- User with 8 messages averaging 2-hour response time: shows "Usually responds quickly"
- User with 3 messages: shows no response time indicator (insufficient data)
- User with 15 messages averaging 18-hour response time: shows "Usually responds within a day"

**Edge Cases**:
- Weekend/holiday responses: Include all response times (don't filter out slow weekend responses)
- Very slow responders: Show no indicator rather than negative indicator

---

## Q&A History

### Iteration 1 - December 19, 2024

**Q1: What exactly constitutes a "completed exchange" that triggers rating eligibility?**  
**A**: Completed exchange occurs when borrower marks tool as "returned" (self-reported). This provides simple trigger mechanism while giving borrowers incentive to close loops promptly. Tool owners can address return issues through ratings/reviews.

**Q2: How do we handle the neighborhood verification mapping?**  
**A**: Instant verification with loose postal code validation. Users select neighborhood from dropdown, system validates postal code is in same city/region. Prevents obvious fake addresses without requiring detailed boundary mapping.

**Q3: What specific user information is required vs optional during profile setup?**  
**A**: Required: full real name and complete address for verification. Optional: profile photo and bio. Higher friction acceptable for better trust and accountability in tool lending community.

**Q4: What happens when users try to interact before verification is complete?**  
**A**: Instant verification during signup - postal code checked immediately. Users can interact right away if verification passes. Simple postal code validation prevents most abuse without delays.

**Q5: Can users rate/review the same person multiple times across different loans?**  
**A**: Yes, one rating per completed loan. Multiple loans between same users generate multiple rating opportunities. Reflects relationship development and prevents single bad experience from permanent reputation damage.

**Q6: How long should we wait before showing submitted ratings?**  
**A**: Each rating appears exactly 48 hours after individual submission, independent of whether other party rated. Provides consistent, predictable behavior with cooling-off period.

**Q7: What's the character limit and validation rules for user bios and reviews?**  
**A**: Plain text only - bios 200 chars max, reviews 500 chars max. Basic profanity filter, no formatting or links. Keeps system simple and secure while maintaining community standards.

**Q8: How should we calculate and display response time indicators?**  
**A**: Simple categories: "Usually responds quickly" (<4 hours), "Usually responds within a day" (<24 hours), or no indicator if insufficient data. Easy to understand, doesn't penalize new users.

---

## Product Rationale

**Why Borrower-Controlled Completion?**  
Borrowers have the strongest incentive to mark returns promptly (deposit release, future borrowing eligibility). This creates natural accountability without complex workflows. Tool owners retain power through rating system to address problems.

**Why Loose Address Verification?**  
Prevents obviously fake addresses while keeping system scalable as communities grow. Community self-policing handles edge cases better than rigid technical controls. Can tighten verification in v2 if abuse occurs.

**Why Multiple Ratings Between Same Users?**  
People improve over time, and ongoing relationships should be reflected in ratings. Single ratings don't capture relationship evolution. Multiple loans deserve multiple feedback opportunities.

**Why 48-Hour Rating Delay?**  
Prevents heat-of-the-moment retaliation ratings while being predictable for users. Cooling-off period encourages more thoughtful, fair ratings that benefit the community.

**Why Plain Text Only?**  
Security and simplicity trump formatting features. Content quality matters more than presentation. Reduces XSS risks and keeps focus on genuine community feedback rather than styled content.