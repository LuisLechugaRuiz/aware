from typing import TYPE_CHECKING

from aware.agent.agent_data import ThoughtGeneratorMode
from aware.memory.memory_manager import MemoryManager
from aware.tools.core.assistant import Assistant
from aware.tools.core.orchestrator import Orchestrator
from aware.tools.private.data_storage_manager import DataStorageManager
from aware.tools.private.thought_generator import ThoughtGenerator
from aware.utils.logger.file_logger import FileLogger

if TYPE_CHECKING:
    from aware.data.database.client_handlers import ClientHandlers


class AgentBuilder:
    def __init__(self, user_id: str, client_handlers: "ClientHandlers"):
        self.user_id = user_id
        self.client_handlers = client_handlers
        self.memory_manager = MemoryManager(user_id=user_id, logger=self.logger)
        self.logger = FileLogger("agent_builder")

    def initialize_user_agents(self, assistant_name: str):
        """Create the initial agents for the user"""
        self.create_agent(
            name=assistant_name,
            tools_class=Assistant.__name__,
            identity=Assistant.get_identity(assistant_name=assistant_name),
            task=Assistant.get_task(),
            instructions="",  # TODO: Fill me!
            thought_generator_mode=ThoughtGeneratorMode.PRE,
        )
        self.create_agent(
            name=Orchestrator.get_process_name(),
            tools_class=Orchestrator.__name__,
            identity=Orchestrator.get_identity(),
            task=Orchestrator.get_task(),
            instructions="",  # TODO: Fill me!
            thought_generator_mode=ThoughtGeneratorMode.POST,
        )

    def create_agent(
        self,
        name: str,
        tools_class: str,
        identity: str,
        task: str,
        instructions: str,
        thought_generator_mode: ThoughtGeneratorMode = ThoughtGeneratorMode.POST,
    ):
        """Create a new agent"""
        try:
            agent_data = self.client_handlers.create_agent(
                user_id=self.user_id,
                name=name,
                tools_class=tools_class,
                identity=identity,
                task=task,
                instructions=instructions,
                thought_generator_mode=thought_generator_mode.value,
            )
            # Store agent on Weaviate
            self.memory_manager.create_agent(
                user_id=self.user_id, agent_data=agent_data
            )

            # Create the processes
            self.client_handlers.create_process(
                user_id=self.user_id,
                agent_id=agent_data.id,
                name="main",
                tools_class=tools_class,
                identity=identity,
                task=task,
                instructions=instructions,
            )
            # Create thought generator process
            self.client_handlers.create_process(
                user_id=self.user_id,
                agent_id=agent_data.id,
                name=ThoughtGenerator.get_process_name(),
                tools_class=ThoughtGenerator.__name__,
                identity=ThoughtGenerator.get_identity(),
                task=ThoughtGenerator.get_task(agent=name, agent_task=task),
                instructions=ThoughtGenerator.get_instructions(),
            )
            # Create data storage manager process
            data_storage_process_data = self.client_handlers.create_process(
                user_id=self.user_id,
                agent_id=agent_data.id,
                name=DataStorageManager.get_process_name(),
                tools_class=DataStorageManager.__name__,
                identity=DataStorageManager.get_identity(),
                task=DataStorageManager.get_task(agent=name, agent_task=task),
                instructions=DataStorageManager.get_instructions(agent=name),
            )
            self.client_handlers.create_topic(
                user_id=self.user_id,
                topic_name="agent_interactions",
                topic_description="Agent interactions:",
            )
            self.client_handlers.create_subscription(
                process_id=data_storage_process_data.id, topic_name="agent_interactions"
            )

        except Exception as e:
            return self.logger.error(f"Error creating agent {name}: {e}")
