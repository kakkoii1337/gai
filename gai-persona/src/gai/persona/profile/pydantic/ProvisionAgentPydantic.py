from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ProvisionAgentPydantic(BaseModel):
    Name: str= Field(..., max_length=255)
    ClassName: Optional[str] = "Assistant"
    AgentTraits: Optional[list] = []
    AgentSkills: Optional[list] = []
    UsageType: Optional[str] = "private"
    AgentDescription: Optional[str] = "Hi there! I am an Assistant class generative AI agent."
    AgentImageStyles: Optional[list] = []
    ImageDataUrl: Optional[str] = None 
