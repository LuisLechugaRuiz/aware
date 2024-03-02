Some ideas from the book: The mind is Flat.

He comments:
'Our brain is an improviser, and it bases its current improvisations on previous improvistations (as our thought generator!): it creates new momentary thoughts and experiences by drawing not on a hidden inner world of knowledge, belifes and motives, but on !! memory traces of previous momentary thoughts and experiences !!'

Interpolating with our design:

Talking about two of our internal processes:
- Main
- Thought

Main would be the "experience flow", the usage of our current tool to act based on previous inputs and following an inner thought.

Thought would be the "thoughts flow", the creation of a new inner thought based on previous experience + thought flow and the memory traces.

In this case is obvious that thought is the one that is connected to our memory traces, but it brings into consideration how to compose the episodic memory.

So far the maximum length of our thought flow is the token limits that we allow by config, after that we trim the prompt so the info is lost. We then save data, interpretations from the 'main process conversation'.

Right now we show both: thoughts + actions on main process and ask data storage manager to save data.

This looks like the right approach, but we should consider if this is how it should be or if we should rethink this logic:

- Main only have access to previous experience and current thought is part of system.
- Thought generator conversation is also used to store the most relevant thoughts.

An interesting think about this approach is that we can see the experiences (or main conversation) as the episodic flow, they are just raw experiences. Then we can see the thought generator conversation as a semantic flow, they are interpretations, recombination of previous experiences (and maybe previous thoughts!!) to create new integrations that are used to optimize the performance of the main process.

This would allow us to create our two different memories:
Episodic memory: From main process, fixed memory, they are interpretations of experiences and doesn't need too be edited (our brain recreates them, but I think this is due to the nature of human biology where we need to refactor our brain on each iteration instead of saving raw memories).

Semantic memory: From thought process, adaptable memory. The new integrations are stored and retrieved again, but how can we make this? Do we need to insert and edit memory on vector database? My opinion and the main goal of future Aware version is: instead of depending on vector database for thoughts we train a SMALL LLM. This LLM will be the one in charge of producing inner thoughts, this brings new questions as right now we just: ask questions to memory and integrate them, but this LLM will give us a already processed response, we should use both. We can see this as our intuition (fast LLM trained on thought traces) and recall (retrieving memories from database). To be considered, but I think this would be key as we can modify the training of these LLMs to optimize thought performance which later optimizes task execution.