"""
Sequential Batch Processing Service with Database-Simulated Pub/Sub
"""
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter
import json
from google.cloud import pubsub_v1
import os

from app.models.prior_auth.pubsub_batch import (
    BatchIngestResponse,
    BatchStatusResponse
)
from app.models.prior_auth.request_progress import (
    RequestProgress,
    RequestStatus
)
from app.services.mongodb_service import mongodb_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class SequentialBatchService:
    """Service for sequential batch processing with database-simulated Pub/Sub"""
    
    def __init__(self):
        pass
    
    def _get_next_batch_id(self) -> str:
        """
        Generates a new unique batch ID using UUID.
        """
        return str(uuid.uuid4())

    def _extract_vendor(self, payload: Dict[str, Any]) -> str:
        """
        Extract vendor name from payload, supporting new models and endpoint structure.
        Handles nested fields and normalizes using VendorName enum.
        """
        
        from app.models import VendorName
        vendor_fields = [
            'vendorname'
        ]
        # Check top-level fields
        from enum import Enum
        for field in vendor_fields:
            if field in payload and payload[field]:
                raw = payload[field]
                if isinstance(raw, Enum):
                    value = raw.value.strip().upper()
                else:
                    value = str(raw).strip().upper()
                
                for v in VendorName:
                    if v.value.upper() == value:
                        
                        return v.value
                
                return value
        # Check nested 'meta' or 'details' fields if present
        for nested in ['meta', 'details', 'info', 'request_info']:
            if nested in payload and isinstance(payload[nested], dict):
                for field in vendor_fields:
                    if field in payload[nested] and payload[nested][field]:
                        value = str(payload[nested][field]).strip().upper()
                       
                        for v in VendorName:
                            if v.value.upper() == value:     
                                return v.value
                        return value
        return "UNKNOWN"
    
    def _count_vendors(self, requests: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count requests by vendor"""
        # Convert Pydantic models to dict before extracting vendor
        dict_requests = []
        for req in requests:
            if hasattr(req, 'dict'):
                dict_requests.append(req.dict())
            else:
                dict_requests.append(req)
        vendors = [self._extract_vendor(r) for r in dict_requests]
        
        counts = dict(Counter(vendors))
       
        return counts

    async def ingest_batch(self, requests: List[Dict[str, Any]]) -> BatchIngestResponse:
        try:
            # Assuming _get_next_batch_id() is now a synchronous method
            batch_id = self._get_next_batch_id()

            request_count = len(requests)
            vendor_counts = self._count_vendors(requests)

            batch_metadata = {
                "batch_id": batch_id,
                "request_count": request_count,
                "vendor_counts": vendor_counts,
                "status": "pending_publish",
                "created_at": datetime.utcnow().isoformat()
            }

            # Insert batch metadata
            await mongodb_service.batch_metadata_collection.insert_one(batch_metadata)

            project_id = "agent-ai-dev"
            # --- Google Pub/Sub Publishing Logic (Synchronous) ---
            topic_path =os.getenv("TOPIC_NAME")

            # PublisherClient() instance is reused from __init__
            publisher = pubsub_v1.PublisherClient()

            # List to hold the publish futures
            publish_futures = []

            for i, payload in enumerate(requests):
                payload_dict = payload.dict() if hasattr(payload, 'dict') else payload
                vendor = self._extract_vendor(payload_dict)
                request_id = str(uuid.uuid4())
                message_data = {
                    "batch_id": batch_id,
                    "sequence_no": i + 1,
                    "request_id": str(request_id),
                    "total_count": request_count,
                    "vendor": vendor,
                    "payload": payload_dict
                }

                attributes = {
                    "batch_id": batch_id,
                    "sequence_no": str(i + 1),
                    "total_count": str(request_count),
                    "vendor": vendor,
                    "agent_type": "prior_auth"
                }

                # Insert into the correct collections
                patient_name = payload_dict["patientfirstname"]+" "+payload_dict["patientlastname"]
                await mongodb_service.batch_requests_collection.insert_one(
                    {
                         "batch_id": batch_id,
                        "sequence_no": str(i + 1),
                        "total_count": str(request_count),
                        "request_id": str(request_id),
                        "patient_name": patient_name,
                        "dob": payload_dict["patientdateofbirth"],
                        "appointment_id": payload_dict["appointmentid"],
                        "person_no": payload_dict.get("personnumber"),
                        "date_of_service": payload_dict.get("appointmentdate"),
                        "visit_reason": "Office Visit",
                        "specialty": payload_dict.get("clientspecialty"),
                        "vendor": vendor,
                        "agent_type": "prior_auth"
                    }
                )
                
                # Keep legacy batch_requests_status for backward compatibility
                await mongodb_service.batch_requests_status_collection.insert_one({
                    "batch_id": batch_id,
                    "request_id": str(request_id),
                    "status": str("queued")
                })

                # Use new RequestProgress model
                await mongodb_service.create_or_update_request_progress(
                    request_id=str(request_id),
                    status=RequestStatus.CREATED,
                    remarks=f"Request created in batch {batch_id}"
                )

                await mongodb_service.batch_requests_manual_actions_collection.insert_one({
                    "request_id": str(request_id),
                    "action_type": "MFA",
                    "reason": "OTP Required ",
                    "action_at": datetime.now()
                })

                data = await mongodb_service.get_combined_request_data(request_id)
                

                data_bytes = json.dumps(message_data).encode("utf-8")

                # Publish the message and store the Future object
                # The .publish() method is asynchronous even on the synchronous client.
                future = publisher.publish(topic_path, data=data_bytes, **attributes)
                publish_futures.append(future)

            # Wait for all messages to be published and acknowledged by the service.
            # This is a blocking call. The `result()` method waits for the future to complete.
            for future in publish_futures:
                future.result()

            await mongodb_service.batch_metadata_collection.update_one(
                {"batch_id": batch_id},
                {"$set": {"status": "published"}}
            )

            return BatchIngestResponse(
                batch_id=batch_id,
                status="success",
                message=f"Batch {batch_id} published successfully to Pub/Sub",
                request_count=request_count,
                vendor_counts=vendor_counts,
                created_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error publishing batch {batch_id} to Pub/Sub: {str(e)}")
            await mongodb_service.batch_metadata_collection.update_one(
                {"batch_id": batch_id},
                {"$set": {"status": "publish_failed"}}
            )
            raise


    async def process_complete_batch_flow(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            ingest_response = await self.ingest_batch(requests)
            batch_id = ingest_response.batch_id
            batch_metadata = await mongodb_service.batch_metadata_collection.find_one({"batch_id": str(batch_id)})

            return {
                "batch_id": batch_id,
                "total_requests": ingest_response.request_count,
                "requests_per_payer": ingest_response.vendor_counts,
            }
        
        except Exception as e:
            logger.error(f"Error in complete batch flow: {str(e)}")
            raise
    
    async def get_batch_status(self, batch_id: str) -> BatchStatusResponse:
        """Get detailed status of a batch"""
        try:
            # Get batch metadata
            batch_doc = await mongodb_service.batch_metadata_collection.find_one({"batch_id": batch_id})
            
            if not batch_doc:
                raise ValueError(f"Batch {batch_id} not found")
            return BatchStatusResponse(
                batch_id=batch_id,
                status=batch_doc["status"],
                request_count=batch_doc["request_count"],
                published_count=batch_doc["request_count"],
                failed_count=0 if batch_doc["status"]=="published" else batch_doc["request_count"] ,
                vendor_counts=batch_doc["vendor_counts"],
                created_at=batch_doc["created_at"],
                committed_at=batch_doc.get("committed_at")
            )
        
        except Exception as e:
            logger.error(f"Error getting batch {batch_id} status: {str(e)}")
            raise
    
    async def update_request_status(self, request_id: str, status: RequestStatus, remarks: Optional[str] = None):
        """Update request status using the new RequestProgress model"""
        try:
            await mongodb_service.create_or_update_request_progress(
                request_id=request_id,
                status=status,
                remarks=remarks
            )
            logger.info(f"Updated request {request_id} status to {status.value}")
        except Exception as e:
            logger.error(f"Error updating request {request_id} status: {str(e)}")
            raise

# Global service instance
sequential_batch_service = SequentialBatchService()
