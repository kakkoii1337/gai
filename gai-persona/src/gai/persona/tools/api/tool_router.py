import uuid
import os
import json
import re
from datetime import datetime

# fastapi
from fastapi import APIRouter, Body, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from gai.lib.common.errors import InternalException
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.persona.tools.pydantic.ToolPydantic import ToolPydantic
from gai.lib.common.utils import get_app_path
from gai.ttt.client.ttt_client import TTTClient


# Implementations Below
tool_router = APIRouter()

here = os.path.dirname(__file__)

### GET /api/v1/persona/tool/readable/{persona_id}
## List public tools or private tools owned by persona_id
@tool_router.get("/api/v1/persona/tools/readable/{persona_id}")
async def get_persona_tools_readable(persona_id:str):
    template_path = os.path.join(here,"..","data","tool_templates.json")
    with open(template_path, 'r') as f:
        data = json.load(f)
    tools = [ToolPydantic(**tool) for tool in data]
    return tools

### POST /api/v1/persona/tool/duplicate/{tool_id}
@tool_router.post("/api/v1/persona/tool/duplicate/{tool_id}")
async def post_persona_tools_duplicate(tool_id:str):
    template_path = os.path.join(here,"..","data","tool_templates.json")
    with open(template_path, 'r') as f:
        data = json.load(f)
        # find prompt with prompt_id

    # Find the prompt with the given prompt_id
    tool_to_duplicate = next((item for item in data if item.get('Id') == tool_id), None)
    
    if not tool_to_duplicate:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Duplicate the prompt with a new name
    new_tool = tool_to_duplicate.copy()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_tool['Id'] = str(uuid.uuid4())  # Assign a new unique ID
    new_tool['UsageType']="private"

    # Generate new name
    old_name = new_tool["ToolName"]
    pattern = r"_\d+$"
    if re.search(pattern, old_name):
        new_name = re.sub(pattern, f"_{timestamp}", old_name)
    else:
        new_name = f"{old_name}_{timestamp}"
    new_tool["ToolName"]=new_name

    # Append the duplicated tool to the list
    data.append(new_tool)

    # Write the updated data back to the JSON file
    with open(template_path, 'w') as f:
        json.dump(data, f, indent=4)

    return new_tool['Id']

### DELETE /api/v1/persona/tool/{tool_id}
@tool_router.delete("/api/v1/persona/tool/{tool_id}")
async def delete_persona_tool(tool_id: str):
    template_path = os.path.join(here, "..", "data", "tool_templates.json")

    # Read the JSON file
    with open(template_path, 'r') as f:
        data = json.load(f)
    
    # Find index of the tool with the given tool_id
    tool_index = next((index for (index, d) in enumerate(data) if d['Id'] == tool_id), None)
    tool = ToolPydantic(**data[tool_index])

    if tool_index is None:
        raise HTTPException(status_code=404, detail="tool not found")
    
    if tool.UsageType == "public":
        raise HTTPException(status_code=409, detail="Cannot delete public tool")

    # Remove the tool from the list
    data.pop(tool_index)

    # Write the updated data back to the JSON file
    with open(template_path, 'w') as f:
        json.dump(data, f, indent=4)

    return {"detail": "Tool deleted successfully"}


# PUT /api/v1/persona/tool
# Update private tool
@tool_router.put("/api/v1/persona/tool")
async def put_persona_tool(tool: ToolPydantic=Body(...)):
    
    # Check if tool exists and owned by caller before deleting
    try:
        template_path = os.path.join(here, "..", "data", "tool_templates.json")

        # Read the JSON file
        with open(template_path, 'r') as f:
            data = json.load(f)
        
        # Find index of the tool with the given prompt_id
        tool_index = next((index for (index, d) in enumerate(data) if d['Id'] == tool.Id), None)
        data[tool_index]=tool.dict()

        # Write the updated data back to the JSON file
        with open(template_path, 'w') as f:
            json.dump(data, f, indent=4)

        return {"detail": "Tool updated successfully"}

    except Exception as e:
        logger.error(f"tools_router.put_persona_tool: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
