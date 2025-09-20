"""
API routes initialization
"""
from fastapi import APIRouter
from app.api import  system, sequential_batch, sse_and_consumer

# Create main API router
api_router = APIRouter()

api_router.include_router(system.router)
api_router.include_router(sequential_batch.router)
api_router.include_router(sse_and_consumer.router)


# Include all route modules
api_router.include_router(system.router)
api_router.include_router(sequential_batch.router)
api_router.include_router(sse_and_consumer.router)
__all__ = ["api_router"]
