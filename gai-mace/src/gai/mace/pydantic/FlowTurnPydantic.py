from pydantic import BaseModel
class FlowTurnPydantic(BaseModel):
    TurnNo: int
    Src: str
    Dest: str
