from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class GenerateDescriptionPydantic(BaseModel):
    Name: str= Field(..., max_length=255)
    AgentTraits: Optional[list] = []
