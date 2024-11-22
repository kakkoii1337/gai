import os
os.environ["LOG_LEVEL"] = "DEBUG"
import asyncio
from threading import Thread    
import argparse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from rich.console import Console
console=Console()
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.mace.user.api.persona.persona_router import persona_router
from gai.mace.user.api.dialogue.dialogue_router import dialogue_router,on_chat
from gai.mace.user.mace_client import MaceClient
from gai.mace.node.mace_server import MaceServer
from gai.persona.profile.api.profile_router import profile_router
from gai.persona.profile.pydantic.ProvisionAgentPydantic import ProvisionAgentPydantic
from gai.persona.images.api.image_router import image_router
from gai.persona.prompts.api.prompt_router import prompt_router
from gai.persona.tools.api.tool_router import tool_router
from gai.persona.docs.api.document_router import document_router
from gai.persona.persona_builder import PersonaBuilder

# command-line arguments
parser = argparse.ArgumentParser(description="Start Gai Agent service.")
parser.add_argument('--mode', type=str, default="user", help='Either "user"(default) or "node"')
parser.add_argument('--nats', type=str, default="nats://localhost:4222", help='Specify nats address')
parser.add_argument("--all", action="store_true", help="Load all routers")
parser.add_argument('--persona', type=str, default="Sara", help='Specify the persona (e.g., Sara)')
parser.add_argument('--ttt', type=str, default="http://localhost:12031", help='TTT host and port')
parser.add_argument('--rag', type=str, default="http://localhost:12036", help='RAG host and port')
parser.add_argument('--tti', type=str, default="http://localhost:12035", help='TTT host and port')
parser.add_argument('--tts', type=str, default="http://localhost:12032", help='TTT host and port')
parser.add_argument('--stt', type=str, default="http://localhost:12033", help='TTT host and port')
parser.add_argument('--itt', type=str, default="http://localhost:12034", help='TTT host and port')
args = parser.parse_args()
mode = args.mode
persona_name = args.persona
nats = args.nats
ttt=args.ttt
rag=args.rag
tti=args.tti

# environment arguments
if os.environ.get("GAIMACE_MODE",None):
    mode=os.environ["GAIMACE_MODE"]
if os.environ.get("GAIMACE_NATS",None):
    nats=os.environ["GAIMACE_NATS"]
if os.environ.get("GAIMACE_PERSONA",None):
    persona_name=os.environ["GAIMACE_PERSONA"]
if os.environ.get("GAIMACE_TTT",None):
    ttt=os.environ["GAIMACE_TTT"]
if os.environ.get("GAIMACE_RAG",None):
    rag=os.environ["GAIMACE_RAG"]
if os.environ.get("GAIMACE_TTI",None):
    tti=os.environ["GAIMACE_TTI"]

# derived arguments
persona_dir = "~/.gai/persona/00000000-0000-0000-0000-000000000000"
if mode == "node":
    persona_dir=f"~/.gai/persona/nodes/{persona_name}"
import_dir=os.path.expanduser(persona_dir)

# Report arguments
console.print(f"[yellow]connection={nats}[/yellow]")
console.print(f"[yellow]import_dir={import_dir}[/yellow]")
console.print(f"[yellow]ttt={ttt}[/yellow]")
console.print(f"[yellow]rag={rag}[/yellow]")
console.print(f"[yellow]tti={tti}[/yellow]")

# Run Node
async def run_node():
    # import persona
    builder = PersonaBuilder()
    builder = await builder.import_async(import_dir=import_dir)
    persona = builder.build()
    node = await MaceServer.create(
        servers=nats,
        persona=persona)
    
    logger.info("Running Gai Mace Node")
    await node.serve()

# Run User
async def run_user(app):
    # Start custom persona thread
    async def start_persona():

        # Either persona_dir or persona_name must be provided but persona_dir takes precedence
        import_dir=os.path.expanduser(persona_dir)
        if os.path.exists(import_dir):
            console.print(f"[green]MACE node importing persona from {import_dir}.")

            async def run_server():
                builder = PersonaBuilder()
                builder = await builder.import_async(import_dir=import_dir)
                persona = builder.build()
                if persona.ttt is None:
                    from gai.ttt.client.ttt_client import TTTClient
                    # Get the ttt from environment not from gai.yml
                    persona.ttt = TTTClient({
                        "url": f"{ttt}//gen/v1/chat/completions",
                    })
                node = await MaceServer.create(
                    servers=nats,
                    persona=persona)
                await node.serve()

            from gai.mace.node.thread_manager import ThreadManagerSingleton            
            tm = ThreadManagerSingleton.GetInstance()
            tm.run_thread("User", run_server)           
            
        else:
            console.print(f"[pink]import_dir={import_dir}[/] not found. MACE node not started.")

    # Add this at the beginning, before your other routes
    @app.get("/")
    async def root():
        return "gaimace"

    # Setup APIs
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

    # Startup
    @app.on_event("startup")
    async def startup_event():
        mace_client = await MaceClient.create(
            servers=nats
        )
        await mace_client.subscribe(async_chat_handler=on_chat)
        app.state.mace_client = mace_client
        await start_persona()

if __name__ == "__main__":
    if mode == "node":
        asyncio.run(run_node())
    else:
        app = FastAPI()
        asyncio.run(run_user(app))
        logger.info("Running Gai Mace User")
        uvicorn.run(app, host="0.0.0.0", 
                    port=12033,
                    ws_ping_interval=20,    # Server will ping every 20 seconds
                    ws_ping_timeout=300     # Server will wait 5 min for pings before closing
                    )