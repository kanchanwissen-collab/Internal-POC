from pydantic import BaseModel

class ProcedureCode(BaseModel):
    """Procedure code model"""
    code: str
    unit: str
    modifiercode: str
    diagnosiscode: str
