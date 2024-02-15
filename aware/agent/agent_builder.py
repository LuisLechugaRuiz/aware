from aware.agent.agent_data import ThoughtGeneratorMode
from aware.data.database.client_handlers import ClientHandlers
from aware.memory.memory_manager import MemoryManager
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.tools.default_data.assistant_data import Assistant
from aware.tools.default_data.orchestrator_data import Orchestrator
from aware.tools.default_data.data_storage_manager_data import DataStorageManager
from aware.tools.default_data.thought_generator_data import ThoughtGenerator
from aware.utils.logger.file_logger import FileLogger


class AgentBuilder:
    def __init__(self, user_id: str):
        self.logger = FileLogger("agent_builder")
        self.user_id = user_id
        self.memory_manager = MemoryManager(user_id=user_id, logger=self.logger)

    def initialize_user_agents(self, assistant_name: str):
        """Create the initial agents for the user"""
        main_assistant_process_ids = self.create_agent(
            name=assistant_name,
            tools_class=Assistant.__name__,
            identity=Assistant.get_identity(assistant_name=assistant_name),
            task=Assistant.get_task(),
            instructions=Assistant.get_instructions(),
            thought_generator_mode=ThoughtGeneratorMode.POST,
        )
        # TODO: Should we add a get_event for each tool? We want both: Flexible events, but some can be attached directly to tool? TBD.
        ClientHandlers().create_event_subscription(
            process_ids=main_assistant_process_ids,
            event_name="user_message",
        )

        self.create_agent(
            name=Orchestrator.get_name(),
            tools_class=Orchestrator.__name__,
            identity=Orchestrator.get_identity(),
            task=Orchestrator.get_task(),
            instructions=Orchestrator.get_instructions(),
            thought_generator_mode=ThoughtGeneratorMode.PRE,
        )

    def create_agent(
        self,
        name: str,
        tools_class: str,
        identity: str,
        task: str,
        instructions: str,
        thought_generator_mode: ThoughtGeneratorMode = ThoughtGeneratorMode.PRE,
    ) -> ProcessIds:
        """Create a new agent"""
        try:
            agent_data = ClientHandlers().create_agent(
                user_id=self.user_id,
                name=name,
                tools_class=tools_class,
                identity=identity,
                task=task,
                instructions=instructions,
                thought_generator_mode=thought_generator_mode.value,
            )
            self.logger.info(f"Agent created on database, uuid: {agent_data.id}")
            # Store agent on Weaviate
            self.memory_manager.create_agent(
                user_id=self.user_id, agent_data=agent_data
            )

            # Create the processes
            main_process_data = ClientHandlers().create_process(
                user_id=self.user_id,
                agent_id=agent_data.id,
                name="main",
                tools_class=tools_class,
                identity=identity,
                task=task,
                instructions=instructions,
                service_name=name,  # Use the name of the agent as service name, TODO: Fix me using internal and external requests.
            )
            main_process_ids = ProcessIds(
                user_id=self.user_id,
                agent_id=agent_data.id,
                process_id=main_process_data.id,
            )
            # Create thought generator process
            ClientHandlers().create_process(
                user_id=self.user_id,
                agent_id=agent_data.id,
                name=ThoughtGenerator.get_name(),
                tools_class=ThoughtGenerator.__name__,
                identity=ThoughtGenerator.get_identity(),
                task=ThoughtGenerator.get_task(agent=name, agent_task=task),
                instructions=ThoughtGenerator.get_instructions(agent=name),
            )
            # Create data storage manager process
            data_storage_process_data = ClientHandlers().create_process(
                user_id=self.user_id,
                agent_id=agent_data.id,
                name=DataStorageManager.get_name(),
                tools_class=DataStorageManager.__name__,
                identity=DataStorageManager.get_identity(),
                task=DataStorageManager.get_task(agent=name, agent_task=task),
                instructions=DataStorageManager.get_instructions(agent=name),
            )
            # TODO: Here we need differentiation between internal topics - between processes of same agent and external topics between agents... otherwise here agent_interactions would be any.
            ClientHandlers().create_topic(
                user_id=self.user_id,
                topic_name="agent_interactions",
                topic_description="Agent interactions:",
            )
            ClientHandlers().create_topic_subscription(
                process_id=data_storage_process_data.id, topic_name="agent_interactions"
            )
            return main_process_ids

        except Exception as e:
            return self.logger.error(f"Error creating agent {name}: {e}")
