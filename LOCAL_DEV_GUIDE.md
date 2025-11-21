# Local Development Guide

## Quick Start

This project has been configured for local development with two separate servers:

### 1. Start API Server (Port 5000)

```bash
cd /home/nelso/Documents/openai_chatbot
python3 dev_server.py
```

The API server will start on `http://localhost:5000` with these endpoints:
- `GET /api/health` - Health check
- `GET /api/model-status` - List available models
- `POST /api/chat` - Chat endpoint

### 2. Start Frontend Dev Server (Port 5173)

```bash
cd /home/nelso/Documents/openai_chatbot/frontend
npm run dev
```

The frontend will start on `http://localhost:5173` and automatically proxy `/api/*` requests to the backend.

### 3. Access the Application

Open your browser to: **http://localhost:5173/**

---

## Testing

### Backend Tests
```bash
cd /home/nelso/Documents/openai_chatbot
pytest tests/python/ -q
```

### Frontend Tests
```bash
cd /home/nelso/Documents/openai_chatbot/frontend
npm test -- --run
```

---

## Why Not `vercel dev`?

During testing, we discovered that `vercel dev` was configured with a custom `devCommand` in the remote project settings that only starts Vite, without properly initializing Python serverless functions. The endpoints would hang because the Python runtime wasn't being started.

**Root Cause:** The Vercel project was linked with `devCommand: "cd frontend && npm run dev"` in remote settings, causing Vercel CLI to skip its standard dev server initialization and only run the frontend.

**Solution:** Use separate local dev servers (Flask + Vite) with Vite's proxy configuration to route `/api/*` to the Flask backend. This setup:
- ✅ Works reliably for local development
- ✅ Matches production behavior (frontend → API)
- ✅ Allows debugging both frontend and backend independently
- ✅ All 45 tests passing (37 backend + 8 frontend)

---

## Environment Variables

Ensure `.env` has:
```
GEMINI_API_KEY=your_actual_key_here
```

**Note:** The key in the current `.env` was flagged as leaked by Google. You'll need to generate a new one from https://aistudio.google.com/app/apikey

---

## Deployment to Vercel

When ready to deploy:

1. Ensure `vercel.json` is minimal (no `devCommand`):
```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "pip install -r requirements.txt",
  "framework": null
}
```

2. Set environment variable in Vercel dashboard:
   - `GEMINI_API_KEY` = your production API key

3. Deploy:
```bash
git push origin main
# Then deploy via Vercel dashboard or CLI
```

Vercel will automatically:
- Build the frontend static assets
- Create serverless functions from `api/*.py`
- Route `/api/*` to Python functions
- Serve frontend from `/`

