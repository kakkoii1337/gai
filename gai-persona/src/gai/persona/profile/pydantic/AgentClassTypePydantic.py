from pydantic import BaseModel, Field, ConfigDict

class AgentClassTypePydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Allows the model to work with ORM objects
    
    Id: str = Field(..., max_length=36)
    ClassName: str = Field(..., max_length=128)
    ClassDescription: str = Field(None, max_length=255)  # Assuming a reasonable max length for text fields

