from typing import Optional

from aware.agent.agent_data import AgentData
from aware.communications.requests.request import Request
from aware.data.database.client_handlers import ClientHandlers
from aware.memory.memory_manager import MemoryManager
from aware.process.process_ids import ProcessIds
from aware.tools.tools import Tools
from aware.utils.logger.file_logger import FileLogger


DEF_IDENTITY = """You are data_storage_manager, a process responsible for storing relevant data to ensure optimal performance of a specific agent."""
DEF_TASK = """Your task is to store relevant data to be retrieved in the future to optimize {{ agent }}'s performance.
{{ agent }}'s Task:
{{ agent_task }}"""
DEF_INSTRUCTIONS = """- Strategic Data Storage: Use the store function for saving valuable insights from interactions into the database. Focus on data that enhances {{ agent }}'s comprehension and performance in its task.

Operational Focus:
- Anticipate Information Needs: When storing data, consider potential future queries. This proactive step facilitates quicker data retrieval and anticipates future information requirements.
- Relevance and Enhancement: Ensure all stored data is pertinent and contributes to a richer understanding and profile of the users interacting with {{ agent }}.
- Strategy Adaptation: Regularly adjust your data management strategy to align with the dynamic nature of interactions and the evolving needs of the task.
- Context Updating: After storing all the relevant data use stop function to update the {{ agent }}'s context with the latest information.

Operational Limitation:
- Your role is backend-centric, dedicated to data management and storage. Refrain from direct interaction in conversations and concentrate on utilizing tools for profile updates and data storage."""


class DataStorageManager(Tools):
    def __init__(
        self,
        client_handlers: "ClientHandlers",
        process_ids: ProcessIds,
        agent_data: AgentData,
        request: Optional[Request],
        run_remote: bool = False,
    ):
        super().__init__(
            client_handlers=client_handlers,
            process_ids=process_ids,
            agent_data=agent_data,
            request=request,
            run_remote=run_remote,
        )
        self.logger = FileLogger("data_storage_manager")

    @classmethod
    def get_identity(cls) -> str:
        return DEF_IDENTITY

    @classmethod
    def get_task(cls, agent: str, agent_task: str) -> str:
        return DEF_TASK.format(agent=agent, agent_task=agent_task)

    @classmethod
    def get_instructions(cls, agent: str) -> str:
        return DEF_INSTRUCTIONS.format(agent=agent)

    def set_tools(self):
        return [
            # self.append_profile,
            # self.edit_profile,
            self.store,
            self.stop,
        ]

    # TODO: Temporally disabled, we need a way to manage the full profile (and fields) ensuring max tokens.
    # def append_profile(self, field: str, data: str):
    #     """
    #     Append data into a specific field of the profile.

    #     Args:
    #         field (str): Field to edit.
    #         data (str): Data to be inserted.
    #     """
    #     result = self.process_data.agent_data.profile.append_profile(
    #         field=field, data=data
    #     )
    #     self.update_agent_data()
    #     return result

    # def edit_profile(self, field: str, old_data: str, new_data: str):
    #     """
    #     Edit the profile overwriting the old data with the new data.

    #     Args:
    #         field (str): Field to edit.
    #         old_data (str): Old data to be replaced.
    #         new_data (str): New data to replace the old data.
    #     """
    #     result = self.process_data.agent_data.profile.edit_profile(
    #         field=field, old_data=old_data, new_data=new_data
    #     )
    #     self.update_agent_data()
    #     return result

    def store(self, data: str, potential_query: str):
        """
        Stores data in the Weaviate database with an associated potential query for future retrieval.

        Args:
            data (str): The data to be stored.
            potential_query (str): A related query for future data retrieval, should be a question.
        """
        memory_manager = MemoryManager(
            user_id=self.process_ids.user_id,
            logger=self.logger,
        )

        return memory_manager.store_data(data=data, potential_query=potential_query)

    def stop(self, new_context: str):
        """Stop saving info. Call this function after all relevant data has been stored and provide a new context that overrides the previous one with the new information.

        Args:
            new_context (str): The new context to be set.
        """
        logger = FileLogger("migration_tests")
        logger.info("Stopping data storage.")

        self.agent_data.context = new_context
        self.update_agent_data()

        self.finish_process()
        return "Context updated, agent stopped."
