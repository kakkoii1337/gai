from typing import List, Optional
from pydantic import BaseModel,ConfigDict
from enum import Enum
from gai.persona.tools.pydantic.ToolParameterPydantic import ToolParameterPydantic
import uuid

class ToolPydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Allows the model to work with ORM objects
    Id: str
    CreatorId: str
    UsageType: str
    ToolPrompt: Optional[str] = None
    ToolName: str
    ToolDesc: Optional[str] = None
    ToolApiUrl: Optional[str] = None
    ToolApiKey: Optional[str] = None
    ToolParameters: List[ToolParameterPydantic] = []

    def create_schema(self):
        function_schema = {
            "type": "function",
            "function": {
                "name": self.ToolName,
                "description": self.ToolDesc,
                "arguments": {
                }
            }
        }
        for param in self.ToolParameters:
            function_schema["function"]["arguments"][param.ParamName] = {
                "type": param.ParamType,
                "description": param.ParamDescription
            }
        return function_schema
    
    @staticmethod
    def from_schema(schema:dict, id:str, caller_id:str, usage_type:str,tool_prompt:str):
        tool = ToolPydantic(
            Id=id,
            CreatorId=caller_id,
            UsageType=usage_type,
            ToolName=schema["function"]["name"],
            ToolDesc=schema["function"]["description"],
            ToolParameters=[],
            ToolPrompt=tool_prompt
            
        )
        for order,arg_name in enumerate(schema["function"]["arguments"]["properties"]):
            tool.ToolParameters.append(ToolParameterPydantic(
                Id=str(uuid.uuid4()),
                ToolId=id,
                ParamOrder=order,
                ParamName=arg_name,
                ParamType=schema["function"]["arguments"]["properties"][arg_name]["type"],
                ParamDescription=schema["function"]["arguments"]["properties"][arg_name]["description"]
            ))
        return tool

