from abc import ABC, abstractmethod


class Tools(ABC):
    def __init__(self, user_id: str, chat_id: str):
        self.user_id = user_id
        self.chat_id = chat_id

    @abstractmethod
    def get_tools(self):
        pass

    def stop_agent(self):
        # TODO: Implement me to stop agent execution, setting it to false at Supabase.
        pass
