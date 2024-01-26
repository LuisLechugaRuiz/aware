from aware.agent.process import Process
from aware.system.thought_generator.thought_generator_tools import ThoughtGeneratorTools


class UserThoughtGenerator(Process):
    def __init__(self, user_id: str, process_id: str):
        super().__init__(
            user_id=user_id,
            process_id=process_id,
            agent_name="Thought Generator",
            run_remote=False,
            tools=ThoughtGeneratorTools(user_id=user_id, process_id=process_id),
            module_name="assistant",
        )

    @classmethod
    def get_process_name(self):
        return "user_thought_generator"
