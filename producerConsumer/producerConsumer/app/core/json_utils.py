from bson import ObjectId
from datetime import datetime

def convert_mongo_data(data):
    """
    Recursively converts MongoDB data types (like ObjectId and datetime) to JSON-serializable formats.
    """
    if isinstance(data, list):
        return [convert_mongo_data(item) for item in data]
    if isinstance(data, dict):
        return {key: convert_mongo_data(value) for key, value in data.items()}
    if isinstance(data, ObjectId):
        return str(data)
    if isinstance(data, datetime):
        return data.isoformat()
    return data
