import asyncio,re
from gai.rag.client.rag_client_async import RagClientAsync
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

class on_ASYNC_RETRIEVAL_handler:

    async def __call__(self,rag:RagClientAsync,collection_name:str, search_query:str):
        response = await rag.retrieve_async(collection_name=collection_name, query_texts=search_query, n_results=4)
            
        if not response:
            raise Exception("on_Retrieve_Text: No documents retrieved.")
        docs = response
        documents=[]
        if docs:
            for i, doc in enumerate(docs):
                title = f"Document[{i}](ID:{doc['ids']}):"
                text = doc['documents']
                text = re.sub(r'\s+', ' ', text)
                doc = f"{title}\n{text}"
                doc = {
                    "title": title,
                    "text": text
                }
                documents.append(doc)
        return documents
