from datetime import datetime
import json
from openai.types.chat import ChatCompletionMessageToolCallParam
import tiktoken
from typing import Any, List, Dict, Optional, Tuple
import tzlocal
import socket


def colored(st, color: Optional[str], background=False):
    return (
        f"\u001b[{10*background+60*(color.upper() == color)+30+['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'].index(color.lower())}m{st}\u001b[0m"
        if color is not None
        else st
    )


def get_current_date():
    # Automatically detect the local timezone
    local_timezone = tzlocal.get_localzone()

    # Current date and time in user's timezone
    current_time_in_user_tz = datetime.now(local_timezone)

    # Format the datetime in a more readable format, including the timezone name
    return current_time_in_user_tz.strftime("%Y-%m-%d %H:%M:%S %Z%z")


def get_local_ip():
    try:
        # Create a dummy socket to connect to an external server
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Use a public DNS server (Google's) to find the local IP
            # The connection is not actually established
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception as e:
        print(f"Error obtaining local IP: {e}")
        return None


def get_free_port():
    try:
        # Create a dummy socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Bind to an address with port 0
            s.bind(("", 0))
            # Get the assigned port and return it
            return s.getsockname()[1]
    except Exception as e:
        print(f"Error obtaining a free port: {e}")
        return None


def count_message_tokens(
    messages: List[Dict[str, Any]], model_name: str = "gpt-3.5-turbo"
) -> int:
    """
    Returns the number of tokens used by a list of messages.

    Args:
    messages (list): A list of messages, each of which is a dictionary containing the role and content of the message.
    model_name (str): The name of the model used to encode the messages.

    Returns:
    int: The number of tokens used by the list of messages.
    """
    encoding, tokens_per_message, tokens_per_name = get_encoding(model_name)
    num_tokens = 0
    for message in messages:
        num_tokens += get_message_tokens(
            message, encoding, tokens_per_message, tokens_per_name
        )
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def get_encoding(
    model_name: str = "gpt-4",
) -> Tuple[tiktoken.core.Encoding, int, int]:
    if model_name.startswith("gpt-3.5-turbo"):
        tokens_per_message = (
            4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        )
        tokens_per_name = -1  # if there's a name, the role is omitted
        encoding_model = "gpt-3.5-turbo"
    elif model_name.startswith("gpt-4"):
        tokens_per_message = 3
        tokens_per_name = 1
        encoding_model = "gpt-4"
    else:
        raise NotImplementedError(
            f"count_message_tokens() is not implemented for model {model_name}.\n"
            " See https://github.com/openai/openai-python/blob/main/chatml.md for"
            " information on how messages are converted to tokens."
        )
    try:
        encoding = tiktoken.encoding_for_model(encoding_model)
    except KeyError:
        print(f"Model {model_name} not found. Defaulting to cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    return (encoding, tokens_per_message, tokens_per_name)


def get_message_tokens(
    message: Dict[str, Any],
    encoding: tiktoken.core.Encoding,
    tokens_per_message: int = 3,
    tokens_per_name: int = 1,
) -> int:
    if encoding is None:
        encoding = get_encoding()

    num_tokens = tokens_per_message
    for key, value in message.items():
        if key == "tool_calls":
            tool_call_value = ""
            value: List[ChatCompletionMessageToolCallParam]
            for tool in value:
                for item in value:
                    function_dict = {
                        "arguments": tool.function.arguments,
                        "name": tool.function.name,
                    }
                    tool_call_param_dict = {
                        "id": tool.id,
                        "function": function_dict,
                        "type": tool.type,
                    }
                    tool_call_value += json.dumps(tool_call_param_dict)
            value = tool_call_value

        num_tokens += len(encoding.encode(value))
        if key == "name":
            num_tokens += tokens_per_name
    return num_tokens


def count_string_tokens(string: str, model_name: str = "gpt-3.5-turbo") -> int:
    """
    Returns the number of tokens in a text string.

    Args:
    string (str): The text string.
    model_name (str): The name of the encoding to use. (e.g., "gpt-3.5-turbo")

    Returns:
    int: The number of tokens in the text string.
    """
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
