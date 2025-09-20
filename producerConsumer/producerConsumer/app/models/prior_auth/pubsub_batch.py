"""
New models for sequential batch processing with Pub/Sub simulation
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class BatchStatus(str, Enum):
    """Batch processing status"""
    PENDING = "PENDING"
    COMMITTED = "COMMITTED" 
    FAILED = "FAILED"


class RequestStatus(str, Enum):
    """Individual request processing status"""
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class BatchMetadata(BaseModel):
    """Batch metadata table model"""
    batch_id: str = Field(..., description="Sequential batch ID (auto-increment)")
    created_at: datetime = Field(default_factory=datetime.now)
    status: BatchStatus = Field(default=BatchStatus.PENDING)
    request_count: int = Field(..., ge=0, description="Number of JSON requests in the batch")
    vendor_counts: Dict[str, int] = Field(default_factory=dict, description="Count by vendor")
    
    class Config:
        # MongoDB collection name
        collection_name = "batch_metadata"


class BatchRequest(BaseModel):
    """Individual request in the batch"""
    batch_id: str = Field(..., description="Reference to batch_metadata.batch_id")
    sequence_no: int = Field(..., description="Sequence number within the batch (1, 2, 3, ...)")
    vendor: str = Field(..., description="Vendor name")
    payload: Dict[str, Any] = Field(..., description="Original JSON request")
    status: RequestStatus = Field(default=RequestStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Pub/Sub headers (simulating Google Pub/Sub)
    pubsub_message_id: Optional[str] = None
    pubsub_attributes: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        collection_name = "batch_requests"


class PubSubMessage(BaseModel):
    """Pub/Sub message format (simulating Google Pub/Sub)"""
    message_id: str = Field(..., description="Unique message ID")
    data: Dict[str, Any] = Field(..., description="Message payload")
    attributes: Dict[str, str] = Field(default_factory=dict, description="Message attributes")
    publish_time: datetime = Field(default_factory=datetime.now)
    
    # Additional headers for our simulation
    batch_id: str
    sequence_no: int
    vendor: str


class BatchIngestRequest(BaseModel):
    """Request model for incoming batch data - matches existing format"""
    response: List[Dict[str, Any]] = Field(..., description="Array of JSON requests")


class BatchIngestResponse(BaseModel):
    """Response model for batch ingestion"""
    batch_id: str
    status: str
    message: str
    request_count: int
    vendor_counts: Dict[str, int]
    created_at: datetime


class BatchStatusResponse(BaseModel):
    """Response model for batch status queries"""
    batch_id: str
    status: str
    request_count: int
    published_count: int
    failed_count: int
    vendor_counts: Dict[str, int]
    created_at: datetime
    committed_at: Optional[datetime] = None


class ConsumerProcessingResult(BaseModel):
    """Result from consumer processing"""
    batch_id: str
    sequence_no: int
    vendor: str
    status: str
    message_id: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.now)


class APIResponse(BaseModel):
    """Standard API response format"""
    status: str
    message: str
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
