import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Database
from app.routes import auth, interview, dashboard

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    Database.connect_db()
    yield
    # Shutdown: Close MongoDB Connection
    Database.disconnect_db()

app = FastAPI(
    title="InterviewFroge",
    description="AI-first Interview Preparation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware (signed cookies for authentication)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="interview_froge_session",
    max_age=3600 * 24 * 7,  # 7 days
    same_site="lax"
)

# Include API Routers
app.include_router(auth.router)
app.include_router(interview.router)
app.include_router(dashboard.router)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        # Temporary placeholder if index.html is still missing during start
        return {"message": "Welcome to InterviewFroge API. Frontend is being built."}
    return FileResponse(index_path)

@app.get("/{catchall:path}")
async def serve_spa(catchall: str):
    # If request is an API request, let it raise 404 instead of returning index.html
    if catchall.startswith("api/") or catchall.startswith("api"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # If request looks like a file with extension (e.g. logo.png), let it raise 404
    if "." in catchall:
        raise HTTPException(status_code=404, detail="File not found")
        
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "SPA Index file not found"}
