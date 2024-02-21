from typing import Any, Dict, List

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
            main_process_ids = self.create_agent_by_config(agent_files["config"])
            self.create_agent_communication(
                process_ids=main_process_ids,
                communication_config=agent_files["communication"],
            )
            self.create_agent_profile(
                process_ids=main_process_ids, profile_config=agent_files["profile"]
            )
            self.create_process_state_machine(
                process_ids=main_process_ids,
                state_machine_config=agent_files["state_machine"],
            )
        # main_assistant_process_ids = self.create_agent(
        #     name=assistant_name,
        #     tools_class=Assistant.__name__,
        #     task=Assistant.get_task(),
        #     instructions=Assistant.get_instructions(),
        #     thought_generator_mode=ThoughtGeneratorMode.POST,
        # )
        # # TODO: Should we add a get_event for each tool? We want both: Flexible events, but some can be attached directly to tool? TBD. No, they are connected to agent.
        # ClientHandlers().create_event_subscription(
        #     process_ids=main_assistant_process_ids,
        #     event_name="user_message",
        # )

        # self.create_agent(
        #     name=Orchestrator.get_name(),
        #     tools_class=Orchestrator.__name__,
        #     task=Orchestrator.get_task(),
        #     instructions=Orchestrator.get_instructions(),
        #     thought_generator_mode=ThoughtGeneratorMode.PRE,
        # )

    def create_agent_by_config(self, agent_config: Dict[str, Any]) -> ProcessIds:
        process_ids = self.create_agent(
            agent_name=agent_config["name"],
            tools_class=agent_config["tools_class"],
            memory_mode=AgentMemoryMode(agent_config["memory_mode"]),
            modalities=agent_config["modalities"],
            thought_generator_mode=ThoughtGeneratorMode(
                agent_config["thought_generator_mode"]
            ),
        )
        return process_ids

    def create_agent_communication(
        self, process_ids: ProcessIds, communication_config: Dict[str, Any]
    ):
        external_events = communication_config["external_events"]
        if len(external_events) > 0:
            for event_name in external_events:
                ClientHandlers().create_event_subscription(
                    process_ids=process_ids, event_name=event_name
                )
        # TODO: Configure topics and requests properly.

    def create_agent_profile(
        self, process_ids: ProcessIds, profile_config: Dict[str, Any]
    ):
        # TODO: implement me
        ClientHandlers().create_profile()

    def create_process_state_machine(
        self, process_ids: ProcessIds, state_machine_config: Dict[str, Any]
    ):
        for name, content in state_machine_config.items():
            ClientHandlers().create_process_state(
                user_id=self.user_id,
                process_id=process_ids.process_id,
                name=name,
                task=content["task"],
                instructions=content["instructions"],
                tools=content["tools"],
            )
        initial_state_name = next(iter(state_machine_config.keys()))
        # TODO: Implement me.
        ClientHandlers().update_current_process_state(
            user_id=self.user_id,
            process_id=process_ids.process_id,
            process_state_name=initial_state_name,
        )

    def create_agent(
        self,
        agent_name: str,
        tools_class: str,
        memory_mode: AgentMemoryMode,
        modalities: List[str],
        thought_generator_mode: ThoughtGeneratorMode = ThoughtGeneratorMode.PRE,
    ) -> ProcessIds:
        """Create a new agent"""
        try:
            agent_data = ClientHandlers().create_agent(
                user_id=self.user_id,
                name=agent_name,
                tools_class=tools_class,
                memory_mode=memory_mode.value,
                modalities=modalities,
                thought_generator_mode=thought_generator_mode.value,
            )
            self.logger.info(f"Agent created on database, uuid: {agent_data.id}")
            # Store agent on Weaviate
            self.memory_manager.create_agent(
                user_id=self.user_id, agent_data=agent_data
            )
            self.create_internal_processes(agent_id=agent_data.id, agent_name=name)

            # Main process

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

    def create_internal_processes(
        self, agent_id: str, agent_name: str, tools_class: str
    ):
        """Create the internal processes for the agent"""
        internal_processes_path = get_internal_processes_path()
        internal_processes_json_loader = JsonLoader(root_dir=internal_processes_path)

        # TODO: Main only have communications.json as config.json and state_machine.json are provided at agent level!
        # TODO: First read only main and create the main_process, return main_process ids at the end.
        main_process_data = ClientHandlers().create_process(
            user_id=self.user_id,
            agent_id=agent_id,
            name="main",
            tools_class=tools_class,
            flow_type=ProcessFlowType.INTERACTIVE,
            service_name=agent_name,  # Use the name of the agent as service name, TODO: Fix me using internal and external requests.
        )
        main_process_ids = ProcessIds(
            user_id=self.user_id,
            agent_id=agent_id,
            process_id=main_process_data.id,
        )

        # Then we create all the internal processes.
        internal_processes_files_dict = internal_processes_json_loader.search_files(
            file_names=["communications.json", "config.json", "state_machine.json"]
        )
        for process_folder, process_files in internal_processes_files_dict.items():
            process_ids = self.create_internal_process(
                agent_id=agent_id,
                agent_name=agent_name,
                process_folder=process_folder,
                process_files=process_files,
            )
            self.create_internal_process_state_machine(
                process_ids=process_ids,
                state_machine_config=process_files["state_machine"],
            )
