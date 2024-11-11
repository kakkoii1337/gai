from pydantic import BaseModel, Field
from typing import Optional
from pydantic.types import constr

class AgentImagePydantic(BaseModel):
    Id: str
    ImageType: str = "png"
    AgentImagePrompt: str
    AgentImageNegativePrompt: str
    Image512: bytes
    Image256: Optional[bytes]
    Image128: Optional[bytes]
    Image64: Optional[bytes]

