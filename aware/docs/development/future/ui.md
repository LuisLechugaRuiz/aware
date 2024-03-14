Remember that we want dynamic UIs.

But lets start by the first one:

For our scientific papers we want to have a chat (left side) and the paper itself (the one that is being created) all time updated on the right side. We can show it as a streaming, even the modifications. We need to think how to make this appeal.

But this would be novel and it will help to interact with our system to create any kind of document (for now just paper based on ArXiv).

Remember about generality.

Maybe on the left side is the chat and on the right is the specific item that is being created. In our case just the document. TBD.

—
View:

# Organization
Metrics

Overview (graph) 
showing discrete team

Artifacts
For all teams in the org.

# Team
Metrics

GRAPH
showing agents with inter-agent communication. This graphic should show each agent as a node and the connection between them with lines. It will use a different color to identify the different connection. Should look like a neural network of agents interconnected with different things (on top right we show all the labels, by default all of them are actived, but user can specify one of them. When any is active (not set as completed) the color gets intensify. This will help to see very clear how agents are connected, later we will want to edit them using similar concept than Figma. We have the nodes with the entries to services and we can plug any (output of agent) to input of agent, where the entry that is already existing depends on the services available. We can also plug in  events or topics which is a blackboard that is outside of the graphic and powers the agents. We can overlap everything, but ideally we can disable thing by thing to focus on certain. This is why react is very good for this case. We will create first all nodes, then the lines that represent the connections for different things: requests, actions (agent to agent lines) and events, topics (requires a external blackboard or a rectangle with different names and formats) and is connected from rectangle to agent.
This way overview ALWAYS have a “compute graph” that just displays the NODES in the screen. Then we can have different connections depending on what are we doing.

# Agent
METRICS

GRAPH
Graph of STATE MACHINE!!
DISPLAY MAIN STATE MACHINE ON SCREEN

ARTIFACTS.

In general view looks similar with some metrics ( depending on the hierarchy level ) and artifacts.

This will enable us to measure one by one how good is performing. It should also have a graphic that shows the connection of lower hierarchy (i.e: which teams do the org have like nodes separated for specific purspose)

—-

On GRAPH ABSTRACTION:

It is an abstract that includes:

display_nodes: this function should be implemented to show all nodes as separated entities, just dots into the graph (maybe better naming such as display nodes but without the connections, be very explicit here)

display_relationship: this function is used to communicate two nodes or node with something external. It can receive a color (for the lines) and when called it will render a different connection between the discrete things. This can be used multiple times by the classes that implement this function. This will add each new to labels that user can click to show / hide.

Example:
For teams we have:

display_nodes:
Get agents and show each point as a node. Each node is interconnected with agent, so when the user clicks it will move him to agent “screen!!”

display_relationships:
Multiple implementations:
(Client/server) agent to agent:
Requests
Actions

(Pu/sub) blackboard to agent:
Topics
Events