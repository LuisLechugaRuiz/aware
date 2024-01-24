from aware.events.event import Event


class AssistantMessageEvent(Event):
    def __init__(self, chat_id: str, user_id: str, assistant_name: str, message: str):
        self.assistant_name = assistant_name
        self.message = message
        super().__init__(chat_id, user_id)
