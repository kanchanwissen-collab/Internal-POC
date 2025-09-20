from pydantic import BaseModel, Field
from typing import Dict, Optional

class BatchMetadata(BaseModel):
    """Metadata for processed batches"""
    batch_id: str = Field(..., description="Unique 16-digit batch identifier")
    timestamp: str = Field(..., description="ISO timestamp when batch was processed")
    total_requests: int = Field(..., ge=0, description="Total number of requests in the batch")
    vendor_counts: Dict[str, int] = Field(..., description="Count of requests per vendor")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
