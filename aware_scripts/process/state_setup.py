from typing import Dict, Optional

# TODO: REPLICATE THE LOGIC OF THIS FILE BUT WITH THE LOGIC ON THE UI.


# TODO: STATE MACHINE SHOULD NOT BE INSIDE PROCESS.
from aware.agent.agent_data import AgentData, AgentState, AgentMemoryMode, ThoughtGeneratorMode
from aware.process.process_data import ProcessData, ProcessFlowType, ProcessType
from aware.process.state_machine.transition import Transition
from aware.tool.capability.capability import Capability
from aware.tool.capability.capability_registry import CapabilityRegistry
from aware.process.state_machine.transition import Transition, TransitionType
from aware.process.state_machine.state import ProcessState
from aware.process.process_ids import ProcessIds
from aware.process.process_info import ProcessInfo
from aware.utils.logger.process_logger import ProcessLogger # TODO: move to process/utils.

from aware_capabilities import get_capabilities_folder_path
from aware_use_cases import get_template_config_path


DEF_TRANSITION_INSTRUCTIONS = """When selecting transition choose 0 to continue, 1 to end or the name of the state to transition to."""


class StateSetup:
    # 1. Get the capability:
    def __init__(self, process_ids: ProcessIds, process_info: ProcessInfo, process_logger: ProcessLogger):
        self.process_ids = process_ids
        # TODO: get process info from database
        self.process_info = process_info
        self.process_logger = process_logger
        self.capabilities_registry = CapabilityRegistry(
            process_ids=self.process_ids,
            process_logger=self.process_logger,
            capabilities_folders=[get_capabilities_folder_path()],
            save_on_db=False)
        
        # TODO: move this to agent_setup?
        #   We need general level setup folder where we can do all this stuff - ala stk.
        template_config_path = get_template_config_path() # This will get autonomous template.
        # Now we need to create the state setup
        # Now we need to get the specific agent that will be edited (for now just adding a state).

    # This should happen for each time create new state is called.
    def create_process_state(self, name: str, is_default: bool) -> ProcessState:
        task = input("Introduce the task: ")
        instructions = input("Introduce the instructions: ")

        # TODO: Add MULTIPLE capabilities.
        capability = self.get_capability()
        tool_transitions = self.get_tool_transitions(capability, is_default)
        # Create process state.
        return ProcessState(name=name, tool_transitions=tool_transitions, task=task, instructions=instructions)

    def add_task(self, task):
        self.task = task

    def add_instructions(self, instructions):
        self.instructions = instructions

    def run(self, is_default: bool):
        # Ideally we ask for team name and agent name and it should be able to make the change.
        team_name = input("Introduce the team name: ")
        # team_id = self.team_database_handler.get_team_id(team_name)
        agent_name = input("Introduce the agent name: ")
        # agent_id = self.agent_database_handler.get_agent_id(agent_name, team_id)
        # from it we get the process_ids that we need to save on supabase (the agent itself and so on.)
        if is_default:
            name = "default"
        else:
            name = input("Name of the state: ")
        process_state = self.create_process_state(name, is_default)
        print(f"---PROCESS STATE---\n{process_state.to_string()}")

        # TODO: THIS SHOULD SAVE ON SPECIFIC PROCESS FOR USER - AGENT ON OUR CONFIG.

        # TODO: save process state on supabase.
        # ProcessDatabaseHandler().create_process_state(
        #     user_id=self.process_ids.user_id,
        #     agent_id=self.process_ids.agent_id,
        #     process_state=process_state,
        # )

    def get_tool_transitions(self, capability: Capability, is_default: bool) -> Dict[str, Transition]:
        tools = capability.get_tools()
        tool_transitions: Dict[str, Transition] = {}
        print(DEF_TRANSITION_INSTRUCTIONS)
        for tool in tools:
            if is_default:
                transition_type = TransitionType.CONTINUE
                new_state = None
            else:
                transition_input = input(f"- Tool: {tool.name} - Transition: ")
                try:
                    transition_input_int = int(transition_input)  # Convert input to integer
                    if transition_input_int == 0:
                        transition_type = TransitionType.CONTINUE
                    elif transition_input_int == 1:
                        transition_type = TransitionType.END
                    else:
                        # If input is an integer other than 0 or 1, treat it as OTHER
                        transition_type = TransitionType.OTHER
                    new_state = None
                except ValueError:
                    # If input cannot be converted to integer, treat it as OTHER with new_state as the input
                    transition_type = TransitionType.OTHER
                    new_state = transition_input
            tool_transitions[tool.name] = Transition(type=transition_type, new_state=new_state)
        return tool_transitions

    def get_capability(self) -> Capability:
        # TODO: Print for now, make this a dropdown into the UI.
        capability: Optional[Capability] = None
        while not capability:
            capabilities_str = " | ".join(self.capabilities_registry.capabilities.keys())
            capability = input(f"Please select one of these capabilities:\n{capabilities_str}\nCapability: ")

            capability_class_type = self.capabilities_registry.get_capability(capability)
            if capability_class_type is None:
                print("Capability not found.")
                capability = None
            else:
                capability = capability_class_type(
                    process_info=process_info,
                )
        return capability


