No need to save manually the pydantic but we send the complex format as we do when translating to OPENAI.

We have a (request creator) that gets a function and translates to request (args and so on as we do for communications.

We use the JSONPYDANTICPARSER.

Create tools for devs:
Request to JsonPydanticParser. With request being the arguments needed. The user sends them on terminal for now, but in the future using a UI to create relationship for agents one to one. It just introduces the formats and we instantly create and action server for this task. (For now just a request but feedback would be highly effective, but we need to improve action service to be able to receive updates over the current requests. The client of action server can UPDATE ACTION STATUS AND THIS AFFECT TO THE SERVER.

This way we have a update_action() on client as we do with create_request but for specific action. ACTION HAVE POTENTIAL TO BE SYNC.

If the action is sync is a request.

Agent should be able to select it on run time.

He just calls send_request and creates it sync or async and we just adapt over it. So AGENT IS AGNOSTIC OF IF SYNC OR ASYNC. He just need to use it when needed. But he should know when to do it sync or async.

This means: both action and client send a request with sync or async and depending if it is sync or not we create a request or an action.