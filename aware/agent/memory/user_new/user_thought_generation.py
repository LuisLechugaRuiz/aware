from queue import Queue

from aware.agent.memory.working_memory.thought_generation import ThoughtGeneration
from aware.agent.memory.user.user_profile import UserProfile
from aware.architecture.user.user_message import UserMessage
from aware.chat.chat import Chat


class UserThoughtGeneration(ThoughtGeneration):
    def __init__(
        self,
        assistant_name: str,
        user_name: str,
        initial_thought: str,
        user_profile: str,
        context,
    ):
        chat = Chat(
            module_name="user_thought_generation",
            logger=self.logger,
            system_prompt_kwargs={
                "user_name": self.user_name,
                "assistant_name": self.assistant_name,
                "user_profile": user_profile,
                "context": context,
            },
        )
        super().__init__(
            chat=chat, user_name=user_name, initial_thought=initial_thought
        )
        self.assistant_name = assistant_name
        self.messages_queue: Queue[UserMessage] = Queue()

    def update_system(self, user_profile: UserProfile, context: str):
        """Override the default update system to add the user profile and context."""
        system_prompt_kwargs = {
            "user_name": self.user_name,
            "assistant_name": self.assistant_name,
            "user_profile": user_profile.to_string(),
            "context": context,
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)

    def run(self):
        while True:
            # Empty the queue - Add user and assistant messages.
            is_user_message = False
            while not is_user_message:
                if not self.messages_queue.empty():
                    message = self.messages_queue.get()
                    self.chat.conversation.add_user_message(
                        message.message, user_name=message.user_name
                    )
                    is_user_message = message.user_name == self.user_name
            self.run_agent()