# TODO: move this logic higher in the setup hierarchy to agent level.
if __name__ == "__main__":
    process_ids = ProcessIds(user_id="user_id", agent_id="agent_id", process_id="process_id")
    agent_data = AgentData(
        id="agent_id",
        name="mocked_agent",
        description="mocked_description",
        context="mocked_context",
        capability_class="mocked_capability_class",
        state=AgentState.FINISHED,
        memory_mode=AgentMemoryMode.STATEFUL,
        modalities=["mocked_modalities"],
        thought_generator_mode=ThoughtGeneratorMode.DISABLED,
    )
    process_data = ProcessData(
        id="process_id",
        name="mocked_process",
        capability_class="mocked_capability_class",
        prompt_name="mocked_prompt_name",
        flow_type=ProcessFlowType.INDEPENDENT,
        type=ProcessType.INTERNAL,
    )
    process_info = ProcessInfo(
        agent_data=agent_data,
        process_ids=process_ids,
        process_data=process_data
    )
    process_logger = ProcessLogger(user_id="user_id", agent_name="mocked_agent", process_name="mocked_process")
    state_setup = StateSetup(process_ids=process_ids, process_info=process_info, process_logger=process_logger)
    is_default_input = input("Is default? (y/n): ")
    is_default = is_default_input == "y"
    state_setup.run(is_default)
        
# TODO: WE NEED ONE MORE THING!

# We need to get agent from the name.

# So I log with my user_id and then I can get directly the process ids just by knowning the team_name and agent_name!!
        
# StateSetup!
# def add_tool():
    
# {
#     "default": {
#         "tools": {
#             "search": "continue",
#             "intermediate_thought": "continue",
#             "final_thought": "end"
#         },
#         "task": "Optimize {agent_name}'s performance in executing its task through strategic thought generation.
# {agent_name}'s Task:
# {agent_task}",
#         "instructions": "Thought Generation Steps:
# 1. Gather task-relevant information.
# 2. For complex tasks, apply intermediate_thought and refine as necessary.
# 3. Finalize with a strategic final_thought to guide {agent_name}.

# Operational Principles:
# - Prioritize backend processing without engaging in direct interactions.
# - Ensure thoughts are pertinent and flexible to the demands of {agent_name}'s task.",
#     }
# }


    
#     # TODO: Here we should differentiate between request_message and response_message, we can also ask if is sync or async
#     is_async = input("Is async? (y/n): ")
#     if is_async:
#         # START CREATING ACTION - INCLUDE FEEDBACK!!
#     else:
#         # CREATE REQUEST


#     # TODO: Move to arguments creation function!
#     args = {}
#     while input("Add argument? (y/n): ") == "y":
#         name = input("Name: ")
#         type = input("Type: ")
#         args[name] = type
#     schema = NewPydanticParser.get_openai_schema(name=name, args=args, description=description)
#     print("Schema: ", schema)