from pydantic import BaseModel
from typing import Optional

class AgentImagePydantic(BaseModel):
    Id: str
    AgentImageStyles: list
    DataUrlImage512: str
