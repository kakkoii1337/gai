from threading import Thread, Event, Lock
import os
import json
import asyncio

# File-based persistent registry
here = os.path.dirname(__file__)
REGISTRY_FILE = os.path.join(here, "persistent_thread_registry.json")

class ThreadManagerSingleton:
    _instance = None
    _lock = Lock()

    def __init__(self):
        if ThreadManagerSingleton._instance is not None:
            raise ValueError("An instantiation already exists!")
        ThreadManagerSingleton._instance = self

    @staticmethod
    def GetInstance():
        if ThreadManagerSingleton._instance is None:
            ThreadManagerSingleton()
        return ThreadManagerSingleton._instance

    def load_registry(self):
        if os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        return {}

    def run_thread(self, name, func):

        # Update the registry to support self-stopping threads
        data = self.load_registry()
        data[name] = {"stop": False}  # Register thread with stop state False
        with open(REGISTRY_FILE, "w") as f:
            json.dump(data, f)

        # Start a new loop
        def thread_func():
            async def wrapped_func():
                try:
                    await func()
                except Exception as e:
                    print(f"Error in thread {name}: {e}")
            asyncio.run(wrapped_func())

        # Start the thread
        thread = Thread(target=thread_func, name=name)
        thread.start()
        #thread.join()

    def stop_thread(self, name):
        with ThreadManagerSingleton._lock:

            # Update the registry to support self-stopping threads
            data = self.load_registry()
            if name in data:
                data[name]["stop"] = True
                with open(REGISTRY_FILE, "w") as f:
                    json.dump(data, f)
                print(f"Thread {name} marked to stop.")
            else:
                print(f"Thread {name} not found in the registry.")

    def is_stopped(self, name):
        data = self.load_registry()
        if name in data:
            return data[name]["stop"]
        return True
