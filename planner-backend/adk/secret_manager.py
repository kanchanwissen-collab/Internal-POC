from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.cloud import secretmanager
from google.api_core.exceptions import GoogleAPICallError
 
router = APIRouter()
client = secretmanager.SecretManagerServiceClient()
project_id = "empyrean-flight-467605-f9"  # replace with your project id
 
class SecretRequest(BaseModel):
    userid: str
    password: str
    service_account_name: str
    alias: str | None = ""   # ✅ optional alias field
 
@router.post("/secrets/{secret_name}")
def add_secret_with_alias(secret_name: str, request: SecretRequest):
    parent = f"projects/{project_id}/secrets/{secret_name}"
    payload = (
        f"userid={request.userid},"
        f"password={request.password},"
        f"service_account_name={request.service_account_name}"
    )
 
    try:
        # Step 1: Add secret version
        response = client.add_secret_version(
            request={
                "parent": parent,
                "payload": {"data": payload.encode("UTF-8")}
            }
        )
        version_name = response.name  # projects/.../versions/{id}
        version_id = int(version_name.split("/")[-1])
 
        try:
            if not request.alias:
                raise GoogleAPICallError("Alias not provided.")
 
            # Get existing aliases
            secret = client.get_secret(name=parent)
            current_aliases = dict(secret.version_aliases)
 
            # ✅ Always overwrite alias to latest version
            current_aliases[request.alias] = version_id
 
            # Update secret with modified aliases
            client.update_secret(
                secret={
                    "name": parent,
                    "version_aliases": current_aliases
                },
                update_mask={"paths": ["version_aliases"]}
            )
 
        except GoogleAPICallError as e:
            # rollback immediately if alias fails
            client.destroy_secret_version(request={"name": version_name})
            raise HTTPException(
                status_code=503,
                detail=f"Alias update failed. Secret version destroyed. Please retry. {e}"
            )
 
        return {"version": version_name, "alias": request.alias}
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add secret version: {e}")
 
 
 
# ✅ GET -> retrieve latest (or specific) secret version
@router.get("/secrets/{secret_name}")
def get_secret(secret_name: str, version: str = "latest"):
    try:
        version_name = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
        response = client.access_secret_version(request={"name": version_name})
        secret_string = response.payload.data.decode("UTF-8")
 
        # Parse the "key=value" pairs into dictionary
        secret_data = dict(item.split("=", 1) for item in secret_string.split(","))
 
        return secret_data
    except ValueError:
        raise HTTPException(status_code=500, detail="Secret is in an invalid format.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve secret: {e}")