import logging,json,re
from typing import List
from gai.lib.dialogue.MonologueMessageBuilder import MonologueMessageBuilder
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

class on_RELEVANCE_handler:

    def handle_RELEVANCE(self, ttt, subject:str, topic: str):
        self.ttt = ttt
        self.subject = subject
        self.topic = topic
        json_schema={
            "type": "object",
            "properties": {
                "relevance": {
                    "type": "string",
                    "enum": ["high","medium","low"]
                }
            },
            "required": ["relevance"]
        }
        self.subject=re.sub(r'\s+',' ',self.subject)
        self.topic=re.sub(r'\s+',' ',self.topic)
        user_message = f'''{{"Subject": "{self.subject}", "Topic": "{self.topic}"}}'''

        builder = MonologueMessageBuilder(messages=[])
        monologue_messages=builder.AddUserMessage(user_message
            ).AddAssistantMessage(                
            ).Build()
        messages = [{
            "role": x.Role, 
            "content": x.Content
            } for x in monologue_messages]
        result = self.ttt(messages=messages, json_schema=json_schema,stream=False,temperature=0)
        result=json.loads(result.extract()["content"])
        content={"Subject":self.subject,"Topic":self.topic, **result}
        return content

    def on_RELEVANCE(self):
        ttt = self.ttt
        subject=self.subject
        topic=self.topic
        try:
            result=self.handle_RELEVANCE(
                ttt=ttt,
                subject=subject,
                topic=topic
            )
            self.content=result
        except Exception as e:
            logger.error(f"on_RELEVANCE_handler: Error handling RELEVANCE. error={e}")
            self.error=True
            self.content={"error": str(e)}
        
        if hasattr(self, "state"):
            logger.info({"state": self.state, "data": self.content})
            self.step+=1
            self.results.append({"state": self.state, "result": self.content,"step": self.step})
