import os,re,json
from gai.lib.dialogue.MonologueMessageBuilder import MonologueMessageBuilder
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

from gai.ttt.client.ttt_client import TTTClient
from gai.lib.tools.scraper import Scraper
from gai.lib.tools.googler import Googler
from gai.lib.common.file_utils import split_text


class use_GOOGLE_handler:

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

    def handle_GOOGLE(self, ttt:TTTClient, search_query:str, chunk_size:int=1000, chunk_overlap:int=100, n_search:int=4):

        # Google the search query
        self.googler = Googler()
        urls=self.googler.google(search_query)
        urls=[result["url"] for result in urls]

        # used for sorting chunk files by name
        # def sort_key(filename):
        #     parts = filename.split('.')[0]
        #     try:
        #         return int(parts)
        #     except ValueError:
        #         return float('inf')

        # important: must remove excess whitespace for this to work
        subject = search_query
        subject=re.sub(r'\s+',' ',subject)        

        results = []
        for url in urls:
            try:
                html, links = Scraper().scrape(url)

                # Split the text into chunk files
                chunk_dir = split_text(text=html,sub_dir=None, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                chunks = os.listdir(chunk_dir)

                # Read the content of each chunk file to check their relevance
                for chunk in chunks:

                    try:
                        chunk_path = os.path.join(chunk_dir, chunk)
                        with open(chunk_path, 'r') as f:
                            chunk = f.read()
                        
                        chunk=re.sub(r'\s+',' ',chunk)
                        user_message = f"""Compare the relevance between '{{"Subject": "{subject}"}}' and '{{"Topic": "{chunk}" }}'.
                        1. Begin your response with an open curly brace "{{".
                        2. Identify the relevance string belonging to one of these valid values: "high", "medium", "low".
                        3. End your response with a closing curly brace "}}".
                        4. Validate your response against this json schema: 
                            ```jsonschema
                            {self.json_schema}
                            ```
                        """
                        user_message = re.sub(r'\s+', ' ', user_message)
                        builder = MonologueMessageBuilder(messages=[])
                        messages=builder.AddUserMessage(user_message
                            ).AddAssistantMessage(                
                            ).BuildRoleMessages()
                        relevance = ttt(messages=messages, 
                                    json_schema=self.json_schema,
                                    stream=False,
                                    temperature=0,
                                    max_tokens=2000,
                                    tool_choice="none")
                        relevance=json.loads(relevance.extract()["content"])
                        result={"subject":subject,"topic":chunk, **relevance}                    
                        if result.get("relevance") == "high":
                            results.append(result)
                            logger.info(f"on_SCRAPE_handler: found {len(results)}/{n_search}")
                            if len(results)>=n_search:
                                return results

                    except Exception as e2:
                        logger.warning(f"on_SCRAPE_handler: chunk processing error. {str(e2)}")

                logger.info(f"on_SCRAPE_handler: scraped {url}")
            except Exception as e:
                logger.warning(f"on_SCRAPE_handler: scraped {url} error. {str(e)}")

        return results


    def use_google(self):
        return self.tool_name=="google"

    def on_GOOGLE(self):

        try:
            jsoned=json.loads(self.TOOL_CALL_output)
            search_query=json.loads(jsoned["arguments"])["search_query"]
        except Exception as e:
            logger.warning(f"on_GOOGLE_handler: {str(e)}")
            self.error = str(e)
            self.content = []
            return

        logger.info(f"on_GOOGLE_handler: search_query='{search_query}'")

        # required attributes
        ttt = self.ttt
        n_search = self.n_search if hasattr(self,"n_search") else 5

        self.relevances=self.handle_GOOGLE(
            ttt=ttt,
            search_query=search_query,
            n_search=n_search)
        self.content=self.relevances

        # Prepare for GENERATE (aka tool_prompt)
        # tool_prompt = f"""👩‍🔬, use only the information provided to you by the user to answer the user''s question.
        #     👩‍🔬, whenever possible, do not simply answer the question but try to be as informative as you can.
        #     Remember, these information are scraped from the web so you may need to proofread and edit the content before responding.
        #     👩‍🔬 will reply in point forms, precede each point with a newline "\n", and be precise in your articulation.
        #     👩‍🔬 will provide your own reasoned subjective perspective, noting where your view differs from or expands on the contents.
        #     Rules:
        #         - Consolidate the materials provided by the user and then organise them point by point.
        #         - Don't just answer the question, be as informative as you can. For example, provide and proofread some background information or fun-fact to support your answer and make it interesting.
        #         - Begin your report by saying `According to my online research,...`
        #         - Always provide your answers in point form.
        #     """
        from gai.lib.dialogue.dialogue_utils import ExtractRecap
        recap=ExtractRecap(self.dialogue_messages)
        system_message = f"""Take into consideration the conversation <recap> below: <recap>{recap}</recap>
Refer to the following online search result from the google query `{search_query}`:
`{self.content}`.
Based on the recap and search result as context, answer the user's following question.
            """
        builder = MonologueMessageBuilder()
        self.monologue_messages=builder.AddSystemMessage(system_message
            ).AddUserMessage(self.user_message
            ).AddAssistantMessage().Build()
        self.tool_name="text"
        self.tool_choice="none"
        self.max_tokens=2000

        if hasattr(self, "state"):
            logger.info({"state": self.state, "data": self.content})
            self.step+=1
            self.results.append({"state": self.state, "result": self.content,"step": self.step})   
