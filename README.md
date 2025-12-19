# Life Story Game – AI Interviewer

An AI-powered interviewer that transforms personal life stories into meaningful board game narratives. Built with React, Vite, Tailwind CSS (frontend) and FastAPI + LangGraph + Google Gemini (backend).

The AI conducts a compassionate chronological interview adapted to the user's age, exploring life phases from family history through childhood, adolescence, adulthood, and present day, then synthesizes a structured narrative with title, chapters, and key moments.

## 🚀 Tech Stack

- **Frontend**: React 19, Vite 7, Tailwind CSS 4, TanStack Query, Zustand
- **Backend**: FastAPI, Python 3.13, LangGraph Agent
- **AI Model**: Google Gemini (fallback cascade: 2.5-flash → 2.0-flash → lite variants)
- **Database**: PostgreSQL with SQLAlchemy ORM, Alembic migrations
- **Architecture**: Clean Architecture (Domain → Application → Infrastructure → Interface)
- **Testing**: Pytest (100+ tests), Playwright E2E
- **Deployment**: Render (backend), Vercel (frontend)

## 📋 Features

- 🎭 **Age-Aware Interview**: Phases adapt based on user's age range (under 18, 18-30, 31-45, 46-65, 65+)
- 📖 **Chronological Journey**: GREETING → AGE_SELECTION → FAMILY_HISTORY → CHILDHOOD → ADOLESCENCE → EARLY_ADULTHOOD → MIDLIFE → PRESENT → SYNTHESIS
- 🏷️ **Theme Tracking**: Select story themes (family, career, love, etc.) and track which have been addressed
- ✨ **AI Fallback Cascade**: Automatic retry across Gemini models on rate limits
- 🔐 **Authentication**: JWT-based auth with secure password hashing
- 💾 **Story Persistence**: Save and continue interviews across sessions
- 📝 **Snippets**: Save important moments from conversations
- 💬 **Context-Aware**: Full conversation history with AI context management
- 🎨 **Modern UI**: Dark mode chat interface with phase timeline and theme tags
- ⚡ **Fast**: Async FastAPI with connection pooling
- 🛡️ **Production-Ready**: Input validation, error handling, comprehensive tests

## 📁 Project Structure

```
/
├── backend/                      # FastAPI backend (Clean Architecture)
│   ├── app/                      # Interface Layer (FastAPI)
│   │   ├── main.py               # FastAPI application entry point
│   │   ├── api/endpoints/        # API route handlers (thin controllers)
│   │   ├── core/                 # Auth, security, agent configuration
│   │   ├── db/                   # Database session management
│   │   ├── models/               # SQLAlchemy ORM models
│   │   └── services/             # Interview service orchestration
│   │
│   ├── domain/                   # Domain Layer (Business Logic)
│   │   ├── entities/             # Domain entities (User, Story, Message, Snippet)
│   │   ├── exceptions.py         # Domain-specific exceptions
│   │   └── services/             # Domain services (PhaseService)
│   │
│   ├── application/              # Application Layer (Use Cases)
│   │   ├── interfaces/           # Repository & service abstractions
│   │   └── use_cases/            # Business use cases (auth, interview, story)
│   │
│   └── infrastructure/           # Infrastructure Layer (Implementations)
│       ├── persistence/          # SQLAlchemy repository implementations
│       ├── services/             # External service adapters (AI, Auth)
│       └── container.py          # Dependency injection container
│
├── frontend/                     # React + Vite frontend
│   ├── src/
│   │   ├── App.tsx               # Main application component
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/                # Page components
│   │   ├── hooks/                # Custom React hooks
│   │   ├── stores/               # Zustand state management
│   │   └── lib/                  # Utilities and API client
│   ├── vite.config.ts            # Build config
│   └── package.json              # Frontend dependencies
│
├── alembic/                      # Database migrations
│   └── versions/                 # Migration scripts
│
├── tests/
│   ├── python/                   # Backend unit tests (100+ tests)
│   └── e2e/                      # Playwright E2E tests
│
├── docs/                         # Documentation
│   ├── backend_structure.md      # Backend architecture guide
│   ├── master_execution_plan.md  # Migration roadmap
│   └── DATABASE_SCHEMA_GUIDELINE.md
│
├── scripts/                      # Utility scripts
├── docker-compose.yml            # Local development with Docker
├── Dockerfile                    # Container build
├── render.yaml                   # Render deployment config
└── requirements.txt              # Python dependencies
```

