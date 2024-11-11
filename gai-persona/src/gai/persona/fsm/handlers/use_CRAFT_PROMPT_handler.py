import json,re
from typing import List
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.persona.profile.pydantic.AgentPydantic import AgentPydantic
from gai.lib.dialogue.MonologueMessageBuilder import MonologueMessageBuilder
from gai.lib.dialogue.dialogue_utils import ExtractRecap

"""

This handle is used to create a custom system message for the agent.

Custom messages are only allowed for non-tool calls.

If this is a tool call, the system message will be empty.

"""
class use_CRAFT_PROMPT_handler:

    def _create_system_message(self,
            agent_data:AgentPydantic,
            recap:str,
            custom_message:str,
            tool_name:str)->str:
        
        agent_emoji = "👩‍💼"
        
        # If this is a tool call, don't show the system message
        if tool_name and tool_name != "text":
            return ""

        system_message = ""

        # prime directive: This is necessary for the AI to operate in a multi-agent environment
        prime_directive="""Your name is {agent_data.Name} and you are an artificial being.\n"""
        system_message = prime_directive.format(agent_data=agent_data)

        # role prompt, use this to guide the AI to play a certain role
        # role_prompt="{agent_data.Name}, you will be specific and meticulous in articulation and demonstrate human-like emotions whenever suitable.\nYou must stay in character throughout your conversation.\n"
        # system_message += role_prompt.format(agent_data=agent_data)

        # recap, use this to remind the AI of the historical context of the conversation
        recap_prompt = "{agent_data.Name}, this is a short recap of your conversation so far <recap>{recap}</recap>.\nRefer to this recap to understand the background of your conversation. You will continue from where you left off as {agent_data.Name}."
        system_message += recap_prompt.format(agent_data=agent_data, recap=json.dumps(recap))

        # custom message, use this to provide additional context to the AI
        if custom_message:
            system_message += "\n"+custom_message

        # Final reminder
        #system_message += """NOTE: The user will always remind you of your name before saying "this is your cue"."""

        system_message = re.sub(r'\s+', ' ', system_message)
        return system_message

    def handle_CRAFT_PROMPT(self, 
                 user_message:str, 
                 agent_data: AgentPydantic,
                 tool_name:str,
                 recap : str|list,
                 custom_message:str=None,
                 ):
        # title
        state_title="CRAFT_PROMPT"

        # recap
        if isinstance(recap, list):
            recap = json.dumps(recap)

        # system_message
        system_message=self._create_system_message(
            agent_data=agent_data, 
            tool_name=tool_name,
            recap=recap,
            custom_message=custom_message)

        # update monologue_messages
        self.monologue_messages = MonologueMessageBuilder(
            ).AddSystemMessage(Content=system_message,Title=state_title
            ).AddUserMessage(Content=f"{agent_data.Name}, {user_message}", Title=state_title
            ).AddAssistantMessage().Build()
        
        return system_message

    def on_CRAFT_PROMPT(self):
        self.content={"system_message":self.handle_CRAFT_PROMPT(
            agent_data=self.agent_data,
            recap=ExtractRecap(self.dialogue_messages),
            tool_name=self.tool_name,
            user_message=self.user_message,
            custom_message=self.custom_message
            )}
        
        logger.info({"state": self.state, "data": self.content})
        self.step+=1
        self.results.append({"state": self.state, "result": self.content,"step": self.step})
