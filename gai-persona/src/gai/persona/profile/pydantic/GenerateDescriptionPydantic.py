from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from gai.persona.profile.pydantic.AgentLLMPydantic import AgentLLMPydantic

class GenerateDescriptionPydantic(BaseModel):
    LLM: AgentLLMPydantic
    Name: str= Field(..., max_length=255)
    AgentTraits: Optional[list] = []