## 🏗️ Clean Architecture

The backend follows Clean Architecture principles with clear layer separation:

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Layer                          │
│     (FastAPI routes, Pydantic schemas, HTTP handling)       │
├─────────────────────────────────────────────────────────────┤
│                   Application Layer                         │
│         (Use Cases, DTOs, Interface definitions)            │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                            │
│      (Entities, Value Objects, Domain Services)             │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                       │
│    (SQLAlchemy repos, LangGraph AI, JWT auth services)      │
└─────────────────────────────────────────────────────────────┘
```

**Dependency Rule**: Inner layers never depend on outer layers. Dependencies point inward.

### Key Patterns

- **A/C Hybrid DI**: Manual constructor injection + FastAPI's `Depends()` for flexibility
- **Repository Pattern**: Abstract data access behind interfaces
- **Use Case Pattern**: Business operations encapsulated in single-purpose classes
- **Entity Mapping**: Domain entities ↔ ORM models via explicit mappers

## Prerequisites

- **Node.js** 18+
- **Python** 3.11+
- **PostgreSQL** 14+
- **Docker** (optional, for local development)

## 🔧 Setup

### 1. Clone & Configure

```bash
git clone <repo-url>
cd openai_chatbot
```

Create `.env` (NEVER commit):
```bash
# AI Configuration
GEMINI_API_KEY="your_google_gemini_api_key"

# Database
DATABASE_URL="postgresql://user:pass@localhost:5432/lifestory"

# Auth
SECRET_KEY="your-secret-key-min-32-chars"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
```

### 2. Install Dependencies

**Backend:**
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend && npm install
```

### 3. Database Setup

```bash
# With Docker
docker-compose up -d db

# Run migrations
alembic upgrade head
```

## 🧪 Testing

**Backend:** ✅ 100+ tests
```bash
pytest tests/python/ -v
```

**Domain Tests:**
```bash
pytest tests/python/test_domain_entities.py -v
```

**E2E Tests:**
```bash
cd frontend && npx playwright test
```

## 🚀 Running Locally

**Backend:**
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend && npm run dev
# Frontend at http://localhost:5173
```

**With Docker:**
```bash
docker-compose up
# Backend at http://localhost:8000
# Frontend at http://localhost:5173
```

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| GET | `/api/auth/me` | Get current user |

### Stories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stories` | List user's stories |
| POST | `/api/stories` | Create new story |
| GET | `/api/stories/{id}` | Get story details |
| DELETE | `/api/stories/{id}` | Delete story |

### Interview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/stories/{id}/chat` | Send message to AI |
| POST | `/api/stories/{id}/advance-phase` | Move to next phase |

### Snippets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stories/{id}/snippets` | List story snippets |
| POST | `/api/stories/{id}/snippets` | Create snippet |
| PATCH | `/api/snippets/{id}` | Update snippet |
| DELETE | `/api/snippets/{id}` | Delete snippet |

## 🚢 Deployment

### Backend (Render)

1. Connect GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy from `render.yaml` configuration

### Frontend (Vercel)

1. Connect GitHub repository to Vercel
2. Set `VITE_API_URL` environment variable
3. Deploy (auto-deploys on push to `main`)

## 🔒 Security

- ✅ JWT authentication with secure token handling
- ✅ Password hashing with bcrypt
- ✅ API keys server-side only
- ✅ Input validation on all endpoints
- ✅ CORS configuration for production
- ✅ SQL injection prevention via SQLAlchemy ORM

## 📦 Key Dependencies

**Backend:**
- FastAPI, SQLAlchemy, Alembic
- LangGraph, google-generativeai
- python-jose, passlib, bcrypt
- pytest, httpx

**Frontend:**
- React 19, TypeScript
- TanStack Query, Zustand
- Tailwind CSS, Radix UI
- Vite, Playwright

## 🤝 Contributing

Focus areas:
- Use case implementation
- Test coverage expansion
- UI/UX improvements
- Documentation

## 📝 License

MIT License

## 🔗 Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Google AI Studio](https://aistudio.google.com/)

---

**Built with ❤️ for preserving life stories through AI**
