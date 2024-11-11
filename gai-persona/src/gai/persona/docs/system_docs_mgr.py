import os
import uuid
from gai.rag.client.rag_client_async import RagClientAsync
from gai.persona.docs.pydantic.FlattenedAgentDocumentPydantic import FlattenedAgentDocumentPydantic
from gai.lib.common.logging import getLogger
from gai.lib.common.errors import InternalException
logger = getLogger(__name__)

class SystemDocsMgr:

    def __init__(self,rag_client:RagClientAsync=None):
        self.rag = rag_client
        
    async def list_documents_async(self, persona_id=None):
        docs = []
        try:
            if not persona_id:
                result = await self.rag.list_collections_async()
                collections=result["collections"]
            else:
                collections=[persona_id]

            for agent_id in collections:
                result = await self.rag.list_documents_async(collection_name=agent_id)
                if result:
                    for doc in result:
                        flattened_doc = FlattenedAgentDocumentPydantic(AgentId=agent_id,**doc.dict())

                        # Merge ChunkGroup[0] into Document Header for the UI
                        if doc and len(doc.ChunkGroups) > 0:
                            flattened_doc.ChunkGroupId = doc.ChunkGroups[0].Id
                            flattened_doc.ChunkSize = doc.ChunkGroups[0].ChunkSize
                            flattened_doc.ChunkOverlap = doc.ChunkGroups[0].Overlap
                            flattened_doc.ChunkCount = doc.ChunkGroups[0].ChunkCount
                        docs.append(flattened_doc)   
            return docs

        except Exception as e:
            id = str(uuid.uuid4())
            logger.error(f'agent_documents_router.list_documents_async: error={str(e)} id={id}')
            raise InternalException(id)