from typing import Any, Dict, List, Optional

from aware.agent.agent_config import AgentConfig
from aware.agent.agent_communication import AgentCommunicationConfig
from aware.agent.database.agent_database_handler import AgentDatabaseHandler
from aware.agent.agent_profile import AgentProfile
from aware.communication.primitives.primitives_config import CommunicationPrimitivesConfig
from aware.config.internal_processes.processes_config_loader import ProcessesConfigLoader
from aware.database.weaviate.memory_manager import MemoryManager
from aware.communication.communication_builder import (
    CommunicationBuilder,
)
from aware.process.process_config import ProcessConfig
from aware.process.process_builder import ProcessBuilder
from aware.process.process_ids import ProcessIds
from aware.process.process_data import ProcessFlowType, ProcessType
from aware.process.state_machine.state import ProcessState
from aware.utils.logger.file_logger import FileLogger

from aware_use_cases.config.config_loader import AgentConfigFiles, ConfigLoader


class AgentBuilder:
    def __init__(self, user_id: str):
        self.logger = FileLogger("agent_builder")
        self.user_id = user_id
        self.memory_manager = MemoryManager(user_id=user_id, logger=self.logger)
        self.agent_database_handler = AgentDatabaseHandler()

    def initialize_user_agents(self, config_template_name: str, user_id: str, assistant_name: str):
        """Create the initial agents for the user"""
        config_loader = ConfigLoader(template_name=config_template_name, user_id=user_id)

        communication_builder = CommunicationBuilder(user_id=self.user_id)
        self.setup_communications(communication_builder, config_loader)

        agent_dict = config_loader.get_all_agents_files()
        for agent_folder, agent_config_files in agent_dict.items():
            agent_config = AgentConfig.from_json(agent_config_files.config)
            if agent_config.name == "assistant":
                # Override assistant by the specific user given assistant name
                agent_config.name = assistant_name
                agent_config_files.config = agent_config.to_json()

            self.create_agent(
                agent_config_files=agent_config_files,
                communication_builder=communication_builder,
            )

        communication_builder.end_setup()

    # TODO: THIS SHOULD BE THE ENTRY POINT TO CREATE AGENTS FROM AGENTBUILDER TOOL
    # TODO: Add a default config -> All tools transition to continue and stop to end? Or request the AgentBuilder to build the states - Transitions of each agent if needed..
    def create_agent(
        self,
        agent_config_files: AgentConfigFiles,
        communication_builder: Optional[CommunicationBuilder] = None,
    ):
        if communication_builder is None:
            communication_builder = CommunicationBuilder()
            standalone_create_agent = True
        else:
            standalone_create_agent = False

        # 1. Create the agent
        agent_config = AgentConfig.from_json(agent_config_files.config)
        main_process_ids = self.create_new_agent(agent_config)

        # 2. Create the communication
        agent_communication_config = AgentCommunicationConfig.from_json(agent_config_files.communication)
        communication_builder.setup_agent(
            process_ids=main_process_ids,
            communication_config=agent_communication_config,
        )

        # 3. Create the main process state machine
        state_machine_states = self.get_process_states(agent_config_files.state_machine)
        process_builder = ProcessBuilder(
            user_id=self.user_id,
            agent_id=main_process_ids.agent_id,
        )
        process_builder.create_process_state_machine(
            process_ids=main_process_ids,
            state_machine_states=state_machine_states,
        )

        # 4. Create the agent profile
        agent_profile = AgentProfile.from_json(agent_config_files.profile)
        self.create_agent_profile(
            process_ids=main_process_ids, agent_profile=agent_profile
        )

        if standalone_create_agent:
            communication_builder.end_setup()

    def create_agent_profile(
        self, process_ids: ProcessIds, agent_profile: AgentProfile
    ):
        # TODO: implement me
        self.agent_database_handler.create_profile(
            process_ids=process_ids, agent_profile=agent_profile
        )

    def create_new_agent(
        self,
        agent_config: AgentConfig
    ) -> ProcessIds:
        """Create a new agent"""
        try:
            # Store agent on database
            agent_data = self.agent_database_handler.create_agent(
                user_id=self.user_id,
                name=agent_config.name,
                capability_class=agent_config.capability_class,
                memory_mode=agent_config.memory_mode.value,
                modalities=agent_config.modalities,
                thought_generator_mode=agent_config.thought_generator_mode.value,
            )
            self.logger.info(f"Agent created on database, uuid: {agent_data.id}")
            # Store agent on Weaviate
            result = self.memory_manager.create_agent(
                user_id=self.user_id, agent_data=agent_data
            )
            self.logger.info(f"Agent created on vector memory with result: {result}")

            # Create internal processes
            main_process_ids = self.create_internal_processes(
                agent_id=agent_data.id,
                agent_name=agent_config.name,
                capability_class=agent_config.capability_class,
            )

            return main_process_ids

        except Exception as e:
            return self.logger.error(f"Error creating agent {agent_config.name}: {e}")

    def create_internal_processes(
        self,
        agent_id: str,
        agent_name: str,
        capability_class: str,
    ):
        """Create the internal processes for the agent"""
        # Create main process using agent's capability class
        main_process_config = ProcessConfig(
            name=agent_name,
            capability_class=capability_class,
            prompt_name="meta",
            flow_type=ProcessFlowType.INTERACTIVE,
        )
        process_builder = ProcessBuilder(user_id=self.user_id, agent_id=agent_id)
        main_process_ids = process_builder.create_process_by_config(
            process_config=main_process_config, process_type=ProcessType.MAIN
        )

        # Create the internal processes
        internal_processes_files_dict = ProcessesConfigLoader().get_all_processes_files()
        for process_folder, process_files in internal_processes_files_dict.items():
            process_config = ProcessConfig.from_json(process_files.config)
            process_ids = process_builder.create_process_by_config(
                process_config=process_config, process_type=ProcessType.INTERNAL
            )
            process_states = self.get_process_states(process_files.state_machine)
            process_builder.create_process_state_machine(
                process_ids=process_ids,
                state_machine_states=process_states,
            )

        return main_process_ids

    def get_process_states(self, state_machine_config: Dict[str, Any]) -> List[ProcessState]:
        state_machine_states: List[ProcessState] = []
        for state_name, state_info in state_machine_config.items():
            state_info["name"] = state_name
            state_machine_states.append(ProcessState.from_json(state_info))
        return state_machine_states

    def setup_communications(
        self,
        communication_builder: CommunicationBuilder,
        config_loader: ConfigLoader
    ):
        primitives_config = config_loader.get_communication_primitives()
        communication_config_dict = {
            "actions_config": primitives_config.actions,
            "events_config": primitives_config.events,
            "requests_config": primitives_config.requests,
            "topics_config": primitives_config.topics
        }
        comm_primitives_config = CommunicationPrimitivesConfig.from_json(communication_config_dict)
        communication_builder.setup_communications(comm_primitives_config)
