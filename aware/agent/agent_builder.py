from typing import List

from aware.agent.agent_data import AgentMemoryMode, ThoughtGeneratorMode
from aware.config import get_default_agents_path, get_internal_processes_path
from aware.data.database.client_handlers import ClientHandlers
from aware.memory.memory_manager import MemoryManager
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessFlowType
from aware.tools.default_data.assistant_data import Assistant
from aware.tools.default_data.orchestrator_data import Orchestrator
from aware.tools.default_data.data_storage_manager_data import DataStorageManager
from aware.tools.default_data.thought_generator_data import ThoughtGenerator
from aware.utils.logger.file_logger import FileLogger
from aware.utils.json_loader import JsonLoader


# TODO: Refactor -> It should interact with our json properly.

# 1. Read agent config from config.json at default_agents folder.
# 2. Create agent.


# 3. Read state machine config from state_machine.json and create process states for main process.
# 4. Read state machine config for each process at internal processes and create process states for each process.


# 5. Read communication config from communication.json and create communication channels for each process (external at agent folder and internal at internal processes folder).
class AgentBuilder:
    def __init__(self, user_id: str):
        self.logger = FileLogger("agent_builder")
        self.user_id = user_id
        self.memory_manager = MemoryManager(user_id=user_id, logger=self.logger)

    def initialize_user_agents(self, assistant_name: str):
        """Create the initial agents for the user"""
        default_agents_path = get_default_agents_path()
        default_agents_json_loader = JsonLoader(root_dir=default_agents_path)

        agent_files_dict = default_agents_json_loader.search_files(
            file_names=[
                "config.json",
                "communication.json",
                "profile.json",
                "state_machine.json",
            ]
        )
        for agent_folder, agent_files in agent_files_dict.items():
            agent_config = agent_files["config"]
            process_ids = self.create_agent(
                name=agent_config["name"],
                tools_class=agent_config["tools_class"],
                memory_mode=AgentMemoryMode(agent_config["memory_mode"]),
                modalities=agent_config["modalities"],
                thought_generator_mode=ThoughtGeneratorMode(
                    agent_config["thought_generator_mode"]
                ),
            )
            communications = agent_files["communications"]
            external_events = communications["external_events"]
            if len(external_events) > 0:
                for event in external_events:
                    ClientHandlers().create_event_subscription(
                        process_ids=process_ids, event_name=event
                    )
            # TODO: Configure topics and requests properly.
            state_machine = agent_files["state_machine"]
            for name, content in state_machine.items():
                # TODO: set the first state as the current state.
                ClientHandlers().create_process_state(
                    user_id=self.user_id,
                    process_id=process_ids.process_id,
                    name=name,
                    task=content["task"],
                    instructions=content["instructions"],
                    tools=content["tools"],
                )

        main_assistant_process_ids = self.create_agent(
            name=assistant_name,
            tools_class=Assistant.__name__,
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
            task=Orchestrator.get_task(),
            instructions=Orchestrator.get_instructions(),
            thought_generator_mode=ThoughtGeneratorMode.PRE,
        )

    def create_agent(
        self,
        name: str,
        tools_class: str,
        memory_mode: AgentMemoryMode,
        modalities: List[str],
        thought_generator_mode: ThoughtGeneratorMode = ThoughtGeneratorMode.PRE,
    ) -> ProcessIds:
        """Create a new agent"""
        try:
            agent_data = ClientHandlers().create_agent(
                user_id=self.user_id,
                name=name,
                tools_class=tools_class,
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
                task=task,
                instructions=instructions,
                flow_type=ProcessFlowType.INTERACTIVE,
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
                task=ThoughtGenerator.get_task(agent_name=name, agent_task=task),
                instructions=ThoughtGenerator.get_instructions(agent_name=name),
                flow_type=ProcessFlowType.INTERACTIVE,
            )
            # Create data storage manager process
            data_storage_process_data = ClientHandlers().create_process(
                user_id=self.user_id,
                agent_id=agent_data.id,
                name=DataStorageManager.get_name(),
                tools_class=DataStorageManager.__name__,
                task=DataStorageManager.get_task(agent_name=name, agent_task=task),
                instructions=DataStorageManager.get_instructions(agent_name=name),
                flow_type=ProcessFlowType.INDEPENDENT,
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
