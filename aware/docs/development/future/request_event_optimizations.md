# Request - Event Optimizations

Requests are the main trigger for most of the agents, there are three options:

- Events: An event external to the system, it will be handled by the event_subscriber.
- Requests: A petition that a client sends to a service, is the main way how the agents collaborate to complete a task, it should be the core communication as the normal flow would be: First we get an external event that needs to be managed, an agent (from a specific team) receives it. The agent will use his tools to process the event and then for most cases it will request something to other agents which have a different tool. This way the agents will start collaborating until the event has been properly managed. For now we are not tracking any particular event, but something to consider would be to also track the EventStatus as we do for Requests

In the future how I see this is:
We track request status to understand the performance of an agent to solve an atomic inquiry.
We track event status to understand the performance of a team to handle a specific event.

This way we have a global vision:
Event managing.

And local vision:
Request managing.

The main thing that I wanted to comment about this point is that we will also need a intelligent priority system. This will help to optimize our system and solve the most urgent tasks first.

So two points about this:

We need:

- TRACKING
- PRIORITIES

For tracking we need to implement the logic at [Communications protocols](/aware/communications/communication_protocols.py)

## Update

An initial version of PRIORITIES has been created by just adding the LLM to determine the priority. This is a very short-term implementation as this is not properly done. To stablish priorities we need a general vision of current execution, it should not be the own agent determining the priority, it should be an agent (or the team-leader) which has an overview of current executions.