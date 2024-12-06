import os
import json
import asyncio
import base64
from io import BytesIO
from typing import Dict
from time import sleep

from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse,JSONResponse
from gai.persona.persona_builder import PersonaBuilder
from gai.ttt.client.ttt_client import TTTClient
from gai.mace.user.api.dependencies import get_settings, Settings, get_imagecache, ImageCache
from gai.lib.common.logging import getLogger
from gai.mace.node.mace_server import MaceServer

logger = getLogger(__name__)

CUSTOM_PERSONA_DIR = "~/.gai/persona/00000000-0000-0000-0000-000000000000"

# Implementations Below
persona_router = APIRouter()

################################ PERSONAS ################################

@persona_router.get("/api/v1/settings")
async def get_settings_endpoint(settings: Settings = Depends(get_settings)):
    return settings

# POST "/api/v1/user/persona"
@persona_router.post("/api/v1/user/persona")
async def post_user_persona_reload(settings: Settings = Depends(get_settings)):

    import_dir=os.path.expanduser(CUSTOM_PERSONA_DIR)
    if not os.path.exists(import_dir):
        logger.warn(f"[magenta]Custom persona is not created yet. Abort loading persona thread.[/magenta]")
        return
    logger.info(f"[green]MACE node importing persona from {import_dir}.")
    
    async def run_server():
        builder = PersonaBuilder()
        builder = await builder.import_async(import_dir=import_dir)
        persona = builder.build()
        if persona.ttt is None:
            # Get the ttt from environment not from gai.yml
            persona.ttt = TTTClient({
                "url": f"{settings.TTT}//gen/v1/chat/completions",
            })
        node = await MaceServer.create(
            servers=settings.NATS,
            persona=persona)
        await node.serve()

    from gai.mace.node.thread_manager import ThreadManagerSingleton            
    tm = ThreadManagerSingleton.GetInstance()
    if tm.is_stopped("User"):
        tm.run_thread("User", run_server)           

# GET "/api/v1/user/personas"
@persona_router.get("/api/v1/user/personas")
async def get_dialogue_participants(request: Request,imagecache: ImageCache = Depends(get_imagecache)):
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
        if data.get("Image128", None) and not imagecache.Image128.get(name, None):
            # 128x128
            imagecache.Image128[name] = base64.b64decode(data["Image128"])
        if data.get("Image64",None) and not imagecache.Image64.get(name, None):
            # 64x64
            imagecache.Image64[name] = base64.b64decode(data["Image64"])

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
async def get_persona_image(persona_name:str,request: Request,image_cache: ImageCache = Depends(get_imagecache)):
    if not image_cache.Image128.get(persona_name, None):
        await get_dialogue_participants(request,image_cache)
    response = StreamingResponse(BytesIO(image_cache.Image128[persona_name]), media_type="image/png")
    return response    

# GET "/api/v1/user/persona/{persona_name}/thumbnail"
@persona_router.get("/api/v1/persona/{persona_name}/thumbnail")
async def get_persona_thumbnail(persona_name:str,request: Request,image_cache: ImageCache = Depends(get_imagecache)):
    # If cache miss, fetch from MACE
    if not image_cache.Image64.get(persona_name, None):
        await get_dialogue_participants(request,image_cache)
    # If still not found, return None
    if not image_cache.Image64.get(persona_name, None):
        return None
    
    response = StreamingResponse(BytesIO(image_cache.Image64[persona_name]), media_type="image/png")
    return response    
