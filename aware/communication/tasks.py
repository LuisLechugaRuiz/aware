from aware.communication.primitives.event import Event
from aware.communication.primitives.action import Action
from aware.communication.primitives.request import Request
from aware.communication.primitives.topic import Topic
from aware.communication.protocols.database.protocols_database_handler import (
    ProtocolsDatabaseHandler,
)
from aware.chat.conversation_schemas import ToolResponseMessage, UserMessage
from aware.chat.database.chat_database_handler import ChatDatabaseHandler
from aware.process.database.process_database_handler import ProcessDatabaseHandler
from aware.process.process_handler import ProcessHandler
from aware.server.celery_app import app


@app.task(name="communication_dispatcher.create_action")
def create_action(primitive_str: str) -> Action:
    action = Action.from_json(primitive_str)
    service_process_ids = ProcessDatabaseHandler().get_process_ids(
        process_id=action.service_process_id
    )
    ProcessHandler(process_ids=service_process_ids).start()


@app.task(name="communication_dispatcher.create_request")
def create_request(primitive_str: str) -> Request:
    request = Request.from_json(primitive_str)
    service_process_ids = ProcessDatabaseHandler().get_process_ids(
        process_id=request.service_process_id
    )
    ProcessHandler(process_ids=service_process_ids).start()


@app.task(name="communication_dispatcher.create_event")
def create_event(primitive_str: str) -> Event:
    event = Event.from_json(primitive_str)
    event_subscribers = (
        ProtocolsDatabaseHandler().get_event_subscribers_from_type(
            event.event_type_id
        )
    )
    for event_subscriber in event_subscribers:
        process_ids = ProcessDatabaseHandler().get_process_ids(
            event_subscriber.process_id
        )
        ProcessHandler(process_ids=process_ids).start()


@app.task(name="communication_dispatcher.set_action_completed")
def set_action_completed(primitive_str: str):
    action = Action.from_json(primitive_str)
    client_process_ids = ProcessDatabaseHandler().get_process_ids(
        action.client_process_id
    )
    # - Add new message with the response and start the client process.
    client_process_handler = ProcessHandler(process_ids=client_process_ids)
    client_process_handler.add_message(
        message=UserMessage(
            name=action.service_name, content=action.response_to_string()
        ),  # TODO: is name = action.service_name correct or should it be the service_process_name?
    )
    client_process_handler.start()


@app.task(name="communication_dispatcher.set_request_completed")
def set_request_completed(primitive_str: str):
    # Add message to client process.
    request = Request.from_json(primitive_str)

    chat_database_handler = ChatDatabaseHandler()
    # - Sync requests: Update last conversation message with the response and step (continue from current state) the client process.
    client_conversation_with_keys = (
        chat_database_handler.get_conversation_with_keys(
            request.client_process_id
        )
    )
    # TODO: Instead of getting the last one we need to search for the message which function call matches the service_name!
    message_key, message = client_conversation_with_keys[-1]
    if not isinstance(message, ToolResponseMessage):
        raise ValueError("Last message is not a tool response message.")
    message.content = request.response_to_string()
    chat_database_handler.update_message(message_key, message)
    # TODO: Refine this logic, we should have more control over agents that are waiting for a response, split between the current transition and the state.
    client_process_ids = ProcessDatabaseHandler().get_process_ids(
        request.client_process_id
    )
    # Re-activate the client process.
    ProcessHandler(process_ids=client_process_ids).start()


@app.task(name="communication_dispatcher.set_event_completed")
def set_event_completed(primitive_str: str):
    pass
    # TODO: determine if we need to do something here, I guess not as this is used to start processes and event publisher is external.


@app.task(name="communication_dispatcher.update_action_feedback")
def update_action_feedback(primitive_str: str):
    action = Action.from_json(primitive_str)
    # TODO: Do we need to add the action feedback on client prompt?


@app.task(name="communication_dispatcher.update_topic")
def update_topic(primitive_str: str) -> str:
    topic = Topic.from_json(primitive_str)
    topic_subscribers = (
        ProtocolsDatabaseHandler().get_topic_subscribers_from_topic(topic.id)
    )
    for topic_subscriber in topic_subscribers:
        process_ids = ProcessDatabaseHandler().get_process_ids(
            topic_subscriber.process_id
        )
        # TODO: I don't think we should start in case of new topic! Lets determine better the concept of topics in the future.
        #   starting it will break our logic as we don't have any internal logic to set_topic_completed or similar, maybe it might be neccessary, but for now lets assume not.
        # self.process_handler.start(process_ids)
