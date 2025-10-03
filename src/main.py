from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
import uvicorn

from src.core.database import get_session
from src.core.response.handlers import global_exception_handler
from src.core.config import settings

# Import routers from apps
from src.apps.blog import post_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    async with get_session() as session:
        await session.exec(select(1))
    print("✅ Database connection succecfully")
    yield
    # Shutdown: Clean up resources if needed
    print("🔄 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_INFO,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add global exception handler
app.add_exception_handler(Exception, global_exception_handler)


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with health check."""
    return {"message": "🚀 Server is running!", "status": "healthy", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Service is running normally"}


# Include app routers
# Note: These routers will be automatically imported from apps created by the CLI
app.include_router(post_router)

# You can add more routers here as you create new apps
# app.include_router(other_app_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload in development
        log_level="info",
    )
