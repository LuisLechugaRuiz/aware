# Request creation

This file includes new ideas about how to create new requests on demmand.

The core insight is that requests are created selecting client agent and service agent, this way we automatically setup the proper Client and Service on the respective agents.

This way we avoid needing to create them manually. We just need to define the requests of our system initially and then it will create the protocols.

## Request format
- Client name
- Service name
- Query
- Response format

## Request vs Action

We should do the same for action, which is just an async request.

The main difference is that action requires the feedback format.

## Setup

Two ways to create requests:

### Deterministic setup:

The requests are defined on setup, this means that the agent only have certain space of freedom, we give him a tool for each request he can use.

In this case a external source needs to setup request. It can be orchestrator (team leader) or user via the setup scripts (and soon the UI).

These requests live into team/ folder at use-case as they are for agent to agent inside a specific team.

### Real-time creation:

This is the strongest one as it increases the space of freedom between the agents, in this version the agents can create requests to any other agents in the team.

It just needs to define the format properly, but it also requires deep knowledge about the capabilities of any other agent as the response format is just a "template" and the fields will depend on the other agent possibilities.

For an autonomous system this would be the way to go:

Requests are just created on demand.
Client - Servers are only stablished until the request finishes.

Limitations:
We need to add info about each other agent at agent prompt.
We need to share info about capabilities of other agents, how to ensure that format makes sense?

### Hybrid

Options:
- deterministic setup agent-client.
- real-time creation.

In this version we have a deterministic setup configuring the services that the agents on the team are displaying.

These services expect specific format as input (should it be free format?) and have already a custom response designed for the service.

This will allow us to broadcast the services available (deterministic setup) while giving freedom to the agents to communicate with any other agent in the team.

We can start with free-format as this will help us to use a generic tool (called create request (sync or async)) and send a natural language query while ensuring proper response format.

This looks to me the best:

Deterministic: we understand service agent possibilities and create a tailored service.
Dynamic: Any client in the team can make requests to this service.

The only question is if free-format or query has specific format.
This modifies if we can use generic tool (create_request) or we need to give a tool to each agent in the team for each service.
