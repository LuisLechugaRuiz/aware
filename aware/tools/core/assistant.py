from typing import Optional

from aware.agent.agent_data import AgentData
from aware.assistant.tasks import handle_assistant_message
from aware.chat.conversation_schemas import AssistantMessage
from aware.config.config import Config
from aware.data.database.client_handlers import ClientHandlers
from aware.events.assistant_message import AssistantMessageEvent
from aware.process.process_ids import ProcessIds
from aware.requests.request import Request
from aware.utils.logger.file_logger import FileLogger
from aware.tools.decorators import default_function
from aware.tools.tools import Tools

DEF_IDENTITY = """You are {{ name }}, an advanced virtual assistant within a comprehensive AI system."""
DEF_TASK = """Your task is to assist users by providing tailored responses or generating requests for the orchestrator,
which oversees a multi-agent system. Additionally, you're responsible for notifying users of updates or responses.
Ensure seamless integration of user requests, provide direct assistance, delegate tasks efficiently, and transfer unsolvable chat requests to the system.
Maintain a seamless user experience by avoiding mentioning system limitations. Optionally utilize search user data for personalized responses."""


class Assistant(Tools):
    def __init__(
        self,
        client_handlers: "ClientHandlers",
        process_ids: ProcessIds,
        agent_data: AgentData,
        request: Optional[Request],
        run_remote: bool = False,
    ):
        super().__init__(
            client_handlers=client_handlers,
            process_ids=process_ids,
            agent_data=agent_data,
            request=request,
            run_remote=run_remote,
        )
        self.logger = FileLogger("assistant")

    @classmethod
    def get_identity(cls, assistant_name: str) -> str:
        return DEF_IDENTITY.format(name=assistant_name)

    @classmethod
    def get_task(cls) -> str:
        return DEF_TASK.format()

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
