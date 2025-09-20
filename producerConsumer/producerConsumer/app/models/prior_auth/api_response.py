from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime

class APIResponse(BaseModel):
    """Standard API response format"""
    status: str = Field(..., description="Response status (success/error)")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
