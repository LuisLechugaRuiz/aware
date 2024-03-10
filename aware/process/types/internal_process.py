from aware.process.process_ids import ProcessIds
from aware.process.process_interface import ProcessInterface


class InternalProcess(ProcessInterface):
    def __init__(self, process_ids: ProcessIds):
        super().__init__(ids=process_ids)

    @property
    def name(self) -> str:
        return self.process_data.name

    # TODO: Address me properly. Each internal process should have his own prompt!! This requires a small change on chat.py
    @property
    def prompt_name(self) -> str:
        return self.process_data.prompt_name

    def on_finish(self):
        pass
