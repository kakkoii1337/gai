import os
os.environ["LOG_LEVEL"] = "DEBUG"
import json
import argparse
from rich.console import Console
console=Console()
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.lib.common.utils import get_app_path

# config from args
parser = argparse.ArgumentParser(description="Start Gai Agent service.")
parser.add_argument('--nats', type=str, default="nats://localhost:4222", help='NATS servers address')
parser.add_argument("--all", action="store_true", help="Load all routers")
parser.add_argument('--persona', type=str, help='Specify the persona (e.g., sara)')
parser.add_argument('--persona-dir', type=str, help='Specify the persona (e.g., sara)')
parser.add_argument('--ttt', type=str, default="http://localhost:12031", help='TTT host and port')
parser.add_argument('--rag', type=str, default="http://localhost:12036", help='RAG host and port')
args = parser.parse_args()
persona_name = args.persona
nats=args.nats
ttt=args.ttt
rag=args.rag
persona_dir=args.persona_dir

# override by environ
if os.environ.get("GAIMACE_PERSONA",None):
    persona_name=os.environ["GAIMACE_PERSONA"]
if os.environ.get("GAIMACE_TTT",None):
    ttt=os.environ["GAIMACE_TTT"]
if os.environ.get("GAIMACE_RAG",None):
    rag=os.environ["GAIMACE_RAG"]
if os.environ.get("GAIMACE_NATS",None):
    nats=os.environ["GAIMACE_NATS"]
if os.environ.get("GAIMACE_PERSONA_DIR",None):
    persona_dir=os.environ["GAIMACE_PERSONA_DIR"]

# MaceServer Class
from gai.mace.node.mace_server import MaceServer      

# Start Mace service
async def main():

    console.print(f"[yellow]Building persona: {persona_name}[/]")
    console.print(f"[yellow]ttt={ttt}[/]")

    # Load provisioning details and build persona
    from gai.persona.persona_builder import PersonaBuilder
    from gai.persona.profile.pydantic.ProvisionAgentPydantic import ProvisionAgentPydantic

    # import persona

    # Either persona_dir or persona_name must be provided but persona_dir takes precedence
    import_dir=None
    if persona_name:
        import_dir=os.path.abspath(os.path.join("persona","data",persona_name))
    if persona_dir:
        import_dir=os.path.expanduser(persona_dir)
    if not import_dir:
        raise Exception("Please provide either persona_dir or persona_name")

    console.print(f"[yellow]import_dir={import_dir}[/]")
    

    builder = PersonaBuilder()
    builder = await builder.import_async(import_dir=import_dir)
    persona = builder.build()
    if hasattr(persona,"ttt") and persona.ttt:
        persona.ttt.url=ttt
    if hasattr(persona,"rag") and persona.rag:
        persona.rag.url=rag

    node = await MaceServer.create(
        servers=nats,
        persona=persona)
    await node.serve()

if __name__ == "__main__":
    logger.info("Gai Persona version 0.0.1")
    logger.info(f"Starting persona: {args.persona}")
    import asyncio
    asyncio.run(main())