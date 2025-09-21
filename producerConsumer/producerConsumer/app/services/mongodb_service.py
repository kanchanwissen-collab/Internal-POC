"""
MongoDB database service for Outbox Pattern
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.core.config import settings
from app.core.logging import get_logger
from app.models.prior_auth.mongodb import (
    BatchMetadataDocument, 
    BatchItemDocument, 
    BatchStatus, 
    ItemStatus,
    BatchProcessingResult
)
from app.models.prior_auth.request_progress import (
    RequestProgress,
    RequestStatus
)
import os

logger = get_logger(__name__)

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


class MongoDBService:
    """MongoDB service for batch processing with Outbox Pattern"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.batch_metadata_collection: Optional[AsyncIOMotorCollection] = None
        self.batch_requests_collection: Optional[AsyncIOMotorCollection] = None
        self.batch_requests_status_collection: Optional[AsyncIOMotorCollection] = None
        self.batch_requests_manual_actions_collection: Optional[AsyncIOMotorCollection] = None
        self.request_progress_collection: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.mongodb_database]
            self.batch_metadata_collection = self.database["batch_metadata"]
            self.batch_requests_collection = self.database["batch_requests"]
            self.batch_requests_status_collection = self.database["batch_requests_status"]
            self.batch_requests_manual_actions_collection = self.database["batch_requests_manual_actions"]
            self.request_progress_collection = self.database["requestProgress"]
            await self._create_indexes()
            
            logger.info(f"Connected to MongoDB: {settings.mongodb_url}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create necessary indexes"""
        try:

            await self.batch_metadata_collection.create_index("batch_id", unique=True)
            await self.batch_metadata_collection.create_index("status")
            await self.batch_metadata_collection.create_index("created_at")

            #request_items
            await self.batch_requests_collection.create_index("request_id", unique=True)
            await self.batch_requests_status_collection.create_index("request_id", unique=True)
            await self.batch_requests_manual_actions_collection.create_index("request_id")
            await self.request_progress_collection.create_index("requestId", unique=True)
            await self.request_progress_collection.create_index("status")
            await self.request_progress_collection.create_index("lastUpdatedAt")
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    async def create_or_update_request_progress(self, request_id: str, status: RequestStatus, remarks: Optional[str] = None) -> RequestProgress:
        """Create or update request progress using the new RequestProgress model"""
        try:
            now = datetime.utcnow()
            progress_data = RequestProgress(
                requestId=request_id,
                status=status,
                lastUpdatedAt=now,
                remarks=remarks
            )
            
            # Use upsert to create or update
            result = await self.request_progress_collection.update_one(
                {"requestId": request_id},
                {"$set": progress_data.dict()},
                upsert=True
            )
            
            logger.info(f"Request progress {'created' if result.upserted_id else 'updated'} for request {request_id} with status {status.value}")
            return progress_data
            
        except Exception as e:
            logger.error(f"Error creating/updating request progress for {request_id}: {str(e)}")
            raise

    async def get_request_progress(self, request_id: str) -> Optional[RequestProgress]:
        """Get request progress by request ID"""
        try:
            progress_doc = await self.request_progress_collection.find_one({"requestId": request_id})
            if progress_doc:
                # Remove MongoDB's _id field
                progress_doc.pop("_id", None)
                return RequestProgress(**progress_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting request progress for {request_id}: {str(e)}")
            return None

    async def get_combined_request_data(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches combined data for a single request using a MongoDB aggregation pipeline.
        The pipeline joins batch_requests with batch_requests_status and batch_requests_manual_actions.
        """
        pipeline = [
            # Stage 1: Match the specific request_id from the batch_requests collection
            {"$match": {"request_id": request_id}},

            # Stage 2: Join with the batch_requests_status collection (one-to-one relationship)
            {"$lookup": {
                "from": self.batch_requests_status_collection.name,
                "localField": "request_id",
                "foreignField": "request_id",
                "as": "status_data"
            }},

            # Stage 3: Deconstruct the status_data array.
            {"$unwind": {
                "path": "$status_data",
                "preserveNullAndEmptyArrays": True
            }},

            # Stage 4: Join with the batch_requests_manual_actions collection (one-to-many relationship)
            {"$lookup": {
                "from": self.batch_requests_manual_actions_collection.name,
                "localField": "request_id",
                "foreignField": "request_id",
                "as": "manual_actions"
            }},

            # Stage 5: Project the final output document to be clean and readable
            {"$project": {
                "_id": 0,  # Exclude the default MongoDB ObjectId
                "request_id": "$request_id",
                "batch_id": "$batch_id",
                "sequence_no": "$sequence_no",
                "request_count": "$request_count",
                "vendor": "$vendor",
                "message_type": "$message_type",
                "status": "$status_data",  # The unwound status document
                "manual_actions": "$manual_actions"  # The array of manual actions
            }}
        ]

        # Execute the aggregation pipeline
        cursor = self.batch_requests_collection.aggregate(pipeline)

        # Return the first (and only) result from the aggregation
        combined_data = await cursor.to_list(length=1)
        if combined_data:
            return combined_data[0]
        return None


    async def get_all_combined_request_data(self) -> List[Dict[str, Any]]:
        """
        Fetches combined data for all requests using a MongoDB aggregation pipeline.
        This starts from requestProgress collection to ensure ALL requests are included,
        then LEFT JOINs with other collections.
        """
        pipeline = [
            # Stage 1: Start from requestProgress collection to get ALL requests
            {"$match": {}},  # Get all documents from requestProgress

            # Stage 2: LEFT JOIN with batch_requests collection 
            {"$lookup": {
                "from": self.batch_requests_collection.name,
                "localField": "requestId",
                "foreignField": "request_id",
                "as": "request_details"
            }},

            # Stage 3: LEFT JOIN with batch_requests_status collection (legacy)
            {"$lookup": {
                "from": self.batch_requests_status_collection.name,
                "localField": "requestId",
                "foreignField": "request_id",
                "as": "legacy_status_data"
            }},

            # Stage 4: LEFT JOIN with batch_requests_manual_actions collection
            {"$lookup": {
                "from": self.batch_requests_manual_actions_collection.name,
                "localField": "requestId",
                "foreignField": "request_id",
                "as": "manual_actions"
            }},

            # Stage 5: Project the final output document
            {"$project": {
                "_id": 0,  # Exclude the default MongoDB ObjectId
                "request_id": "$requestId",  # From requestProgress
                "batch_id": {"$arrayElemAt": ["$request_details.batch_id", 0]},  # From batch_requests (may be null)
                "sequence_no": {"$arrayElemAt": ["$request_details.sequence_no", 0]},  # From batch_requests (may be null)
                "request_count": {"$arrayElemAt": ["$request_details.total_count", 0]},  # From batch_requests (may be null)
                "vendor": {"$arrayElemAt": ["$request_details.vendor", 0]},  # From batch_requests (may be null)
                "message_type": {"$arrayElemAt": ["$request_details.agent_type", 0]},  # From batch_requests (may be null)
                "patient_name": {"$arrayElemAt": ["$request_details.patient_name", 0]},  # From batch_requests (may be null)
                "dob": {"$arrayElemAt": ["$request_details.dob", 0]},  # From batch_requests (may be null)
                "appointment_id": {"$arrayElemAt": ["$request_details.appointment_id", 0]},  # From batch_requests (may be null)
                "legacy_status": {"$arrayElemAt": ["$legacy_status_data.status", 0]},  # From batch_requests_status (may be null)
                "progress": {  # From requestProgress (always present)
                    "status": "$status",
                    "lastUpdatedAt": "$lastUpdatedAt",
                    "remarks": "$remarks"
                },
                "manual_actions": "$manual_actions"  # From manual_actions (array, may be empty)
            }}
        ]

        # Execute the aggregation pipeline starting from requestProgress collection
        cursor = self.request_progress_collection.aggregate(pipeline)

        # Return the list of results from the aggregation
        combined_data = await cursor.to_list(length=None)
        return combined_data

    async def get_all_request_progress_for_dashboard(self) -> List[Dict[str, Any]]:
        """
        Simple method to get all requests from requestProgress collection
        formatted for the dashboard API
        """
        try:
            # Get all requests from requestProgress
            progress_docs = await self.request_progress_collection.find({}).to_list(length=None)
            
            formatted_requests = []
            for doc in progress_docs:
                # Try to get additional details from batch_requests if available
                request_details = await self.batch_requests_collection.find_one(
                    {"request_id": doc.get("requestId")}
                )
                
                formatted_request = {
                    "request_id": doc.get("requestId"),
                    "batch_id": request_details.get("batch_id", "Unknown") if request_details else "Unknown",
                    "patient_name": request_details.get("patient_name", "Unknown") if request_details else "Unknown",
                    "payer_id": request_details.get("vendor", "Unknown") if request_details else "Unknown",
                    "status": map_status_for_frontend(doc.get("status", "unknown")),
                    "created_at": doc.get("lastUpdatedAt"),
                    "last_updated": doc.get("lastUpdatedAt"),
                    "current_step": doc.get("remarks"),
                    "user_actions_pending": 0  # Default value
                }
                formatted_requests.append(formatted_request)
            
            return formatted_requests
            
        except Exception as e:
            logger.error(f"Error fetching request progress for dashboard: {str(e)}")
            raise


# Global MongoDB service instance
mongodb_service = MongoDBService()
