from aware.chat.conversation_schemas import AssistantMessage
from aware.chat.database.chat_database_handler import ChatDatabaseHandler
from aware.process.process_info import ProcessInfo
from aware.tool.decorators import default_function, tool
from aware.tool.capability.capability import Capability


class Assistant(Capability):
    def __init__(
        self,
        process_info: ProcessInfo,
    ):
        super().__init__(process_info=process_info)
        self.chat_database_handler = ChatDatabaseHandler()

    @default_function
    @tool
    def talk(self, message: str, should_stop: bool = False):
        """
        Use this tool as the only way to communicate with the user.

        Args:
            message (str): The message to be sent.
            should_stop (bool, optional): If the process should stop after sending the message. Defaults to False.

        Returns:
            str
        """
        assistant_message = AssistantMessage(name=self.agent_data.name, content=message)
        self.logger.info(f"Sending message to user: {assistant_message.to_string()}")
        self.chat_database_handler.send_message_to_user(
            user_id=self.process_ids.user_id,
            process_id=self.process_ids.process_id,
            message_type=assistant_message.__class__.__name__,
            role=assistant_message.role,
            name=assistant_message.name,
            content=assistant_message.content,
        )
        if should_stop:
            # TODO: how to set input completed from tool?
            #  IN THE PAST: self.finish_process() but now we only finish by completing the event
        return "Message sent to the user."

    @tool
    def search_info(self, query: str):
        """
        Search the query on semantic database.

        Args:
            query (str): The search query.

        Returns:
            str
        """
        # Dummy function to direct the thought_generator's search.
        return f"Searching for: {query}. Check the thought."
