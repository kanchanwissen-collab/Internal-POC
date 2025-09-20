from pydantic import BaseModel
from typing import Dict, Optional

class VendorStatistics(BaseModel):
    """Aggregated vendor statistics"""
    total_batches: int
    total_requests: int
    vendor_statistics: Dict[str, int]
    unique_vendors: int
    last_updated: Optional[str] = None
