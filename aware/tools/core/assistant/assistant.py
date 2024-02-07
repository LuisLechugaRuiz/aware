from aware.assistant.tasks import handle_assistant_message
from aware.chat.conversation_schemas import AssistantMessage
from aware.config.config import Config
from aware.data.database.client_handlers import ClientHandlers
from aware.events.assistant_message import AssistantMessageEvent
from aware.process.process_data import ProcessData
from aware.utils.logger.file_logger import FileLogger
from aware.tools.decorators import default_function
from aware.tools.tools import Tools


class Assistant(Tools):
    def __init__(self, process_data: ProcessData):
        super().__init__(process_data)

    def get_tools(self):
        return [
            self.talk,
            self.send_request,
            self.search_info,
        ]

    def send_request(self, request: str):
        """
        Send a request to the orchestrator, should be very explicit.

        Args:
            request (str): The request the system needs to solve.

        Returns:
            None
        """
        self.create_async_request("orchestrate", request)
        return "Request sent to the system; the status will be updated soon."

    @default_function
    def talk(self, message: str):
        """
        Use this tool as the only way to communicate with the user.

        Args:
            message (str): The message to be sent.

        Returns:
            str
        """
        logger = FileLogger("migration_tests")
        assistant_message = AssistantMessage(
            name=Config().assistant_name, content=message
        )
        logger.info(f"Sending message to user: {assistant_message.to_string()}")
        ClientHandlers().get_supabase_handler().send_message_to_user(
            user_id=self.process_data.ids.user_id,
            process_id=self.process_data.ids.process_id,
            message_type=assistant_message.__class__.__name__,
            role=assistant_message.role,
            name=assistant_message.name,
            content=assistant_message.content,
        )
        assistant_message_event = AssistantMessageEvent(
            process_ids=self.process_data.ids,
            assistant_name=assistant_message.name,
            message=message,
        )
        handle_assistant_message.delay(assistant_message_event.to_json())

        self.stop_agent()
        return "Message sent to the user."

    def search_info(self, query: str):
        """
        Search the query on semantic database.

        Args:
            query (str): The search query.

        Returns:
            str
        """
        return self.create_request("search", query)
