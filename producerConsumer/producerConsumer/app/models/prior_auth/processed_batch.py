from pydantic import BaseModel
from app.models.prior_auth.batch_metadata import BatchMetadata
from app.models.prior_auth.batch import BatchRequest

class ProcessedBatch(BaseModel):
    """Complete processed batch with metadata and original data"""
    metadata: BatchMetadata
    original_data: BatchRequest
