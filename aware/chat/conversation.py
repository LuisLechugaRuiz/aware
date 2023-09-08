# from transformers import Conversation as HuggingfaceConversation -> Can't use HuggingfaceConversation as it doesn't accept tool_call_id as part of the message. https://github.com/huggingface/transformers/blob/main/src/transformers/pipelines/conversational.py#L83
from typing import Dict, List, Optional
from openai.types.chat import ChatCompletionMessageToolCallParam

from aware.data.data_saver import DataSaver


class Conversation:
    """ "Wrapper over huggingface conversation to add some functionalities."""

    def __init__(self, module_name: str, system_message: str):
        # Add RAG | Ensure we don't surpass max tokens | Save on RAG | Retrieve from RAG.
        super().__init__()
        self.system_message = system_message
        self.messages = [{"role": "system", "content": system_message}]

        # self.data_saver = DataSaver(module_name) -> TODO: Enable when addressing the tools.
        # self.data_saver.start_new_conversation(system_message)

        # In case conversation is too long we should move info to RAG and call restart. (Create intelligent algorithm for this).

    def add_assistant_message(self, message: str):
        self._add_message({"role": "assistant", "content": message})

    def add_assistant_tool_message(
        self, tool_calls: List[ChatCompletionMessageToolCallParam]
    ):
        self._add_message(
            {
                "role": "assistant",
                "tool_calls": tool_calls,
            }
        )

    def add_user_message(self, message: str, user_name: Optional[str] = None):
        if user_name:
            self._add_message({"role": "user", "content": message, "name": user_name})
        else:
            self._add_message({"role": "user", "content": message})

    def add_tool_message(self, id: str, message: str):
        self._add_message(
            {
                "role": "tool",
                "content": message,
                "tool_call_id": id,
            }
        )

    def _add_message(self, message: Dict[str, str]):
        self.messages.append(message)
        # self.data_saver.add_message(message)

    def edit_system_message(self, message: str):
        self.messages[0]["content"] = message
        self.system_message = message
        # self.data_saver.edit_system_message(message)

    def restart(self):
        # Move to RAG and clear all messages unless system.
        # Find system message
        self.messages = [self.system_message]
        # self.data_saver.start_new_conversation(self.system_message)
