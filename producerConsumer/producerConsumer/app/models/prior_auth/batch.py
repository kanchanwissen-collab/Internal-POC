"""
Pydantic models for batch processing
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ProcedureCode(BaseModel):
    """Procedure code model"""
    code: str
    unit: str
    modifiercode: str
    diagnosiscode: str


class OtherField(BaseModel):
    """Other field model for additional data"""
    other_que: str
    other_ans: str


class TaskAssignmentDocument(BaseModel):
    """Task assignment document model"""
    name: str
    assignedto: str


class TaskAssignment(BaseModel):
    """Task assignment model"""
    document1: TaskAssignmentDocument



# Parent class for vendor requests
from typing import Literal, Annotated, Union

class VendorRequestBase(BaseModel):
    vendorname: str
    # Add any truly common fields here if needed

# Import the only child class for now
from app.models.prior_auth.evicore_request import EvicoreRequest
from app.models.prior_auth.cohere_request import CohereRequest
# Discriminated union for vendor requests
VendorRequest = Annotated[
    Union[EvicoreRequest,CohereRequest],
    Field(discriminator="vendorname")
]


class BatchMetadata(BaseModel):
    """Metadata for processed batches"""
    batch_id: str = Field(..., description="Unique 16-digit batch identifier")
    timestamp: str = Field(..., description="ISO timestamp when batch was processed")
    total_requests: int = Field(..., ge=0, description="Total number of requests in the batch")
    vendor_counts: Dict[str, int] = Field(..., description="Count of requests per vendor")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class BatchRequest(BaseModel):
    response: List[VendorRequest]
    

class ProcessedBatch(BaseModel):
    """Complete processed batch with metadata and original data"""
    metadata: BatchMetadata
    original_data: BatchRequest


class BatchSummary(BaseModel):
    """Summary information for a processed batch"""
    batch_id: str
    timestamp: str
    total_requests: int
    vendor_counts: Dict[str, int]
    unique_vendors: int
    processing_time_ms: Optional[float] = None


class VendorStatistics(BaseModel):
    """Aggregated vendor statistics"""
    total_batches: int
    total_requests: int
    vendor_statistics: Dict[str, int]
    unique_vendors: int
    last_updated: Optional[str] = None


class APIResponse(BaseModel):
    """Standard API response format"""
    status: str = Field(..., description="Response status (success/error)")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


