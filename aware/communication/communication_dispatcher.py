# TODO: This class will receive certain "events" from communication handler and manage the reaction at system level. i.e: Activating other processes or adding info to their conversations.
from aware.communication.primitives.action import Action
from aware.communication.primitives.request import Request
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
        pass

    def create_event(self, event: Event) -> Event:
        pass

    def update_topic(
        self,
        topic_publisher: TopicPublisher,
        message: Dict[str, Any],
        function_call_id: str,
    ) -> str:
        pass

    # @app.task...
    def set_action_completed(self, action_str: str):
        action = Action.from_json(action_str)
        # - Add new message with the response and start the client process.
        self.process_handler.add_message(
            process_ids=client_process_ids,
            json_message=UserMessage(
                name=action.service_name, content=action.response_to_string()
            ),  # TODO: is name = action.service_name correct or should it be the service_process_name?
        )
        client_process_ids = self.process_database_handler.get_process_ids(
            action.client_process_id
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

    def update_request_feedback(self, request: Request, feedback: str):
        pass
