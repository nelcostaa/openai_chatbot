# Master Execution Plan: Life Story Game SaaS

**Strategy:** Local Backend (Docker) ↔ Remote Managed Database (DigitalOcean)

**Last Updated:** 2025-12-08

This document outlines the exact step-by-step process to migrate from the stateless MVP to the stateful SaaS architecture.

---

## Prerequisites

- ✅ **DigitalOcean Managed Database:** Connection string configured
- ✅ **Trusted Sources:** IP address whitelisted
- ✅ **Docker & Docker Compose:** Installed and running
- ✅ **Gemini API Key:** Configured in `.env`

---

## 🎯 Completed Phases

### ✅ Phase 0: Foundation Setup
**Status:** COMPLETE

- ✅ Database models (User, Story, Message, Summary, Subscription)
- ✅ SQLAlchemy ORM + Alembic migrations
- ✅ Docker Compose (backend, frontend, redis)
- ✅ FastAPI application structure
- ✅ Environment configuration

**Evidence:**
- Database schema: 5 tables created (alembic version: 35c3ce144bee)
- Docker services running: backend:8000, frontend:8080, redis:6379
- Health endpoint: `GET /health` returns 200 OK

---

### ✅ Phase 1: Infrastructure & Connectivity
**Status:** COMPLETE

- ✅ Backend Docker container operational
- ✅ PostgreSQL connection established (DigitalOcean)
- ✅ FastAPI app serving on port 8000
- ✅ Database session management working

**Deliverables:**
- `backend/app/main.py` - Application entry point
- `backend/app/db/session.py` - DB connection logic
- `backend/app/db/base.py` - Model registry
- `docker-compose.yml` - Service orchestration

---

### ✅ Phase 2: Database Schema Implementation
**Status:** COMPLETE

**Models Created:**
- `User` - Authentication and profile
- `Story` - User stories with route/phase tracking
- `Message` - Chat history (linked to stories)
- `Summary` - Chapter summaries
- `Subscription` - User subscription data

**Migrations Applied:**
- `5abab21711bd` - Initial database schema
- `35c3ce144bee` - Add summaries table

**Evidence:**
```bash
$ alembic current
35c3ce144bee (head)
```

---

### ✅ Phase 3: The Streaming Brain (Vertical Slice 3)
**Status:** COMPLETE - FULLY TESTED

**Architecture Implemented:**
```
FastAPI Endpoint → Service Layer → LangGraph Agent → Gemini API → Database
     ↓                  ↓                ↓                ↓            ↓
  interview.py   interview.py      agent.py      Google Gemini   PostgreSQL
```

**Core Components:**
- ✅ `backend/app/core/agent.py` - LangGraph state graph with 5-model fallback cascade
- ✅ `backend/app/services/interview.py` - Business logic orchestration
- ✅ `backend/app/api/endpoints/interview.py` - REST API endpoint
- ✅ AI Model Fallback: gemini-2.0-flash-exp → gemini-2.0-flash → gemini-2.5-flash → gemini-flash-latest → gemini-2.0-flash-lite

**API Endpoints:**
- `POST /api/interview/{story_id}` - Send message, get AI response
  - Request: `{"message": "user input"}`
  - Response: `{"id": int, "role": str, "content": str, "phase": str}`

**Test Coverage:** 24 tests passing
- 10 tests: Agent fallback logic (`test_agent_fallback.py`)
- 8 tests: Service orchestration (`test_interview_service.py`)
- 6 tests: API endpoint integration (`test_interview_endpoint.py`)

**Evidence:**
```bash
$ pytest tests/python/test_agent_fallback.py tests/python/test_interview_service.py tests/python/test_interview_endpoint.py -v
====== 24 passed, 4 warnings in 9.64s ======
```

---

## 🚧 Next Phases (Revised)

### 📝 Phase 4: User Authentication & Sessions
**Status:** PENDING
**Priority:** HIGH (blocking frontend integration)

**Goal:** Implement user authentication so stories can be owned and accessed securely.

**Step 4.1: Authentication Endpoints**
```python
# Required endpoints:
POST /api/auth/register
POST /api/auth/login
GET /api/auth/me
POST /api/auth/logout
```

**Step 4.2: JWT/Session Management**
- Implement JWT token generation
- Add authentication middleware
- Protect story endpoints with user context

**Step 4.3: User-Story Association**
- Ensure Story.user_id is enforced
- Filter stories by authenticated user
- Add authorization checks

**Success Criteria:**
- User can register and login
- JWT tokens issued and validated
- Stories scoped to authenticated user
- Tests for auth flows passing

---

### 📚 Phase 5: Story Management API
**Status:** PENDING
**Priority:** HIGH (required before frontend migration)

**Goal:** Create endpoints for managing user stories (the missing piece).

**Step 5.1: Story CRUD Endpoints**
```python
POST /api/stories/              # Create new story
GET /api/stories/               # List user's stories
GET /api/stories/{story_id}     # Get story details
PUT /api/stories/{story_id}     # Update story (phase, route, etc.)
DELETE /api/stories/{story_id}  # Delete story
```

**Step 5.2: Story State Management**
- Return `current_phase`, `age_range`, `route_type` in story details
- Allow frontend to query story state instead of tracking locally
- Implement phase transitions via PUT endpoint

