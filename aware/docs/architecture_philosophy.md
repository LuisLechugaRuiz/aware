# Architecture

Lets define the goals behind our architecture using First principles.

Aware is a platform that enables the creation and deployment of multi-agent systems powered by LLMs.

The end goal of the platform is to be able to run autonomously, without human intervention improving itself and reconfiguring as needed.

But we need to align with market goals, for this we need a tradeoff between generality and flexibility.

This tradeoff will affect the use-cases BUT should NOT affect the core development.

This is the reason why the best way to ensure that both goals are aligned is to create architectures by config.

On one side we can create an autonomous platform which is able to create Teams and Agents and coordinate them, on the other side we should be able to create fixed architectures that can be used continuously to satisfy users demand, this will power the wave on our bussiness opportunities and will help us to have user feedback to improve our platform while maintaining the long term goal: Self-evolving autonomous system powered by AI models.