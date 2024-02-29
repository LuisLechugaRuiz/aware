A diffusion model is the translation of noise to a specific form, is useful to materialize specific representations, such as dreams or modifications of something that can be represented from noise.

Is a way to create abstract representations, denoising to transform the potential into something specific due to some constraint.

It can be used to solve manipulation, denoising the positions on the 3D physical space to determine the position of each joint at any given moment.

For this it needs to predict the future, learn the physics of the universe to represent a specific reality.

Once the robot can dream about the future in a way that resembles closely the real world, then it will be able to determine the best action at any given moment.

Is always a prediction about the next action in the future, but the diffusion technique is effective on the representation, on the form.

Can we train LLMs with diffusion models?
A diffusion model translates noise into a specific representation, is working on the space of all possible forms.

The LLMs are working in an abstract plane, the don't represent a specific form but an idea itself that is then transmited through forms (language) into a specific representation.
The diffusion would give a shape, it can show the letters thanks to a denoising of the most possible shape, but it would work over the possibility of pixels, or in this case tokens, it can work denoising between tokens to reach a specific resolution. But this hard in the context of language. In a picture the representation over the form is easily differentiable between levels of resolution, but in language  it becomes arbitrary, there is not a clear separation between the group of forms itself as we construct using the same core block, a vocabulary which depth is constant, only a specific group of these tokens can form a specific meaning.

I'm now imagining a possible aplication of diffusion for language. Language is represented through tokens, the result of the representation depends on the order of each token.

A diffusion model can make resolutions at different scales, moving through noise, jumping between states of different resolutions. In a fractal manner it would represent the increase of the focus on a specific area, increasing the resolution of that reality. For language it can mean travelling between different orders, jumping from specific past to future or even to some pieces that would fit perfectly in the present moment. It would get a picture of the full scene, and will start creating different representations of the same reality with different level of abstractions, from simple sentences to deeper reasoning.

In this way I see reasoning as an augmentation of the resolution. The representation can be a picture, a thought or any other kind of information kind that you are receiving on a specific language. Reasoning would be the capability of being able to move from simple observations to complex laws, increasing the level of understanding. Increasing the resolution is a way of reasoning over the language.

A* diffusion transformer.

What if each "denoising" would be a step to jump between sentences?

Lets imagine that I have a question and I need an answer:
I would start thinking about a simple idea to solve the answer, and then I will be joining several ideas through different steps.

We can split the reasoning trace of current LLMs (or human datasets) into chunks. Batching reasoning trace as a step and jumping between the different token at each step of the denoising.
This way the denoising will follow a temporal reasoning. It will contain the next step at any given time.

What happen with transformers:
They don't have internal memory, the data is only transmited forward in time everytime is called. Is computationally not very efficient to recompute the past on any given moment to predict the future so it would be fundamental to maintain an internal representation that can be shared to avoid processing over and over the same data. This is why we need agents. We need to create the internal behavior of the LLM to avoid repeating the same process again and again, but adding info over time. This is the core philosophy behind Aware, the possibility of hold a continuos reality over different interactions.

Observing the present and processing info.

Storing the info and reflecting from the situation.

Using past learnings to improve current performance.

Is a explicit RL method, where the language is improved using language itself. Without modifying the weights of the LLM, just by using the LLM as a turing machine and rolling the type which would be the info from the maintainance of this internal state.