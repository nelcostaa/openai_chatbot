from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Life Story Game API"}
