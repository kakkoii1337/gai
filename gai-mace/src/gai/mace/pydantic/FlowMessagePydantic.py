from pydantic import BaseModel
from typing import Optional,Union

# Each dialogue contains multiple rounds
# Each round contains multiple turns
# A FlowDiagram describes the turns that takes place in a round
class FlowMessagePydantic(BaseModel):
    DialogueId: str
    RoundNo: int
    FlowDiagram: str
    TurnNo: int
    Sender: str
    Recipient: str
    Content: Optional[str] = None
    Chunk: Optional[str] = None
    ChunkNo: Optional[Union[int|str]] = None
    DialogueMessages: list

