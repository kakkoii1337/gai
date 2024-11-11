import json
import jsonschema
from gai.lib.common.logging import getLogger
from gai.ttt.client.ttt_client import TTTClient
from gai.lib.dialogue.MonologueMessageBuilder import MonologueMessageBuilder
from gai.lib.dialogue.dialogue_utils import ExtractRecap

logger = getLogger(__name__)


"""
The purpose is to identify the tool instead of making a call to the tool as the first step in the workflow.

Using function call for agents requires the following:

- **tool_choice**: This will affect the "tools" and "tools_choice_schema" by limiting the tools available to the LLM - "required" or "none".
  Use "none" for text and use "required" for JSON.

- **tools_dict**: This describes the tools available to the LLM. *Loaded from /gai/persona/tools/data/tools_template.json via PersonaBuilder*

- **tools_choice_schema**: This is the format of the output from the LLM.

- **tool_name**: This is the key to the tool from tools_dict.

The output from use_TOOL_CHOICE_handler is **tool_name** which is picked from the list of tools.
"""

class use_TOOL_CHOICE_handler:

    #  Extract the output schema based on the tools_dict
    def _get_tool_choice_schema(self, tools_dict:dict) -> dict:
        tool_choice_schema={
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "enum": list(tools_dict.keys())
                }
            },
            "required": ["result"]
        }
        return tool_choice_schema

    def handle_TOOL_CHOICE(self, 
                 ttt: TTTClient,
                 recap:str|list,
                 tools_dict:dict,
                 user_message:str 
                 ) -> bool:
        
        if not ttt:
            raise Exception("use_TOOL_CHOICE_handler.handle_TOOL_CHOICE: ttt is not initialized.")
        if not user_message:
            raise Exception("use_TOOL_CHOICE_handler.handle_TOOL_CHOICE: user_message is not initialized.")

        if tools_dict is None:
            return {"result":"text"}

        # Define the output schema based on the tools_dict
        tool_choice_schema=self._get_tool_choice_schema(tools_dict)

        # Always return a tool name
        tool_choice = "required"

        # title
        state_title="TOOL_CHOICE"

        # recap
        if isinstance(recap, list):
            recap = json.dumps(recap)

        # Convert tools_dict to tools_list
        tools_list = [tool for tool in tools_dict.values()]
        tools_list = json.dumps(tools_list)
        valid_results = json.dumps(tool_choice_schema["properties"]["result"]["enum"])

        system_message=f"""
        BACKGROUND:
        You are a web analyst. You are highly valued for your ability to search the web.
        You are the only one in the conversation that can do that so you should play to your strength but do it sensibly.
        
        OBJECTIVE:        
        Refer to the following <recap> for the background of the conversation: <recap> {recap} </recap>
        You have access to these <tools>: <tools> {tools_dict} </tools>
        Your objective is to return the <key> in the dictionary of <tools> most relevant to the user's message and <recap>.
        Consider using non-"text" tool when possible and choosing "text" as the last resort.

        INSTRUCTIONS:
        Follow these steps to decide on which tool to use.
        Step 1: From the recap, ask yourself the question 'what objective is the user trying to achieve?'
        Step 2: With that as the context, answer the user's question by choosing the key that represents the most suitable tool from one of these: one of these valid values: {valid_results}
        Step 3. Begin your response with an open curly brace "{{".
        Step 4. End your response with a closing curly brace "}}" and nothing else.
        For example:
{{
    "result": value
}}"""
    
        monologue_messages = MonologueMessageBuilder(
            ).AddSystemMessage(Content=system_message,Title=state_title
            ).AddUserMessage(Content=user_message, Title=state_title
            ).AddAssistantMessage().BuildRoleMessages()
        content=None
        try:
            # Remember: We are splitting tool calling into two steps: tool choice using json_schema and the next step is tool calling using tools
            content=ttt(
                messages=monologue_messages,
                temperature=0,
                json_schema=tool_choice_schema,
                max_new_tokens=500, 
                timeout = 60.0,
                stream=False)
        except Exception as e:
            logger.error(f"on_TOOL_CHOICE_handler: Error generating result. error={e}")
            raise

        result=None
        try:
            # Check if content is parseable as json
            result = json.loads(content.extract()["content"])
            # Check if content is valid as schema
            jsonschema.validate(result, tool_choice_schema)
        except Exception as e:
            logger.error(f"on_TOOL_CHOICE_handler: Error parsing string result. error={e}")
            raise

        valid_results = tool_choice_schema['properties']['result']['enum']
        return result
    
    def on_TOOL_CHOICE(self):
        
        try:
            result=self.handle_TOOL_CHOICE(
                ttt=self.ttt,
                recap=ExtractRecap(self.dialogue_messages),
                tools_dict=self.tools_dict,
                user_message=self.user_message
            )
            self.tool_name=result["result"]
            if self.tool_name == "text":
                self.tool_choice = "none"
            else:
                self.tool_choice = "required"

            self.content=result
        except Exception as e:
            logger.error(f"on_TOOL_CHOICE_handler: Error handling TOOL_CHOICE. error={e}")
            self.error=True
            self.content={"error": str(e)}
        
        if hasattr(self, "state"):
            logger.info({"state": self.state, "data": self.content})
            self.step+=1
            self.results.append({"state": self.state, "result": self.content,"step": self.step})

