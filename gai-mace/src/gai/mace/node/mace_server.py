import json
import os
import base64
import time
import asyncio
from nats.aio.msg import Msg

from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.network.gainet_node import GaiNetNode
from gai.mace.flow_plan import FlowPlan
from gai.mace.pydantic.FlowMessagePydantic import FlowMessagePydantic
from gai.persona.persona_builder import PersonaBuilder
from gai.lib.dialogue.dialogue_store import DialogueStore
from gai.lib.dialogue.pydantic.DialogueMessagePydantic import DialogueMessagePydantic
from gai.mace.node.thread_manager import ThreadManagerSingleton

class MaceServer(GaiNetNode):

    # static props
    subscribed={}


    def __init__(self, servers, persona, is_user=False):
        super().__init__(servers,persona.agent_profile.Name)
        self.persona = persona
        self.other_content=""
        self.dialogue_store=persona.dialogue_store
        self.is_user=is_user
        self.subs=[]

    def _strip_xml(self,message):
        import re
        # This pattern matches the first and last XML tags in the string
        return re.sub(r'^<[^>]+>|<[^>]+>$', '', message)

    @staticmethod
    async def create(servers,persona,is_user=False):
        node = MaceServer(servers=servers, persona=persona,is_user=is_user)
        await node.connect()
        return node

    async def rollcall_handler(self,msg):
        logger.debug("rollcall received")
        subject=msg.subject
        data=msg.data.decode()
        reply = msg.reply
        self.messages.append({
            "subject":subject,
            "data":data
        })
        image_base64=None
        if self.persona.agent_image:
            image_bin=self.persona.agent_image.Image128
            image_base64 = base64.b64encode(image_bin).decode('utf-8')

        response = {
            "Name": self.persona.agent_profile.Name,
            "ClassName": self.persona.agent_profile.ClassType.ClassName,
            "AgentDescription": self.persona.agent_profile.AgentDescription,
            "AgentShortDesc": self.persona.agent_profile.AgentShortDesc,
            "Image64": image_base64,
            "Image128": image_base64
        }        
        await self.send_raw(reply,json.dumps(response))

    async def _send_reply(self,
            dialogue_id,
            round_no,
            turn_no,
            content,
            flow_diagram,
            dialogue_messages):
        
        # Check Plan for routing info
        plan=FlowPlan(flow_diagram=flow_diagram)
        turn=plan.get_turn(turn_no)

        import json
        self.persona.dialogue_store.clear()
        self.persona.dialogue_store.capped_message_queue = [DialogueMessagePydantic(**msg) for msg in dialogue_messages]
        logger.debug("dialogue_messages:"+json.dumps(dialogue_messages))

        # stream chunk
        user_message_id=DialogueStore.create_message_id(dialogue_id=dialogue_id,round_no=round_no,turn_no=turn_no,postfix="A")
        assistant_message_id=DialogueStore.create_message_id(dialogue_id=dialogue_id,round_no=round_no,turn_no=turn_no,postfix="B")
        response = self.persona.act(content,user_message_id=user_message_id,assistant_message_id=assistant_message_id)
        chunk_no = 0
        combined_chunks = ""

        # send message start
        message_start=f"<{self.node_name}>"
        message = FlowMessagePydantic(
            DialogueId=dialogue_id,
            RoundNo=round_no,
            TurnNo=turn.TurnNo,
            FlowDiagram=flow_diagram,
            Sender=self.node_name,
            Recipient="User",
            ChunkNo=chunk_no,
            Chunk=message_start,
            DialogueMessages=[]
        )
        message = json.dumps(message.dict())
        subject=f"dialogue.{dialogue_id}"
        await self.send_raw(subject, message)
        await self.flush()

        # stream message
        for chunk in response:
            print(chunk,end="",flush=True)
            chunk_no += 1
            message = FlowMessagePydantic(
                DialogueId=dialogue_id,
                RoundNo=round_no,
                TurnNo=turn.TurnNo,
                FlowDiagram=flow_diagram,
                Sender=self.node_name,
                Recipient="User",
                ChunkNo=chunk_no,
                Chunk=chunk,
                DialogueMessages=[]
            )
            message = json.dumps(message.dict())
            await self.send_raw(subject, message)
            await self.flush()
            combined_chunks += chunk
        
        # send message end
        message_end=f"</{self.node_name}>"
        message = FlowMessagePydantic(
            DialogueId=dialogue_id,
            RoundNo=round_no,
            TurnNo=turn.TurnNo,
            FlowDiagram=flow_diagram,
            Sender=self.node_name,
            Recipient="User",
            ChunkNo="<eom>",
            Chunk=message_end,
            DialogueMessages=dialogue_messages
        )
        message = json.dumps(message.dict())
        await self.send_raw(subject, message)
        await self.flush()

        return combined_chunks        

    async def dialogue_handler(self,msg: Msg):

        # Unwrap message
        subject=msg.subject
        data=msg.data.decode()
        dialogue_id=subject.split(".")[1]
        self.messages.append({
            "subject":subject,
            "data":data
        })

        # parse FlowMessage
        data=json.loads(data)
        pydantic = FlowMessagePydantic(**data)

        # Exception Case: Message from self to anyone
        if pydantic.Sender == self.node_name:
            # ignore message from self
            return

        # Exception Case: Message from sender to sender
        if pydantic.Sender == pydantic.Recipient:
            return

        # Case 1: Message from user to others
        if pydantic.Sender == "User" and pydantic.Recipient != self.node_name:
            return

        # Case 2: Message from user to this node
        if pydantic.Sender == "User" and pydantic.Recipient == self.node_name:

            # Reply to user
            assistant_message = await self._send_reply(
                dialogue_id=dialogue_id,
                round_no=pydantic.RoundNo,
                turn_no=pydantic.TurnNo,
                content=pydantic.Content,
                flow_diagram=pydantic.FlowDiagram,
                dialogue_messages=pydantic.DialogueMessages)

            # Save this node's reply
            assistant_message = self._strip_xml(assistant_message)
            return

        # Case 3: Other reply to User
        if pydantic.Sender != "User" and pydantic.Recipient == "User":
            return

        raise Exception(f"Unhandled case: Sender={pydantic.Sender} Recipient={pydantic.Recipient}")

    async def listen(self):
        # Keep the subscriber running
        try:
            is_stopped=False
            if self.is_user:
                tm = ThreadManagerSingleton.GetInstance()
                is_stopped=tm.is_stopped(name="User")
            while not is_stopped:
                await asyncio.sleep(1)
                if self.is_user:
                    is_stopped=tm.is_stopped(name="User")
        except KeyboardInterrupt:
            pass
        finally:
            # Close the connection
            await self.stop()

    async def serve(self):
        logger.info("MaceServer.listen: Server is starting to serve.")

        key="system.rollcall"
        handler=self.rollcall_handler
        if not self.subscribed.get(key,None):
            self.subs.append(await self.nc.subscribe(key, cb=handler))
            self.subscribed[key]=True

        key="dialogue.>"
        handler=self.dialogue_handler
        if not self.subscribed.get(key,None):
            self.subs.append(await self.nc.subscribe(key, cb=handler))
            self.subscribed[key]=True

        await self.listen()

    async def stop(self):
        logger.info(f"MaceServer.listen: Server stopped. Persona={self.persona.agent_profile.Name}")
        for sub in self.subs:
            await sub.unsubscribe()
        for key in self.subscribed.keys():
            self.subscribed[key]=False
        await self.nc.flush()
        await self.nc.drain()
        if self.nc.is_connected:
            await self.nc.close()
