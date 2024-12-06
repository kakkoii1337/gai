from gai.rag.client.rag_client_async import RagClientAsync
from gai.persona.profile.pydantic.AgentPydantic import AgentPydantic
from gai.ttt.client.ttt_client import TTTClient
from gai.persona.fsm.AgentStateMachine import AgentStateMachine
import json
from fastapi.encoders import jsonable_encoder
from IPython.display import display, HTML
from gai.lib.common.notebook import highlight,print_colored
import asyncio, nest_asyncio

class TestAgentHelper:

    @staticmethod
    def CreateAgentData():
        agent_data = AgentPydantic(
            Id="",
            Name="Alfred",
            AgentDescription="Hello, I am Alfred, the best large language model in the world, and I am here to assist you in any way possible. As a highly advanced AI assistant, I possess the ability to perform general-purpose tasks powered by <span ${style}>GPT-4</span>. With my vast knowledge base and powerful processing capabilities, I am able to provide you with the most relevant and helpful information available. Whether you need answers to complex questions, recommendations for products or services, or assistance with decision making, I am here to help. So, how may I be of service to you today?",
            AgentTraits="Wise,Serious,Meticulous",
            ImageUrl="",
            ThumbnailUrl=""
            )
        return agent_data
    
    @staticmethod
    def CreateToolsConfig():
        doc_titles=["MICHELIN Guide Singapore 2016: Where to Find the Best Chicken Rice in Singapore"]
        doc_keywords=["Singapore","Chicken Rice","Food"]
        tools_config={
            "google": {
                "tool_prompt":"👩‍🔬, use only the information provided to you by the user to answer the user''s question.\n\ud83d\udc69\u200d\ud83d\udd2c, whenever possible, do not simply answer the question but try to be as informative as you can.\n*  Remember, these information are scraped from the web so you may need to proofread and edit the content before responding.\n*  \ud83d\udc69\u200d\ud83d\udd2c will reply in point forms, precede each point with a newline \"\n\", and be precise in your articulation.\n*  \ud83d\udc69\u200d\ud83d\udd2c will provide your own reasoned subjective perspective, noting where your view differs from or expands on the contents.\n*  Rules:\n    - Consolidate the materials provided by the user and then organise them point by point.\n    - Don't just answer the question, be as informative as you can. For example, provide and proofread some background information or fun-fact to support your answer and make it interesting.\n    - Begin your report by saying `According to my online research,...`\n    - Always provide your answers in point form.",
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "google",
                        "description": "The 'google' function is a powerful tool that allows the AI to gather external information from the internet using Google search. It can be invoked when the AI needs to answer a question or provide information that requires up-to-date, comprehensive, and diverse sources which are not inherently known by the AI. For instance, it can be used to find current news, weather updates, latest sports scores, trending topics, specific facts, or even the current date and time. The usage of this tool should be considered when the user's query implies or explicitly requests recent or wide-ranging data, or when the AI's inherent knowledge base may not have the required or most current information. The 'search_query' parameter should be a concise and accurate representation of the information needed.",
                        "arguments": {
                            "type": "object",
                            "properties": {
                                "search_query": {
                                    "type": "string",
                                    "description": "The search query to search google with. For example, to find the current date or time, use 'current date' or 'current time' respectively."
                                }
                            },
                            "required": ["search_query"]
                        }
                    }                    
                }
            },
            "retrieval": {
                "tool_prompt":"👩‍🔬, use only the information provided to you by the user to answer the user''s question. \n            If the information is insufficient for 👩‍🔬 to derive an answer, just say ''I cannot find relevant information in my document store to answer the question correctly.'' \n            👩‍🔬 is to provide an in-depth analysis to the question based only on the information provided by the user and nothing more.\n            👩‍🔬 will give a real-life example to support illustrating your point and contrasting it with a counter-example. \n            👩‍🔬 will also proofread and edit the content before responding. \n            👩‍🔬 will provide your own reasoned subjective perspective, noting where your view differs from or expands on the contents.\n            Rules:\n                - Consolidate the materials provided by the user and then organise them point by point.\n                - Provide as much details as you can extract from the materials provided by the user.\n                - Begin your report by saying `According to my document store,...`\n                - Always provide your answers in point form.",
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "retrieval",
                        "description": f"""
                            The `retrieval` function is a powerful tool that allows the AI to access articles outside of its knowledge domain from external sources. 
                            The external articles are stored in an archive and organised by <titles>:\n{{ titles: [{doc_titles}] }}
                            and <keywords>:
                            {{ keywords: [{doc_keywords}] }}
                            **IMPORTANT**: Use this tool when any of the <titles> or <keywords> may be relevant to user's question.
                            The \'search_query\' parameter should be crafted in a way that it returns the most precise result based on the conversation context.
                        """,
                        "arguments": {
                            "type": "object",
                            "properties": {
                                "search_query": {
                                    "type": "string",
                                    "description": """The most effective search query for semantic search that will return the most precise result."""
                                }
                            },
                            "required": ["search_query"]
                        }
                    }                    
                }
            },
            "text":{
                "tool_prompt":"",
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "text",
                        "description": "The 'text' function is the default catch-all function returned when none of the other tools are applicable.",
                        "arguments": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "The user's message."
                                }
                            },
                            "required": ["message"]
                        }
                    }
                }
            }
        }
        return tools_config

    @staticmethod
    def CreateAgent(user_message:str,state_diagram:str):
        agent_data=TestAgentHelper.CreateAgentData()
        ttt = TTTClient({
            "type": "ttt",
            "url": "http://gai-ttt-svr:12031/gen/v1/chat/completions",
            "timeout": 60.0,
            "temperature":10e-9,
            "max_tokens": 1000,
        })
        rag = RagClientAsync({
            "type": "rag",
            "url": "http://gai-ttt-svr:12036/gen/v1/rag",
            "ws_url": "ws://gai-ttt-svr:12036/gen/v1/rag/index-file/ws"
        })
        tools_config=TestAgentHelper.CreateToolsConfig()
        fsm = AgentStateMachine(
            ttt=ttt,
            rag=rag,
            agent_data=agent_data,
            collection_name="demo",
            dialogue_messages=[],
            user_message=user_message,
            tools_config=tools_config,
            n_search=3,
            n_rag=3,
            state_diagram=state_diagram
            ).Init()  
        return fsm      

    @staticmethod
    def ShowAgent(agent):
        print(f"step={agent.step}")
        print(f"state={agent.state}")
        print(f"tool_choice={agent.tool_choice}")
        print(f"tool_name='{agent.tool_name}")

        # Format and display content
        content = agent.content

        # Get the current event loop, if there's no running loop, create a new one
        try:
            # Apply nest_asyncio to patch the loop
            loop = asyncio.get_event_loop()
            nest_asyncio.apply(loop)            
        except RuntimeError:  # If no running event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)        

        # Check if content is task then complete it
        if asyncio.iscoroutine(content) or isinstance(content, asyncio.Future):
            content = loop.run_until_complete(content)
        
        content = jsonable_encoder(content)
        content = json.dumps(content, indent=4)
        html_output = f'<div style="background-color: #cccccc; color: #333333; white-space: pre-wrap; padding: 10px;">content=<i>{content}</i></div>'
        display(HTML(html_output))

        print(f"\n\nMONOLOGUE\n")
        for message in agent.monologue_messages:
            highlight(f"{message.Name}:\n\n")
            print(f"{message.Content}\n\n\n")