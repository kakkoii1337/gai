import uuid
import os
import json
import re
from datetime import datetime
import mimetypes
import asyncio
import websockets


# fastapi
from fastapi import APIRouter, Body, HTTPException, Header, Depends, Request,UploadFile,File,WebSocket,WebSocketDisconnect
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from gai.lib.common.errors import InternalException, DocumentNotFoundException
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.persona.prompts.pydantic.PromptPydantic import PromptPydantic
from gai.lib.common.utils import get_app_path
from gai.ttt.client.ttt_client import TTTClient
from gai.persona.docs.system_docs_mgr import SystemDocsMgr
from gai.rag.client.rag_client_async import RagClientAsync
from gai.persona.docs.pydantic.FlattenedAgentDocumentPydantic import FlattenedAgentDocumentPydantic
from gai.lib.common.errors import DuplicatedDocumentException
from gai.lib.config.config_utils import get_client_config

# Implementations Below
document_router = APIRouter()

here = os.path.dirname(__file__)

# POST /api/v1/persona/{personaId}/document/step/upload
# Description: Step 1 of 4 - Upload the agent document to a temporary directory on the API server.
@document_router.post("/api/v1/persona/{persona_id}/document/step/upload")
async def post_document_step_upload(
        persona_id: str,
        file: UploadFile = File(...)):

    # Create temp directory "/tmp/{agent_id}"
    temp_dir = os.path.join("/tmp", persona_id)
    os.makedirs(temp_dir, exist_ok=True)

    # Create a random file name save the uploaded file into it
    temp_filename = str(uuid.uuid4()) + mimetypes.guess_extension(file.content_type)
    file_location = os.path.join(temp_dir, temp_filename)
    with open(file_location, "wb+") as file_object:
        content = await file.read()
        file_object.write(content)

    logger.info(f'document_router.post_document_step_upload: temp document created {temp_filename}')
    # return the temp file name
    return {
        "filename": temp_filename
    }

# POST /api/v1/persona/{persona_id}/document/step/header
# Description: Step 2 of 4 - Upload the agent document to RAG server to create header
@document_router.post("/api/v1/persona/{persona_id}/document/step/header")
async def post_document_step_header(persona_id:str, agent_document: FlattenedAgentDocumentPydantic=Body(...)):
    
    # validate
    if not agent_document.FileName or agent_document.AgentId != persona_id:
        raise HTTPException(status_code=400, detail="FileName and AgentId are required")

    try:
        rag_config = get_client_config("rag")
        rag=RagClientAsync(rag_config)

        temp_dir = os.path.join("/tmp", persona_id)
        tempfile_path = os.path.join(temp_dir, agent_document.FileName)        
        logger.info(f"document_router.post_document_step_header: creating header...")

        result = await rag.step_header_async(
            collection_name=agent_document.AgentId,     # agent_id
            file_path=tempfile_path,                    # tmpfile_path
            file_type=agent_document.FileType,
            title=agent_document.Title,
            source=agent_document.Source,
            authors=agent_document.Authors,
            publisher=agent_document.Publisher,
            published_date=agent_document.PublishedDate,
            comments=agent_document.Comments,
            keywords=agent_document.Keywords)
        return result
    except DuplicatedDocumentException:
        raise
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"document_router.post_document_step_header: {id} Error=Failed to create document header,{str(e)}")
        raise InternalException(id)
    
# POST /api/v1/persona/{persona_id}/document/step/split
# Description: Step 3 of 4 - Split file and save chunks on RAG server
class DocumentSplitRequest(BaseModel):
    DocumentId: str
    ChunkSize: int = 1000
    ChunkOverlap: int = 100
@document_router.post("/api/v1/persona/{persona_id}/document/step/split")
async def post_document_step_split(
    persona_id:str,
    req: DocumentSplitRequest = Body(...)
    ):
    
    # validate input
    if not persona_id or not req.DocumentId:
        raise HTTPException(status_code=400, detail="agent_id and document_id are required")
    
    try:
        rag_config = get_client_config("rag")
        rag=RagClientAsync(config=rag_config)

        logger.info(f"document_router.post_document_step_split: creating header...")

        result = await rag.step_split_async(
            collection_name=persona_id,
            document_id=req.DocumentId,
            chunk_size=req.ChunkSize,
            chunk_overlap=req.ChunkOverlap
        )
        return result
    except DuplicatedDocumentException:
        raise
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"document_router.post_document_step_split: {id} Error=Failed to split chunks,{str(e)}")
        raise InternalException(id)
    
### POST /api/v1/persona/{persona_id}/document/step/index
# Description: Step 4 of 4 - Index chunks into vector database
class DocumentIndexRequest(BaseModel):
    document_id: str
    chunkgroup_id: str
