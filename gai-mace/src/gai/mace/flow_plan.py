import re
from gai.mace.pydantic.FlowTurnPydantic import FlowTurnPydantic

# FlowPlan is the object representation of the sequence diagram
class FlowPlan:

    def __init__(self, flow_diagram:str):
        self.flow_diagram=re.sub(r'[^\S\n]+',' ',flow_diagram)
        self.turns=[]
        
        result=[]
        turns = self.flow_diagram.split("\n")
        turns = [turn.strip() for turn in turns if turn.strip() != "" and turn.strip() != "sequenceDiagram"]
        for i,turn in enumerate(turns):
            seq_turn = FlowTurnPydantic(
                TurnNo=i,
                Src=turn.split("->>")[0],
                Dest=turn.split("->>")[1]
            )
            result.append(seq_turn)
        self.turns=result

    def get_turn(self, turn_no: int) -> FlowTurnPydantic:
        if turn_no >= len(self.turns):
            return None
        return self.turns[turn_no]