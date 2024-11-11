import logging

class use_ERROR_handler:

    def __init__(self):
        self.error = None

    def has_error(self):
        return self.error is not None
    
    def not_has_error(self):
        return not self.has_error()

    def handle_ERROR(self):
        fsm = self.fsm
        fsm.content = fsm.error
        fsm.log(logging.ERROR)

    def on_ERROR(self):
        self.handle_ERROR()
