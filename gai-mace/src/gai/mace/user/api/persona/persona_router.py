import json
import asyncio
import base64
from io import BytesIO
from typing import Dict

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse,JSONResponse

from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

# Implementations Below
persona_router = APIRouter()
image_storage: Dict[str, bytes] = {}
thumbnail_storage: Dict[str, bytes] = {}

################################ PERSONAS ################################

# GET "/api/v1/user/personas"
@persona_router.get("/api/v1/user/personas")
async def get_dialogue_participants(request: Request):
    mace_client = request.app.state.mace_client
    await mace_client.rollcall()
    personas=[]
    for msg in mace_client.rollcall_messages:
        data=json.loads(msg["data"])
        name = data["Name"]
        class_name = data["ClassName"]
        short_desc = data["AgentShortDesc"]
        desc=data["AgentDescription"]
        image_url = f"http://localhost:12033/api/v1/persona/{name}/image"
        thumbnail_url = f"http://localhost:12033/api/v1/persona/{name}/thumbnail"
        if not image_storage.get(name,None):
            # 128x128
            image_storage[name] = base64.b64decode(data["Image128"])
        if not thumbnail_storage.get(name,None):
            # 64x64
            thumbnail_storage[name] = base64.b64decode(data["Image64"])

        data = {
            "Name":name,
            "ClassName":class_name,
            "AgentShortDesc":short_desc,
            "AgentDescription":desc,
            "ImageUrl": image_url,
            "ThumbnailUrl": thumbnail_url
        }

        personas.append(data)
    return personas

# GET "/api/v1/user/persona/{persona_name}/image"
@persona_router.get("/api/v1/persona/{persona_name}/image")
async def get_persona_image(persona_name:str):
    if not image_storage.get(persona_name):
        await get_dialogue_participants()
    response = StreamingResponse(BytesIO(image_storage[persona_name]), media_type="image/png")
    response.headers["Cache-Control"] = "public, max-age=86400"  # Example: cache for 1 day
    return response

# GET "/api/v1/user/persona/{persona_name}/thumbnail"
@persona_router.get("/api/v1/persona/{persona_name}/thumbnail")
async def get_persona_thumbnail(persona_name:str):
    if not thumbnail_storage.get(persona_name):
        await get_dialogue_participants()
    response = StreamingResponse(BytesIO(thumbnail_storage[persona_name]), media_type="image/png")
    response.headers["Cache-Control"] = "public, max-age=86400"  # Example: cache for 1 day
    return response