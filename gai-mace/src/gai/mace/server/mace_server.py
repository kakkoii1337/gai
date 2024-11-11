import json
import os
import base64
import time
from nats.aio.msg import Msg

from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.network.gainet_node import GaiNetNode
from gai.mace.flow_plan import FlowPlan
from gai.mace.pydantic.FlowMessagePydantic import FlowMessagePydantic
from gai.persona.persona_builder import PersonaBuilder
from gai.lib.dialogue.dialogue_store import DialogueStore
from gai.lib.dialogue.pydantic.DialogueMessagePydantic import DialogueMessagePydantic

class MaceServer(GaiNetNode):

    # static props
    subscribed={}


    def __init__(self, servers, persona):
        super().__init__(servers,persona.agent_profile.Name)
        self.persona = persona
        self.other_content=""
        self.dialogue_store=persona.dialogue_store

    def _strip_xml(self,message):
        import re
        # This pattern matches the first and last XML tags in the string
        return re.sub(r'^<[^>]+>|<[^>]+>$', '', message)

    @staticmethod
    async def create(servers,persona):
        node = MaceServer(servers=servers, persona=persona)
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

    # async def broadcast_handler(self,msg):
    #     subject=msg.subject
    #     data=msg.data.decode()
    #     reply=msg.reply
    #     self.messages.append({
    #         "subject":subject,
    #         "data":data
    #     })

    #     # generate llm response
    #     data=json.loads(data)
    #     message  = data["content"]
    #     message_id = data["message_id"]
    #     response = self.persona.act(message)

    #     # stream chunk
    #     chunk_id = 0
    #     for chunk in response:
    #         payload = {
    #             "name":self.node_name,
    #             "message_id":message_id,
    #             "chunk_id":chunk_id,
    #             "content":chunk
    #         }
    #         await self.send_raw(reply, json.dumps(payload))
    #         await self.flush()
    #         chunk_id+=1

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

        # if DialogueStore.dialogue_id != pydantic.DialogueId:
        #    raise Exception("DialogueID mismatch!")
        # if DialogueStore.round_no != pydantic.RoundNo:
        #    if pydantic.RoundNo > DialogueStore.round_no and pydantic.TurnNo > 0:
        #        logger.warning(f"Expecting round {DialogueStore.round_no} and turn {DialogueStore.turn_no+1} but received round {pydantic.RoundNo} and turn {pydantic.TurnNo}.")
        # DialogueStore.round_no = pydantic.RoundNo
        # DialogueStore.turn_no = pydantic.TurnNo

        # Exception Case: Message from self to anyone
        if pydantic.Sender == self.node_name:
            # ignore message from self
            return

        # Exception Case: Message from sender to sender
        if pydantic.Sender == pydantic.Recipient:
            return

        # Case 1: Message from user to others
        if pydantic.Sender == "User" and pydantic.Recipient != self.node_name:

            # If step came from user, save user message
            # self.dialogue_store.add_user_message(
            #     user_id=self.persona.caller_id,
            #     content=pydantic.Content + f" {pydantic.Recipient}, let's begin with you.",
            #     timestamp=int(time.time())
            #     )

            return

        # Case 2: Message from user to this node
        if pydantic.Sender == "User" and pydantic.Recipient == self.node_name:

            # If step came from user, save user message
            # self.dialogue_store.add_user_message(
            #     user_id=self.persona.caller_id,
            #     content=pydantic.Content + f" {pydantic.Recipient}, let's begin with you.",
            #     timestamp=int(time.time())
            #     )

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
            
        #     if pydantic.Chunk:
        #         self.other_content+=pydantic.Chunk

        #     if pydantic.ChunkNo=="<eom>":
        #         self.other_content = self._strip_xml(self.other_content)
        #         self.dialogue_store.add_assistant_message(name=pydantic.Sender,content=self.other_content)
        #         self.other_content=""

            return

        raise Exception(f"Unhandled case: Sender={pydantic.Sender} Recipient={pydantic.Recipient}")

    async def serve(self):
        logger.info("Server is starting to serve.")

        key="system.rollcall"
        handler=self.rollcall_handler
        if not self.subscribed.get(key,None):
            await self.nc.subscribe(key, cb=handler)
            self.subscribed[key]=True

        key="dialogue.>"
        handler=self.dialogue_handler
        if not self.subscribed.get(key,None):
            await self.nc.subscribe(key, cb=handler)
            self.subscribed[key]=True


        #await self.nc.subscribe("broadcast.>", cb=self.broadcast_handler)
        await self.listen()