@document_router.post("/api/v1/persona/{persona_id}/document/step/index")
async def post_document_step_index(persona_id:str,
                           req: DocumentIndexRequest=Body(...)):
    
    # validate input
    if not persona_id or not req.document_id or not req.chunkgroup_id:
        raise HTTPException(status_code=400, detail="agent_id, document_id, and chunkgroup_id are required")

    async def callback_async(status):
        global active_websocket
        logger.info(f"document_router.post_document_step_index: status={status}")
        if active_websocket:
            logger.debug(f"document_router.post_document_step_index: publish={status}")
            await active_websocket.send_text(json.dumps(status))

    try:
        rag_config = get_client_config("rag")
        rag=RagClientAsync(config=rag_config)        
        result = await rag.step_index_async(
            collection_name=persona_id,
            document_id=req.document_id,
            chunkgroup_id=req.chunkgroup_id,
            async_callback=callback_async)
        
        return {"chunk_ids": result.ChunkIds}
    except DuplicatedDocumentException:
        raise
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f"document_router.post_document_step_index: {id} Error=Failed to index chunks,{str(e)}")
        raise InternalException(id)


### GET /api/v1/persona/{persona_id}/documents
@document_router.get("/api/v1/persona/{persona_id}/documents")
async def get_persona_document_list(persona_id:str):
    rag_config = get_client_config("rag")
    mgr = SystemDocsMgr(
        rag=RagClientAsync(config=rag_config)
    )

    docs = await mgr.list_documents_async(persona_id=persona_id)
    return {
        "documents":docs
    }

# GET /api/v1/persona/{persona_id}/chunk/{chunk_id}
@document_router.get("/api/v1/persona/{persona_id}/document/{document_id}")
async def get_persona_document( persona_id,document_id):

    # validate input
    if not document_id:
        raise HTTPException(status_code=400, detail="document_id is required")
    
    try:
        rag_config = get_client_config("rag")
        rag=RagClientAsync(config=rag_config)
        chunk = await rag.get_document_header_async(collection_name=persona_id,document_id=document_id)
        return chunk
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f'document_router.get_document_async: error={str(e)}')
        raise InternalException(id)

# GET /api/v1/persona/{persona_id}/chunks/{chunkgroup_id}
@document_router.get("/api/v1/persona/{persona_id}/chunks/{chunkgroup_id}")
async def get_persona_document_chunk_list( persona_id,chunkgroup_id):

    # validate input
    if not chunkgroup_id:
        raise HTTPException(status_code=400, detail="chunkgroup_id is required")
    
    try:
        rag_config = get_client_config("rag")
        rag=RagClientAsync(config=rag_config)
        return await rag.list_chunks_async(chunkgroup_id=chunkgroup_id)
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f'document_router.get_list_chunks_async: error={str(e)}')
        raise InternalException(id)

# GET /api/v1/persona/{persona_id}/chunk/{chunk_id}
@document_router.get("/api/v1/persona/{persona_id}/chunk/{chunk_id}")
async def get_persona_document_chunk( persona_id,chunk_id):

    # validate input
    if not chunk_id:
        raise HTTPException(status_code=400, detail="chunk_id is required")
    
    try:
        rag_config = get_client_config("rag")
        rag=RagClientAsync(config=rag_config)
        chunk = await rag.get_document_chunk_async(collection_name=persona_id,chunk_id=chunk_id)
        return chunk
    except Exception as e:
        id = str(uuid.uuid4())
        logger.error(f'document_router.get_chunk_async: error={str(e)}')
        raise InternalException(id)

# DELETE /api/v1/persona/{persona_id}/document/{document_id}
@document_router.delete("/api/v1/persona/{persona_id}/document/{document_id}")
async def delete_persona_document( persona_id, document_id):
    
    # validate input
    if not persona_id or not document_id:
        raise HTTPException(status_code=400, detail="persona_id and document_id are required")

    try:
        rag_config = get_client_config("rag")
        rag=RagClientAsync(config=rag_config)
        await rag.delete_document_async(persona_id, document_id)
        return {"message":f"document {document_id} deleted"}
    except DocumentNotFoundException:
        raise
    except Exception as e:
        id = uuid.uuid4()
        logger.error(f'agent_documents_router.delete_document_async: error={str(e)}')
        raise InternalException(id)


    
# Websocket -------------------------------------------------------------------------------------------------------------------------------------------

active_websocket = None

# WEBSOCKET "/api/v1/persona/{persona_id}/step/index/ws"
# This endpoint is only required for maintaining a websocket connection to provide real-time status updates.
# The actual work is done by ws_manager.
@document_router.websocket("/api/v1/persona/{persona_id}/document/step/index/ws")
async def index_file_websocket_async(websocket:WebSocket, persona_id):
    global active_websocket
    await websocket.accept()
    active_websocket=websocket
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        del websocket
    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"websocket closed.")