**Step 5.3: Message History Endpoint**
```python
GET /api/stories/{story_id}/messages  # Fetch conversation history
```

**Success Criteria:**
- Frontend can create/list/view stories
- Story state (phase, age, route) comes from backend
- Message history accessible per story
- Tests for story CRUD passing

---

### 🎨 Phase 6: Frontend Integration (Revised)
**Status:** PENDING
**Dependencies:** Phase 4 (Auth) + Phase 5 (Story API)

**Goal:** Migrate frontend from stateless to stateful architecture.

**Step 6.1: Setup TanStack Query Provider**
```jsx
// frontend/src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient()

<QueryClientProvider client={queryClient}>
  <App />
</QueryClientProvider>
```

**Step 6.2: Create Data Hooks**
```javascript
// frontend/src/hooks/useAuth.ts
export const useAuth = () => {
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => api.get('/api/auth/me')
  })
}

// frontend/src/hooks/useStories.ts
export const useStories = () => {
  return useQuery({
    queryKey: ['stories'],
    queryFn: () => api.get('/api/stories/')
  })
}

export const useStory = (storyId: number) => {
  return useQuery({
    queryKey: ['stories', storyId],
    queryFn: () => api.get(`/api/stories/${storyId}`)
  })
}

// frontend/src/hooks/useChat.ts
export const useChatMessages = (storyId: number) => {
  return useQuery({
    queryKey: ['stories', storyId, 'messages'],
    queryFn: () => api.get(`/api/stories/${storyId}/messages`)
  })
}

export const useSendMessage = (storyId: number) => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (message: string) => 
      api.post(`/api/interview/${storyId}`, { message }),
    onSuccess: () => {
      queryClient.invalidateQueries(['stories', storyId, 'messages'])
      queryClient.invalidateQueries(['stories', storyId])
    }
  })
}
```

**Step 6.3: Refactor App.jsx**
- ❌ Remove: `useState([messages])` (local state)
- ❌ Remove: `useState(currentPhase)` (fetch from story)
- ❌ Remove: `useState(ageRange)` (fetch from story)
- ✅ Add: `const { data: story } = useStory(storyId)`
- ✅ Add: `const { data: messages } = useChatMessages(storyId)`
- ✅ Add: `const sendMessage = useSendMessage(storyId)`

**Step 6.4: Update API Base URL**
```javascript
// frontend/src/lib/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

**Success Criteria:**
- Frontend fetches story state from backend
- Message history loaded from database
- New messages persisted via API
- Phase transitions reflected in story state
- No more local useState for chat/phase/age

---

### 🚀 Phase 7: Production Deployment
**Status:** PENDING
**Dependencies:** Phase 6 (Frontend Integration)

**Goal:** Deploy to production.

**Backend Deployment:**
1. Build production Docker image
2. Push to DigitalOcean Container Registry
3. Deploy to App Platform or Droplet
4. Configure production environment variables

**Frontend Deployment:**
1. Set `VITE_API_URL` to production backend URL
2. Build optimized production bundle
3. Deploy to Vercel/Netlify
4. Test end-to-end flow

**Success Criteria:**
- Backend accessible at production URL
- Frontend connects to production backend
- Database migrations applied
- SSL/HTTPS configured
- Monitoring and logging enabled

---

## 📊 Architecture Summary

### Current State (Phase 3 Complete)
```
┌─────────────────┐
│   Frontend      │ ← Stateless (local state)
│   (React)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │ ← Stateful (PostgreSQL)
│   Backend       │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ Postgres│ │ Gemini │
│   DB    │ │  API   │
└─────────┘ └────────┘
```

### Target State (Phase 6 Complete)
```
┌─────────────────┐
│   Frontend      │ ← Stateful (TanStack Query)
│   (React)       │    Fetches story/messages from backend
└────────┬────────┘
         │
         ▼ (REST API)
┌─────────────────┐
│   FastAPI       │ ← Stateful + Authenticated
│   Backend       │    User sessions, story ownership
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ Postgres│ │ Gemini │
│   DB    │ │  API   │
└─────────┘ └────────┘
```

---

## 🔧 Troubleshooting

### Docker Container Metadata Error
**Symptom:** `KeyError: 'ContainerConfig'`

**Solution:**
```bash
docker compose down
docker system prune -f
docker compose up --build
```

### Migration Conflicts
**Symptom:** Alembic detects changes in models

**Solution:**
```bash
alembic revision --autogenerate -m "Fix conflicts"
alembic upgrade head
```

### Port Already in Use
**Symptom:** `Address already in use: 8000`

**Solution:**
```bash
lsof -ti:8000 | xargs kill -9
docker compose up
```

---

## 📖 Next Immediate Action

**START WITH: Phase 4 (User Authentication)**

This is the critical missing piece that blocks frontend integration. Once users can authenticate and own stories, Phase 5 (Story Management API) becomes straightforward, which then enables Phase 6 (Frontend Integration).

**Revised Order:**
1. ✅ Phase 0-3: Infrastructure + Backend Logic (DONE)
2. 🚧 Phase 4: User Auth (NEXT)
3. 🚧 Phase 5: Story Management API
4. 🚧 Phase 6: Frontend Integration (with TanStack Query)
5. 🚧 Phase 7: Production Deployment
