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
from gai.persona.prompts.pydantic.PromptPydantic import PromptPydantic
from gai.lib.common.utils import get_app_path
from gai.ttt.client.ttt_client import TTTClient

# Implementations Below
prompt_router = APIRouter()

here = os.path.dirname(__file__)

### GET /api/v1/persona/prompt/readable/{persona_id}
@prompt_router.get("/api/v1/persona/prompts/readable/{persona_id}")
async def get_persona_prompts_readable(persona_id:str):
    template_path = os.path.join(here,"..","data","prompt_templates.json")
    with open(template_path, 'r') as f:
        data = json.load(f)
    prompts = [PromptPydantic(**prompt) for prompt in data]
    return prompts

### POST /api/v1/persona/prompt/duplicate/{prompt_id}
@prompt_router.post("/api/v1/persona/prompt/duplicate/{prompt_id}")
async def post_persona_prompts_duplicate(prompt_id:str):
    template_path = os.path.join(here,"..","data","prompt_templates.json")
    with open(template_path, 'r') as f:
        data = json.load(f)
        # find prompt with prompt_id

    # Find the prompt with the given prompt_id
    prompt_to_duplicate = next((item for item in data if item.get('Id') == prompt_id), None)
    
    if not prompt_to_duplicate:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Duplicate the prompt with a new name
    new_prompt = prompt_to_duplicate.copy()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_prompt['Id'] = str(uuid.uuid4())  # Assign a new unique ID
    new_prompt['UsageType']="private"

    # Generate new name
    old_name = new_prompt["Name"]
    pattern = r"\(\d+\)$"
    if re.search(pattern, old_name):
        new_name = re.sub(pattern, f"({timestamp})", old_name)
    else:
        new_name = f"{old_name} ({timestamp})"
    new_prompt["Name"]=new_name

    # Append the duplicated prompt to the list
    data.append(new_prompt)

    # Write the updated data back to the JSON file
    with open(template_path, 'w') as f:
        json.dump(data, f, indent=4)

    return new_prompt['Id']

### DELETE /api/v1/persona/prompt/{prompt_id}
@prompt_router.delete("/api/v1/persona/prompt/{prompt_id}")
async def delete_persona_prompts(prompt_id: str):
    template_path = os.path.join(here, "..", "data", "prompt_templates.json")

    # Read the JSON file
    with open(template_path, 'r') as f:
        data = json.load(f)
    
    # Find index of the prompt with the given prompt_id
    prompt_index = next((index for (index, d) in enumerate(data) if d['Id'] == prompt_id), None)
    prompt = PromptPydantic(**data[prompt_index])

    if prompt_index is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if prompt.UsageType == "public":
        raise HTTPException(status_code=409, detail="Cannot delete public prompt")

    # Remove the prompt from the list
    data.pop(prompt_index)

    # Write the updated data back to the JSON file
    with open(template_path, 'w') as f:
        json.dump(data, f, indent=4)

    return {"detail": "Prompt deleted successfully"}

# PUT /api/v1/persona/prompt
# Update private prompt
@prompt_router.put("/api/v1/persona/prompt")
async def put_persona_prompt(prompt: PromptPydantic=Body(...)):
    
    # Check if prompt exists and owned by caller before deleting
    try:
        template_path = os.path.join(here, "..", "data", "prompt_templates.json")

        # Read the JSON file
        with open(template_path, 'r') as f:
            data = json.load(f)
        
        # Find index of the prompt with the given prompt_id
        prompt_index = next((index for (index, d) in enumerate(data) if d['Id'] == prompt.Id), None)
        data[prompt_index]=prompt.dict()

        # Write the updated data back to the JSON file
        with open(template_path, 'w') as f:
            json.dump(data, f, indent=4)

        return {"detail": "Prompt updated successfully"}

    except Exception as e:
        logger.error(f"prompts_router.put_persona_prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
### POST /api/v1/persona/prompt/activate/{prompt_id}
# Activate custom prompt
@prompt_router.post("/api/v1/persona/{persona_id}/prompt/{prompt_id}")
async def post_persona_prompt_activate(persona_id,prompt_id):

    # Load Persona
    from gai.persona.persona_builder import PersonaBuilder
    app_path = get_app_path()
    persona_path = os.path.join(app_path,"persona",persona_id)
    builder = PersonaBuilder()
    await builder.import_async(persona_path)

    # Load Prompt
    template_path = os.path.join(here, "..", "data", "prompt_templates.json")
    with open(template_path, 'r') as f:
        data = json.load(f)
    custom_prompt = next((d for d in data if d['Id'] == prompt_id), None)
    custom_prompt = PromptPydantic(**custom_prompt)

    # Save Persona Prompt
    builder.custom_prompt = custom_prompt
    await builder.export_async(persona_path)