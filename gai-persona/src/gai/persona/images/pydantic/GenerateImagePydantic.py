from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class GenerateImagePydantic(BaseModel):
    Name: str=Field(..., max_length=255)
    AgentId: Optional[str] = None
    AgentDescription: Optional[str] = "Hi there! I am an Assistant class generative AI agent."
    AgentTraits: Optional[list] = []
    AgentImageStyles: Optional[list] = []
