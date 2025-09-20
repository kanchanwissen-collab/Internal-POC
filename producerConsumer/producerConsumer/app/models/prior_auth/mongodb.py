"""
MongoDB models for Outbox Pattern implementation
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMMITTED = "committed"
    FAILED = "failed"


class ItemStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class BatchMetadataDocument(BaseModel):
    """MongoDB document for batch metadata"""
    batch_id: str = Field(..., description="Unique 16-digit batch identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    total_items: int = Field(..., ge=0)
    vendor_counts: Dict[str, int] = Field(default_factory=dict)
    status: BatchStatus = Field(default=BatchStatus.PENDING)
    processing_time_ms: Optional[float] = None
    committed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    # Add batch ordering for sequential processing
    batch_sequence: int = Field(..., description="Sequential order for batch processing")
    
    class Config:
        collection_name = "batches"


class BatchItemDocument(BaseModel):
    """MongoDB document for individual batch items"""
    item_id: str = Field(..., description="Unique identifier for this item")
    batch_id: str = Field(..., description="Reference to parent batch")
    request_id: str = Field(..., description="Original request ID from JSON payload")
    request_data: Dict[str, Any] = Field(..., description="Full JSON payload")
    vendor_name: str = Field(..., description="Vendor name extracted from request")
    status: ItemStatus = Field(default=ItemStatus.PENDING)
    sent: bool = Field(default=False)
    publish_id: Optional[str] = Field(None, description="Pub/Sub message ID when published")
    created_at: datetime = Field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    retry_count: int = Field(default=0)
    error_message: Optional[str] = None
    # Add item ordering within batch for sequential processing
    item_sequence: int = Field(..., description="Sequential order within batch")
    
    class Config:
        collection_name = "batch_items"


class OutboxEvent(BaseModel):
    """Outbox event for publishing"""
    event_id: str
    batch_id: str
    item_id: str
    event_type: str = "batch_item_created"
    payload: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    published: bool = False
    publish_id: Optional[str] = None
    published_at: Optional[datetime] = None


class BatchProcessingResult(BaseModel):
    """Result of batch processing operation"""
    batch_id: str
    total_items: int
    vendor_counts: Dict[str, int]
    processing_time_ms: float
    created_at: datetime
    status: BatchStatus
