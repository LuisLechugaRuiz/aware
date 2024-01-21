from aware.agent.process import Process
from aware.system.thought_generator.thought_generator_tools import ThoughtGeneratorTools


class ThoughtGenerator(Process):
    def __init__(self, chat_id: str, user_id: str):
        self.chat_id = chat_id
        self.user_id = user_id
        super().__init__(
            user_id=user_id,
            chat_id=chat_id,
            run_remote=False,
            tools=ThoughtGeneratorTools(user_id=user_id, chat_id=chat_id),
            module_name="system",
        )

    @classmethod
    def get_process_name(self):
        return "thought_generator"
