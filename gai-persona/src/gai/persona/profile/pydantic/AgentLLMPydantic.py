from pydantic import BaseModel
from typing import Optional

class AgentLLMPydantic(BaseModel):
    Engine: str
    Model: str
    ApiKey: Optional[str] = None