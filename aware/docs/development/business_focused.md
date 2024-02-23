# Modifications to provide different use-cases.

We need both: flexiblity and deterministic behavior.

We want our system to be able to scale and build it autonomously.

This is useful for some markets:
- Personal assistant

And to develop new systems by our developers (or users that want to create using Aware).

But we also want to have deterministic behavior:
- Specific teams.
- Specific workflows.
- Controllable outputs....

This would be similar to having a specific SNAPSHOT of a system.

We are already doing this with our "configuration" where we setup Assistant - TeamBuilder - AgentBuilder to create the self-evolving system, we can do the same concept to build multiple use-cases and iterate over the newly generated system to improve it over time.

### What we need for this?
We need a way to export our current configuration from database to config, this way we ensure we can run this system instead of our self-evolving version!!