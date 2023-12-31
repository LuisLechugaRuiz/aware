import json
from typing import Dict, List, Optional
from openai.types.chat import ChatCompletionMessageToolCallParam

from aware.config.config import Config
from aware.data.data_saver import DataSaver
from aware.utils.helpers import count_message_tokens


class Conversation:
    """Conversation class to keep track of the messages and the current state of the conversation."""

    def __init__(self, module_name: str, model_name: str, should_trim: bool = True):
        # Add RAG | Ensure we don't surpass max tokens | Save on RAG | Retrieve from RAG.
        super().__init__()
        self.model_name = model_name

        self.system_message = None
        self.messages = []
        self.should_trim = should_trim

        # self.data_saver = DataSaver(module_name) -> TODO: Enable when addressing the tools.

    def add_assistant_message(
        self,
        message: str,
        assistant_name: Optional[str] = None,
    ):
        if assistant_name:
            self._add_message(
                {
                    "role": "assistant",
                    "name": assistant_name,
                    "content": message,
                }
            )
        else:
            self._add_message({"role": "assistant", "content": message})

    def add_assistant_tool_message(
        self,
        tool_calls: List[ChatCompletionMessageToolCallParam],
        assistant_name: Optional[str] = None,
    ):
        if assistant_name:
            self._add_message(
                {
                    "role": "assistant",
                    "name": assistant_name,
                    "tool_calls": tool_calls,
                }
            )
        else:
            self._add_message({"role": "assistant", "tool_calls": tool_calls})

    def add_system_message(self, message: str):
        self._add_message({"role": "system", "content": message})
        self.system_message = message
        # self.data_saver.start_new_conversation(system_message)

    def add_tool_message(self, id: str, message: str):
        self._add_message(
            {
                "role": "tool",
                "content": message,
                "tool_call_id": id,
            }
        )

    def add_user_message(self, message: str, user_name: Optional[str] = None):
        if len(self.messages) < 1:
            raise Exception("System message not found!!!")

        if user_name:
            self._add_message({"role": "user", "name": user_name, "content": message})
        else:
            self._add_message({"role": "user", "content": message})

    # TODO: We can store removed messages on a conversation copy and "reflect" at the end, detecting if we need to save important information.
    def _add_message(self, message: Dict[str, str]):
        # Check if we need to trim the conversation.
        if self.should_trim:
            current_message_tokens = self.get_current_tokens()
            new_message_tokens = count_message_tokens(
                self.get_message_string(message), self.model_name
            )
            while (
                current_message_tokens + new_message_tokens
            ) > Config().max_conversation_tokens:
                # Trim the oldest user message, leaving the system message (first message) intact.
                if len(self.messages) > 1:
                    # Check if the next message is a 'tool' message and the current one is 'assistant' with 'tool_calls'.
                    if (
                        len(self.messages) > 2
                        and self.messages[1].get("role") == "assistant"
                        and "tool_calls" in self.messages[1]
                    ):
                        # Remove 'assistant' message with 'tool_calls'.
                        removed_message = self.messages.pop(
                            1
                        )  # Remove 'assistant' message
                        current_message_tokens -= count_message_tokens(
                            self.get_message_string(removed_message), self.model_name
                        )
                        # Continue removing messages with the role 'tool'.
                        while (
                            len(self.messages) > 1
                            and self.messages[1].get("role") == "tool"
                        ):
                            removed_tool_message = self.messages.pop(1)
                            current_message_tokens -= count_message_tokens(
                                self.get_message_string(removed_tool_message),
                                self.model_name,
                            )
                    else:
                        # Remove the oldest message if the above condition is not met.
                        removed_message = self.messages.pop(1)
                        current_message_tokens -= count_message_tokens(
                            self.get_message_string(removed_message), self.model_name
                        )
                else:
                    # Break the loop if only the system message is left to prevent its removal.
                    raise Exception(
                        "Only system message left!!! Threshold is too small...."
                    )

        # Add the new message.
        self.messages.append(message)
        # self.data_saver.add_message(message)

    def get_current_tokens(self):
        return count_message_tokens(
            messages=self.to_string(), model_name=self.model_name
        )

    def to_string(self, get_system_message: bool = True):
        conversation_string = ""
        # print("DEBUG MESSAGES LENGTH: ", len(self.messages))
        # if not get_system_message:
        #     for message in self.messages[1:]:
        #         conversation_string += self.get_message_string(message) + "\n"
        #         return conversation_string

        for message in self.messages:
            conversation_string += self.get_message_string(message) + "\n"
        return conversation_string

    # TODO: Check if this exactly the format that OpenAI uses internally.
    def get_message_string(self, message):
        if message["role"] == "assistant" and "tool_calls" in message:
            tool_call_str = ""
            for tool_call in message["tool_calls"]:
                tool_call: ChatCompletionMessageToolCallParam
                function_dict = {
                    "arguments": tool_call.function.arguments,
                    "name": tool_call.function.name,
                }
                tool_call_param_dict = {
                    "id": tool_call.id,
                    "function": function_dict,
                    "type": tool_call.type,
                }
                tool_call_str += json.dumps(tool_call_param_dict)
            return f"assistant: {tool_call_str}"
        else:
            role = message["role"]
            content = message.get("content", "")
            tool_call_id = message.get("tool_call_id", "")
            user_name = message.get("name", "")
            if tool_call_id:
                return f"{role} (ID: {tool_call_id}): {content}"
            elif user_name:
                return f"{role} ({user_name}): {content}"
            else:
                return f"{role}: {content}"

    def edit_system_message(self, message: str):
        if not self.system_message:
            self.add_system_message(message)
        else:
            self.messages[0]["content"] = message
            self.system_message = message
        # self.data_saver.edit_system_message(message)

    def get_remaining_tokens(self):
        return Config().max_conversation_tokens - self.get_current_tokens()

    def should_trigger_warning(self):
        warning_tokens = (
            Config().max_conversation_tokens * Config().conversation_warning_threshold
        )
        return self.get_current_tokens() >= int(warning_tokens)

    def restart(self):
        # Move to RAG and clear all messages unless system.
        # Find system message
        self.messages = []
        self.add_system_message(self.system_message)
        # self.data_saver.start_new_conversation(self.system_message)
