import threading

from aware.agent.memory.agent import (
    AgentContextManager,
    AgentThoughtGenerator,
    AgentDataStorageManager,
)
from aware.architecture.user.user_message import UserMessage


class AgentWorkingMemory:
    def __init__(self, agent_name: str, user_name: str):
        self.agent_name = agent_name
        self.user_name = user_name
        self.data_storage_manager = AgentDataStorageManager(agent_name=self.agent_name)

        # TODO: RETRIEVE INITIAL CONTEXT FROM JSON - ANOTHER JSON FOR USER WORKING MEMORY.
        self.context_manager = AgentContextManager(
            agent_name=self.agent_name,
            initial_context="",
        )
        self.context_manager_thread = threading.Thread(target=self.update_context)
        self.context_manager_thread.start()

        self.thought_generator = AgentThoughtGenerator(
            agent_name=self.agent_name,
            initial_thought="",  # TODO: GET FROM JSON
            context="",  # TODO: GET FROM JSON
        )
        self.thought_generator_thread = threading.Thread(target=self.generate_thought)
        self.thought_generator_thread.start()

    def add_message(self, message: UserMessage):
        self.context_manager.add_message(message)
        self.thought_generator.add_message(message)
        self.data_storage_manager.add_message(message)

    def update_context(self):
        while True:
            self.context_manager.edit_system(context=self.get_context())
            self.context_manager.step()

    def generate_thought(self):
        while True:
            self.thought_generator.edit_system(context=self.get_context())
            self.thought_generator.step()

    def get_context(self):
        return self.context_manager.get_context()

    def get_thought(self):
        return self.thought_generator.get_thought()
