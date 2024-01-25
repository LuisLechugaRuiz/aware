from aware.events.event import Event


class AssistantMessageEvent(Event):
    def __init__(
        self, process_id: str, user_id: str, assistant_name: str, message: str
    ):
        self.assistant_name = assistant_name
        self.message = message
        super().__init__(process_id, user_id)
