from aware.agent.process import Process
from aware.system.thought_generator.thought_generator_tools import ThoughtGeneratorTools


class ThoughtGenerator(Process):
    def __init__(self, user_id: str, process_id: str):
        super().__init__(
            user_id=user_id,
            process_id=process_id,
            agent_name="Thought Generator",
            run_remote=False,
            tools=ThoughtGeneratorTools(user_id=user_id, process_id=process_id),
            module_name="system",
        )

    @classmethod
    def get_process_name(self):
        return "thought_generator"
