# Main ideas on refactor

## Agent

### Config
Main configs to setup agent.

Includes:
- ThoughtGeneratorMode by default always PRE except on Assistant which is POST (or async soon).
- Memory: Stateless or statefull to determine if this agent is disposable or should have a continuous memory.
- Modality: To determine the modalities the underlying model that powers the agent can handle, all text for now but preparing for further implementations.

### State machine config
Creating state machine setup at a simple .json, but it should be created from python to json.

It defines:

#### States
Starts by name and contains different data as:

- Task
- Instructions
- Tools

#### Tools
Each tool make a transition to a specific step.

### Communications
Communications should be used to provide connections between agents, this way the agent can communicate info directly to other agents.
- Requests (To process requests from other agents or request them) - Sends or receives.
- Events (Specific trigger to wake up agent with specific info) - Only receives.
- Topic (share info directly through channel communication) - Sends or receives.

This way we can give tools such as:
create_request - To agent.
send_message - On channel (TOPIC).

We share the possible communications on system prompt so we don't need to provide explicit tools for this!
Automatic - Send request (if any connection one to one).
Send message (if any connection to channel).

## Internal processes

Configuration is similar to agent - It also have a state 


## Actionable Steps

- Create initial json for agents and internal_processes. (Request should have a description of what is needed).
- Add "default_functions" based on requests, channels and events (External and Internal). 