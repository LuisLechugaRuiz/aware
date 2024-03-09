from aware.agent.agent_builder import AgentBuilder as InternalAgentBuilder
from aware.communication.requests.request import Request


# TODO: IMPLEMENT THE WAY TO CALL REQUEST PROPERLY. WE NEED TO PASS BOTH: STANDARD ARGUMENTS (FOR INTERNAL PROCESSING, such as user_id or process_ids) + the request_message (JSON TO args).
def create_agent(
    self, request: Request, name: str, tools: str, task: str, instructions: str
):
    """
    Create a new agent which satisfies the request description.

    Args:
        name (str): Agent's name, a specific variable name used to describe the agent, will be used to identify the agent. Should follow convention: lower followed by "_".
        tools (str): The tools that the agent should use to accomplish the next step.
        task (str): Agent's task, a highlevel description of his mission, should be general to solve similar requests.
        instructions (str): Specific instructions or recommendations about possible combinations of tool executions that could be performed to satisfy the requests.
    """
    # TODO: Implement me properly.
    agent_builder = InternalAgentBuilder(user_id=request.user_id)

    try:
        agent_builder.create_agent(
            name=name,
            capability_class=tools,
            task=task,
            instructions=instructions,
        )
        return f"Agent {name} created successfully"
    except Exception as e:
        return f"Error creating agent {name}: {e}"


# TODO: IMPLEMENT THE WAY TO CALL REQUEST PROPERLY. WE NEED TO PASS BOTH: STANDARD ARGUMENTS (FOR INTERNAL PROCESSING, such as user_id or process_ids) + the request_message (JSON TO args).
def create_agent(self, request: Request, name: str, description: str, tools: str):
    """
    Create a new agent which satisfies the request description.

    Args:
        name (str): Agent's name, a specific variable name used to describe the agent, will be used to identify the agent. Should follow convention: lower followed by "_".
        description (str): Description of the agent, explaining his role inside the team depending on the tools he uses.
        tools (str): The tools that the agent should use to accomplish the next step.
    """
    # TODO: Implement me properly.
    agent_builder = InternalAgentBuilder(user_id=request.user_id)

    try:
        # TODO: agent builder should be able to create a new agent without detailing task and instructions (which are part of state machine).
        agent_builder.create_agent(
            name=name,
            capability_class=tools,
            task=task,
            instructions=instructions,
        )
        return f"Agent {name} created successfully"
    except Exception as e:
        return f"Error creating agent {name}: {e}"
