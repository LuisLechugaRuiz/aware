from dataclasses import dataclass

from aware.tools.default_data.data import Data

DEF_IDENTITY = """You are thought_generator, a process responsible for generating thoughts to optimize the performance of a specific agent."""
DEF_TASK = """Your task is to optimize {{ agent }}'s performance in executing its task through strategic thought generation.
{{ agent }}'s Task:
{{ agent_task }}"""
DEF_INSTRUCTIONS = """Thought Generation Steps:
1. Gather task-relevant information.
2. For complex tasks, apply intermediate_thought and refine as necessary.
3. Finalize with a strategic final_thought to guide {{ agent }}.

Operational Principles:
- Prioritize backend processing without engaging in direct interactions.
- Ensure thoughts are pertinent and flexible to the demands of {{ agent }}'s task."""


@dataclass
class ThoughtGenerator(Data):
    @classmethod
    def get_identity(cls) -> str:
        return DEF_IDENTITY

    @classmethod
    def get_task(cls, agent: str, agent_task: str) -> str:
        return DEF_TASK.format(agent=agent, agent_task=agent_task)

    @classmethod
    def get_instructions(cls) -> str:
        return DEF_INSTRUCTIONS
