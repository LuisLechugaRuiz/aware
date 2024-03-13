# TODO: Create the setup to create agent by filling some fields.
# TODO: Use also the setup of process states!!
from aware.process.state_machine.setup.setup import StateSetup


class AgentSetup:
    def __init__(self, client: Client):
        self.client = client
        self.logger = SystemLogger("agent_setup")