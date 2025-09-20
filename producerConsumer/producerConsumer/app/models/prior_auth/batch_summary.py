from pydantic import BaseModel
from typing import Dict, Optional

class BatchSummary(BaseModel):
    """Summary information for a processed batch"""
    batch_id: str
    timestamp: str
    total_requests: int
    vendor_counts: Dict[str, int]
    unique_vendors: int
    processing_time_ms: Optional[float] = None
