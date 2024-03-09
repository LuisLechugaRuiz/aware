from aware.process.process_ids import ProcessIds
from aware.process.process_interface import ProcessInterface


class InternalProcess(ProcessInterface):
    def __init__(self, process_ids: ProcessIds):
        super().__init__(ids=process_ids)

    def step(self, should_continue: bool):
        """Step process on internal process, using should_continue to determine if the process has finished."""
        # TODO: Improve is_process_finished:
        #   We use this var as thought_generator should loop until generating the new thought, then we plan to add a decorator @stop_process, but this should not affect main...
        #   Now that we are splitting both processes it might make sense to rethink Agent StateMachine as we have explicit process.
        self.process_handler.step(
            process_ids=self.process_ids,
            is_process_finished=not should_continue,
        )
