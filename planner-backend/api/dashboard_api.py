from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from db.config.connection import get_db
from db.models.dbmodels.utility.httpResponseEnum import HttpResponseEnum

router = APIRouter()

def map_status_for_frontend(db_status: str) -> str:
    """
    Map database status values to frontend-friendly status names
    """
    status_mapping = {
        "in_progress": "running",
        "failed": "failed", 
        "created": "queued",
        "user_action_required": "manual-action",  # Changed to match frontend expectation
        "completed": "completed",
        "succeeded": "completed",
        "processing": "running",
        "action_needed": "manual-action"  # Changed to match frontend expectation
    }
    return status_mapping.get(db_status.lower(), db_status)

class DashboardStats(BaseModel):
    total_requests: int = Field(..., description="Total number of preauth requests")
    pending_requests: int = Field(..., description="Number of pending requests")
    completed_requests: int = Field(..., description="Number of completed requests")
    failed_requests: int = Field(..., description="Number of failed requests")
    user_action_required: int = Field(..., description="Number of requests requiring user action")
    success_rate: float = Field(..., description="Success rate percentage")

class RequestSummary(BaseModel):
    request_id: str
    batch_id: Optional[str] = None
    patient_name: str
    payer_id: str
    status: str
    created_at: datetime
    last_updated: datetime
    current_step: Optional[str] = None
    user_actions_pending: int = 0

