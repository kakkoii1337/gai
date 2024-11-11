from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.persona.fsm.handlers.completion_handler_base import CompletionHandlerBase

class use_GENERATE_handler(CompletionHandlerBase):

    def on_GENERATE(self):

        # Fixed attributes
        stream = True
        tool_choice = "none"
        tool = None
        json_schema = None

        # required attributes
        messages = self.monologue_messages
        ttt = self.ttt

        message_info="MESSAGES:\n"
        for message in messages:
            message_info+=f"\n{message.Name}:\n{message.Content}\n"
        logger.info(message_info)
        
        content=self.handle_completion(ttt=ttt,
            messages=messages,
            tool=tool,
            json_schema=json_schema,
            stream=stream,
            tool_choice=tool_choice,
            )
        
        if stream:
            self.content = ""
            self.streamer = (chunk for chunk in content )
        else:
            self.content = content

        if hasattr(self, "state"):
            logger.info({"state": self.state, "data": self.content})
            self.step+=1
            self.results.append({"state": self.state, "result": self.content,"step": self.step})     