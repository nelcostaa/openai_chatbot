# Life Story Game - Frontend

This is the Life Story Game frontend built with React, Vite, and TailwindCSS, originally developed in Lovable.

## Features

- React 18 with Vite for fast development
- TailwindCSS + shadcn/ui component library
- Story interview interface with phases and chapters
- Age selection cards
- Chapter summaries and timeline tracking

## Development Setup

### Prerequisites

- Node.js 18+
- npm or bun

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

### Running Locally

```bash
# Install dependencies
npm install

# Start development server (runs on port 8080)
npm run dev
```

The frontend will be available at `http://localhost:8080`

### Running with Docker

From the project root:

```bash
# Start both frontend and backend
docker-compose up

# Or just frontend
docker-compose up frontend
```

## API Integration

The frontend communicates with the FastAPI backend via REST API. See `src/lib/api.js` for available endpoints.

### Feature Status

✅ **Working:**
- Frontend UI and navigation
- Basic message GET/POST to `/api/messages/`
- Health check endpoint
- Chat interface components

⚠️ **Frontend Ready, Backend Missing:**
- User authentication/registration
- Story creation and management
- Chapter tracking
- Phase progression logic
- Age selection persistence
- Story history/retrieval

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx              # Main application component
│   ├── main.jsx             # Application entry point
│   ├── lib/
│   │   └── api.js           # API service layer
│   ├── components/          # React components
│   ├── pages/               # Page components
│   └── assets/              # Static assets
├── public/                  # Public static files
├── package.json             # Dependencies
└── vite.config.ts           # Vite configuration
```

## Backend Integration Requirements

The following backend features need to be implemented for full functionality:

### 1. Authentication System
- User registration endpoint
- Login/logout endpoints
- JWT token handling
- Session management

### 2. Story Management API
- POST `/api/stories/` - Create story
- GET `/api/stories/` - List user stories
- GET `/api/stories/{id}` - Get story details
- PUT `/api/stories/{id}` - Update story
- DELETE `/api/stories/{id}` - Delete story

### 3. Chapter System
- POST `/api/chapters/` - Create chapter
- GET `/api/chapters/?story_id={id}` - List story chapters
- PUT `/api/chapters/{id}` - Update chapter

### 4. Phase Logic
- Phase progression tracking
- Age-based transitions
- State persistence

## Development Notes

- Frontend runs standalone for UI development
- Mock responses provided for unimplemented endpoints
- Check browser console for backend integration warnings
- API errors are logged for debugging

## Building for Production

```bash
npm run build
```

Built files will be in `dist/` directory.

## Original Lovable Project

This frontend was originally developed in Lovable. See `README.lovable.md` for Lovable-specific documentation.

**Lovable Project URL**: https://lovable.dev/projects/4f796862-6d26-4e37-8dfc-1682828add2e
