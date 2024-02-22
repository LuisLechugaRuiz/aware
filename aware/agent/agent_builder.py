from typing import Any, Dict, List

from aware.agent.agent_data import AgentMemoryMode, ThoughtGeneratorMode
from aware.config import get_default_agents_path, get_internal_processes_path
from aware.data.database.client_handlers import ClientHandlers
from aware.memory.memory_manager import MemoryManager
from aware.process.process_builder import ProcessBuilder
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessFlowType
from aware.utils.logger.file_logger import FileLogger
from aware.utils.json_loader import JsonLoader


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
                "communications.json",
                "profile.json",
                "state_machine.json",
            ]
        )
        for agent_folder, agent_files in agent_files_dict.items():
            main_process_ids = self.create_agent_by_config(
                assistant_name=assistant_name,
                agent_config=agent_files["config"],
                agent_state_machine_config=agent_files["state_machine"],
            )
            self.create_agent_communications(
                process_ids=main_process_ids,
                communications_config=agent_files["communications"],
            )
            self.create_agent_profile(
                process_ids=main_process_ids, profile_config=agent_files["profile"]
            )

    def create_agent_by_config(
        self,
        assistant_name: str,
        agent_config: Dict[str, Any],
        agent_state_machine_config: Dict[str, Any],
    ) -> ProcessIds:
        agent_name = agent_config["name"]
        if agent_name == "assistant":
            agent_name = assistant_name
        process_ids = self.create_agent(
            agent_name=agent_name,
            tools_class=agent_config["tools_class"],
            memory_mode=AgentMemoryMode(agent_config["memory_mode"]),
            modalities=agent_config["modalities"],
            thought_generator_mode=ThoughtGeneratorMode(
                agent_config["thought_generator_mode"]
            ),
        )
        # TODO: Move this inside create_agent as this will be needed, but we need a way to pass state_machine_config from AgentBuilder tool.
        process_builder = ProcessBuilder(
            user_id=self.user_id, agent_id=process_ids.agent_id
        )
        process_builder.create_process_state_machine(
            process_ids=process_ids, state_machine_config=agent_state_machine_config
        )
        return process_ids

    def create_agent_communications(
        self, process_ids: ProcessIds, communications_config: Dict[str, Any]
    ):
        external_events = communications_config["external_events"]
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
        ClientHandlers().create_profile(
            process_ids=process_ids, profile_config=profile_config
        )

    # TODO: This is the entry point to create agents from AgentBuilder tool, but now it needs to have the state_machine_config style to be usable.
    # TODO: Add a default config -> All tools transition to continue and stop to end? Or request the AgentBuilder to build the states - Transitions of each agent if needed..
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
            # Store agent on database
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
            result = self.memory_manager.create_agent(
                user_id=self.user_id, agent_data=agent_data
            )
            self.logger.info(f"Agent created on vector memory with result: {result}")

            # Create internal processes
            main_process_ids = self.create_internal_processes(
                agent_id=agent_data.id, agent_name=agent_name, tools_class=tools_class
            )
            return main_process_ids

        except Exception as e:
            return self.logger.error(f"Error creating agent {agent_name}: {e}")

    def create_internal_processes(
        self, agent_id: str, agent_name: str, tools_class: str
    ):
        """Create the internal processes for the agent"""
        internal_processes_path = get_internal_processes_path()
        internal_processes_json_loader = JsonLoader(root_dir=internal_processes_path)

        # TODO: Main only have communications.json as config.json and state_machine.json are provided at agent level!
        main_config = {
            "name": "main",
            "tools_class": tools_class,
            "flow_type": ProcessFlowType.INTERACTIVE,
        }
        process_builder = ProcessBuilder(user_id=self.user_id, agent_id=agent_id)
        main_process_ids = process_builder.create_process_by_config(
            process_config=main_config, service_name=agent_name
        )
        # TODO: Add main communications?
        # TODO: Add process state machine when deciding how to pass it from AgentBuilder tool.

        # Create the internal processes
        internal_processes_files_dict = internal_processes_json_loader.search_files(
            file_names=["communications.json", "config.json", "state_machine.json"]
        )
        for process_folder, process_files in internal_processes_files_dict.items():
            process_ids = process_builder.create_process_by_config(
                process_config=process_files["config"]
            )
            process_builder.create_process_state_machine(
                process_ids=process_ids,
                state_machine_config=process_files["state_machine"],
            )
            process_builder.create_process_communications(
                process_ids=process_ids,
                communications_config=process_files["communications"],
            )

        return main_process_ids
