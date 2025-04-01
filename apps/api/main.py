import json
import os
import sys

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add API directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Create upload directories
from config import settings

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PDF_TEMP_DIR, exist_ok=True)

# Import routers
from routers.auth import router as auth_router
from routers.conversation import router as conversation_router
from routers.pdf import router as pdf_router

# from routers.user import router as user_router
# from routers.ai import router as ai_router

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="API for MediaWhisperer",
    docs_url=f"{settings.API_PREFIX}/docs",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth_router,
    prefix=f"{settings.API_PREFIX}/auth",
    tags=["Authentication"],
)
app.include_router(
    pdf_router,
    prefix=f"{settings.API_PREFIX}/pdf",
    tags=["PDF Management"],
)
app.include_router(
    conversation_router,
    prefix=f"{settings.API_PREFIX}/conversation",
    tags=["Conversations"],
)
# app.include_router(
#     user_router,
#     prefix=f"{settings.API_PREFIX}/user",
#     tags=["User Management"],
# )
# app.include_router(
#     ai_router,
#     prefix=f"{settings.API_PREFIX}/ai",
#     tags=["AI Interactions"],
# )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to MediaWhisperer API"}


# Health check endpoint
@app.get(f"{settings.API_PREFIX}/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
