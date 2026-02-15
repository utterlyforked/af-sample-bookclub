# Lesson Planning & Management - Feature Requirements (v1.1)

**Version History**:
- v1.0 - Initial specification
- v1.1 - Iteration 1 clarifications (added: lesson structure definitions, file handling, scheduling behavior, access controls)

---

## Feature Overview

The Lesson Planning & Management feature enables language tutors to create structured lesson plans, organize teaching materials, and manage their lesson schedule efficiently. This feature serves as the organizational backbone for tutors, allowing them to prepare comprehensive lessons with multiple components (vocabulary, grammar, activities, materials) while maintaining a clear schedule of upcoming and past lessons with specific students.

This feature directly supports the tutor's workflow from preparation through lesson delivery, ensuring they can focus on teaching rather than administrative tasks.

---

## User Stories

- As a language tutor, I want to create detailed lesson plans so that I can organize my teaching content and ensure comprehensive coverage of topics
- As a tutor, I want to attach files and materials to lessons so that all my teaching resources are organized in one place
- As a tutor, I want to schedule lessons with specific students so that I can manage my teaching calendar effectively
- As a tutor, I want to track lesson completion and notes so that I can monitor student progress over time
- As a tutor, I want to duplicate successful lesson plans so that I can reuse effective content with different students
- As a tutor, I want to view my upcoming lessons so that I can prepare in advance

---

## Acceptance Criteria (UPDATED v1.1)

- Tutors can create lesson plans with title, description, objectives, and estimated duration
- Lesson plans support multiple content sections: vocabulary, grammar points, activities, and homework assignments
- Tutors can attach multiple files (PDFs, images, documents) to each lesson plan with a 10MB limit per file
- Tutors can schedule lessons by assigning lesson plans to specific students with date/time
- Scheduled lessons can be marked as completed with session notes and actual duration
- Tutors can duplicate existing lesson plans to create new variations
- Tutors can view calendar of scheduled lessons filtered by date range or student
- Only lesson creators can edit their lesson plans and schedules
- File uploads are scanned and must be common educational formats (PDF, DOC, DOCX, JPG, PNG)
- Lesson plans can be saved as drafts and published when ready

---

## Detailed Specifications (UPDATED v1.1)

**Lesson Plan Structure**

**Decision**: Lesson plans have a fixed structure with four content sections: Vocabulary, Grammar, Activities, and Homework.

**Rationale**: Language lessons typically follow this pedagogical structure. Fixed sections provide consistency and ensure tutors address all key learning components. Simpler than custom sections for MVP.

**Examples**:
- Vocabulary section: "New words: 'restaurant', 'menu', 'waiter' with definitions and example sentences"
- Grammar section: "Present perfect tense - usage rules and conjugation patterns"
- Activities section: "Role-play ordering food at a restaurant (15 minutes)"
- Homework section: "Complete exercises 1-5 on page 23, write 5 sentences using new vocabulary"

**Edge Cases**:
- Sections can be left empty if not needed for that lesson
- Each section supports rich text formatting and bullet points

---

**File Attachment Handling**

**Decision**: Files are uploaded directly to lessons with 10MB per file limit, 50MB total per lesson. Supported formats: PDF, DOC, DOCX, JPG, PNG, MP3, MP4.

**Rationale**: Tutors need to attach worksheets, audio files, images, and reference materials. 10MB handles most educational content while preventing abuse. Audio/video support common for language learning.

**Examples**:
- PDF worksheet attached to Activities section
- Audio pronunciation file attached to Vocabulary section
- Image flashcards attached to lesson plan
- Video dialogue attached to Activities section

**Edge Cases**:
- Files over 10MB show error: "File too large. Maximum 10MB per file."
- Unsupported formats show error: "File type not supported. Use PDF, DOC, DOCX, JPG, PNG, MP3, or MP4."
- If lesson reaches 50MB total, show: "Lesson storage full. Remove files to add more."
- Files are virus scanned on upload; infected files are rejected

---

**Lesson Scheduling Behavior**

**Decision**: Lessons are scheduled by selecting a lesson plan, student, date, and time. One lesson plan can be scheduled multiple times with different students or dates.

**Rationale**: Tutors often reuse good lesson plans across students and repeat lessons. Flexible scheduling supports various teaching patterns.

