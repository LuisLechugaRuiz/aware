from aware.agent.agent_data import AgentData, AgentState, ThoughtGeneratorMode
from aware.process.process_communications import ProcessCommunications


# TODO: make this cleaner, a small state machine to decide which process run first.
class AgentStateMachine:
    @classmethod
    def step(
        cls, agent_data: AgentData, process_communications: ProcessCommunications
    ) -> AgentState:
        state = agent_data.state
        thought_generator_mode = agent_data.thought_generator_mode
        has_request = process_communications.incoming_request is not None

        if state == AgentState.IDLE:
            cls.on_start(thought_generator_mode=agent_data.thought_generator_mode)
        elif state == AgentState.MAIN_PROCESS:
            if thought_generator_mode == ThoughtGeneratorMode.POST:
                return AgentState.THOUGHT_GENERATOR
            else:
                return cls.on_loop_finished(
                    has_request=has_request,
                    thought_generator_mode=thought_generator_mode,
                )
        elif state == AgentState.THOUGHT_GENERATOR:
            if thought_generator_mode == ThoughtGeneratorMode.PRE:
                return AgentState.MAIN_PROCESS
            else:
                return cls.on_loop_finished(
                    has_request=has_request,
                    thought_generator_mode=thought_generator_mode,
                )

    def on_start(cls, thought_generator_mode: ThoughtGeneratorMode) -> AgentState:
        if thought_generator_mode == ThoughtGeneratorMode.PRE:
            return AgentState.THOUGHT_GENERATOR
        else:
            return AgentState.MAIN_PROCESS

    @classmethod
    def on_loop_finished(
        cls, has_request: bool, thought_generator_mode: ThoughtGeneratorMode
    ) -> AgentState:
        # Check if has requests and schedule the newest one or just stop it!
        if has_request:
            return cls.on_start(thought_generator_mode)
        return AgentState.IDLE
