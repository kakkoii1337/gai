import os
from gai.mace.server.mace_server import MaceServer      
from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

persona_name = "Sara"

async def main():

    class MockPersona:
        class AgentProfile:
            def __init__(self):
                self.Name = persona_name
        def __init__(self):
            self.agent_profile = self.AgentProfile()
        def act(self,user_message,stop_conditions=None,n_search=None):
            response=f"Hi, my name is {self.agent_profile.Name}"
            response=response.split(" ")
            for chunk in response:
                yield chunk+" "

    persona = MockPersona()

    node = await MaceServer.create(
        servers="nats://nats01:4222",
        persona=persona)
    await node.serve()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())