**Examples**:
- "Spanish Beginner Lesson 1" scheduled with Maria on Monday 2pm and with Juan on Tuesday 3pm
- "Present Tense Practice" rescheduled from Tuesday to Wednesday (updates existing entry)
- Same lesson plan scheduled weekly with same student for ongoing curriculum

**Edge Cases**:
- Cannot schedule lessons in the past (error: "Cannot schedule lessons for past dates")
- Double-booking same time slot shows warning: "You have another lesson at this time with [Student]. Continue anyway?"
- Scheduling requires published lesson plan (drafts cannot be scheduled)

---

**Lesson Status and Completion**

**Decision**: Scheduled lessons have three states: Upcoming, Completed, Cancelled. Only tutors can change status and add completion notes.

**Rationale**: Simple status tracking without complex workflow. Tutors control their own schedule and student progress tracking.

**Examples**:
- Upcoming lesson shows "Scheduled for Dec 15, 2pm with Maria"
- Completed lesson shows "Completed Dec 13, 2pm with Juan - Duration: 45 min, Notes: Student struggled with pronunciation"
- Cancelled lesson shows "Cancelled Dec 12 - Notes: Student sick"

**Edge Cases**:
- Lessons automatically stay "Upcoming" until manually changed
- Completion requires actual duration (cannot be blank)
- Cancellation notes are optional
- Cannot change Completed lessons back to Upcoming

---

**Access Control and Privacy**

**Decision**: Tutors can only see and edit their own lesson plans and schedules. Students cannot access lesson plans directly.

**Rationale**: Lesson plans are tutor intellectual property and preparation materials. Students don't need backend access to lesson content - tutors share materials during lessons as needed.

**Examples**:
- Tutor A cannot see Tutor B's lesson plans in any view
- Student cannot browse or search lesson plans
- Only the lesson creator can edit, duplicate, or delete lesson plans

**Edge Cases**:
- If tutor account is deactivated, their lesson plans remain but are inaccessible
- Shared materials during lessons (future feature) would be separate from lesson plan access

---

## Q&A History

### Iteration 1 - December 15, 2024

**Q1: What specific sections/fields should a lesson plan have beyond title and description?**  
**A**: Four fixed sections: Vocabulary, Grammar, Activities, and Homework. Each section supports rich text with formatting. Also includes objectives field and estimated duration.

**Q2: How should file attachments work - size limits, file types, storage per lesson?**  
**A**: 10MB per file, 50MB total per lesson. Supported formats: PDF, DOC, DOCX, JPG, PNG, MP3, MP4. Files are virus scanned and attached directly to lessons.

**Q3: What's the relationship between lesson plans and scheduled lessons - can one plan be used multiple times?**  
**A**: One lesson plan can be scheduled multiple times with different students or dates. Lesson plans are templates; scheduled lessons are specific instances with date/time/student.

**Q4: How should lesson status tracking work (upcoming, completed, cancelled)?**  
**A**: Three states: Upcoming, Completed, Cancelled. Only tutors can change status. Completed lessons require actual duration and optional notes. Cancelled lessons have optional notes.

**Q5: Who can see/edit lesson plans - just the creator, or can they be shared?**  
**A**: Only the creator can see/edit their lesson plans. No sharing in v1. Students cannot access lesson plans directly.

**Q6: Should there be lesson templates or categories for common lesson types?**  
**A**: No templates in v1. Tutors create from scratch or duplicate existing plans. Keep it simple for MVP.

**Q7: How should the calendar/scheduling interface work?**  
**A**: Calendar view shows scheduled lessons filtered by date range or student. Click date to schedule new lesson by selecting lesson plan + student + time.

**Q8: What happens to scheduled lessons if the underlying lesson plan is edited?**  
**A**: Scheduled lessons reference the lesson plan at time of scheduling. Editing lesson plan doesn't change past scheduled lessons, but future scheduled lessons use updated content.

---

## Product Rationale

**Why fixed lesson sections instead of custom sections?**  
Language lessons follow established pedagogical patterns. Fixed structure ensures consistency and guides tutors to cover all essential elements without overwhelming them with customization options in MVP.

**Why 10MB file limit?**  
Handles most educational content (worksheets, short videos, audio clips) while preventing storage abuse. Large video files can be linked externally if needed.

