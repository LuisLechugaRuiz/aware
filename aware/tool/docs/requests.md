About requests...

A request is a petition from agent to agent.

Until now we were sending them as part of tools, but we are on a refactor to avoid including any bussiness logic inside our tool set.
The goal is to be able to configure the tools from outside.

We want to avoid creating requests / stopping the processes inside the tool classes.

On requests:

Sometimes we want to send a request -> Send info to other agent and wait / or track it async, but it can also means executing some tool.

I think the best solution for this dilema is to always delegate the execution to the server, so we just send a detailed natural language message so the server can use the proper tools to achieve it.

Rethinking this... The approach of sending a natural language instruction is limited. In the previous case orchestrator is compiling relevant info i.e: Tool classes availables, so if the communication
relays only on natural language them we loose this structure and it becomes more error prone as we delegate on client the responsability to understand the info and use it properly...

We have right now a dummy class called Service which doesn't do much at the end as we are just doing agent to agent with natural language.
But it might make sense that a agent can manage multiple Services, the difference is the INFO that it needs to satisfy the request, therefore we might want to add an option to create_service
for each agent and ask for specific fields that later should be filled by the Client and parsed properly ( showed on the prompt ) for the Server to best perform his task.