class UserActionSummary(BaseModel):
    action_id: str
    request_id: str
    patient_name: str
    action_type: str
    action_status: str
    requested_at: datetime
    metadata: Optional[str] = None

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    days: int = Query(7, description="Number of days to look back for stats")
) -> DashboardStats:
    """
    Get dashboard statistics for the specified time period
    """
    db = get_db()
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all requests in the time period
        requests_cursor = db["requestProgress"].find({
            "lastUpdatedAt": {"$gte": start_date, "$lte": end_date}
        })
        requests = await requests_cursor.to_list(None)
        
        total_requests = len(requests)
        
        # Count by status (using mapped frontend statuses)
        frontend_status_counts = {}
        for request in requests:
            db_status = request.get("status", "UNKNOWN")
            frontend_status = map_status_for_frontend(db_status)
            frontend_status_counts[frontend_status] = frontend_status_counts.get(frontend_status, 0) + 1
        
        # Map to dashboard stats using frontend status names
        pending_requests = frontend_status_counts.get("running", 0) + frontend_status_counts.get("queued", 0)
        completed_requests = frontend_status_counts.get("completed", 0)
        failed_requests = frontend_status_counts.get("failed", 0)
        user_action_required = frontend_status_counts.get("manual-action", 0)
        
        # Calculate success rate
        success_rate = 0.0
        if total_requests > 0:
            success_rate = (completed_requests / total_requests) * 100
        
        return DashboardStats(
            total_requests=total_requests,
            pending_requests=pending_requests,
            completed_requests=completed_requests,
            failed_requests=failed_requests,
            user_action_required=user_action_required,
            success_rate=round(success_rate, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/requests")
async def get_recent_requests(
    limit: int = Query(20, description="Number of requests to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID")
) -> List[RequestSummary]:
    """
    Get recent preauth requests with summary information
    """  
    db = get_db()
    
    try:
        # Build query filter
        query_filter = {}
        if status:
            query_filter["status"] = status
        
        # Get request progress data
        progress_cursor = db["requestProgress"].find(query_filter).sort([("lastUpdatedAt", -1)]).limit(limit)
        progress_data = await progress_cursor.to_list(None)
        
        results = []
        for progress in progress_data:
            request_id = progress["requestId"]
            
            # Get original request details (optional - may not exist for all requests)
            original_request = await db["priorAuthRequest"].find_one({"requestId": request_id})
            
            # Filter by user_id if specified (only if original_request exists)
            if user_id and original_request and original_request.get("userId") != user_id:
                continue
            
            # Try to get details from batch_requests collection if priorAuthRequest doesn't exist
            batch_request = None
            if not original_request:
                batch_request = await db["batch_requests"].find_one({"request_id": request_id})
            
            # Count pending user actions
            user_actions_count = await db["priorAuthUserAction"].count_documents({
                "requestId": request_id,
                "actionStatus": "PENDING"
            })
            
            # Use data from whichever source is available
            if original_request:
                patient_name = original_request.get("patientName", "Unknown")
                payer_id = original_request.get("payerId", "Unknown")
                created_at = original_request.get("createdAt") or progress.get("lastUpdatedAt")
                batch_id = original_request.get("batchId")  # Check if priorAuthRequest has batch_id
            elif batch_request:
                patient_name = batch_request.get("patient_name", "Unknown")
                payer_id = batch_request.get("vendor", "Unknown")
                created_at = batch_request.get("created_at") or progress.get("lastUpdatedAt")
                batch_id = batch_request.get("batch_id")  # Get batch_id from batch_requests
            else:
                patient_name = "Unknown"
                payer_id = "Unknown"
                created_at = progress.get("lastUpdatedAt")  # fallback to progress timestamp
                batch_id = None
            
            # If we still don't have batch_id, try to find it from batch_requests collection
            if not batch_id and not batch_request:
                batch_request = await db["batch_requests"].find_one({"request_id": request_id})
                if batch_request:
                    batch_id = batch_request.get("batch_id")
            
            # Ensure created_at is never None
            if created_at is None:
                created_at = progress.get("lastUpdatedAt")
            
            # Map status to frontend-friendly name
            frontend_status = map_status_for_frontend(progress.get("status", "UNKNOWN"))
            
            results.append(RequestSummary(
                request_id=request_id,
                batch_id=batch_id,
                patient_name=patient_name,
                payer_id=payer_id,
                status=frontend_status,
                created_at=created_at,
                last_updated=progress.get("lastUpdatedAt"),
                current_step=progress.get("workflowStep"),
                user_actions_pending=user_actions_count
            ))
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/user-actions")
async def get_pending_user_actions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(10, description="Number of actions to return")
) -> List[UserActionSummary]:
    """
    Get pending user actions that require attention
    """  
    db = get_db()
    
    try:
        # Build query filter
        query_filter = {"actionStatus": "PENDING"}
        if user_id:
            query_filter["userId"] = user_id
        
        # Get pending user actions
        actions_cursor = db["priorAuthUserAction"].find(query_filter).sort([("requestedAt", -1)]).limit(limit)
        actions = await actions_cursor.to_list(None)
        
        results = []
        for action in actions:
            request_id = action["requestId"]
            
            # Get patient name from original request
            original_request = await db["priorAuthRequest"].find_one({"requestId": request_id})
            patient_name = original_request.get("patientName", "Unknown") if original_request else "Unknown"
            
            results.append(UserActionSummary(
                action_id=action["id"],
                request_id=request_id,
                patient_name=patient_name,
                action_type=action["actionType"],
                action_status=action["actionStatus"],
                requested_at=action["requestedAt"],
                metadata=action.get("metadata")
            ))
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/request-details/{request_id}")
async def get_request_details(request_id: str):
    """
    Get detailed information about a specific request
    """    
    db = get_db()
    
    try:
        # Get request progress
        progress = await db["requestProgress"].find_one({"requestId": request_id})
        if not progress:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Get original request
        original_request = await db["priorAuthRequest"].find_one({"requestId": request_id})
        
        # If no priorAuthRequest, try to get from batch_requests
        batch_request = None
        if not original_request:
            batch_request = await db["batch_requests"].find_one({"request_id": request_id})
        
        # Get all user actions
        user_actions_cursor = db["priorAuthUserAction"].find({"requestId": request_id}).sort([("requestedAt", 1)])
        user_actions = await user_actions_cursor.to_list(None)
        
        # Get conversation history if it exists
        conversation_history = await db.conversationHistory.find({"requestId": request_id}).to_list(None)
        
        return {
            "request_id": request_id,
            "progress": progress,
            "original_request": original_request,
            "batch_request": batch_request,  # Include batch request data if available
            "user_actions": user_actions,
            "conversation_history": conversation_history,
            "timeline": await build_request_timeline(db, request_id),
            "http_status": HttpResponseEnum.OK
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def build_request_timeline(db, request_id: str) -> List[Dict[str, Any]]:
    """
    Build a timeline of events for a request
    """
    timeline = []
    
    # Add original request creation
    original_request = await db["priorAuthRequest"].find_one({"requestId": request_id})
    if original_request and original_request.get("createdAt"):
        timeline.append({
            "timestamp": original_request["createdAt"],
            "event": "REQUEST_CREATED",
            "description": f"Preauth request created for patient {original_request.get('patientName')}",
            "details": {"payer_id": original_request.get("payerId")}
        })
    else:
        # Check batch_requests collection if priorAuthRequest doesn't exist
        batch_request = await db["batch_requests"].find_one({"request_id": request_id})
        if batch_request and batch_request.get("created_at"):
            timeline.append({
                "timestamp": batch_request.get("created_at"),
                "event": "REQUEST_CREATED",
                "description": f"Batch request created for patient {batch_request.get('patient_name', 'Unknown')}",
                "details": {"payer_id": batch_request.get("vendor", "Unknown")}
            })
    
    # Add progress updates (we could store these separately for better timeline)
    progress = await db["requestProgress"].find_one({"requestId": request_id})
    if progress:
        timeline.append({
            "timestamp": progress["lastUpdatedAt"],
            "event": "STATUS_UPDATE",
            "description": progress.get("remarks", "Status updated"),
            "details": {"status": progress.get("status")}
        })
    
    # Add user actions
    user_actions_cursor = db["priorAuthUserAction"].find({"requestId": request_id}).sort([("requestedAt", 1)])
    user_actions = await user_actions_cursor.to_list(None)
    
    for action in user_actions:
        timeline.append({
            "timestamp": action["requestedAt"],
            "event": "USER_ACTION",
            "description": f"User action required: {action['actionType']}",
            "details": {
                "action_type": action["actionType"],
                "status": action["actionStatus"],
                "metadata": action.get("metadata")
            }
        })
    
    # Sort timeline by timestamp, handling None values
    timeline.sort(key=lambda x: x["timestamp"] if x["timestamp"] is not None else datetime.min)
    
    return timeline

@router.get("/dashboard/payer-stats")
async def get_payer_statistics(
    days: int = Query(30, description="Number of days to look back")
):
    """
    Get statistics grouped by payer
    """ 
    db = get_db()
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Aggregate requests by payer
        pipeline = [
            {
                "$match": {
                    "createdAt": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$payerId",
                    "total_requests": {"$sum": 1},
                    "requests": {"$push": "$requestId"}
                }
            }
        ]
        
        payer_groups = await db["priorAuthRequest"].aggregate(pipeline).to_list(None)
        
        # Get status information for each payer's requests
        payer_stats = []
        for group in payer_groups:
            payer_id = group["_id"]
            request_ids = group["requests"]
            
            # Get status counts for this payer's requests (using frontend statuses)
            frontend_status_counts = {}
            for request_id in request_ids:
                progress = await db["requestProgress"].find_one({"requestId": request_id})
                if progress:
                    db_status = progress.get("status", "UNKNOWN")
                    frontend_status = map_status_for_frontend(db_status)
                    frontend_status_counts[frontend_status] = frontend_status_counts.get(frontend_status, 0) + 1
            
            # Calculate success rate using frontend status
            completed = frontend_status_counts.get("completed", 0)
            total = group["total_requests"]
            success_rate = (completed / total * 100) if total > 0 else 0
            
            payer_stats.append({
                "payer_id": payer_id,
                "total_requests": total,
                "completed_requests": completed,
                "failed_requests": frontend_status_counts.get("failed", 0),
                "pending_requests": frontend_status_counts.get("running", 0) + frontend_status_counts.get("queued", 0),
                "user_action_required": frontend_status_counts.get("manual-action", 0),
                "success_rate": round(success_rate, 2)
            })
        
        return {
            "payer_statistics": payer_stats,
            "period_days": days,
            "http_status": HttpResponseEnum.OK
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dashboard/mark-action-completed/{action_id}")
async def mark_user_action_completed(action_id: str, response_data: Dict[str, Any]):
    """
    Mark a user action as completed from the dashboard
    """  
    db = get_db()
    
    try:
        # Update the user action
        result = await db["priorAuthUserAction"].update_one(
            {"id": action_id},
            {
                "$set": {
                    "actionStatus": "COMPLETED",
                    "actionedAt": datetime.now(),
                    "metadata": response_data.get("metadata", "")
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User action not found")
        
        return {
            "success": True,
            "message": "User action marked as completed",
            "http_status": HttpResponseEnum.OK
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
