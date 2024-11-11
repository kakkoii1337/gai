from gai.lib.common.logging import getLogger
from gai.persona.fsm.handlers.completion_handler_base import CompletionHandlerBase
from gai.lib.dialogue.MonologueMessageBuilder import MonologueMessageBuilder
from gai.lib.dialogue.dialogue_utils import ExtractRecap
logger = getLogger(__name__)

"""
This is the second part of the tool call. It is called after the tool choice has been made.
It is implemented from a copy of use_GENERATE_handler.py that is configured for tool calls.
Tool Calls:
- stream=False
- json_schema=None
- tool_choice="required"
- temperature=0
- top_p=0.5
- top_k=1
"""

class use_TOOL_CALL_handler(CompletionHandlerBase):

    def on_TOOL_CALL(self):

        # Fixed attributes
        stream = False
        tool_choice = "required"
        tool = self.tools_dict[self.tool_name]
        json_schema = None

        # required attributes
        import json
        recap=ExtractRecap(self.dialogue_messages)
        if isinstance(recap, list):
            recap = json.dumps(recap)

        system_message=f"""
        BACKGROUND:
        You are a web analyst. You are highly valued for your ability to search the web.
        You are the only one in the conversation that can do that so you should play to your strength but do it sensibly.
        
        OBJECTIVE:        
        Refer to the following <recap> for the background of the conversation: <recap> {recap} </recap>        
        From the recap, ask yourself the question 'what objective is the user trying to achieve?'
        With that as the context, answer the user's question by crafting a tool call using the most relevant arguments.
        """

        builder = MonologueMessageBuilder()
        self.monologue_messages = builder.AddSystemMessage(system_message
            ).AddUserMessage(self.user_message
            ).AddAssistantMessage(
            ).Build()
        content=self.handle_completion(ttt=self.ttt,
            messages=self.monologue_messages,
            tool_choice=tool_choice,
            tool=tool,
            json_schema=json_schema,
            stream=False
            )
        self.content = content
        self.TOOL_CALL_output=content

        if hasattr(self, "state"):
            logger.info({"state": self.state, "data": self.content})
            self.step+=1
            self.results.append({"state": self.state, "result": self.content,"step": self.step})