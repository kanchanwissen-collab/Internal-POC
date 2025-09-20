from enum import Enum

class VendorName(str, Enum):
    Evicore = "Evicore"
    Cohere  = "Cohere"
    Humana  = "Humana"
    # Add more vendors as needed
