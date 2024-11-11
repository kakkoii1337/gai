import os
os.environ["LOG_LEVEL"] = "DEBUG"
import asyncio
from threading import Thread    
import argparse
from fastapi import FastAPI
import uvicorn
from rich.console import Console
console=Console()
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.persona.profile.api.profile_router import profile_router
from gai.persona.images.api.image_router import image_router
from gai.persona.prompts.api.prompt_router import prompt_router
from gai.persona.tools.api.tool_router import tool_router
from gai.persona.docs.api.document_router import document_router
from gai.mace.user.api.persona.persona_router import persona_router
from gai.mace.user.api.dialogue.dialogue_router import dialogue_router,on_chat
from gai.mace.user.mace_client import MaceClient
from fastapi.middleware.cors import CORSMiddleware

# Set up argparse to handle command-line arguments
parser = argparse.ArgumentParser(description="Start Gai Agent service.")
parser.add_argument('--nats', type=str, default="nats://localhost:4222", help='Specify nats address')
parser.add_argument('--persona-dir', type=str, default="~/.gai/persona/00000000-0000-0000-0000-000000000000", help='Specify the persona directory.')
parser.add_argument("--all", action="store_true", help="Load all routers")
parser.add_argument('--ttt', type=str, default="http://localhost:12031", help='TTT host and port')
parser.add_argument('--rag', type=str, default="http://localhost:12036", help='RAG host and port')
parser.add_argument('--tti', type=str, default="http://localhost:12035", help='TTT host and port')
parser.add_argument('--tts', type=str, default="http://localhost:12032", help='TTT host and port')
parser.add_argument('--stt', type=str, default="http://localhost:12033", help='TTT host and port')
parser.add_argument('--itt', type=str, default="http://localhost:12034", help='TTT host and port')

args = parser.parse_args()
nats = args.nats
ttt=args.ttt
rag=args.rag
tti=args.tti
persona_dir=args.persona_dir

# override by environ
if os.environ.get("GAIMACE_NATS",None):
    nats=os.environ["GAIMACE_NATS"]
if os.environ.get("GAIMACE_TTT",None):
    ttt=os.environ["GAIMACE_TTT"]
if os.environ.get("GAIMACE_RAG",None):
    rag=os.environ["GAIMACE_RAG"]
if os.environ.get("GAIMACE_TTI",None):
    tti=os.environ["GAIMACE_TTI"]
if os.environ.get("GAIMACE_PERSONA_DIR",None):
    persona_dir=os.environ["GAIMACE_PERSONA_DIR"]

console.print(f"[yellow]connection={nats}[/]")

# Setup APIs
app = FastAPI()
app.include_router(profile_router)
app.include_router(image_router)
app.include_router(prompt_router)
app.include_router(tool_router)
app.include_router(document_router)
app.include_router(dialogue_router)
app.include_router(persona_router)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5123"],  # Specify the origins (use ["*"] for all origins)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods or specify specific ones ["POST", "GET"]
    allow_headers=["*"],  # Allow all headers or specify specific ones
)

def run_server_coroutine(node):
    # Set up a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the coroutine using the new event loop
        loop.run_until_complete(node.serve())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())  # Close all async generators
        loop.close()  # Safely close the loop

# Startup
mace_client:MaceClient=None
@app.on_event("startup")
async def startup_event():
    global mace_client
    mace_client = await MaceClient.create(
        servers="nats://localhost:4222"
    )
    await mace_client.subscribe(async_chat_handler=on_chat)
    app.state.mace_client = mace_client

    # Mace Server
    from gai.mace.server.mace_server import MaceServer      
    from gai.persona.persona_builder import PersonaBuilder
    from gai.persona.profile.pydantic.ProvisionAgentPydantic import ProvisionAgentPydantic

    # Either persona_dir or persona_name must be provided but persona_dir takes precedence
    import_dir=os.path.expanduser(persona_dir)
    console.print(f"[yellow]import_dir={import_dir}[/]")

    builder = PersonaBuilder()
    builder = await builder.import_async(import_dir=import_dir)
    persona = builder.build()
    if hasattr(persona,"ttt") and persona.ttt:
        persona.ttt.url=ttt
    if hasattr(persona,"rag") and persona.rag:
        persona.rag.url=rag

    node = await MaceServer.create(servers=nats, persona=persona)
    thread = Thread(target=run_server_coroutine, args=(node,))
    thread.start()
            

if __name__ == "__main__":
    logger.info("Gai Local App Server version 0.0.1")
    uvicorn.run(app, host="0.0.0.0", 
                port=12033,
                ws_ping_interval=20,    # Server will ping every 20 seconds
                ws_ping_timeout=300     # Server will wait 5 min for pings before closing
                )