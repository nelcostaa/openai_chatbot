from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.endpoints import messages

app = FastAPI(title="Life Story Game API")

# Configure CORS for Vercel Frontend
origins = [
    "http://localhost:5173",  # Local Vite
    "https://your-vercel-app.vercel.app",  # Vercel Prod
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Life Story Game API"}
