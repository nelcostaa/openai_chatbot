from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.endpoints import auth, interview, messages, snippets, stories

app = FastAPI(title="Life Story Game API")

# Configure CORS for Frontend
origins = [
    "http://localhost:5173",  # Local Vite (default)
    "http://localhost:8080",  # Local Vite (Docker)
    "http://localhost:3000",  # Alternative dev server
    "https://openai-chatbot-eight.vercel.app",  # Vercel Production
    "https://recollectlife.vercel.app",  # Future custom domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(stories.router, prefix="/api/stories", tags=["stories"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
app.include_router(snippets.router, prefix="/api/snippets", tags=["snippets"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Life Story Game API"}
