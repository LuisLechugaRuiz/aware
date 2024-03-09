from dataclasses import dataclass

from aware.tool.default_data.data import Data

DEF_TASK = """Optimize {agent_name}'s performance in executing its task through strategic thought generation.
{agent_name}'s Task:
{agent_task}"""
DEF_INSTRUCTIONS = """Thought Generation Steps:
1. Gather task-relevant information.
2. For complex tasks, apply intermediate_thought and refine as necessary.
3. Finalize with a strategic final_thought to guide {agent_name}.

Operational Principles:
- Prioritize backend processing without engaging in direct interactions.
- Ensure thoughts are pertinent and flexible to the demands of {agent_name}'s task."""


@dataclass
class ThoughtGenerator(Data):
    @classmethod
    def get_tool_class(cls) -> str:
        return "ThoughtGenerator"

    @classmethod
    def get_task(cls, agent_name: str, agent_task: str) -> str:
        return DEF_TASK.format(agent_name=agent_name, agent_task=agent_task)

    @classmethod
    def get_instructions(cls, agent_name: str) -> str:
        return DEF_INSTRUCTIONS.format(agent_name=agent_name)
