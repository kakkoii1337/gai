from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from gai.persona.profile.pydantic.AgentClassTypePydantic import AgentClassTypePydantic
from gai.persona.fsm.pydantic.AgentFlowPydantic import AgentFlowPydantic
from gai.persona.prompts.pydantic.PromptPydantic import PromptPydantic
from gai.persona.tools.pydantic.ToolPydantic import ToolPydantic

class AgentPydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Allows the model to work with ORM objects

    Id: Optional[str] = Field(...)
    Name: Optional[str] = Field(..., max_length=255)
    Generator: Optional[str] = Field(None, max_length=128)
    AgentDescription: Optional[str] = None
    ImageUrl: Optional[str] = None
    ThumbnailUrl: Optional[str] = None
    AssociatedUserId: Optional[str] = None
    AgentTraits: Optional[str] = Field(None, max_length=255)
    AgentVoiceId: Optional[int] = None
    AgentVoiceType: Optional[str] = Field(None, max_length=50)
    AgentVoiceName: Optional[str] = Field(None, max_length=50)
    UsageType: Optional[str] = Field(None, max_length=50)
    AgentSkills: Optional[str] = Field(None, max_length=255)
    AgentShortDesc: Optional[str] = None
    AgentHyperparameters: Optional[Dict[str, Any]] = None
    
    ClassType: AgentClassTypePydantic = None
    Tools: Optional[list[ToolPydantic]] = None
    CustomPrompt: Optional[PromptPydantic] = None
    AgentFlow: Optional[AgentFlowPydantic] = None

