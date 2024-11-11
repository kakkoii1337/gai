from typing import Optional
import uuid
from gai.lib.common.logging import getLogger


logger = getLogger(__name__)
from gai.lib.common.errors import InternalException
from gai.persona.fsm.AgentStateMachine import AgentStateMachine
from gai.persona.tools.pydantic.ToolPydantic import ToolPydantic
from gai.persona.images.system_images_mgr import SystemImagesMgr
from gai.persona.profile.pydantic.AgentPydantic import AgentPydantic
from gai.ttt.client.ttt_client import TTTClient
from gai.rag.client.rag_client_async import RagClientAsync
from gai.persona.images.pydantic.AgentImagePydantic import AgentImagePydantic
from gai.lib.dialogue.dialogue_message import DialogueMessage
from gai.lib.dialogue.dialogue_store import DialogueStore
from gai.lib.dialogue.pydantic.DialogueMessagePydantic import DialogueMessagePydantic

class Persona:
    
    def __init__(self, 
                caller_id:str,
                agent_profile:AgentPydantic,
                agent_image:AgentImagePydantic=None,
                ttt:TTTClient=None,
                rag:RagClientAsync=None,
                dialogue_id:str=None,
                dialogue_store=None,
                api_host:str=None
                ):
        self.caller_id = caller_id
        self.agent_profile = agent_profile
        self.state_diagram = agent_profile.AgentFlow.StateDiagram if agent_profile.AgentFlow else None
        self.ttt = ttt
        self.rag = rag
        self.agent_image = agent_image
        self.inner_dialogue_messages = []
        self.dialogue_id=dialogue_id
        self.dialogue_store=dialogue_store
        if not self.dialogue_store:
            self.dialogue_store = DialogueStore(
                caller_id=caller_id,
                agent_id=agent_profile.Id,
                dialogue_id=dialogue_id,
                api_host=api_host,
                message_count_cap=10,
                message_char_cap=4000
            )

    def tools_list_to_tools_config(self, tools:list[ToolPydantic]):
        if not tools or tools.__len__() == 0:
            return None
        tools_config = {}
        for tool in tools:
            tools_config[tool.ToolName]={}
            tools_config[tool.ToolName]["schema"] = tool.create_schema()
            tools_config[tool.ToolName]["tool_prompt"]=tool.ToolPrompt
        return tools_config

    def act(self,
            user_message:str,
            user_message_id:str=None,
            assistant_message_id:str=None,
            n_search:int=3,
            ):
        custom_message = self.agent_profile.CustomPrompt.Content if self.agent_profile.CustomPrompt else None

        if not self.ttt:
            raise Exception("Persona.act: ttt not set.")

        if not self.state_diagram:
            raise Exception("Persona.act: state_diagram not set.")
        
        if not user_message_id:
            user_message_id = DialogueStore.create_message_id(dialogue_id=self.dialogue_id,round_no=0,turn_no=0,postfix="A")

        if not assistant_message_id:
            assistant_message_id = DialogueStore.create_message_id(dialogue_id=self.dialogue_id,round_no=0,turn_no=0,postfix="B")

        # Load internal messages and query dialogue client
        dialogue_messages = self.dialogue_store.list_dialogue_messages()

        tools_config = self.tools_list_to_tools_config(self.agent_profile.Tools)
        asm = AgentStateMachine(
            ttt=self.ttt,
            rag=self.rag,
            agent_data=self.agent_profile,
            collection_name=self.agent_profile.Id,
            dialogue_messages=dialogue_messages,
            tools_config=tools_config,
            state_diagram=self.state_diagram,
            user_message=user_message,
            n_search=n_search,
            custom_message=custom_message
            ).Init()
        
        for chunk in asm.Chat():
            if chunk:
                yield chunk

        # Update internal messages and publish dialogue client
        self.monologue_messages = asm.monologue_messages

        self.dialogue_store.update_dialogue(
            user_message_id=user_message_id,
            assistant_message_id=assistant_message_id,
            user_message=user_message,
            monologue=asm.monologue_messages
            )