**Why allow lesson plan reuse across students?**  
Tutors invest significant time creating good lesson plans. Reusability maximizes their efficiency and encourages thorough preparation since plans can serve multiple students.

**Why no student access to lesson plans?**  
Lesson plans are tutor preparation materials and intellectual property. Students receive lesson content during sessions. Direct access would complicate privacy and potentially undermine tutor value proposition.

---

## Functional Requirements

### Lesson Plan Creation and Management

**What**: Tutors create structured lesson plans with educational content

**Why**: Organized preparation leads to better teaching outcomes and professional presentation

**Behavior**:
- Create lesson plan with title, description, objectives, estimated duration
- Add content to four sections: Vocabulary, Grammar, Activities, Homework
- Save as draft or publish (only published plans can be scheduled)
- Rich text editing with formatting options
- Duplicate existing plans to create variations

### File and Material Organization  

**What**: Attach teaching materials directly to lesson plans

**Why**: Centralizes all lesson resources for easy access during teaching

**Behavior**:
- Upload files up to 10MB each, 50MB total per lesson
- Support educational formats: PDF, DOC, DOCX, JPG, PNG, MP3, MP4
- Files are virus scanned on upload
- Preview files within lesson plan view
- Remove or replace attached files

### Lesson Scheduling System

**What**: Schedule specific lesson plans with students at defined times

**Why**: Manages teaching calendar and tracks lesson delivery with students

**Behavior**:
- Select lesson plan, student, date, and time to create scheduled lesson
- View calendar of upcoming lessons filtered by date or student
- One lesson plan can be scheduled multiple times
- Prevent scheduling in past dates
- Warning for double-booking same time slot

### Progress and Completion Tracking

**What**: Track lesson delivery status and outcomes

**Why**: Monitor teaching progress and student engagement over time  

**Behavior**:
- Mark scheduled lessons as Completed, Cancelled, or leave as Upcoming
- Record actual lesson duration and session notes for completed lessons
- Optional cancellation notes for cancelled lessons
- View history of completed lessons per student
- Cannot modify completed lesson status back to upcoming

---

## Data Model (Initial Thoughts)

**Entities This Feature Needs**:
- LessonPlan: Template containing educational content and materials
- ScheduledLesson: Instance of lesson plan assigned to student with date/time
- LessonFile: Files attached to lesson plans
- User: Tutors who create plans, Students who receive lessons

**Key Relationships**:
- LessonPlan belongs to one Tutor (creator)
- ScheduledLesson references one LessonPlan and one Student
- LessonFile belongs to one LessonPlan
- One LessonPlan can have many ScheduledLessons (reusability)

---

## User Experience Flow

1. Tutor clicks "Create Lesson Plan" and enters title, description, objectives
2. Tutor adds content to Vocabulary, Grammar, Activities, and Homework sections
3. Tutor uploads relevant files (worksheets, audio, images)
4. Tutor saves as draft or publishes lesson plan
5. To schedule: tutor selects date on calendar, chooses lesson plan and student, sets time
6. System creates scheduled lesson entry visible in calendar view
7. After lesson delivery: tutor marks as completed with duration and notes
8. Completed lessons appear in student progress history

---

## Edge Cases & Constraints

- **File Upload Limits**: 10MB per file, 50MB per lesson with clear error messages
- **Scheduling Conflicts**: Warn on double-booking but allow override for flexibility
- **Past Date Scheduling**: Block scheduling lessons in the past to prevent data entry errors
- **Draft Lesson Plans**: Cannot be scheduled until published to ensure content is ready
- **Lesson Plan Dependencies**: Editing published plans affects future scheduled lessons but not completed ones
- **Account Deactivation**: Lesson plans become inaccessible but data is preserved

---

## Out of Scope for This Feature

- Lesson plan templates or categories
- Sharing lesson plans between tutors  
- Student access to lesson plan content
- Advanced calendar features (recurring lessons, reminders)
- Integration with external calendar systems
- Lesson plan versioning or revision history
- Bulk scheduling operations
- Video conferencing integration
- Student homework submission tracking

---

## Dependencies

**Depends On**: User Authentication (to identify tutor/student), Student Management (to assign lessons to students)

**Enables**: Progress Tracking (lesson completion data), Session Notes (detailed lesson outcomes), Student Dashboard (upcoming lesson visibility)