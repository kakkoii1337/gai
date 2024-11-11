from typing import Optional
from pydantic import BaseModel,ConfigDict
from enum import Enum

class ToolParameterPydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Allows the model to work with ORM objects
    Id: str
    ToolId: str
    ParamOrder: int
    ParamName: str
    ParamType: str
    ParamDescription: Optional[str] = None
