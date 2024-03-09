# Multimodal

We need two parameters to define the modalities:

Input - Output.

We will also need a common interface to interact with all the modalities using a general purpose class.

Some examples:
Input: Text
Output: Image
Model: Dalle-3

Input: Text
Output: Video
Model: Sora

Input: Images, Text
Output: Text
Model: GPT4-V

Input: Sound
Output: Text
Model: Whisper
.....

The cool thing about this is that we can configure any agent based on input - output, it can be agnostic of the agent itself.

For this we need to define how to use tools in this case and we need to create a dict which maps each combination to a different model.