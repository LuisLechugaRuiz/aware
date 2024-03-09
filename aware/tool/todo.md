# TODO

This repo should only contain the logic of how to run tools (tool interface + tool manager) along with capabilities and database.

We need a external repo for specific use-cases where we place all tools that we are creating for that.

We should also split between Capabilities (Akin to class and the main container that determines the potential actions of an agent) and tools (specific methods that can be called by the agent).
This way we can have specific Capabilities that requires logging on different devices, even some logic or instructions specific for the capabilities itself!