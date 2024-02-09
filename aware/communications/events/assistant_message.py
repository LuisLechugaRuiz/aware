from aware.communications.events.event import Event
from aware.process.process_ids import ProcessIds


class AssistantMessageEvent(Event):
    def __init__(self, process_ids: ProcessIds, assistant_name: str, message: str):
        self.assistant_name = assistant_name
        self.message = message
        super().__init__(process_ids)
