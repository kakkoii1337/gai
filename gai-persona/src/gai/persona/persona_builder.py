import uuid
import os
import json
from io import BytesIO
from PIL import Image
import yaml
import asyncio
import mimetypes

# Gai
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.lib.common.errors import (
    InternalException
    )

# Agent Profile
from gai.persona.persona import Persona
from gai.persona.profile.pydantic.ProvisionAgentPydantic import ProvisionAgentPydantic
from gai.persona.profile.pydantic.AgentPydantic import AgentPydantic
from gai.persona.profile.pydantic.AgentClassTypePydantic import AgentClassTypePydantic

# Flows
from gai.persona.fsm.pydantic.AgentFlowPydantic import AgentFlowPydantic

# Tools
from gai.persona.tools.pydantic.ToolPydantic import ToolPydantic

# Prompts
from gai.persona.prompts.pydantic.PromptPydantic import PromptPydantic

# Images
from gai.persona.images.pydantic.AgentImagePydantic import AgentImagePydantic
from gai.persona.images.system_images_mgr import SystemImagesMgr

# Documents
from gai.persona.docs.pydantic.FlattenedAgentDocumentPydantic import FlattenedAgentDocumentPydantic
from gai.rag.client.dtos.indexed_doc import IndexedDocPydantic

# LLM
from gai.tti.client.tti_client import TTIClient
from gai.ttt.client.ttt_client import TTTClient
from gai.rag.client.rag_client_async import RagClientAsync

