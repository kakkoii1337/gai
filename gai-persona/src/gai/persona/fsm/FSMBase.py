from gai.persona.fsm.FSMBuilder import FSMBuilder
from gai.lib.common.logging import getLogger
logger=getLogger(__name__)
import os,sys

class FSMBase:

    """
    The FSMBase class must be initialised by a string of mermaid state diagram. 
    If the string is not provided, then the state_diagram_path is used to read the diagram from file.
    The default location of the state diagram file is in the same location of the FSM.
    """
    def __init__(self, state_diagram_path = None, state_diagram = None):

        # Convert state diagram into array of lines
        state_diagram = "\n".join(line.strip() for line in state_diagram.splitlines() if line.strip())
        self.state_diagram = state_diagram
        lines=[]
        if not self.state_diagram:
            self.state_diagram_path = state_diagram_path
            if not self.state_diagram_path:
                # Find the path of the class that implements FSMBase and load the state diagram from the same directory
                class_module = type(self).__module__
                module_file = sys.modules[class_module].__file__
                module_dir = os.path.dirname(module_file)
                self.state_diagram_path = os.path.join(module_dir, "state_diagram.md")
                #state_diagram_path = os.path.join(this_dir(type(self).__file__), "state_diagram.md")
            with open(self.state_diagram_path,"r") as f:
                lines = f.readlines()
        else:
            lines = state_diagram.split("\n")

        # Recombine useable data back into the state diagram
        self.state_diagram=""
        for line in lines:
            if not line.startswith("```") and not line.startswith("#") and not line.startswith("stateDiagram-v2"):
                self.state_diagram += line +"\n"

    def Init(self):
        builder = FSMBuilder(self.state_diagram)
        self.machine = builder.build(self)
        self.validate_model()
        return self

    def log(self, log_level):
        logger.log(log_level, {"state": self.state, "data": self.content})

    def Debug(self):
        print("Current State:", self.state)
        print("States:", self.machine.states)
        print("Transitions:")
        for event in self.machine.events.values():
            for transitions in event.transitions.values():
                for transition in transitions:
                    if hasattr(transition,"after"):
                        if hasattr(transition,"conditions"):
                            condition_str = ""
                            for condition in transition.conditions:
                                if not condition_str:
                                    condition_str = condition.func
                                else:
                                    condition_str = " and " + condition.func
                            print(f"  Trigger {event.name} can lead to a state change from {transition.source} to {transition.dest} after {transition.after} if {condition_str}")
                        else:
                            print(f"  Trigger {event.name} can lead to a state change from {transition.source} to {transition.dest} after {transition.after}")
                    else:
                        print(f"  Trigger {event.name} can lead to a state change from {transition.source} to {transition.dest}")
    
    def validate_model(self):
        model = self
        machine = self.machine
        errors = []

        # # Check for the existence of action methods for each transition's 'after' event
        # for state in machine.states:
        #     # The typical action method for a state would be on_<STATE NAME>
        #     action_method = f"on_{state}"
        #     if not hasattr(model, action_method):
        #         errors.append(f"Model is missing required method: {action_method}")

        # Check for the existence of condition functions in the transitions
        for event in machine.events.values():
            for transition in event.transitions.values():
                if len(transition) > 1:
                    for trans in transition:
                        if hasattr(trans,"conditions"):
                            for condition in trans.conditions:
                                condition_name = condition.func
                                condition_function = getattr(model, condition_name, None)
                                if not condition_function:
                                    errors.append(f"Model is missing required condition method: {condition_name}")
                                if not callable(condition_function):
                                    errors.append(f"Condition function {condition_name} is not callable.")

        # Report errors or confirm validation
        if errors:
            error_message = "Machine validation failed with the following errors:\n" + "\n".join(errors)
            raise ValueError(error_message)
        else:
            print("Machine validation successful.")

    """
    Used by handler classes to validate the existence of and extract value from the attribute of the main agent class
    """
    def _get_attr(self, attr):
        try:
            return getattr(self, attr)
        except Exception as e:
            logger.error(f"use_GENERATE_handler: Attribute not found error={attr}")
            raise

    def Chat(self, user_message=None):
        self.Init()
        if not hasattr(self, 'state'):
            raise Exception("State not defined. Did you forget to call Init() for the FSM?")
        if user_message:
            self.user_message = user_message
        if not self.user_message:
            raise Exception("User message not provided.")
        if self.stream:
            def _stream():
                while self.state != 'END':
                    try:
                        content=""
                        if self.state == "GENERATE":
                            for chunk in self.streamer:
                                if chunk:
                                    content += chunk
                                    yield chunk
                        self.content=content
                        self.next()
                    except Exception as e:
                        logger.error(f"FSMBase.Chat: error={e} state={self.state}")
                        raise
            return (chunk for chunk in _stream())
        else:
            while self.state != 'END':
                try:
                    self.next()
                except Exception as e:
                    logger.error(f"FSMBase.Chat: error={e} state={self.state}")
                    raise
            return self.content
