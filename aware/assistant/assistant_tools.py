from aware.agent.tools import Tools
from aware.agent.decorators import default_function
from aware.chat.new_conversation_schemas import AssistantMessage
from aware.config.config import Config
from aware.data.database.client_handlers import ClientHandlers
from aware.utils.logger.file_logger import FileLogger


class AssistantTools(Tools):
    def __init__(self, user_id: str, chat_id: str):
        super().__init__(user_id, chat_id)

    def get_tools(self):
        return [
            self.talk,
            self.send_request,
            self.search_user_info,
        ]

    def send_request(self, user_name: str, request: str):
        """
        Send a request to the system, make a very explicit request.

        Args:
            user_name (str): The name of the user which is running the system.
            request (str): The request the system needs to solve.

        Returns:
            None
        """
        pass
        # new_request = Request(request=request)
        # goal_handle = self.system_action_clients[user_name].send_goal(new_request)
        # self.active_goal_handles[new_request.get_id()] = (user_name, goal_handle)
        # self.update_request(new_request)
        # print(colored(f"Request: {request}", "yellow"))
        # return "Request sent to the system; the status will be updated soon."

    # NOT USED FOR NOW TO HAVE A GROUP COMMUNICATION - FOR NOW JUST BROADCASTING
    # def send_message_to_user(self, user_name: str, message: str):
    #     self.users[user_name].send_message(message)

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
            chat_id=self.chat_id,
            user_id=self.user_id,
            process_name="assistant",
            message_type=assistant_message.__class__.__name__,
            role=assistant_message.role,
            name=assistant_message.name,
            content=assistant_message.content,
        )
        self.stop_agent()
        return "Message sent to the user."

    def search_user_info(self, user_name: str, query: str):
        """
        Search the query on user's semantic database.

        Args:
            user_name (str): The user name to be searched.
            query (str): The search query.

        Returns:
            str
        """
        pass
        # try:
        #     print(f"Searching for {query} on {user_name}'s database")
        #     data = self.database_clients[user_name].send(
        #         topic=f"{user_name}_{DEF_GET_THOUGHT}", message=query
        #     )
        #     return f"Search returned: {data}"
        # except Exception as e:
        #     return f"Error searching: {e}"
