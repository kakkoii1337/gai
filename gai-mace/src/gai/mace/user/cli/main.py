import asyncio
import re
import json
from nats.aio.msg import Msg
from aioconsole import ainput
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.console import Console
console = Console()

from gai.mace.user.mace_client import MaceClient
from gai.mace.pydantic.FlowMessagePydantic import FlowMessagePydantic
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

async def main():
    colors = {
        "Sara": "yellow",
        "Diana": "green",
        "Christine": "cyan"
    }
    combined_text = Text()  # To hold the chat messages content

    # MaceClient setup parameters
    seq_diagram = """
        sequenceDiagram
            User->>Sara
            Sara->>Diana
            Diana->>Christine
    """

    # Create MaceClient instance
    node = await MaceClient.create(servers="nats://localhost:4222")
    q = asyncio.Queue()

    # Define async callback for incoming messages
    async def on_chat(msg: Msg):
        data=msg.data.decode()
        if not data:
            return
        
        data=json.loads(data)
        pydantic = FlowMessagePydantic(**data)

        # Case 1: from "User" to Persona
        if pydantic.Sender == "User":
            # Ignore
            return
        
        # Case 2: from "Persona" to User
        if pydantic.Recipient == "User":
            if pydantic.Chunk:
                q.put(pydantic.Chunk)
            if pydantic.ChunkNo=="<eom>":
                q.put(None)

    # Subscribe to chat messages
    await node.subscribe(async_chat_callback=on_chat)

    # Initialize message panel with a placeholder text
    messages = "[dim]Output will appear here[/dim]\n\n"
    message_panel = Panel(messages, title="Messages", border_style="white", height=40)
    console.clear()
    console.print(message_panel)

    # Set up Live context to keep updating the message panel at the top
    with Live(console=console, refresh_per_second=1) as live:
        try:
            while True:
                user_input = await ainput("Enter message to broadcast (type 'exit' to quit): \n")
                live.update(message_panel)

                # Prepare the message panel at the top
                message_panel = Panel(combined_text if combined_text else messages, title="Messages", border_style="white", height=40)
                live.update(message_panel)

                if user_input.strip().lower() == "exit":
                    print("Exiting...")
                    await node.close()
                    break

                # Broadcast or process 'next' command
                if user_input.strip():
                    if user_input.strip().lower() == "next":
                        await node.next()
                    else:
                        await node.dialogue(msg=user_input)
                        # Append user input to the combined_text for continuity
                        combined_text.append(Text(f"User:\n\n{user_input}\n\n", style="white"))
                        # Update the Live panel with new content
                        live.update(Panel(combined_text, title="Messages", border_style="white", height=40))
                else:
                    await node.next()


        except KeyboardInterrupt:
            print("Interrupted! Exiting...")
            await node.close()

if __name__ == "__main__":
    asyncio.run(main())
