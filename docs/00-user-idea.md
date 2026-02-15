# BookCircle - Product Requirements Document

## Vision

Reading is better together, but coordinating a book club shouldn't require endless group texts, spreadsheets, and forgotten conversations. **BookCircle** is a lightweight platform that helps reading groups stay organized, engaged, and excited about their next great read.

## Problem Statement

Book clubs today rely on fragmented tools:
- Group chats get cluttered and conversations are lost
- Book selection happens through informal polls in texts or emails
- There's no shared history of what the group has read
- New members can't easily catch up on context
- Discussion insights disappear after meetings end

## Target Users

- **Primary**: Adults (25-65) who participate in casual book clubs with friends, coworkers, or neighbors
- **Secondary**: Librarians or community organizers running multiple reading groups

## Core Features

### 1. Book Management
Enable groups to maintain a living library of their reading journey.

**User Stories:**
- As a group member, I want to add a book to our list so everyone knows what we're reading
- As a member, I want to see our reading history so I can remember past discussions
- As a member, I want to view book details (title, author, cover) so I can find it at the library or bookstore

**Acceptance Criteria:**
- Users can add books with title, author, and cover image (upload or URL)
- Books are categorized as "Current Book" or "Past Books"
- Each book has a dedicated detail page showing basic information
- Cover images display in list and detail views

### 2. Reading Groups
Allow users to create intimate communities around shared reading interests.

**User Stories:**
- As a book club organizer, I want to create a private group so my friends can join
- As an organizer, I want to invite people via email or shareable link
- As a member, I want to see who else is in my group
- As a reader, I want to join multiple book clubs for different interests

**Acceptance Criteria:**
- Users can create groups with a name and optional description
- Group creators can generate invite links
- Users can send email invitations to specific addresses
- Member list shows all participants with names and photos
- Users can belong to unlimited groups
- Each group has its own book list and discussions

### 3. Discussions
Transform fleeting conversations into a searchable, lasting dialogue.

**User Stories:**
- As a member, I want to post thoughts about the current book so I can share insights between meetings
- As a member, I want to reply to others' posts so we can have ongoing conversations
- As a member, I want to see all discussion threads in one place

**Acceptance Criteria:**
- Users can create discussion posts (text-based, 2000 char limit)
- Posts are associated with the current book
- Users can reply to posts (one level of threading)
- Discussions display in reverse chronological order
- Posts show author name, photo, and timestamp
- Simple formatting support (bold, italic, links)

### 4. Book Selection
Make choosing the next book collaborative and democratic.

**User Stories:**
- As a member, I want to suggest a book for our next read
- As a member, I want to vote on book suggestions so we read what the group wants
- As an organizer, I want to mark the winning book as our current selection

**Acceptance Criteria:**
- Users can submit book suggestions (title, author, optional description)
- All members can upvote or downvote suggestions
- Suggestions display with vote counts
- Group admins can promote a suggestion to "Current Book"
- Previous current book automatically moves to "Past Books"
- Users can only vote once per suggestion

### 5. User Authentication & Profiles
Establish identity and personalization.

**User Stories:**
- As a new user, I want to sign up with email and password
- As a returning user, I want to log in securely
- As a user, I want to set my name and photo so others recognize me
- As a user, I want to see all my book clubs in one dashboard

**Acceptance Criteria:**
- Email and password registration
- Secure login with session management
- Password reset via email
- User profile includes: name, email, profile photo, bio (optional)
- Dashboard shows all groups user belongs to
- Profile photos appear next to posts and in member lists

## Out of Scope (V1)

To maintain focus and ship quickly, the following are intentionally excluded:

- Reading progress tracking
- Meeting/event scheduling
- Star ratings or formal reviews
- Book recommendations or discovery features
- Mobile apps (web-responsive only)
- Direct messaging between members
- File attachments in discussions
- Advanced moderation tools
- Analytics or insights
- Third-party integrations (Goodreads, etc.)

## Success Metrics

- **Engagement**: Average posts per member per book (target: 3+)
- **Retention**: Groups with activity in 3+ consecutive months (target: 60%)
- **Growth**: Members inviting others to join (target: 1.5 invites per user)
- **Completion**: Groups that finish books and select new ones (target: 70%)

## Technical Considerations

- Mobile-responsive web application
- Support for groups up to 50 members (can expand later)
- Image uploads capped at 5MB
- Standard web hosting requirements

## Timeline & Prioritization

**Phase 1 (MVP)**: Groups, Books, Basic Discussions - 6-8 weeks
**Phase 2**: Voting & Selection - 2-3 weeks  
**Phase 3**: Polish & Refinement - 2 weeks

---

*Document Version: 1.0*  
*Last Updated: February 14, 2026*  
