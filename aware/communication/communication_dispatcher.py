# TODO: This class will receive certain "events" from communication handler and manage the reaction at system level. i.e: Activating other processes or adding info to their conversations.
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
from aware.utils.logger.process_loger import ProcessLogger


class CommunicationDispatcher:
    def __init__(self, process_logger: ProcessLogger):
        self.chat_database_handler = ChatDatabaseHandler()
        self.process_database_handler = ProcessDatabaseHandler()
        self.process_handler = ProcessHandler(process_logger=process_logger)
        self.logger = process_logger.get_logger("communication_dispatcher")

    def create_request(self, request: Request) -> Request:
        service_process_ids = self.process_database_handler.get_process_ids(
            process_id=request.service_process_id
        )
        self.process_handler.start(service_process_ids)

    def create_event(self, event: Event) -> Event:
        event_subscribers = ProtocolsDatabaseHandler().get_event_subscribers_from_type(
            event.event_type_id
        )
        for event_subscriber in event_subscribers:
            process_ids = self.process_database_handler.get_process_ids(
                event_subscriber.process_id
            )
            self.logger.info(
                f"Triggering process: {event_subscriber.process_id} with event: {event.to_json()}"
            )
            self.process_handler.start(process_ids)

    def update_topic(
        self,
        topic_str: str,
    ) -> str:
        topic = Topic.from_json(topic_str)
        topic_subscribers = ProtocolsDatabaseHandler().get_topic_subscribers_from_topic(
            topic.id
        )
        for topic_subscriber in topic_subscribers:
            process_ids = self.process_database_handler.get_process_ids(
                topic_subscriber.process_id
            )
            self.logger.info(
                f"Triggering process: {topic_subscriber.process_id} with topic: {topic.to_json()}"
            )
            self.process_handler.start(process_ids)

    # @app.task...
    def set_action_completed(self, action_str: str):
        action = Action.from_json(action_str)
        client_process_ids = self.process_database_handler.get_process_ids(
            action.client_process_id
        )
        # - Add new message with the response and start the client process.
        self.process_handler.add_message(
            process_ids=client_process_ids,
            json_message=UserMessage(
                name=action.service_name, content=action.response_to_string()
            ),  # TODO: is name = action.service_name correct or should it be the service_process_name?
        )
        # TODO: Step or start? remember actions run async.
        self.process_handler.start(process_ids=client_process_ids)

    # @app.task...
    def set_request_completed(self, request_str: str):
        # Add message to client process.
        request = Request.from_json(request_str)
        # - Sync requests: Update last conversation message with the response and step (continue from current state) the client process.
        client_conversation_with_keys = (
            self.chat_database_handler.get_conversation_with_keys(
                request.client_process_id
            )
        )
        message_key, message = client_conversation_with_keys[-1]
        if not isinstance(message, ToolResponseMessage):
            raise ValueError("Last message is not a tool response message.")
        message.content = request.response_to_string()
        self.chat_database_handler.update_message(message_key, message)
        # TODO: Refine this logic, we should have more control over agents that are waiting for a response, split between the current transition and the state.
        client_process_ids = self.process_database_handler.get_process_ids(
            request.client_process_id
        )
        # Re-activate the client process.
        self.process_handler.start(process_ids=client_process_ids)

    # TODO: Implement this to manage events state.
    # def set_event_completed(self, event: Event):
    #     pass

    def update_action_feedback(self, action_str: str):
        action = Action.from_json(action_str)
