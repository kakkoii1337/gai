import uuid
import asyncio
import os
import json
import os
from gai.mace.node.thread_manager import ThreadManagerSingleton

# File-based persistent registry
here = os.path.dirname(__file__)
REGISTRY_FILE = os.path.join(here,"persistent_thread_registry.json")
thread_registry = {}

class TestServer:
    counter = 0

    def __init__(self,name):
        self.name=name

    async def serve(self):
        # if os.path.exists("/tmp/counter.txt"):
        #     os.remove("/tmp/counter.txt")
        with open("/tmp/counter.txt", "w") as f:
            f.write(str(self.counter))

        tm = ThreadManagerSingleton.GetInstance()
        is_stopped=tm.is_stopped(name=self.name)
        while not is_stopped:
            self.counter += 1
            with open("/tmp/counter.txt", "w") as f:
                f.write(f"{self.name}:{self.counter}")
            await asyncio.sleep(1)
            is_stopped=tm.is_stopped(name=self.name)

        print(f"Thread {self.name} stopped.")

    def get_counter(self):
        return self.counter
