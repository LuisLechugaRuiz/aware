# On LLMs and cache

Current prompts are too slow, but this might be fixable if we have control of the LLM.

Current LLMs works with Attention, where each new token is looking back to all previous tokens.

Our prompts have always a history (conversation). So far we are adding the conversation at the end and system at start, but this is a wrong interpretation of how it should work based on the current architecture.

Conversation is fixed, doesn't change, is the HISTORY or WORKING MEMORY. Can be catched as the interpretation comes after the tokens. Then we can add the new variables that affect the generation of new tokens. This way we only need to interpret this variables that modifies the existing catche. We might need to process much less tokens at any given time. But there is a catch: We trim the conversation removing old messages, but is this bad? Our interpretation of tokens still doesn't change, it just means that we don't need to send as many tokens, this is converging, we just need to save on catche a specific amount of tokens, we can TOTALLY remove conversation as it should be part of cache and we should only trim the cache to avoid computing too much tokens when processing the variables. This is the way to go.

Current limitation?

The architecture of ChatML or OpenAI.

It consider:

System (hidden prompt) which includes both the instruction and variables (not for OpenAI as they are in a primitive state right now).

Then it comes any of User-Assistant-Tool..... Which composes the conversation.

But this order is WRONG! it doesn't help to cache as System is variable but conversation is fixed, so I think we should design new templates for our prompts. Working with this catche can make everything much easier to optimize, we can have 1.2k tokens at System and still be super efficient as we don't need to process the conversation again and again.

While this is true it brings a new interrogation into the system:
When we process the output we are computing the attention based on all previous tokens, but we are including the System there, later when we compile this new info into catche it contains a weird mix, maybe this can be the way to go, but then the attention becomes arbitrary. I think what we should do would be just computing only the attention for each new generation? So we have:

Input:
- History
- Instructions

This generates:
- Output

Then we process attention for output on:
- History
- Output

Which becomes just the cached history.

Then we repeat the loop with optimized history.