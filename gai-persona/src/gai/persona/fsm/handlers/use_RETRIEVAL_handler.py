import asyncio,re
from gai.lib.dialogue.MonologueMessageBuilder import MonologueMessageBuilder
from gai.rag.client.rag_client_async import RagClientAsync
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

class use_RETRIEVAL_handler:

    def handle_RETRIEVAL(self, rag: RagClientAsync, collection_name: str, search_query: str, n_rag: int):
        # Check if there is already a running event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop
            loop = None
        
        if loop and loop.is_running():
            # If there is a running loop, schedule the coroutine to run on it
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(asyncio.create_task(self._retrieve(rag, collection_name, search_query, n_rag)))
        else:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self._retrieve(rag, collection_name, search_query, n_rag))        


    async def _retrieve(self, rag: RagClientAsync, collection_name: str, search_query: str, n_rag: int):
        response = await rag.retrieve_async(collection_name=collection_name, query_texts=search_query, n_results=n_rag)
            
        if not response:
            raise Exception("on_Retrieve_Text: No documents retrieved.")
        docs = response
        documents = []
        if docs:
            for i, doc in enumerate(docs):
                text = doc['documents']
                text = re.sub(r'\s+', ' ', text)
                documents.append(text)
        return documents

    def use_retrieval(self):
        return self.tool_name=="retrieval"

    def on_RETRIEVAL(self):

        # required attributes
        rag = self.rag
        collection_name = self.collection_name
        user_message = self.user_message
        
        # Set default number of results to retrieve
        n_rag=4
        if hasattr(self, "n_rag"):
            n_results = self.n_rag

        self.chunks = self.handle_RETRIEVAL(
            rag=rag, 
            collection_name=collection_name, 
            search_query=user_message,
            n_rag=n_rag)
        self.content=self.chunks

        # Prepare for GENERATE (aka tool_prompt)
        # system_prompt = """👩‍🔬, use only the information provided to you by the user to answer the user''s question. 
        #     If the information is insufficient for 👩‍🔬 to derive an answer, just say ''I cannot find relevant information in my document store to answer the question correctly.'' 
        #     👩‍🔬 is to provide an in-depth analysis to the question based only on the information provided by the user and nothing more.
        #     👩‍🔬 will give a real-life example to support illustrating your point and contrasting it with a counter-example. 
        #     👩‍🔬 will also proofread and edit the content before responding. 
        #     👩‍🔬 will provide your own reasoned subjective perspective, noting where your view differs from or expands on the contents.
        #     Rules:
        #         - Consolidate the materials provided by the user and then organise them point by point.
        #         - Provide as much details as you can extract from the materials provided by the user.
        #         - Begin your report by saying `According to my document store,...`
        #         - Always provide your answers in point form.
        #     """
        tool_prompt = self.tool_prompts[self.tool_name]
        user_message = f"""
            Refer to the following context: `{self.content}`. 
            Based on the earlier context, answer the question {self.user_message}."
            """
        builder = MonologueMessageBuilder()
        self.monologue_messages=builder.AddSystemMessage(tool_prompt
            ).AddUserMessage(user_message
            ).AddAssistantMessage().Build()
        self.tool_name="text"
        self.tool_choice="none"
        self.max_new_tokens=2000
        self.max_tokens=4000

        if hasattr(self, "state"):
            logger.info({"state": self.state, "data": self.content})
            self.step+=1
            self.results.append({"state": self.state, "result": self.content,"step": self.step})   
