from aware.chat.new_chat import Chat
from aware.config.config import Config

from aware.assistant.assistant_tools import AssistantTools
from aware.agent.memory.new_working_memory import WorkingMemory
from aware.chat.new_conversation_schemas import ChatMessage
from aware.utils.logger.file_logger import FileLogger


class Assistant:
    """Your classical chatbot! But it can send requests to the system"""

    def __init__(self, working_memory: WorkingMemory):
        self.tools = AssistantTools().get_tools()
        self.chat = Chat(
            process_name="assistant",
            user_id=working_memory.user_id,
            chat_id=working_memory.chat_id,
            system_prompt_kwargs={
                "requests": "",  # TODO: Implement get_requests
                "context": working_memory.context,
                "thought": working_memory.thought,
            },
            logger=FileLogger("assistant"),
        )
        self.working_memory = working_memory

    def on_user_message(self, chat_message: ChatMessage):
        """
        Callback function for when a user message is received.

        Args:
            user_name (str): The name of the user which sent the message.
            message (str): The message received.
            message_id (str): The id of the message.
            timestamp (str): The timestamp of the message.

        Returns:
            None
        """
        log = FileLogger("migration_tests", should_print=True)
        log.info("Assistant received message")

        self.chat.add_existing_message(chat_message)
        self.chat.call(self.tools)

    # TODO: Implement me, fetch from database.
    # def get_requests(self):
    #     request_str = "\n".join([str(value) for value in self.requests.values()])
    #     # self.requests = {}  # Resetting requests TODO: Decide when to reset requests.
    #     return request_str

    # TODO: How to manage requests !!
    # def update_request(self, request: Request):
    #     self.requests[request.get_id()] = request
    #     feedback = request.get_feedback()
    #     if request.get_status() == RequestStatus.WAITING_USER_FEEDBACK:
    #         # Ask for feedback
    #         print(
    #             f'{colored("Assistant request:", "red")} {request.request} requires feedback: {feedback}'
    #         )
    #         self.chat.conversation.add_assistant_message(
    #             f"Request: {request.request}\n\nRequires feedback: {feedback}"
    #         )
    #         self.talk(f"Request: {request.request}\n\nrequires feedback: {feedback}")

    #         # Wait for feedback
    #         self.wait_user_message()

    #         # Send feedback
    #         user_context_message = self.user_context_messages.get()
    #         user_message = user_context_message.user_message
    #         self.chat.conversation.add_user_message(
    #             message=user_message.message, user_name=user_message.user_name
    #         )
    #         self.user_context_messages.task_done()
    #         request.update_status(
    #             status=RequestStatus.IN_PROGRESS, feedback=user_message.message
    #         )

    #         # Update request
    #         user_name, goal_handle = self.active_goal_handles[request.get_id()]
    #         goal_handle.action = request
    #         self.system_action_clients[user_name].update_goal(goal_handle)
    #     elif request.get_status() == RequestStatus.SUCCESS:
    #         user_name, goal_handle = self.active_goal_handles[request.get_id()]
    #         message = f"Request with id: {request.get_id()} succeeded with feedback: {request.get_feedback()}"
    #         user_message = UserMessage(
    #             user_name=f"{user_name}_system",
    #             message=message,
    #         )
    #         user_context_message = UserContextMessage(
    #             user_message=user_message, context=self.context, thought=self.thought
    #         )
    #         self.requests.pop(request.get_id())
    #         self.active_goal_handles.pop(request.get_id())
    #         self.user_context_messages.put(user_context_message)
    #         print(colored(f"{user_name}_system: ", "green") + message)
    #     elif request.get_status() == RequestStatus.FAILURE:
    #         user_name, goal_handle = self.active_goal_handles[request.get_id()]
    #         message = f"Request with id: {request.get_id()} failed with feedback: {request.get_feedback()}"
    #         user_message = UserMessage(
    #             user_name=f"{user_name}_system",
    #             message=message,
    #         )
    #         user_context_message = UserContextMessage(
    #             user_message=user_message, context=self.context, thought=self.thought
    #         )
    #         # TODO: POP IT LATER!
    #         self.requests.pop(request.get_id())
    #         self.active_goal_handles.pop(request.get_id())
    #         self.user_context_messages.put(user_context_message)
    #         print(colored(f"{user_name}_system: ", "red") + message)

    #     self.update_system()


# TODO: REMOVE!
def main():
    assistant = Assistant(assistant_ip=Config().assistant_ip)
    assistant.run()


if __name__ == "__main__":
    main()
