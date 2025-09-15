import logging
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from api.validate_json import validate_json_logic
from api.agent_tools import trigger_n8n_logic, N8NTriggerRequest, N8NTriggerResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Models for Tools ---
# Corrected model to match the new API input format
class ValidateJsonRequest(BaseModel):
    json_data: Dict[str, Any] = Field(..., description="The JSON dict to be validated.")

class ValidateJsonResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether the JSON passed all validations.")
    http_status: str = Field(..., description="The HTTP status code.")
    error_message: Optional[str] = Field(None, description="A general message about the validation result.")


# --- Pydantic Models for the simplified API ---
class SimplifiedPreAuthRequest(BaseModel):
    request_id: str
    patient_data: Dict[str, Any]

class PreAuthResponse(BaseModel):
    req_id: str
    status: str
    message: str

# --- APIRouter for the new endpoint -----
router = APIRouter()

@router.post("/planner-preauth", response_model=PreAuthResponse)
async def process_simplified_preauth(request_body: SimplifiedPreAuthRequest):
    try:
        # Step 1: Validate the JSON with the new required format
        # validation_response = await validate_json_logic(request_body.patient_data)
        # print(f"validation response is : {validation_response}")
        
        # if not validation_response.is_valid:
        #     return PreAuthResponse(
        #         req_id=request_body.request_id,
        #         status="failed",
        #         message=f"Validation failed: {validation_response.error_message}"
        #     )

        # Step 2: If valid, trigger the N8N webhook with the new payload format and hardcoded data
        
        n8n_request = N8NTriggerRequest(
            request_id=request_body.request_id,
            payer_id="cigna",
            validated_json=request_body.patient_data)
        logging.info("callling n8n")
        
        n8n_response = await trigger_n8n_logic(n8n_request)
        logging.info(f"n8n_response : {n8n_response}")

        if not n8n_response.workflow_triggered:
            logging.info("n8n trigger failed")
            return PreAuthResponse(
                
                req_id=request_body.request_id,
                status="failed",
                message=f"N8N workflow failed to trigger: {n8n_response.message}"
            )
        
        logging("n8n triggered successfully")    
        return PreAuthResponse(
            req_id=request_body.request_id,
            status="success",
            message=f"Successfully triggered N8N workflow with ID: {n8n_response.workflow_id}. Message: {n8n_response.message}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process request: {e}")