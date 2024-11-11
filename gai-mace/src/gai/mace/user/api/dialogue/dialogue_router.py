import json
import asyncio
import time
from typing import Dict

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse,JSONResponse

from pydantic import BaseModel

from nats.aio.msg import Msg

from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.lib.dialogue.dialogue_store import DialogueStore
from gai.mace.pydantic.FlowMessagePydantic import FlowMessagePydantic
from gai.mace.user.mace_client import MaceClient

# Implementations Below
dialogue_router = APIRouter()
response_q = asyncio.Queue()

# Enqueue incoming messages
async def on_chat(msg: Msg):
    global response_q

    data=msg.data.decode()
    if not data:
        return
    
    data=json.loads(data)
    pydantic = FlowMessagePydantic(**data)

    # Case 1: from "User" to Persona
    if pydantic.Sender == "User":
        # Ignore
        return
    
    # Case 2: from "Persona" to User
    if pydantic.Recipient == "User":
        await response_q.put(pydantic)

# Dequeue and stream chunk
async def streamer(mace_client: MaceClient):
    global response_q
    start_time = time.time()
    timeout = 60
    elapsed = 0
    content=""
    try:
        while elapsed <= timeout:
            try:
                # Get message from queue with a small timeout to avoid blocking indefinitely
                pydantic = await asyncio.wait_for(response_q.get(), timeout=0.5)
                if pydantic.ChunkNo=="<eom>":
                    # If end of message, save assistant message to store
                    content=mace_client._strip_xml(content)
                    message_id=DialogueStore.create_message_id(pydantic.DialogueId,pydantic.RoundNo,pydantic.TurnNo,"B")
                    mace_client.dialogue_store.add_assistant_message(message_id=message_id,name=pydantic.Sender, content=content)

                    # Log details
                    print(pydantic.Chunk,end="",flush=True)
                    print()
                    logger.info("List dialogue messages:")
                    messages = await mace_client.list_dialogue_messages()
                    for message in messages:
                        print()
                        print(message)
                        print()

                    # Yield final chunk
                    yield pydantic.Chunk
                    return
                
                print(pydantic.Chunk,end="",flush=True)
                content+=pydantic.Chunk
                yield pydantic.Chunk
            except asyncio.TimeoutError:
                # continue looping and do not terminate
                pass
            finally:
                elapsed = time.time() - start_time
    except Exception as e:
        logger.error("mace_router.stream: error="+e)
        raise Exception("mace_router.stream: error="+e)
    finally:
        pass
        #await mace_client.close()

    if elapsed > timeout:
        raise Exception("mace_router.streamer: timeout")

# POST "/api/v1/user/dialogue/poll"
class PollRequest(BaseModel):
    round_no:int=0
    user_message:str
@dialogue_router.post("/api/v1/user/dialogue/poll")
async def post_user_dialogue_poll(req: PollRequest,request:Request):
    mace_client = request.app.state.mace_client

    # roll call
    await mace_client.rollcall()
    names=[]
    for msg in mace_client.rollcall_messages:
        data=json.loads(msg["data"])
        names.append(data["Name"])
    
    # construct seq diagram
    seq_diagram = ""
    src = "User"
    for name in names:
        dest = name
        seq_diagram += f"{src}->>{dest}\n"
    await mace_client.dialogue(msg=req.user_message,flow_diagram=seq_diagram)
    return StreamingResponse(streamer(mace_client))

# GET "/api/v1/user/dialogue/messages"
@dialogue_router.get("/api/v1/user/dialogue/messages")
async def get_user_dialogue_messages(request: Request):
    mace_client = request.app.state.mace_client
    result = await mace_client.list_dialogue_messages()
    return result

# DELETE "/api/v1/user/dialogue/messages"
@dialogue_router.delete("/api/v1/user/dialogue/messages")
async def delete_user_dialogue_messages(request: Request):
    mace_client = request.app.state.mace_client
    return await mace_client.clear_dialogue()

"""
The endpoint will take in a message and send it to a server with the response handled via on_chat() callback.
on_chat() will queue the request to be picked up by streamer() and stream as response.
The stream ends by either timeout or receiving the terminating tag, ie. </{src}>
"""
# POST "/api/v1/user/dialogue"
class PersonaChatRequest(BaseModel):
    round_no:int=0
    user_message:str
    seq_diagram:str
@dialogue_router.post("/api/v1/user/dialogue")
async def post_user_dialogue(req: PersonaChatRequest, request: Request):
    mace_client=request.app.state.mace_client
    await mace_client.dialogue(msg=req.user_message,flow_diagram=req.seq_diagram)
    return StreamingResponse(streamer(mace_client))

# GET "/api/v1/user/dialogue"
@dialogue_router.get("/api/v1/user/dialogue")
async def get_user_dialogue_next(request:Request):
    mace_client = request.app.state.mace_client
    response = await mace_client.next()
    if not response:
        async def eom_generator():
            yield "<eom>"
        return StreamingResponse(eom_generator())
    
    return StreamingResponse(streamer(mace_client))

# DELETE "/api/v1/user/dialogue/message/{message_id}"
@dialogue_router.delete("/api/v1/user/dialogue/message/{message_id}")
async def delete_user_dialogue_message(message_id:str,request: Request):
    mace_client = request.app.state.mace_client
    logger.info(f"Deleting message {message_id}")
    return await mace_client.delete_dialogue_message(message_id)