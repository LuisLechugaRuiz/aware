from aware.agent.agent_data import AgentData, AgentState, ThoughtGeneratorMode


class AgentStateMachine:
    def __init__(
        self,
        agent_data: AgentData,
        is_process_finished: bool,
    ):
        self.state = agent_data.state
        self.thought_generator_mode = agent_data.thought_generator_mode
        self.is_process_finished = is_process_finished

    def step(
        self,
    ) -> AgentState:
        if self.state == AgentState.IDLE:
            return self.on_start()
        elif self.state == AgentState.MAIN_PROCESS:
            return self.on_main()
        elif self.state == AgentState.THOUGHT_GENERATOR:
            return self.on_thought_generator()

    def on_start(self) -> AgentState:
        if self.thought_generator_mode == ThoughtGeneratorMode.PRE:
            return AgentState.THOUGHT_GENERATOR
        else:
            return AgentState.MAIN_PROCESS

    def on_main(self) -> AgentState:
        """Runs a single iteration of the main process.
        - If mode is POST, we transition to thought generator.
        - Else we finish.
        """
        # Run only one iteration and trigger transition!
        if self.thought_generator_mode == ThoughtGeneratorMode.POST:
            return AgentState.THOUGHT_GENERATOR
        else:
            return AgentState.FINISHED

    def on_thought_generator(self) -> AgentState:
        """Runs until thought generator has finished.
        - If mode is PRE, we transition to main process.
        - Else we finish.
        """
        # TODO: Add here max iterations when adding complex thoughts - with Branches and Merges:
        #   Tree of thoughts to split a task into multiple sub-tasks recursively with max depth and max iterations.
        if not self.is_process_finished:
            return AgentState.THOUGHT_GENERATOR

        if self.thought_generator_mode == ThoughtGeneratorMode.PRE:
            return AgentState.MAIN_PROCESS
        else:
            return AgentState.FINISHED