class PersonaBuilder:

    def __init__(self, 
                 provision: ProvisionAgentPydantic=None,
                 agent_id:str="00000000-0000-0000-0000-000000000000",
                 caller_id:str="00000000-0000-0000-0000-000000000000",
                 dialogue_id:str="00000000-0000-0000-0000-000000000000",
                 api_host:str="http:/localhost:12033",
                 ttt_client: TTTClient=None,
                 rag_client: RagClientAsync=None
                 ):
        if not provision:
            provision = ProvisionAgentPydantic(Name=f"Agent-{str(uuid.uuid4())}")
        self.agent_id=agent_id
        self.caller_id=caller_id
        self.dialogue_id=dialogue_id
        self.api_host=api_host
        self.provision = provision
        self.ttt = ttt_client
        self.rag = rag_client
        self.tools = []
        self.docs: list[IndexedDocPydantic] = []
        self.flows = []
        self.agent_tools = []
        self.agent_image=None
        self.agent_flow=None
        self.here = os.path.dirname(__file__)
        
    def list_agent_class(self) -> list[AgentClassTypePydantic]:
        data_path = os.path.join(self.here, "profile", "data","agent_classes.json")
        with open(data_path,"r") as f:
            list = json.load(f)
            list = [AgentClassTypePydantic(**item) for item in list]
            return list

    def set_class(self, class_name:str):
        try:
            cls = next(cls for cls in self.list_agent_class() if cls.ClassName == class_name)
            if not cls:
                raise Exception("Agent class not found.")
            self.class_type=cls
            return self
        except Exception as e:
            logger.error(f"AgentProfile.set_class: {str(e)}")
            raise e
        
    def list_agent_prompts(self):
        data_path = os.path.join(self.here, "prompts","data","prompt_templates.json")
        with open(data_path,"r") as f:
            list = json.load(f)
            list = [PromptPydantic(**item) for item in list]
            return list

    def set_prompt(self, prompt_name:str):
        try:
            custom_prompt = next((prompt for prompt in self.list_agent_prompts() if prompt.Name == prompt_name), None)
            if not custom_prompt:
                raise Exception("Prompt not found.")
            self.custom_prompt=custom_prompt
            return self
        except Exception as e:
            logger.error(f"AgentProfile.set_prompt: {str(e)}")
            raise e
        
    def list_agent_flows(self):
        if not self.flows:

            data_path = os.path.join(self.here, "fsm", "data","agent_flows.json")
            with open(data_path,"r") as f:
                list = json.load(f)
                self.flows = [AgentFlowPydantic(**item) for item in list]
        return self.flows
    
    def add_agent_flow(self, flow_name:str, state_diagram:str, description:str=None):
        
        try:
            flows = self.list_agent_flows()
            flow = next((flow for flow in flows if flow.Name == flow_name), None)
            if flow:
                raise Exception("Flow already added.")
            flow = AgentFlowPydantic(
                Id=str(uuid.uuid4()),
                Name=flow_name,
                StateDiagram=state_diagram,
                Description=description
            )
            self.flows.append(flow)
            return self
        except Exception as e:
            logger.error(f"AgentProfile.add_agent_flow: {str(e)}")
            raise e

    def set_flow(self, flow_name:str):
        try:
            flow = next((flow for flow in self.list_agent_flows() if flow.Name == flow_name), None)
            if not flow:
                raise Exception("Agent flow not found.")
            self.agent_flow=flow
            return self
        except Exception as e:
            logger.error(f"AgentProfile.set_flow: {str(e)}")
            raise e

    def list_tools(self):
        if not self.tools:
            data_path = os.path.join(self.here, "tools","data","tool_templates.json")
            with open(data_path,"r") as f:
                list = json.load(f)
                self.tools = [ToolPydantic(**item) for item in list]
        return self.tools

    def add_tool(self, tool_name:str, tool_schema:str, tool_prompt:str):

        try:
            tools = self.list_tools()
            tool = next((tool for tool in tools if tool.ToolName == tool_name), None)
            if tool:
                raise Exception("Tool already added.")
            tool = ToolPydantic.from_schema(
                schema=tool_schema,
                tool_prompt=tool_prompt,
                id=str(uuid.uuid4()),
                caller_id=self.caller_id,
                usage_type="private"
            )
            self.tools.append(tool)
            return self
        except Exception as e:
            logger.error(f"AgentTools.add_agent_tool: {str(e)}")
            raise e

    def equip_tool(self, tool_name:str):
        try:
            tool = next((tool for tool in self.list_tools() if tool.ToolName == tool_name), None)
            if not tool:
                raise Exception("Tool not found.")
            if self.agent_tools:
                equipped_tool = next((tool for tool in self.agent_tools if tool.ToolName == tool_name), None)
                if equipped_tool:
                    raise Exception("Tool already equipped.")
            self.agent_tools.append(tool)
            return self
        except Exception as e:
            logger.error(f"AgentTools.add_agent_tool: {str(e)}")
            raise e

    def set_ttt(self, ttt_client:TTTClient):
        self.ttt = ttt_client
        return self

    def set_rag(self, rag_client:RagClientAsync):
        self.rag = rag_client
        return self

    def create_image(self, tti_client: TTIClient):
        try:
            image_styles=self.provision.AgentImageStyles
            images_mgr=SystemImagesMgr(tti_client=tti_client)
            self.agent_image=images_mgr.generate_image(self.agent_id, self.provision.Name, self.provision.AgentTraits, image_styles, self.provision.AgentDescription)
            return self
        except Exception as e:
            id = str(uuid.uuid4())
            logger.error(f'AgentProfile.create_image: error={str(e)} id={id}')
            raise InternalException(id)

    def save_temp_document(self, file_content: bytes, file_content_type: str) -> str:
        """
        Save the uploaded document to a temporary directory and return the temp file name.
        This function is framework-agnostic and doesn't rely on FastAPI-specific components.
        """
        try:
            # Create temp directory "/tmp/{agent_id}"
            temp_dir = os.path.join("/tmp", self.agent_id)
            os.makedirs(temp_dir, exist_ok=True)

            # Create a random file name and guess the file extension based on content type
            temp_filename = str(uuid.uuid4()) + mimetypes.guess_extension(file_content_type)
            file_location = os.path.join(temp_dir, temp_filename)

            # Save file content to the temporary file
            with open(file_location, "wb") as file_object:
                file_object.write(file_content)

            return temp_filename
        except Exception as e:
            id = str(uuid.uuid4())
            logger.error(f"Failed to save uploaded document to tempfile. {id} Error=Failed to create document header,{str(e)}")
            raise InternalException(id)

    async def index_document_async(self,
            file_path:str,
            title:str,
            source:str,
            async_callback
            ):

        # Save a copy of the document to a temporary file
        temp_filename = ""
        with open(file_path, 'rb') as f:
            file_content = f.read()
            file_content_type = "text/plain"
            if file_path.endswith('.pdf'):
                file_content_type = "application/pdf"
            temp_filename = self.save_temp_document(file_content=file_content, file_content_type=file_content_type)

        # Create the document header
        logger.info(f"Creating header for AgentId {self.agent_id} at {file_path}")
        doc_header = await self.rag.step_header_async(
            collection_name=self.agent_id,
            file_path=f"/tmp/{self.agent_id}/{temp_filename}",
            file_type="pdf" if file_path.endswith('.pdf') else "txt",
            title=title,
            source=source
        )

        # check if already exists
        exist = next((doc for doc in self.docs if doc.Id == doc_header.Id),None)
        if exist:
            return self
        self.docs.append(doc_header)

        # Split the document into chunks
        from gai.rag.client.dtos.split_doc_request import SplitDocRequestPydantic
        req = SplitDocRequestPydantic(
            DocumentId=doc_header.Id,
            ChunkSize=1000,
            ChunkOverlap=100,
        )
        logger.info(f"Splitting document {req.DocumentId} for agent {self.agent_id} with chunk size {req.ChunkSize} and overlap {req.ChunkOverlap}")
        chunkgroup = await self.rag.step_split_async(
            collection_name=self.agent_id,
            document_id=req.DocumentId,
            chunk_size=req.ChunkSize,
            chunk_overlap=req.ChunkOverlap
        )

        # Index the document chunks
        logger.info(f"Indexing document {doc_header.Id} for agent {self.agent_id} with chunk group {chunkgroup.Id}")
        await self.rag.step_index_async(
            collection_name=self.agent_id,
            document_id=doc_header.Id,
            chunkgroup_id=chunkgroup.Id,
            async_callback=async_callback
        )

        doc_header.File = file_content

        return self
        
    def build(self):

        # Create profile
        agent_profile = AgentPydantic(
            Id=self.agent_id,
            AssociatedUserId=self.caller_id,
            Name=self.provision.Name, 
            AgentTraits=",".join(self.provision.AgentTraits),
            AgentSkills=",".join(self.provision.AgentSkills),
            AgentImageStyles=",".join(self.provision.AgentImageStyles), 
            UsageType=self.provision.UsageType,
            AgentDescription=self.provision.AgentDescription, 
            ImageDataUrl=self.provision.ImageDataUrl, 
            ImageUrl="",
            ThumbnailUrl="",
            )
        
        # set agent class
        self.set_class(self.provision.ClassName)
        agent_profile.ClassType = self.class_type

        # set agent prompt
        if hasattr(self,"custom_prompt") and self.custom_prompt:
            agent_profile.CustomPrompt = self.custom_prompt

        # set agent flow
        if not hasattr(self,"agent_flow") or not self.agent_flow:
            self.set_flow("Simple Text Flow")
        agent_profile.AgentFlow = self.agent_flow

        # set tools
        if hasattr(self,"agent_tools") and self.agent_tools:
            agent_profile.Tools = self.agent_tools

        # Build Persona
        persona = Persona(
            caller_id=self.caller_id,
            dialogue_id=self.dialogue_id,
            agent_profile=agent_profile,
            agent_image=self.agent_image if hasattr(self,"agent_image") else None,
            ttt=self.ttt,
            rag=self.rag
        )
        return persona

    async def export_async(self, export_dir):
        logger.info(f"persona_builder: Exporting to {export_dir}")
        
        # check if not exist, create.
        export_dir = os.path.abspath(export_dir)        
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # Export agent provision
        with open(os.path.join(export_dir,"provision.yaml"),"w") as f:
            provision = self.provision.dict()

            # export others
            provision["CustomPrompt"] = self.custom_prompt.dict() if hasattr(self,"custom_prompt") and self.custom_prompt else None
            provision["AgentFlow"] = self.agent_flow.dict() if hasattr(self,"agent_flow") and self.agent_flow else None
            provision["AgentTools"] = [tool.dict() for tool in self.agent_tools] if hasattr(self,"agent_tools") and self.agent_tools else None

            # Export TTT
            if self.ttt:
                provision["TTT"] = self.ttt.config

            # Export RAG
            if self.rag:
                provision["RAG"]=self.rag.config
                
            yaml.dump(provision,f)

        # Export image
        if self.agent_image:
            image_dir = os.path.join(export_dir,"img") 
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            image = self.agent_image
            with open(os.path.join(image_dir,"image.json"),"w") as f:
                json.dump({
                    "Id": image.Id,
                    "AgentImagePrompt": image.AgentImagePrompt,
                    "AgentImageNegativePrompt": image.AgentImageNegativePrompt
                },f,indent=4)
            with open(os.path.join(image_dir,"512x512.png"),"wb") as f:
                f.write(BytesIO(image.Image512).getvalue())
            with open(os.path.join(image_dir,"256x256.png"),"wb") as f:
                f.write(BytesIO(image.Image256).getvalue())
            with open(os.path.join(image_dir,"128x128.png"),"wb") as f:
                f.write(BytesIO(image.Image128).getvalue())
            with open(os.path.join(image_dir,"64x64.png"),"wb") as f:
                f.write(BytesIO(image.Image64).getvalue())

        # Export agent flow
        if self.agent_flow:
            with open(os.path.join(export_dir,"flow.md"),"w") as f:
                f.write("```mermaid\n")
                f.write(self.agent_flow.StateDiagram)
                f.write("\n```")

        # Export Documents
        if self.docs:
            doc_dir = os.path.join(export_dir,"docs")
            if not os.path.exists(doc_dir):
                os.makedirs(doc_dir)
            
            for doc in self.docs:
                # source file
                dest_path = os.path.join(doc_dir,doc.FileName)
                with open(dest_path,"wb") as f:
                    f.write(doc.File)

            # Custom JSON encoder to handle datetime serialization
            from datetime import datetime
            class CustomJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()  # Convert datetime to ISO format string
                    return super().default(obj)            
            with open(os.path.join(doc_dir,"manifest.json"),"w") as f:
                manifest=[]
                for doc in self.docs:
                    doc = doc.model_dump()
                    doc.pop("File",None)
                    manifest.append(doc)
                json.dump(manifest,f,indent=4,cls=CustomJSONEncoder)

        return self

    async def import_async(self, import_dir):

        # Import agent profile
        with open(os.path.join(import_dir,"provision.yaml"),"r") as f:
            provision_data = yaml.load(f,Loader=yaml.FullLoader)
            self.provision = ProvisionAgentPydantic(**provision_data)
            
            # Import other
            self.custom_prompt = PromptPydantic(**provision_data["CustomPrompt"]) if provision_data.get("CustomPrompt",None) else None
            self.agent_flow = AgentFlowPydantic(**provision_data["AgentFlow"]) if provision_data.get("AgentFlow",None) else None
            self.agent_tools = [ToolPydantic(**tool) for tool in provision_data["AgentTools"]] if provision_data.get("AgentTools",None) else []
            if provision_data.get("TTT",None):
                self.ttt = TTTClient(provision_data["TTT"])
            if provision_data.get("RAG",None):
                self.rag = RagClientAsync(provision_data["RAG"])

        # Import image
        image_dir = os.path.join(import_dir,"img")
        self.agent_image=None
        if os.path.exists(image_dir) and os.path.isdir(image_dir):
            with open(os.path.join(image_dir,"image.json"),"r") as f:
                image_data = json.load(f)
            with open(os.path.join(image_dir,"512x512.png"),"rb") as f:
                image512 = f.read()
            with open(os.path.join(image_dir,"256x256.png"),"rb") as f:
                image256 = f.read()
            with open(os.path.join(image_dir,"128x128.png"),"rb") as f:
                image128 = f.read()
            with open(os.path.join(image_dir,"64x64.png"),"rb") as f:
                image64 = f.read()
            self.agent_image = AgentImagePydantic(
                Id=image_data["Id"],
                AgentImagePrompt=image_data["AgentImagePrompt"],
                AgentImageNegativePrompt=image_data["AgentImageNegativePrompt"],
                Image512=image512,
                Image256=image256,
                Image128=image128,
                Image64=image64,
                ImageType="png"
            )

        # Import documents
        doc_dir = os.path.join(import_dir,"docs")
        self.docs=[]
        if os.path.exists(doc_dir) and os.path.isdir(doc_dir) and os.listdir(doc_dir):

            # Create listener
            manifest_path = os.path.join(doc_dir,"manifest.json")
            with open(manifest_path,"r") as f:
                manifest = json.load(f)

            for doc in manifest:
                with open(os.path.join(doc_dir,doc["FileName"]),"rb") as f:
                    doc["File"] = f.read()

                self.docs.append(IndexedDocPydantic(**doc))
        
        return self

