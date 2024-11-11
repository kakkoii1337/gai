import json
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.lib.dialogue.MonologueMessageBuilder import MonologueMessageBuilder

class use_BOOLEAN_handler:


    def handle_BOOLEAN(self, ttt, question):
        self.ttt = ttt
        self.question = question
        json_schema={
            "properties": {
                "result": {
                    "type":"boolean"
                }
            }, 
            "required": [
                "result"
            ],
            "title": "Predicate",
            "type": "object"
        }
        monologue_messages = MonologueMessageBuilder(
            ).AddUserMessage(f"Is this true or false: `{self.question}`"
            ).AddAssistantMessage(
            ).Build()
        messages = [{
            "role": x.Role, 
            "content": x.Content
        } for x in monologue_messages]
        result = self.ttt(
            messages=messages, 
            json_schema=json_schema,
            tool_choice="none",
            stream=False,
            temperature=0)

        return json.loads(result.extract()["content"].lower().strip())["result"]


    def on_BOOLEAN(self):
        try:
            result=self.handle_BOOLEAN(
                ttt=self.ttt,
                question=self.user_message
            )
            self.content=result
        except Exception as e:
            logger.error(f"on_BOOLEAN_handler: Error handling BOOLEAN. error={e}")
            self.error=True
            self.content={"error": str(e)}
        
        if hasattr(self, "state"):
            logger.info({"state": self.state, "data": self.content})
            self.step+=1
            self.results.append({"state": self.state, "result": self.content,"step": self.step})
