from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from .routes import router

app = FastAPI(
    title="Project A.E.G.I.S. API",
    description="Enterprise API for Digital Forensics",
    version="2.0.0"
)

# Configure CORS for React frontend (Vite default port is 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint confirming API status and linking to documentation."""
    return JSONResponse(content={
        "status": "online",
        "system": "Project A.E.G.I.S. API Server",
        "version": "2.0.0",
        "message": "Backend API is running successfully.",
        "docs": "/docs",
        "health": "/api/health"
    })

@app.get("/health")
async def root_health():
    """Redirect root /health to /api/health."""
    return RedirectResponse(url="/api/health")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
