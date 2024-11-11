# fastapi
from fastapi import APIRouter, Body, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

# Implementations Below
router = APIRouter()

# POST "/api/v1/persona/chat"
class PersonaChatRequest(BaseModel):
    user_message:str
@router.post("/api/v1/persona/chat")
async def persona_chat(req: PersonaChatRequest,request: Request):
    persona = request.app.state.persona
    response = persona.act(user_message=req.user_message)
    def streamer():
        for chunk in response:
            if chunk:
                yield chunk
    return StreamingResponse(streamer())


    # caller_id = "00000000-0000-0000-0000-000000000000"
    # agent_id = "00000000-0000-0000-0000-000000000000"
    
    # # initialise agent profile
    # agent_profile = AgentProfile(
    #     caller_id=caller_id,
    #     agent_id=agent_id, 
    #     session=session,
    #     api_host="http://localhost:12033")
    # agent_data = agent_profile.get_agent()
    # agent_tool = agent_profile.get_tool().json()
    # agent_prompt = agent_profile.get_prompt()

    # # initialise agent dialogue
    # from gai.agent.dialogue.dialogue_client import DialogueClient
    # agent_dialogue = DialogueClient(
    #     agent_id=agent_id, 
    #     caller_id=caller_id, 
    #     session=session,
    #     api_host="http://localhost:12033")
    # dialogue_messages = agent_dialogue.list_dialogue_messages(req.dialogue_id)

    # # initialise state machine
    # state_diagram = """stateDiagram-v2
    #     INIT --> CRAFT_TEXT_PROMPT: next / on_CRAFT_PROMPT
    #     CRAFT_TEXT_PROMPT --> GENERATE: next / on_GENERATE
    #     GENERATE --> END: next / on_ERROR / has_error
    #     GENERATE --> PROCESS: next / on_PROCESS / not_has_error
    #     PROCESS --> END: next
    #     """
    # ttt = TTTClient({
    #     "type": "ttt",
    #     "url": "http://gai-ttt-svr:12031/gen/v1/chat/completions"
    # })
    # asm = AgentStateMachine(
    #     ttt=ttt,
    #     rag=None,
    #     agent_data=agent_data,
    #     collection_name=agent_id,
    #     dialogue_messages=dialogue_messages,
    #     tools_dict=agent_tool,
    #     state_diagram=state_diagram,
    #     user_message="",
    #     custom_message=agent_prompt,
    #     stop_conditions=["<br><br>","</s>"]
    #     )
    
    # # Chat
    # asm.Init()
    # for chunk in asm.Chat():
    #     yield chunk    

    # #Update dialogue
    # agent_dialogue.update_dialogue(
    #     dialogue_id=req.dialogue_id,
    #     user_message_id=str(uuid.uuid4()), 
    #     user_id=caller_id,
    #     agent_name=asm.agent_name,
    #     monologue=asm.monologue_messages,
    #     user_message=req.user_message
    #     )


