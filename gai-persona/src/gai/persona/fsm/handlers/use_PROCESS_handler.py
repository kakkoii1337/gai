from typing import List
import time

from gai.lib.dialogue.pydantic.MonologueMessagePydantic import MonologueMessagePydantic
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

class use_PROCESS_handler:

    def handle_PROCESS(self,monologue_messages:List[MonologueMessagePydantic],assistant_message:str,assistant_name: str="Assistant"):

        message = monologue_messages.pop()
        if message.Role != "assistant":
            raise Exception(f"Invalid monologue message role: {message.Role}")

        monologue_messages.append(MonologueMessagePydantic(
            Order=len(monologue_messages),
            Name=assistant_name,
            Role="assistant",
            Title="Process_Text",
            Content=assistant_message,
            Timestamp=int(time.time())
        ))

        return monologue_messages


    def on_PROCESS(self):

        self.monologue_messages=self.handle_PROCESS(
            monologue_messages=self.monologue_messages,
            assistant_name=self.agent_name,
            assistant_message=self.content)
        
        if hasattr(self, "state"):
            logger.info({"state": self.state, "data": self.content})
            self.step+=1
            self.results.append({"state": self.state, "result": self.content,"step": self.step})   
