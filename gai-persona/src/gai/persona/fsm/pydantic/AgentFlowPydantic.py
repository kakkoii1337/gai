from pydantic import BaseModel, ConfigDict
from typing import List, Optional,Any

class AgentFlowPydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Allows the model to work with ORM objects
    Id: str
    Name: str
    Description: Optional[str]
    StateDiagram: Optional[str]
