from aware.agent.process import Process
from aware.system.thought_generator.thought_generator_tools import ThoughtGeneratorTools
from aware.utils.logger.file_logger import FileLogger


class UserThoughtGenerator(Process):
    def __init__(self, chat_id: str, user_id: str):
        self.chat_id = chat_id
        self.user_id = user_id
        super().__init__(
            user_id=user_id,
            chat_id=chat_id,
            agent_name="Thought Generator",
            run_remote=False,
            tools=ThoughtGeneratorTools(user_id=user_id, chat_id=chat_id),
            module_name="assistant",
        )

    @classmethod
    def get_process_name(self):
        return "user_thought_generator"
