# Loan Tracking & Management - Feature Requirements

**Version**: 1.0  
**Date**: December 19, 2024  
**Status**: Initial - Awaiting Tech Lead Review

---

## Feature Overview

The Loan Tracking & Management feature provides a comprehensive system for managing active tool loans throughout their lifecycle. It serves as the operational backbone that keeps borrowers and lenders informed about loan status, due dates, and return logistics.

This feature transforms what could be chaotic informal lending into an organized, reliable system. It ensures tool owners always know where their equipment is and when it's due back, while helping borrowers be responsible community members through proactive reminders and easy return processes. The feature builds trust by creating accountability and reducing the anxiety tool owners might feel about lending valuable equipment.

---

## User Stories

- As a tool owner, I want to track which tools are currently lent out and when they're due back so that I can manage my inventory
- As a borrower, I want reminders about return dates so that I can be a reliable community member  
- As both parties, I want to confirm when tools are returned so that loans are properly closed out
- As a tool owner, I want to know how to contact my borrower if my tool becomes overdue so that I can follow up appropriately
- As a borrower, I want to request an extension if I need the tool longer so that I can communicate changes rather than just being late

---

## Acceptance Criteria

- Dashboard showing active loans with due dates, borrower/lender info, and contact options
- Automated email/notification reminders 1 day before due date and on due date
- Simple return confirmation process (both parties confirm return)
- Overdue loan notifications and status tracking
- Users can see complete loan history for tools they've borrowed or lent
- Extension requests can be sent and approved/declined by tool owners
- Loan status is clearly indicated on tool listings (shows "Currently on loan, returns [date]")

---

## Functional Requirements

### Dashboard & Active Loan Display

**What**: A central dashboard showing all active loans for a user, whether they're borrowing or lending

**Why**: Users need a single place to see all their loan obligations and manage their lending/borrowing activity

**Behavior**:
- Shows separate sections for "Tools I'm Borrowing" and "Tools I've Lent Out"
- Each loan displays: tool name/photo, other party's name, pickup date, due date, status
- Color coding for status: green (on time), yellow (due soon), red (overdue)
- Direct message/contact options for each active loan
- Quick action buttons: "Request Extension", "Confirm Return", "Report Issue"

### Notification & Reminder System

**What**: Automated notifications sent via email and in-app to keep parties informed about loan status

**Why**: Prevents overdue returns and maintains community trust by keeping everyone informed

**Behavior**:
- 24 hours before due date: reminder to borrower with return instructions
- On due date: reminder to borrower if not yet returned
- 1 day overdue: notification to both parties with contact encouragement
- 3 days overdue: escalated notification suggesting community mediation
- All reminders include loan details, contact info, and direct links to messaging

### Return Confirmation Process

**What**: A two-step process where both parties confirm the tool has been successfully returned

**Why**: Prevents disputes about whether tools were returned and formally closes out loans

**Behavior**:
- Either party can initiate return process from loan dashboard
- First person marks "Tool Returned" with optional condition notes
- Second person gets notification to confirm return within 48 hours
- If confirmed, loan status changes to "Completed" 
- If not confirmed within 48 hours, both parties get reminder
- Completed loans move to loan history with final condition notes

### Extension Request Workflow

**What**: Formal process for borrowers to request additional time when they need tools longer than originally planned

**Why**: Enables good communication and prevents borrowers from simply being late without notice

**Behavior**:
- Borrowers can request extension anytime before due date
- Extension request includes new proposed return date and reason
- Tool owner gets notification with approve/decline options
- If approved, due date updates across all systems
- If declined, original due date remains with explanation from owner
- Extension requests and responses are logged in loan history

### Loan History & Records

**What**: Complete historical record of all loans for tools and users

**Why**: Builds reputation system, helps resolve disputes, shows community participation

**Behavior**:
- Tool listings show loan history: "Borrowed 12 times, average loan 4 days"
- User profiles show borrowing/lending statistics and rating breakdown
- Detailed loan records include: dates, condition notes, ratings, extensions
- Export capability for personal records ("My 2024 Tool Sharing Activity")

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:
- **Loan**: Core entity tracking the lending transaction
- **LoanStatusHistory**: Audit trail of loan status changes
- **ExtensionRequest**: Requests for additional time
- **ReturnConfirmation**: Two-party confirmation of returns
- **LoanNotification**: Track what notifications were sent when

**Key Relationships**:
- Loan belongs to Tool (from Tool Listing feature)
- Loan has Borrower and Lender (User entities)
- Loan has many LoanStatusHistory entries
- Loan may have ExtensionRequests
- Loan has one ReturnConfirmation when completed

[Note: This is preliminary - Tech Lead will ask questions to clarify]

---

## User Experience Flow

### Primary Flow - Successful Loan Lifecycle
1. User accepts borrowing request → Loan status becomes "Active"
2. System schedules reminder notifications based on due date
3. 24 hours before due: Borrower gets "Return Soon" reminder email
4. On due date: If not returned, borrower gets "Due Today" reminder
5. Borrower initiates return → marks "Tool Returned" on dashboard
6. Tool owner gets notification to confirm return
7. Owner confirms return → Loan status becomes "Completed"
8. Both parties prompted to leave ratings/reviews

### Extension Flow
1. Borrower realizes they need more time → clicks "Request Extension"
2. Borrower specifies new date and reason
3. Tool owner gets notification with approve/decline options
4. If approved: due date updates, new reminders scheduled
5. If declined: borrower gets notification, original due date stands

### Overdue Flow
1. Due date passes without return confirmation → status becomes "Overdue"
2. Both parties get "Tool is Overdue" notification with contact encouragement
3. After 3 days: escalated notification suggests community mediation
4. Tool owner can mark tool as "Lost/Unreturned" if necessary

---

## Edge Cases & Constraints

- **Double confirmation conflicts**: If both parties try to initiate return simultaneously, first submission wins, second gets "Already in progress" message
- **Extension during return process**: Extensions cannot be requested once return confirmation has started
- **Overdue extension requests**: Extension requests on overdue loans require owner approval before due date can be extended
- **Loan limits**: Users can have maximum 5 active borrowed loans and 10 active lent loans to prevent abuse
- **Notification failures**: If email notifications fail, in-app notifications serve as backup
- **Time zone handling**: All dates/times stored in UTC, displayed in user's local time zone

---

## Out of Scope for This Feature

This feature explicitly does NOT include:

- Damage assessment or insurance handling (community trust-based resolution)
- Payment processing for late fees or damages
- Legal dispute resolution beyond basic contact facilitation
- Automated penalty systems for late returns
- Integration with external calendar systems
- SMS notifications (email and in-app only for MVP)
- Bulk loan management for power users (individual loan focus)

---

## Open Questions for Tech Lead

- Should loan due times be specific (e.g., "return by 6 PM") or just dates?
- How should we handle time zones for users in different zones within the same community?
- What's the appropriate database indexing strategy for loan queries (active loans, overdue loans, user history)?

---

## Dependencies

**Depends On**: 
- User Profiles & Community Verification (need user authentication and profiles)
- Borrowing Request & Communication System (loans are created from approved requests)
- Tool Listing & Discovery (loans are tied to specific tool listings)

**Enables**: 
- Enhanced trust scoring and reputation system
- Community moderation features (identifying problem users)
- Analytics and community health metrics