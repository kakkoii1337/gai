import asyncio
import uuid
import time
import json

from gai.lib.common.logging import getLogger
logger = getLogger(__name__)
from gai.network.gainet_node import GaiNetNode
from gai.lib.dialogue.dialogue_store import DialogueStore
from gai.mace.flow_plan import FlowPlan
from gai.mace.pydantic.FlowMessagePydantic import FlowMessagePydantic
from asyncio import Lock


class MaceClient(GaiNetNode):

    # static props
    subscribed={}
    dialogue_store = None


    def __init__(self, servers, dialogue_id, caller_id, api_host):
        super().__init__(servers,"User")

        MaceClient.dialogue_store=DialogueStore(
                caller_id=caller_id,
                agent_id=None,
                dialogue_id=dialogue_id,
                api_host=api_host,
                message_count_cap=10,
                message_char_cap=4000
            )        

        self.other_content=""
        
        self.rollcall_inbox=self.nc.new_inbox()
        self.rollcall_messages=[]

        self.caller_id=caller_id
        self.dialogue_state={
            "flow_diagram":None,
            "user_message":None
        }

    def _strip_xml(self,message):
        import re
        # This pattern matches the first and last XML tags in the string
        return re.sub(r'^<[^>]+>|<[^>]+>$', '', message)

    @staticmethod
    async def create(servers, 
                    dialogue_id="00000000-0000-0000-0000-000000000000", 
                    caller_id="00000000-0000-0000-0000-000000000000", 
                    api_host="http://localhost:12033"
                    ):
        client = MaceClient(servers=servers, dialogue_id=dialogue_id, caller_id=caller_id,api_host=api_host)
        await client.connect()
        return client
    
    # from nats.aio.msg import Msg
    # async def message_logger(self,msg:Msg):
    #     data = msg.data.decode()
    #     data = json.loads(data)
    #     pydantic = FlowMessagePydantic(**data)
    #     if pydantic.Chunk:
    #         if pydantic.ChunkNo=="<eom>":
    #             self.other_content = self._strip_xml(self.other_content)
    #             self.dialogue_store.add_assistant_message(name=pydantic.Sender,content=self.other_content)
    #             self.other_content=""
    #         else:
    #             if pydantic.ChunkNo > 0:
    #                 self.other_content+=pydantic.Chunk

    async def subscribe(self, async_chat_handler=None):

        # subscribe to rollcall
        if not self.subscribed.get(self.rollcall_inbox):
            sub = await self.nc.subscribe(self.rollcall_inbox, cb=self.rollcall_handler)
            self.subscribed[self.rollcall_inbox]=sub

        # subscribe to dialogue
        if async_chat_handler:
            dialogue_id=DialogueStore.dialogue_id
            subject=f"dialogue.{dialogue_id}"
            if not self.subscribed.get(subject,None):
                sub=[await self.nc.subscribe(subject,cb=async_chat_handler)]
                # await self.nc.subscribe(subject,cb=self.message_logger)]
                self.subscribed[subject]=sub

    async def unsubscribe_chat(self):
        dialogue_id=DialogueStore.dialogue_id
        subject=f"dialogue.{dialogue_id}"
        if self.subscribed.get(subject,None):
            for sub in self.subscribed[subject]:
                await sub.unsubscribe()
        
    async def rollcall_handler(self,msg):
        subject = msg.subject
        data=msg.data.decode()

        if data:
            log_data = json.loads(data)
            if log_data.get("Image64",None):
                log_data["Image64"] = "..."
            if log_data.get("Image128",None):
                log_data["Image128"] = "..."
            logger.debug(f"mace_client.rollcall_handler: {log_data}")
        else:
            logger.debug(f"mace_client.rollcall_handler: {data}")
            return

        self.rollcall_messages.append({
            "subject":subject,
            "data":data
        })
        name=json.loads(data)["Name"]
        logger.debug(f"mace_client.rollcall_handler: {name}")

    async def rollcall(self):
        logger.info(f"start rollcall")
        self.rollcall_messages = []
        await self.nc.publish("system.rollcall", self.node_name.encode(), self.rollcall_inbox)
        await asyncio.sleep(2)
        for message in self.rollcall_messages:
            data = json.loads(message["data"])
            logger.info(data["Name"]+":"+data["AgentDescription"])

    # async def broadcast(self, msg, message_id=None):
    #     self.chat_messages = []
    #     if not message_id:
    #         message_id = str(uuid.uuid4())
    #     message = {
    #         "message_id":message_id,
    #         "name":self.node_name,
    #         "content":msg
    #     }
    #     message=json.dumps(message)
    #     await self.nc.publish(f"broadcast.{self.dialogue_id}", message.encode(), self.chat_inbox)
    #     await asyncio.sleep(10)

    async def list_dialogue_messages(self):
        return MaceClient.dialogue_store.list_dialogue_messages()
    
    async def delete_dialogue_message(self,message_id):
        return MaceClient.dialogue_store.delete_dialogue_message(message_id)

    async def clear_dialogue(self):
        dialogue_id = DialogueStore.dialogue_id
        self.dialogue_state={
            "flow_diagram":None,
            "user_message":None
        }
        MaceClient.dialogue_store.clear()
        return dialogue_id

    """
    This will start a new round of dialogue with the following states:
      - dialogue_id : unchanged.
      - round_no    : increase by 1
      - turn_no     : reset to 0
    """
    async def dialogue(self, msg, flow_diagram=None):

        if flow_diagram == None:

            flow_diagram = ""

            # if message is directed at a persona, create a one-turn flow.
            name = msg.split(",")[0]
            found = False
            for rollcall_message in self.rollcall_messages:
                data = json.loads(rollcall_message["data"])
                if data["Name"]==name:
                    found = True
                    flow_diagram += f"User->>{name}"
                    break
            
            # Or, multi-turn poll for everyone with the same message.
            if not found:
                await self.rollcall()
                sender="User"
                for rollcall_message in self.rollcall_messages:
                    data = json.loads(rollcall_message["data"])
                    recipient = data["Name"]
                    flow_diagram += f"{sender}->>{recipient}\n"
        
        # Start a new round of dialogue
        message_id=DialogueStore.NewRound()

        # parse flow
        plan = FlowPlan(flow_diagram=flow_diagram)
        turn = plan.get_turn(turn_no=DialogueStore.turn_no)
        
        # prepare message
        message = FlowMessagePydantic(
            DialogueId=DialogueStore.dialogue_id,
            RoundNo=DialogueStore.round_no,
            TurnNo=DialogueStore.turn_no,
            FlowDiagram=flow_diagram,
            Sender=self.node_name,
            Recipient=turn.Dest,
            Content=msg,
            DialogueMessages=[msg.dict() for msg in MaceClient.dialogue_store.list_dialogue_messages()]
        )
        logger.info(f"\nUser:\n{message.Content}")

        # send message
        subject=f"dialogue.{DialogueStore.dialogue_id}"
        message=json.dumps(message.dict())
        await self.send_raw(subject,message)

        # save message
        message_id=DialogueStore.create_message_id(DialogueStore.dialogue_id,DialogueStore.round_no,DialogueStore.turn_no,"A")
        MaceClient.dialogue_store.add_user_message(
            message_id=message_id,
            user_id=self.caller_id,
            content=msg,
            timestamp=int(time.time())
        )

        self.dialogue_state={
            "flow_diagram":flow_diagram,
            "user_message":msg
        }
        return message_id

    """
    This will continue the next turn within the same round:
      - dialogue_id : unchanged.
      - round_no    : unchanged.
      - turn_no     : increase by 1
    """
    
    async def next(self):

        flow_diagram=self.dialogue_state["flow_diagram"]
        user_message=self.dialogue_state["user_message"]

        if not flow_diagram:
            #raise Exception("Dialogue not started.")
            return None

        DialogueStore.NewTurn()
        flow = FlowPlan(flow_diagram=flow_diagram)
        turn = flow.get_turn(DialogueStore.turn_no)

        if not turn:
            # ran out of turns
            return None
        
        # prepare message
        message = FlowMessagePydantic(
            DialogueId=DialogueStore.dialogue_id,
            RoundNo=DialogueStore.round_no,
            TurnNo=DialogueStore.turn_no,
            FlowDiagram=flow_diagram,
            Sender=self.node_name,
            Recipient=turn.Dest,
            Content="",
            DialogueMessages=[msg.dict() for msg in MaceClient.dialogue_store.list_dialogue_messages()]
        )
        if turn.Src == "User":
            # polling
            message.Content = user_message
        else:
            # pipelining
            message.Content = f"{turn.Dest}, it is your turn to respond."
        logger.info(f"\nUser:\n{message.Content}")

        subject=f"dialogue.{DialogueStore.dialogue_id}"
        message=json.dumps(message.dict())
        await self.send_raw(subject,message)

        self.dialogue_state={
            "flow_diagram":flow_diagram,
            "user_message":user_message
        }

        return turn
