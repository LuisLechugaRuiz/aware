from dataclasses import dataclass

from aware.tools.default_data.data import Data

DEF_TASK = """Store relevant data to be retrieved in the future to optimize {agent_name}'s performance.
{agent_name}'s Task:
{agent_task}"""
DEF_INSTRUCTIONS = """- Strategic Data Storage: Use the store function for saving valuable insights from interactions into the database. Focus on data that enhances {agent_name}'s comprehension and performance in its task.

Operational Focus:
- Anticipate Information Needs: When storing data, consider potential future queries. This proactive step facilitates quicker data retrieval and anticipates future information requirements.
- Relevance and Enhancement: Ensure all stored data is pertinent and contributes to a richer understanding and profile of the users interacting with {agent_name}.
- Strategy Adaptation: Regularly adjust your data management strategy to align with the dynamic nature of interactions and the evolving needs of the task.
- Context Updating: After storing all the relevant data use stop function to update the {agent_name}'s context with the latest information.

Operational Limitation:
- Your role is backend-centric, dedicated to data management and storage. Refrain from direct interaction in conversations and concentrate on utilizing tools for profile updates and data storage."""


@dataclass
class DataStorageManager(Data):
    @classmethod
    def get_tool_class(cls) -> str:
        return "DataStorageManager"

    @classmethod
    def get_task(cls, agent_name: str, agent_task: str) -> str:
        return DEF_TASK.format(agent_name=agent_name, agent_task=agent_task)

    @classmethod
    def get_instructions(cls, agent_name: str) -> str:
        return DEF_INSTRUCTIONS.format(agent_name=agent_name)
