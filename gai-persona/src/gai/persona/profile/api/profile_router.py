import uuid
import os

# fastapi
from fastapi import APIRouter, Body, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from gai.lib.common.errors import InternalException
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.persona.profile.pydantic.ProvisionAgentPydantic import ProvisionAgentPydantic
from gai.persona.profile.pydantic.GenerateDescriptionPydantic import GenerateDescriptionPydantic
from gai.persona.persona_builder import PersonaBuilder
from gai.lib.common.utils import get_app_path
from gai.ttt.client.ttt_client import TTTClient
from gai.lib.common.image_utils import bytes_to_imageurl
from gai.lib.common.utils import get_gai_config
from gai.mace.user.api.dependencies import get_imagecache, ImageCache

# Implementations Below
profile_router = APIRouter()
from gai.lib.common.utils import TTT_CONFIG

### POST /api/v1/persona/provision
@profile_router.post("/api/v1/persona/provision")
async def post_persona_provision(req: ProvisionAgentPydantic=Body(...), image_cache: ImageCache = Depends(get_imagecache)):
    try:
        builder = PersonaBuilder(
            provision=req
        )
        persona=builder.build()
        persona.agent_profile.CustomPrompt
        app_path = get_app_path()
        export_dir=os.path.abspath(os.path.join(app_path,"persona",persona.agent_profile.Id))
        await builder.export_async(export_dir=export_dir)
        
        await builder.import_async(import_dir=export_dir)
        persona=builder.build()
        image_cache.Image128[req.Name] = persona.agent_image.Image128
        image_cache.Image64[req.Name] = persona.agent_image.Image64
        return {"message": "Agent provisioned successfully.","agent_id":persona.agent_profile.Id}
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(str(e)+" "+id)
        raise InternalException(id)

### POST /api/v1/persona/description
@profile_router.post("/api/v1/persona/description")
async def post_persona_description(req: GenerateDescriptionPydantic=Body(...)):
    try:
        ttt_client=TTTClient(config=TTT_CONFIG)
        response = ttt_client(messages=
            f"""system: You are a role-play character generator and you are tasked to create a self-introduction for a fictitious AI character based on the name and personality traits provided by the user. You should assimilate the traits into the self-intro and stay in character.
             user: Generate persona with name {req.Name} and traits{str(req.AgentTraits)}.
             assistant:"""
        ,stream=True)
        def streamer():
            try:
                for chunk in response:
                    chunk=chunk.extract()
                    if type(chunk) is str:
                        yield chunk
            except Exception as e:
                logger.error("Streaming error: "+str(e))
                yield "Error during streaming"
        return StreamingResponse(streamer())
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(str(e)+" "+id)
        raise InternalException(id)

### GET /api/v1/persona/profile
@profile_router.get("/api/v1/persona/profile/{persona_id}")
async def get_persona_profile(persona_id:str):
    builder = PersonaBuilder()
    app_path = get_app_path()
    import_dir=os.path.abspath(os.path.join(app_path,"persona",persona_id))
    import_path=os.path.join(import_dir,"provision.yaml")
    if not os.path.exists(import_path):
        return None
    await builder.import_async(import_dir=import_dir)
    persona=builder.build()
    agent_profile = persona.agent_profile
    image_bytes = persona.agent_image.Image128
    agent_profile.ImageUrl = bytes_to_imageurl(img_data=image_bytes)["url"]
    return persona.agent_profile

### DELETE /api/v1/persona/profile
@profile_router.delete("/api/v1/persona/profile/{persona_id}")
async def delete_persona_profile(persona_id:str):

    app_path = get_app_path()
    import_dir=os.path.abspath(os.path.join(app_path,"persona",persona_id))
    import_path=os.path.join(import_dir,"provision.yaml")
    if os.path.exists(import_path):
        os.remove(import_path)

    import_img_dir = os.path.abspath(os.path.join(app_path,"persona",persona_id,"img"))
    if os.path.exists(import_img_dir):
        for file in os.listdir(import_img_dir):
            os.remove(os.path.join(import_img_dir,file))
        os.rmdir(import_img_dir)

    return {"message": "Agent profile deleted successfully.","agent_id":persona_id}