import json
from queue import Queue
from typing import List

from aware.agent.memory.working_memory import ThoughtGenerator
from aware.architecture.helpers.topics import DEF_SEARCH_DATABASE
from aware.architecture.user.user_message import UserMessage
from aware.chat.chat import Chat
from aware.config.config import Config
from aware.utils.communication_protocols import Client
from aware.utils.logger.file_logger import FileLogger


# TODO: Append thought at start if any (from previous conversation?).
class AgentThoughtGenerator(ThoughtGenerator):
    def __init__(
        self,
        agent_name: str,
        user_name: str,
        initial_thought: str,
        initial_context: str,
    ):
        self.agent_name = agent_name
        self.messages_queue: Queue[UserMessage] = Queue()
        self.logger = FileLogger("agent_thought_generator", should_print=False)
        chat = Chat(
            module_name="agent_thought_generator",
            logger=self.logger,
            system_prompt_kwargs={
                "agent_name": self.agent_name,
                "context": initial_context,
            },
        )
        self.search_user_info_client = Client(
            address=f"tcp://{Config().assistant_ip}:{Config().client_port}",
        )
        self.user_name = user_name

        super().__init__(
            chat=chat,
            user_name=agent_name,
            initial_thought=initial_thought,
            logger=self.logger,
            functions=[self.search_user_info],
        )

    # TODO: SAME THAN FOR CONTEXT MANAGER. WE NEED FULL MESSAGE NOT ONLY USERMESSAGE -> TODO: ABSTRACTION OF OPENAI MESSAGES WHICH CAN BE TRANSLATED INTO STRING.
    def add_message(self, message: UserMessage):
        self.messages_queue.put(message)

    def edit_system(self, context: str):
        """Override current system with updated context."""
        system_prompt_kwargs = {
            "agent_name": self.agent_name,
            "context": context,
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)

    def search_user_info(self, queries: List[str]):
        """
        Search information about the user using the queries.

        Args:
            queries (List[str]): The queries to be searched.

        Returns:
            str: The user info.
        """
        data = self.search_user_info_client.send(
            topic=f"{self.user_name}_{DEF_SEARCH_DATABASE}", message=json.dumps(queries)
        )
        if data is None:
            return "Information not found."
        return data

    def step(self):
        """Run a single agent step to generate a new thought integrating new info from memory based on current conversation."""

        if not self.messages_queue.empty():
            while not self.messages_queue.empty():
                message = self.messages_queue.get()
                self.chat.conversation.add_user_message(
                    message.message, user_name=message.user_name
                )
                self.messages_queue.task_done()
            self.run_agent()
