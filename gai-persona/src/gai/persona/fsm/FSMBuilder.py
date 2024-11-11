from transitions import Machine

class FSMBuilder:

    def __init__(self,sd:str):
        self.transitions_str=sd
    
    def build(self, model):
        states = set()
        transitions = []
        for line in self.transitions_str.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split('-->')
            source = parts[0].strip()
            dest_action = parts[1].split(':')
            dest = dest_action[0].strip()
            action_parts = dest_action[1].split('/')
            trigger = action_parts[0].strip()
            after_handler = action_parts[1].strip() if len(action_parts) > 1 else None
            condition = action_parts[2].strip() if len(action_parts) > 2 else None

            states.add(source)
            states.add(dest)

            transition_dict = {
                'trigger': trigger,
                'source': source,
                'dest': dest,
            }

            # after
            if after_handler:
                if not hasattr(model, after_handler):
                    raise AttributeError(f"after method is required: {after_handler}")
                transition_dict['after'] = after_handler

            # condition
            if condition:
                transition_dict['conditions'] = [condition]

            transitions.append(transition_dict)

        machine = Machine(model=model, states=list(states), initial='INIT', auto_transitions=False)

        for trans in transitions:
            machine.add_transition(**trans)

        return machine

