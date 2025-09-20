from pydantic import BaseModel

class VendorRequestBase(BaseModel):
    vendorname: str
    # Add any truly common fields here if needed
