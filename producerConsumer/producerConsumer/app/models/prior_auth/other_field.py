from pydantic import BaseModel

class OtherField(BaseModel):
    """Other field model for additional data"""
    other_que: str
    other_ans: str
