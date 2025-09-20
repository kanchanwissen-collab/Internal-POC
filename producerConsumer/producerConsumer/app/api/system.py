"""
Health check and system endpoints
"""
from fastapi import APIRouter, status
from datetime import datetime

from app.models import APIResponse

router = APIRouter(tags=["System"])



@router.get("/health", response_model=APIResponse)
async def health_check() -> APIResponse:
    """
    Health check endpoint
    """
    
    return APIResponse(
        status="success",
        message="Service is healthy",
        data={
            "timestamp": datetime.now().isoformat(),
            "service_status": "healthy",
            "uptime": "Available via /metrics endpoint"  # Could implement actual uptime tracking
        }
    )

