"""
Main FastAPI application with MongoDB and Batch-Aware Outbox Pattern
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api import api_router
from app.services.mongodb_service import mongodb_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    setup_logging()
    logger = get_logger(__name__)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Connect to MongoDB
    await mongodb_service.connect()
    
    # Initialize and start batch-aware outbox processor if enabled
    
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Stop sequential batch consumer service
    
    
    # Stop batch-aware outbox processor
    
    # Disconnect from MongoDB
    await mongodb_service.disconnect()
    
    logger.info(f"Shutdown complete for {settings.app_name}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A production-ready FastAPI server implementing producer-consumer pattern for batch JSON processing",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
        ],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    
    return app


# Create the app instance
app = create_app()
