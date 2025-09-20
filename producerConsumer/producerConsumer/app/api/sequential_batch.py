"""
Sequential Batch Processing API endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from app.models import VendorRequest
from pydantic import BaseModel
from app.models.prior_auth.request_progress import RequestProgress, RequestStatus

from app.models.prior_auth.pubsub_batch import (
    APIResponse
)
from app.services import mongodb_service
from app.services.sequential_batch_service import sequential_batch_service
from app.core.logging import get_logger
from app.core.json_utils import convert_mongo_data

class BatchRequestWrapper(BaseModel):
    patient_records: List[VendorRequest]

class StatusUpdateRequest(BaseModel):
    request_id: str
    status: RequestStatus
    remarks: str = None




logger = get_logger(__name__)

router = APIRouter(prefix="/agentic-platform", tags=["Sequential Batch Processing"])

@router.post("/prior-auths", response_model=Dict[str, Any])
async def process_complete_batch(batch_data: BatchRequestWrapper) -> Dict[str, Any]:
    """
    Complete batch processing flow: Ingest -> Publish to Pub/Sub simulation -> Commit
    """
    try:
        if not batch_data.patient_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch cannot be empty"
            )
        result = await sequential_batch_service.process_complete_batch_flow(batch_data.patient_records)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete batch processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in complete batch processing: {str(e)}"
        )



@router.get("/prior-auths/requests")
async def get_all_requests_details():
    """
    Get all requests from requestProgress collection formatted for dashboard.
    This ensures ALL requests are returned, including those with 'created' status.
    """
    try:
        logger.info("Getting all request progress data for dashboard")
        
        # Use the new method that gets ALL requests from requestProgress
        all_requests = await mongodb_service.get_all_request_progress_for_dashboard()
        
        return {
            "status": "success",
            "message": "All requests retrieved successfully",
            "data": all_requests
        }
        
    except Exception as e:
        logger.error(f"Error getting all request progress data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting all request progress data: {str(e)}"
        )


@router.get("/prior-auths/{batch_id}", response_model=APIResponse)
async def get_batch_status(batch_id: str) -> APIResponse:
    """
    Get detailed status of a batch including request counts by status
    """
    try:
        logger.info(f"Getting status for batch {batch_id}")
        
        batch_status = await sequential_batch_service.get_batch_status(batch_id)
        
        return APIResponse(
            status="success",
            message=f"Status retrieved for batch {batch_id}",
            data=batch_status.dict()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting batch {batch_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting batch status: {str(e)}"
        )


@router.put("/prior-auths/requests/{request_id}/status", response_model=Dict[str, Any])
async def update_request_status(request_id: str, status_update: StatusUpdateRequest) -> Dict[str, Any]:
    """
    Update the status of a specific request using the new RequestProgress model
    """
    try:
        logger.info(f"Updating status for request {request_id} to {status_update.status.value}")
        
        # Update using the new RequestProgress model
        await sequential_batch_service.update_request_status(
            request_id=request_id,
            status=status_update.status,
            remarks=status_update.remarks
        )
        
        # Get updated progress
        progress = await mongodb_service.get_request_progress(request_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        return {
            "status": "success",
            "message": f"Request {request_id} status updated to {status_update.status.value}",
            "data": progress.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating request {request_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating request status: {str(e)}"
        )


@router.get("/prior-auths/requests/{request_id}/progress", response_model=Dict[str, Any])
async def get_request_progress(request_id: str) -> Dict[str, Any]:
    """
    Get the progress details for a specific request
    """
    try:
        logger.info(f"Getting progress for request {request_id}")
        
        progress = await mongodb_service.get_request_progress(request_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        return {
            "status": "success",
            "message": f"Progress retrieved for request {request_id}",
            "data": progress.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting request {request_id} progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting request progress: {str(e)}"
        )

