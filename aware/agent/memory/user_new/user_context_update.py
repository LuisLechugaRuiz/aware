from aware.agent.memory.working_memory import ContextUpdate
from aware.agent.memory.user.user_profile import UserProfile
from aware.chat.chat import Chat


class UserContextUpdate(ContextUpdate):
    def __init__(self, assistant_name: str, user_name: str, initial_context: str):
        # TODO: DEFINE CONTEXT PROMPT
        chat = Chat(
            module_name="user_context_update",
            logger=self.logger,
            system_prompt_kwargs={
                "user_name": user_name,
                "assistant_name": assistant_name,
                "user_profile": "",
                "context": initial_context,
            },
        )

        super().__init__(chat=chat, initial_context=initial_context)
        self.assistant_name = assistant_name

    def update_system(self, user_profile: UserProfile, context: str):
        """Override the default update system to add the user profile and context."""
        system_prompt_kwargs = {
            "user_name": self.user_name,
            "assistant_name": self.assistant_name,
            "user_profile": user_profile.to_string(),
            "context": context,
        }
        self.chat.edit_system_message(system_prompt_kwargs=system_prompt_kwargs)
