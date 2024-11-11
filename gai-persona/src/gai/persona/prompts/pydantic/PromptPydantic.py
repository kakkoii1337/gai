from typing import Optional
from pydantic import BaseModel, Field, ConfigDict,validator
from enum import Enum

class PromptPydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Allows the model to work with ORM objects
    Id: str = Field(...)
    Name: str = Field(..., max_length=50)
    Desc: Optional[str] = None
    Content: Optional[str] = None
    CreatorId: str
    UsageType: str
    AgentClassTypeId: str

