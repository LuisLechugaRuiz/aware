from abc import ABC, abstractmethod
from typing import Any, Dict
from openai.types.chat import ChatCompletionMessage

from aware.agent.tools import Tools
from aware.chat.new_chat import Chat
from aware.tools.tools_manager import ToolsManager
from aware.utils.logger.file_logger import FileLogger


class Process(ABC):
    user_id: str
    chat_id: str
    tools: Tools
    process_name: str
    system_prompt_kwargs: Dict[str, Any]
    logger: FileLogger
    chat: Chat

    def __init__(self, user_id: str, chat_id: str, tools: Tools):
        self.user_id = user_id
        self.chat_id = chat_id
        self.tools = tools.get_tools()

    @classmethod
    def create(cls, user_id, chat_id, *args, **kwargs):
        # Create an instance of the derived class
        instance = cls(user_id, chat_id, *args, **kwargs)
        # Derive process_name from the class name
        instance.process_name = instance.get_process_name()
        instance.system_prompt_kwargs = instance.get_system_prompt_kwargs()
        instance.logger = instance.get_logger()
        instance.chat = Chat(
            process_name=instance.process_name,
            user_id=instance.user_id,
            chat_id=instance.chat_id,
            system_prompt_kwargs=instance.system_prompt_kwargs,
            logger=instance.logger,
        )
        print("DEBUG - User ID: ", instance.user_id)
        print("DEBUG - Chat ID: ", instance.chat_id)
        print("DEBUG - Process name: ", instance.process_name)
        print("DEBUG - System prompt kwargs: ", instance.system_prompt_kwargs)
        return instance

    @abstractmethod
    def get_system_prompt_kwargs(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_process_name(self) -> str:
        pass

    @classmethod
    def get_logger(cls) -> FileLogger:
        return FileLogger(cls.get_process_name())

    def request_response(self):
        self.chat.call(self.tools)
        print("DEBUG - Calling tools: ", self.tools)

    # TODO: Clarify what to do with response, do we get the response or we already process it before?
    # In this case it looks better to have a function for tool execution.
    # TODO: Maybe this should be a classmethod? It doesn't need info about user, so we can just call it directly.
    @classmethod
    def process_response(cls, response: ChatCompletionMessage):
        tools_manager = ToolsManager(cls.get_logger())
        tool_calls = response.tool_calls
        if tool_calls is not None:
            tools_manager.get_function_signatures(response.tool_calls)
        else:
            content = response.content
            # TODO: Implement a decorator to mark as default tool calls?
            # if self.default_tool_calls is None:
            #     # TODO: add to conversation - FIX with new format.
            #     tool_calls = self.default_tool_calls(content)
            #     self.chat.conversation.add_assistant_message(
            #         tool_calls, assistant_name=self.chat.assistant_name
            #     )
            #     self.running = False  # TODO: Set to stop so is not executed again. (just not request response?)
            #     self.execute_tools(tool_calls)
            # else:
            # self.chat.conversation.add_assistant_message(
            #     content, assistant_name=self.chat.assistant_name
            # )
            # self.running = False  # TODO: Set to stop so is not executed again. (just not request response?)
        # TODO: Call trim conversation

    def stop_agent(self):
        self.chat.stop_chat()


# Usage example
assistant = Assistant.create(
    user_id="123", chat_id="456", context="debug_context", thought="debug_thought"
)
assistant.on_user_message("debug_message")


# POST PROCESS:
# 1. Get the model response.
# 2. Check if it is a string or a tool_calls.
# TODO: Move to tools manager!


# 1. Save to messages (should happen in the outter?) - chat should always work over existing messages!


def execute_tools():
    self.tools_manager.execute_tools(
        tool_calls=tool_calls,
        functions=self.functions,
        chat=self.chat,
    )


# REFACTOR ON TOOL MANAGER -> IT SHOULD HAVE A SUPABASE CLIENT TO SCHEDULE TOOLS.
# ADD ANOTHER SUPABASE SUBSCRIPTION ON MESSAGE_LISTENER TO GET THE TOOLS FEEDBACK FROM CLIENTS, SAVE THEM AND SCHEDULE NEW TASK.
# THIS SHOULD BE INTEGRATED ALONG THE LOGIC TO ROUTE THE RESPONSES.
