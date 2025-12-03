# Life Story Game - Database Schema Design Guideline

**Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Purpose**: AI-consumable specification for building production database schema

---

## Table of Contents

1. [Project Context](#project-context)
2. [Domain Overview](#domain-overview)
3. [Core Entities](#core-entities)
4. [Supporting Entities](#supporting-entities)
5. [Relationship Map](#relationship-map)
6. [Schema Definitions](#schema-definitions)
7. [Future Considerations](#future-considerations)
8. [Migration Strategy](#migration-strategy)

---

## Project Context

### What This Application Does

**Life Story Game** is an AI-powered life story interviewer that guides users through chronological interviews about their lives. The AI adapts questions based on user age, explores different life phases, tracks conversation themes, and generates story summaries.

### Current Architecture (Stateless)

Currently the application is **completely stateless**:
- Frontend (React) holds all state in memory
- Backend (Python serverless functions) receives full conversation history with each request
- No data persists between sessions
- User loses all progress on page refresh

### Target Architecture (Persistent)

The database will enable:
- User accounts and authentication
- Persistent interview sessions across devices/time
- Story archive with multiple completed interviews
- Per-chapter summaries that can be regenerated
- Theme analytics across stories
- Future: Board game output generation

### Tech Stack Context

- **Frontend**: React 19, Vite 7, Tailwind CSS 4
- **Backend**: Python serverless (Vercel)
- **AI**: Google Gemini (multi-model fallback cascade)
- **Recommended Database**: PostgreSQL (Supabase) or MongoDB

---

## Domain Overview

### Interview Flow

```
GREETING → AGE_SELECTION → [Age-Appropriate Phases] → SYNTHESIS
```

### Age-Phase Mapping

Users select their age range, which determines which life phases apply:

| Age Range | Available Phases |
|-----------|------------------|
| `under_18` | FAMILY_HISTORY, CHILDHOOD |
| `18_30` | FAMILY_HISTORY, CHILDHOOD, ADOLESCENCE, EARLY_ADULTHOOD |
| `31_45` | FAMILY_HISTORY, CHILDHOOD, ADOLESCENCE, EARLY_ADULTHOOD, MIDLIFE |
| `46_60` | FAMILY_HISTORY, CHILDHOOD, ADOLESCENCE, EARLY_ADULTHOOD, MIDLIFE |
| `61_plus` | FAMILY_HISTORY, CHILDHOOD, ADOLESCENCE, EARLY_ADULTHOOD, MIDLIFE, PRESENT |

### Interview Phases (Summarizable Chapters)

| Phase ID | Display Name | Description |
|----------|--------------|-------------|
| `FAMILY_HISTORY` | Family History | Origins, ancestry, family dynamics before birth |
| `CHILDHOOD` | Childhood | Birth to age 12, earliest memories |
| `ADOLESCENCE` | Adolescence | Ages 13-18, teenage years |
| `EARLY_ADULTHOOD` | Early Adulthood | Ages 19-35, major life choices |
| `MIDLIFE` | Midlife | Ages 36-60, achievements and challenges |
| `PRESENT` | Present Day | Current chapter and reflection |

### Non-Summarizable Phases

| Phase ID | Purpose |
|----------|---------|
| `GREETING` | Welcome and setup |
| `AGE_SELECTION` | User selects age range |
| `SYNTHESIS` | AI generates final story structure |

### Available Themes (19 predefined)

```
adventure, family, career, love, challenge, growth, travel, friendship,
legacy, identity, father_figure, mother_figure, mentor, loss, success,
failure, humor, courage, resilience
```

Custom themes are also supported (user-defined).

### Story Routes (Interview Styles)

| Route ID | Name | Description |
|----------|------|-------------|
| `1` | Chronological Steward | Share story in order from beginning to present |
| `2` | Thematic Explorer | Organize by life themes |
| `3` | Anecdotal Spark | Share vivid standalone moments |
| `4` | Interviewer's Chair | Answer structured questions |
| `5` | Reflective Journaler | Explore challenges and growth |
| `6` | Legacy Weaver | Focus on legacy for future generations |
| `7` | Personal Route | User-defined approach |

**Note**: Currently only Route 1 (Chronological Steward) is implemented.

---

## Core Entities

### 1. User

Represents an authenticated user account.

**Key Fields:**
- Unique identifier
- Email (unique, for auth)
- Display name
- Account creation timestamp
- Last activity timestamp
- Preferences (JSON for flexibility)

**Relationships:**
- Has many Stories
- Has many Themes (custom)

### 2. Story

A complete interview session (can be in-progress or completed).

**Key Fields:**
- Unique identifier
- Owner (User reference)
- Title (generated at SYNTHESIS or user-defined)
- Story essence (1-2 sentence summary)
- Selected route (interview style)
- Age range selected
- Current phase (for in-progress stories)
- Status: `draft`, `in_progress`, `completed`, `archived`
- Phase order (array of phases traversed)
- Current phase index
- Creation timestamp
- Last updated timestamp
- Completion timestamp (nullable)

**Relationships:**
- Belongs to User
- Has many Messages
- Has many StoryThemes (junction)
- Has many ChapterSummaries
- Has one SynthesisResult

### 3. Message

Individual conversation turns within a story.

**Key Fields:**
- Unique identifier
- Story reference
- Role: `user`, `assistant`, `system`
- Content (text)
- Phase context (which phase this message belongs to)
- Sequence number (ordering within story)
- Is phase transition marker (boolean)
- Creation timestamp

**Relationships:**
- Belongs to Story

### 4. ChapterSummary

Per-phase summaries generated on demand.

**Key Fields:**
- Unique identifier
- Story reference
- Phase (e.g., `CHILDHOOD`)
- Summary content (text)
- Message range (first and last message IDs included)
- AI model used
- Token count
- Generation timestamp
- Is stale (boolean - true if new messages added after generation)

**Relationships:**
- Belongs to Story

---

## Supporting Entities

### 5. Theme

Both predefined and custom themes.

**Key Fields:**
- Unique identifier
- Name (slug format: `father_figure`)
- Display name (human readable: `Father Figure`)
- Is predefined (boolean)
- Created by (User reference, nullable for predefined)
- Keywords (array of detection keywords)

**Relationships:**
- Optionally belongs to User (custom themes)
- Has many StoryThemes

### 6. StoryTheme (Junction Table)

Links themes to stories with status tracking.

**Key Fields:**
- Story reference
- Theme reference
- Status: `selected` (user chose), `addressed` (AI discussed), `both`
- First addressed at (Message reference)
- Times mentioned (count)

**Relationships:**
- Belongs to Story
- Belongs to Theme

### 7. SynthesisResult

Final story structure generated at SYNTHESIS phase.

**Key Fields:**
- Unique identifier
- Story reference
- Generated title
- Story essence
- Timeline chapters (JSON array of 5 chapters)
- Key story moments (JSON array of 5-7 moments)
- AI model used
- Generation timestamp
- Raw AI response (for debugging)

**Relationships:**
- Belongs to Story

### 8. Route

Interview route/style configuration.

**Key Fields:**
- Unique identifier (matches route ID: `1`, `2`, etc.)
- Name
- Description
- Persona description
- Is implemented (boolean)
- System instruction template

**Relationships:**
- Has many Stories

### 9. Phase

Interview phase configuration.

**Key Fields:**
- Unique identifier (e.g., `CHILDHOOD`)
- Display name
- Description
- Order index (for sequencing)
- Is summarizable (boolean)
- System instruction template
- Applicable age ranges (array)

**Relationships:**
- Has many Messages (via context)
- Has many ChapterSummaries

---

## Relationship Map

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│  - id, email, display_name, created_at, preferences             │
└─────────────────────────────────────────────────────────────────┘
          │
          │ 1:N
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        STORY                                     │
│  - id, user_id, title, route_id, age_range, status              │
│  - current_phase, phase_order[], phase_index                    │
│  - created_at, updated_at, completed_at                         │
└─────────────────────────────────────────────────────────────────┘
          │                    │                    │
          │ 1:N                │ 1:N                │ 1:1
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│    MESSAGE      │  │ CHAPTER_SUMMARY │  │  SYNTHESIS_RESULT   │
│  - id           │  │  - id           │  │  - id               │
│  - story_id     │  │  - story_id     │  │  - story_id         │
│  - role         │  │  - phase        │  │  - title            │
│  - content      │  │  - content      │  │  - essence          │
│  - phase        │  │  - is_stale     │  │  - timeline[]       │
│  - sequence     │  │  - created_at   │  │  - moments[]        │
│  - created_at   │  │                 │  │  - created_at       │
└─────────────────┘  └─────────────────┘  └─────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      STORY_THEME (Junction)                      │
│  - story_id, theme_id, status, first_addressed_msg_id           │
└─────────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────┐            ┌─────────────────┐
│     STORY       │            │     THEME       │
│  (reference)    │            │  - id, name     │
└─────────────────┘            │  - is_predefined│
                               │  - keywords[]   │
                               └─────────────────┘

┌─────────────────┐            ┌─────────────────┐Unique identifier
- Owner (User reference)
- Title (generated at SYNTHESIS or user-defined)
- Story essence (1-2 sentence summary)
- Selected route (interview style)
- Age range selected
- Current phase (for in-progress stories)
- Status: `draft`, `in_progress`, `completed`, `archived`
- Phase order (array of phases traversed)
- Current phase index
- Creation timestamp
- Last updated timestamp
- Completion timestamp (nullable)
│     ROUTE       │            │     PHASE       │
│  - id, name     │            │  - id, name     │
│  - description  │            │  - order_index  │
│  - is_active    │            │  - is_summary   │
└─────────────────┘            └─────────────────┘
```

---

## Schema Definitions

### PostgreSQL Schema

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- CORE TABLES
-- ============================================

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    password_hash VARCHAR(255), -- If using password auth
    auth_provider VARCHAR(50), -- 'email', 'google', 'github', etc.
    auth_provider_id VARCHAR(255), -- External auth ID
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Routes (reference/config table)
CREATE TABLE routes (
    id VARCHAR(20) PRIMARY KEY, -- '1', '2', etc.
    name VARCHAR(100) NOT NULL,
    description TEXT,
    persona TEXT,
    goal TEXT,
    is_implemented BOOLEAN DEFAULT FALSE,
    system_instruction_template TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Phases (reference/config table)
CREATE TABLE phases (
    id VARCHAR(50) PRIMARY KEY, -- 'CHILDHOOD', 'ADOLESCENCE', etc.
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    is_summarizable BOOLEAN DEFAULT TRUE,
    system_instruction_template TEXT,
    applicable_age_ranges TEXT[] DEFAULT '{}', -- Array of age ranges
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_phases_order ON phases(order_index);

-- Stories table
CREATE TABLE stories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    route_id VARCHAR(20) REFERENCES routes(id),
    title VARCHAR(255),
    story_essence TEXT,
    age_range VARCHAR(20), -- 'under_18', '18_30', '31_45', '46_60', '61_plus'
    current_phase VARCHAR(50) REFERENCES phases(id),
    phase_order TEXT[] DEFAULT '{}', -- Array of phase IDs traversed
    phase_index INTEGER DEFAULT -1,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'archived')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_stories_user ON stories(user_id);
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_created ON stories(created_at DESC);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    phase VARCHAR(50) REFERENCES phases(id),
    sequence INTEGER NOT NULL,
    is_phase_transition BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}', -- For additional context (tokens, model used, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_story ON messages(story_id);
CREATE INDEX idx_messages_sequence ON messages(story_id, sequence);
CREATE INDEX idx_messages_phase ON messages(story_id, phase);

-- Chapter summaries table
CREATE TABLE chapter_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    phase VARCHAR(50) NOT NULL REFERENCES phases(id),
    content TEXT NOT NULL,
    first_message_id UUID REFERENCES messages(id),
    last_message_id UUID REFERENCES messages(id),
    ai_model VARCHAR(100),
    token_count INTEGER,
    is_stale BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(story_id, phase)
);

CREATE INDEX idx_chapter_summaries_story ON chapter_summaries(story_id);

-- ============================================
-- SUPPORTING TABLES
-- ============================================

-- Themes table (predefined + custom)
CREATE TABLE themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL, -- slug format: 'father_figure'
    display_name VARCHAR(100) NOT NULL, -- 'Father Figure'
    is_predefined BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    keywords TEXT[] DEFAULT '{}', -- Detection keywords
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_themes_name ON themes(name);
CREATE INDEX idx_themes_predefined ON themes(is_predefined);

-- Story-Theme junction table
CREATE TABLE story_themes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    theme_id UUID NOT NULL REFERENCES themes(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'selected' CHECK (status IN ('selected', 'addressed', 'both')),
    first_addressed_message_id UUID REFERENCES messages(id),
    times_mentioned INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(story_id, theme_id)
);

CREATE INDEX idx_story_themes_story ON story_themes(story_id);
CREATE INDEX idx_story_themes_theme ON story_themes(theme_id);

-- Synthesis results table
CREATE TABLE synthesis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID UNIQUE NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    generated_title VARCHAR(255),
    story_essence TEXT,
    timeline_chapters JSONB DEFAULT '[]', -- Array of {title, description, era}
    key_moments JSONB DEFAULT '[]', -- Array of {moment, description, approximate_time}
    ai_model VARCHAR(100),
    raw_response TEXT, -- Full AI response for debugging
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_synthesis_story ON synthesis_results(story_id);

-- ============================================
-- AUDIT/ANALYTICS TABLES (Future)
-- ============================================

-- Session analytics (optional)
CREATE TABLE session_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    messages_sent INTEGER DEFAULT 0,
    phases_completed INTEGER DEFAULT 0,
    device_type VARCHAR(50),
    user_agent TEXT
);

-- AI usage tracking (optional)
CREATE TABLE ai_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID REFERENCES stories(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    model_used VARCHAR(100) NOT NULL,
    endpoint VARCHAR(50), -- 'chat', 'summary', etc.
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ai_usage_user ON ai_usage_logs(user_id);
CREATE INDEX idx_ai_usage_created ON ai_usage_logs(created_at DESC);

-- ============================================
-- SEED DATA
-- ============================================

-- Insert predefined routes
INSERT INTO routes (id, name, description, is_implemented) VALUES
('1', 'Chronological Steward', 'Share your story in order from beginning to present', TRUE),
('2', 'Thematic Explorer', 'Organize by life themes (love, career, growth)', FALSE),
('3', 'Anecdotal Spark', 'Share vivid, standalone moments and memories', FALSE),
('4', 'Interviewer''s Chair', 'Answer structured, thought-provoking questions', FALSE),
('5', 'Reflective Journaler', 'Explore challenges and personal growth introspectively', FALSE),
('6', 'Legacy Weaver', 'Focus on what you want to leave behind for future generations', FALSE),
('7', 'Personal Route', 'Describe your own approach', FALSE);

-- Insert predefined phases
INSERT INTO phases (id, display_name, description, order_index, is_summarizable, applicable_age_ranges) VALUES
('GREETING', 'Greeting', 'Welcome and introduction', 0, FALSE, '{}'),
('AGE_SELECTION', 'Age Selection', 'User selects their age range', 1, FALSE, '{}'),
('FAMILY_HISTORY', 'Family History', 'Origins, ancestry, family dynamics before birth', 2, TRUE, '{"under_18","18_30","31_45","46_60","61_plus"}'),
('CHILDHOOD', 'Childhood', 'Birth to age 12, earliest memories', 3, TRUE, '{"under_18","18_30","31_45","46_60","61_plus"}'),
('ADOLESCENCE', 'Adolescence', 'Ages 13-18, teenage years', 4, TRUE, '{"18_30","31_45","46_60","61_plus"}'),
('EARLY_ADULTHOOD', 'Early Adulthood', 'Ages 19-35, major life choices', 5, TRUE, '{"18_30","31_45","46_60","61_plus"}'),
('MIDLIFE', 'Midlife', 'Ages 36-60, achievements and challenges', 6, TRUE, '{"31_45","46_60","61_plus"}'),
('PRESENT', 'Present Day', 'Current chapter and reflection', 7, TRUE, '{"61_plus"}'),
('SYNTHESIS', 'Synthesis', 'Generate final story structure', 8, FALSE, '{}');

-- Insert predefined themes
INSERT INTO themes (name, display_name, is_predefined, keywords) VALUES
('adventure', 'Adventure', TRUE, '{"adventure","adventures","exciting","explore","exploration","journey"}'),
('family', 'Family', TRUE, '{"family","families","parents","siblings","relatives","mother","father","brother","sister"}'),
('career', 'Career', TRUE, '{"career","job","work","profession","occupation","employment","workplace"}'),
('love', 'Love', TRUE, '{"love","romance","relationship","partner","spouse","dating","marriage"}'),
('challenge', 'Challenge', TRUE, '{"challenge","challenges","difficult","struggle","overcome","obstacle"}'),
('growth', 'Growth', TRUE, '{"growth","growing","develop","progress","evolve","mature","learn"}'),
('travel', 'Travel', TRUE, '{"travel","traveled","trip","trips","journey","visited","destination"}'),
('friendship', 'Friendship', TRUE, '{"friendship","friends","friend","companion","buddy","pal"}'),
('legacy', 'Legacy', TRUE, '{"legacy","heritage","inheritance","lasting","remember","leave behind"}'),
('identity', 'Identity', TRUE, '{"identity","who you are","sense of self","define","authentic"}'),
('father_figure', 'Father Figure', TRUE, '{"father","dad","daddy","paternal","fatherly"}'),
('mother_figure', 'Mother Figure', TRUE, '{"mother","mom","mommy","maternal","motherly"}'),
('mentor', 'Mentor', TRUE, '{"mentor","mentors","guide","teacher","coach","advisor"}'),
('loss', 'Loss', TRUE, '{"loss","lost","grief","grieving","mourning","passed away","death"}'),
('success', 'Success', TRUE, '{"success","successful","achievement","accomplish","triumph","victory"}'),
('failure', 'Failure', TRUE, '{"failure","failed","setback","mistake","defeat"}'),
('humor', 'Humor', TRUE, '{"humor","humour","funny","laugh","comedy","joke"}'),
('courage', 'Courage', TRUE, '{"courage","courageous","brave","bravery","fearless"}'),
('resilience', 'Resilience', TRUE, '{"resilience","resilient","bounce back","recover","persevere"}');

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stories_updated_at
    BEFORE UPDATE ON stories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_story_themes_updated_at
    BEFORE UPDATE ON story_themes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Mark chapter summaries as stale when new messages added
CREATE OR REPLACE FUNCTION mark_summaries_stale()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chapter_summaries
    SET is_stale = TRUE
    WHERE story_id = NEW.story_id
    AND phase = NEW.phase;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mark_summaries_stale_on_message
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION mark_summaries_stale();
```

### MongoDB Alternative Schema

```javascript
// Users Collection
{
  _id: ObjectId,
  email: String, // unique
  displayName: String,
  authProvider: String, // 'email', 'google', etc.
  authProviderId: String,
  preferences: {
    // Flexible preferences object
  },
  createdAt: Date,
  updatedAt: Date,
  lastActiveAt: Date
}

// Stories Collection
{
  _id: ObjectId,
  userId: ObjectId, // ref: users
  routeId: String, // '1', '2', etc.
  title: String,
  storyEssence: String,
  ageRange: String, // 'under_18', '18_30', etc.
  currentPhase: String,
  phaseOrder: [String], // ['GREETING', 'AGE_SELECTION', 'FAMILY_HISTORY', ...]
  phaseIndex: Number,
  status: String, // 'draft', 'in_progress', 'completed', 'archived'
  
  // Embedded messages (for smaller stories) or referenced
  messages: [{
    role: String, // 'user', 'assistant', 'system'
    content: String,
    phase: String,
    sequence: Number,
    isPhaseTransition: Boolean,
    metadata: Object,
    createdAt: Date
  }],
  
  // Themes with status
  themes: [{
    themeId: ObjectId, // ref: themes
    themeName: String, // denormalized for quick access
    status: String, // 'selected', 'addressed', 'both'
    timesMentioned: Number,
    firstAddressedAt: Date
  }],
  
  // Chapter summaries embedded
  chapterSummaries: [{
    phase: String,
    content: String,
    messageRange: { first: Number, last: Number },
    aiModel: String,
    tokenCount: Number,
    isStale: Boolean,
    createdAt: Date
  }],
  
  // Synthesis result embedded
  synthesis: {
    generatedTitle: String,
    storyEssence: String,
    timelineChapters: [{
      title: String,
      description: String,
      era: String
    }],
    keyMoments: [{
      moment: String,
      description: String,
      approximateTime: String
    }],
    aiModel: String,
    rawResponse: String,
    createdAt: Date
  },
  
  createdAt: Date,
  updatedAt: Date,
  completedAt: Date
}

// Themes Collection (reference data)
{
  _id: ObjectId,
  name: String, // unique slug
  displayName: String,
  isPredefined: Boolean,
  createdBy: ObjectId, // ref: users, null for predefined
  keywords: [String],
  createdAt: Date
}

// Routes Collection (reference data)
{
  _id: String, // '1', '2', etc.
  name: String,
  description: String,
  persona: String,
  isImplemented: Boolean,
  systemInstructionTemplate: String,
  createdAt: Date
}

// Phases Collection (reference data)
{
  _id: String, // 'CHILDHOOD', etc.
  displayName: String,
  description: String,
  orderIndex: Number,
  isSummarizable: Boolean,
  systemInstructionTemplate: String,
  applicableAgeRanges: [String],
  createdAt: Date
}

// Indexes
db.users.createIndex({ email: 1 }, { unique: true })
db.stories.createIndex({ userId: 1 })
db.stories.createIndex({ status: 1 })
db.stories.createIndex({ createdAt: -1 })
db.themes.createIndex({ name: 1 }, { unique: true })
db.themes.createIndex({ isPredefined: 1 })
```

---

## Future Considerations

### Board Game Output Feature

When implementing board game generation, add:

```sql
-- Board game outputs table
CREATE TABLE board_game_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID UNIQUE NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    game_title VARCHAR(255),
    game_type VARCHAR(50), -- 'timeline', 'trivia', 'journey_map', etc.
    game_data JSONB NOT NULL, -- Full game structure
    printable_assets JSONB, -- URLs/paths to generated assets
    generation_version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Multi-Route Support

When implementing additional routes (2-7):

1. Add `system_instruction_template` to routes table
2. Create route-specific phase configurations
3. Consider route-specific theme relevance scoring

### Collaborative Stories

For future multi-user story features:

```sql
-- Story collaborators table
CREATE TABLE story_collaborators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'viewer' CHECK (role IN ('viewer', 'contributor', 'editor', 'owner')),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(story_id, user_id)
);
```

### Story Sharing/Publishing

```sql
-- Published stories (read-only public versions)
CREATE TABLE published_stories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    public_slug VARCHAR(100) UNIQUE,
    visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('private', 'unlisted', 'public')),
    view_count INTEGER DEFAULT 0,
    published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_viewed_at TIMESTAMP WITH TIME ZONE
);
```

### Analytics Dashboard

```sql
-- Aggregate analytics (materialized or computed)
CREATE TABLE user_analytics (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    total_stories INTEGER DEFAULT 0,
    completed_stories INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    most_used_themes TEXT[],
    average_story_length INTEGER,
    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Migration Strategy

### Phase 1: Core Tables

1. Create users, routes, phases tables
2. Seed reference data (routes, phases, predefined themes)
3. Create stories and messages tables
4. Add basic indexes

### Phase 2: Supporting Features

1. Create themes table with predefined themes
2. Create story_themes junction table
3. Create chapter_summaries table
4. Add theme detection triggers

### Phase 3: Synthesis & Analytics

1. Create synthesis_results table
2. Create session_analytics table
3. Create ai_usage_logs table
4. Add analytics functions

### Phase 4: Future Features

1. Board game outputs (when feature ready)
2. Story collaborators (when feature ready)
3. Published stories (when feature ready)

---

## API Integration Notes

### Stateful vs Stateless Considerations

With database:
- Backend can load conversation from DB instead of receiving full history
- Phase tracking moves from frontend state to database
- Theme detection results persist across sessions
- Summaries cached and invalidated intelligently

### Required Backend Changes

1. **Auth middleware**: Validate JWT/session, inject user_id
2. **Story service**: Create, load, update stories
3. **Message service**: Append messages, get conversation history
4. **Summary service**: Cache summaries, detect staleness
5. **Theme service**: Track selected/addressed themes

### Frontend Changes

1. **Auth flow**: Login/signup, token storage
2. **Story list**: View saved stories, create new
3. **Auto-save**: Periodic or per-message persistence
4. **Resume**: Load story state from backend

---

## Security Considerations

1. **Row-level security**: Users can only access their own stories
2. **Rate limiting**: Per-user API limits to prevent abuse
3. **Input validation**: Sanitize all content before storage
4. **Encryption**: Encrypt sensitive story content at rest
5. **Audit logging**: Track access to story data
6. **GDPR compliance**: User data export and deletion

---

## Performance Considerations

1. **Message pagination**: Load messages in chunks for long stories
2. **Summary caching**: Don't regenerate unless stale
3. **Index optimization**: Monitor query patterns, add indexes
4. **Connection pooling**: Use connection pooler for serverless
5. **Read replicas**: For analytics queries (future)

---

*This document serves as the authoritative specification for database schema design. When implementing, prioritize Core Entities first, then Supporting Entities, then Future Considerations as features are developed.*
