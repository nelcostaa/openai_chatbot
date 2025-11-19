# Life Story AI Assistant_ Conversational Phase Specification

*Extracted from: Life Story AI Assistant_ Conversational Phase Specification.pdf*

---

### Life Story AI Assistant: Conversational

### Phase Specification

This document details the four core phases of the user experience, focusing on the AI's role
in guiding the user, the conversational logic, and the final output constraints for the "Story
Card" game.
The system relies on a consistent, multi-turn conversational approach using the Gemini API to
manage the user's narrative data via the Firestore database.

### Phase 1: Documentation (Initial Story Capture)

Goal: Select the user's preferred method for retrieving memories and capture the initial
volume of raw narrative text.
Method Target User Goal in Phase 1 AI Prompting

### Persona Focus

1. Chronological Likes order, facts, Capture events in "Let's start at the
Steward and timelines. sequential, linear very beginning.
order from birth to What are the

### present. earliest significant

### memories you

### have, and what was

### the year?"

2. Thematic Prefers discussing Capture stories "What are the three
Explorer abstract concepts grouped by core most defining
(e.g., love, career, life themes, themes in your life
struggle). ignoring strict (e.g., Travel, Family,

### timelines. Innovation)? Let's

### start with the first

### one."

3. Anecdotal Enjoys sharing Capture individual, "Tell me about a
Spark short, punchy, high-impact time you laughed
isolated moments. stories, moments, until you cried, or

### or 'vignettes.' the most surprising

### thing that ever

| Method | Target User Persona | Goal in Phase 1 | AI Prompting Focus |
| --- | --- | --- | --- |
| 1. Chronological Steward | Likes order, facts, and timelines. | Capture events in sequential, linear order from birth to present. | "Let's start at the very beginning. What are the earliest significant memories you have, and what was the year?" |
| 2. Thematic Explorer | Prefers discussing abstract concepts (e.g., love, career, struggle). | Capture stories grouped by core life themes, ignoring strict timelines. | "What are the three most defining themes in your life (e.g., Travel, Family, Innovation)? Let's start with the first one." |
| 3. Anecdotal Spark | Enjoys sharing short, punchy, isolated moments. | Capture individual, high-impact stories, moments, or 'vignettes.' | "Tell me about a time you laughed until you cried, or the most surprising thing that ever |

---
**Page 2**

### happened to you."

4. The Prefers direct, Capture responses "Let's begin with
Interviewer's structured to pre-set, deep, Question 1: What is
Chair questioning (like a thought-provoking the greatest lesson

### journalist asking). questions. you learned from

### your parents or

### guardians?"

5. The Reflective Enjoys personal, Capture thoughts "Reflect on a
Journaler introspective on challenges, period of great
writing and self- feelings, and challenge. What
analysis. personal growth. were you feeling,

### and how did you

### overcome it?"

6. The Legacy Focused on future Capture stories and "What message do
Weaver impact and what beliefs that define you want to pass
they want to leave their legacy and on to future

### behind. intended value. generations, and

### which stories best

### exemplify that

### message?"

Phase 2: Fleshing Out (Elaboration and Depth)
Goal: Expand the initial raw text into richer, more detailed narratives by employing targeted
follow-up questions based on the method chosen in Phase 1.
The AI must dynamically adjust its questioning strategy based on the user's previous choice.
Phase 1 Method AI Action / Example Question

### Conversational Link Sequence

Chronological Steward Focus on details, "You mentioned moving to
motivations, and impact London in '95. What was
of the recorded events. the biggest challenge you

### faced when you first

### arrived? Was the decision

|  |  |  | happened to you." |
| --- | --- | --- | --- |
| 4. The Interviewer's Chair | Prefers direct, structured questioning (like a journalist asking). | Capture responses to pre-set, deep, thought-provoking questions. | "Let's begin with Question 1: What is the greatest lesson you learned from your parents or guardians?" |
| 5. The Reflective Journaler | Enjoys personal, introspective writing and self- analysis. | Capture thoughts on challenges, feelings, and personal growth. | "Reflect on a period of great challenge. What were you feeling, and how did you overcome it?" |
| 6. The Legacy Weaver | Focused on future impact and what they want to leave behind. | Capture stories and beliefs that define their legacy and intended value. | "What message do you want to pass on to future generations, and which stories best exemplify that message?" |

| Phase 1 Method | AI Action / Conversational Link | Example Question Sequence |
| --- | --- | --- |
| Chronological Steward | Focus on details, motivations, and impact of the recorded events. | "You mentioned moving to London in '95. What was the biggest challenge you faced when you first arrived? Was the decision |

---
**Page 3**

### purely professional, or

### were there personal

### motivations involved?"

Anecdotal Spark Focus on the context "That story about the
before and after the prank war was hilarious!
anecdote, and the emotion But what led up to that

### felt. specific moment? And how

### did that event change your

### relationship with that

### person afterward?"

Reflective Journaler Focus on introspection, "You described feeling
comparison, and the 'burnt out' in that

### lessons learned. challenging period. If you

### could give advice to your

### past self, what would it be?

### How does that past

### struggle compare to your

### current approach to

### stress?"

Legacy Weaver Focus on verifying the "Your legacy is focused on
legacy by connecting it to generosity. Can you share
concrete actions and a specific story where you
beliefs. had to make a sacrifice to

### uphold that belief?"

### Phase 3: Finalizing and Organizing

Goal: Structure the expanded content into a logical life narrative with chapters and sections,
suitable for review and final editing.
1.
Full Biography Storage: All expanded, detailed text is stored as the user's Full
Biography in the Firestore database.
2.
AI Organization: The AI processes the structured stories and proposes a hierarchy:

### ○

Chapters: Broad periods or major sections (e.g., Childhood, Professional Life,
Retirement).

### ○

Sections: Sub-topics within chapters (e.g., Primary School, University Years).

### ○

Stories: The individual, narrative paragraphs developed in Phase 1 and 2.
3.
User Review: The user is prompted to review and approve the proposed

|  |  | purely professional, or were there personal motivations involved?" |
| --- | --- | --- |
| Anecdotal Spark | Focus on the context before and after the anecdote, and the emotion felt. | "That story about the prank war was hilarious! But what led up to that specific moment? And how did that event change your relationship with that person afterward?" |
| Reflective Journaler | Focus on introspection, comparison, and the lessons learned. | "You described feeling 'burnt out' in that challenging period. If you could give advice to your past self, what would it be? How does that past struggle compare to your current approach to stress?" |
| Legacy Weaver | Focus on verifying the legacy by connecting it to concrete actions and beliefs. | "Your legacy is focused on generosity. Can you share a specific story where you had to make a sacrifice to uphold that belief?" |

---
**Page 4**

Chapter/Section titles and ordering. The AI assists in renaming or moving sections based
on user feedback.
Phase 4: Constraint Mapping (Game Card Production)
Goal: Summarize and adapt the detailed narratives into the strict format required for the
physical Story Cards, while preserving the original Full Biography.
This phase is critical for production. The AI must act as a summarization engine to fit the
game constraints.

### 🔴

## CRITICAL GAME CARD CONSTRAINTS

Element Constraint Limit AI Role in Compliance
Card Title Max 60 characters The AI generates a concise,

### compelling title for the

### story based on the

narrative's central point.
Story Text (Body) Max 3 paragraphs or The AI drafts a highly

### approx. 300 characters compressed summary of

### the full story, retaining the

### core event and emotional

impact.

### Process Steps:

1.
Full Draft Summary: For every story the user has finalized, the AI presents a
summarized draft that fits the character constraints.
2.
User Approval: The user must approve (or edit) the compressed Card Title and Story
Text before it is marked as ready for card production.
3.
Full Biography Preservation: The original, detailed text from Phases 1-3 must be
stored and preserved separately from the card-ready text. This detailed version can be
offered to the user as a downloadable 'Book/Autobiography' text file.

### Technical and Deployment Notes

### ●

API for Logic: The entire conversational and summarization logic should be handled by
the Gemini API (gemini-2.5-flash-preview-09-2025 is recommended for high-quality
conversational turns and text generation/summarization).

### ●

Data Storage: Firestore is mandatory for user authentication, storing the multi-turn

| Element | Constraint Limit | AI Role in Compliance |
| --- | --- | --- |
| Card Title | Max 60 characters | The AI generates a concise, compelling title for the story based on the narrative's central point. |
| Story Text (Body) | Max 3 paragraphs or approx. 300 characters | The AI drafts a highly compressed summary of the full story, retaining the core event and emotional impact. |

---
**Page 5**

conversational history, and persistently saving both the raw, expanded, and final Card-
Ready text versions.

### ●

Deployment: The application front-end (web app) should be connected to a secure
backend environment (e.g., Cloud Run or App Engine on Google Cloud) that handles
the API calls and database interactions, potentially leveraging GitHub and Cloud Build
for continuous deployment.
