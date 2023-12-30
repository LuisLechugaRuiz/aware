from typing import Any, Dict, List, Optional
import base64
from openai import OpenAI
from openai._types import NOT_GIVEN
from openai.types.chat import (
    ChatCompletionMessageToolCall,
    ChatCompletionToolParam,
    ChatCompletionMessage,
)
from dotenv import load_dotenv

from aware.chat.conversation import Conversation
from aware.models.model import Model

load_dotenv()


class OpenAIModel(Model):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = OpenAI()
        super().__init__()

    def get_name(self) -> str:
        return self.model_name

    # TODO: get temperature from cfg
    def get_response(
        self,
        conversation: Conversation,
        functions: List[Dict[str, Any]] = [],
        response_format: str = "text",  # or json_object.
        temperature: float = 0.7,
    ) -> ChatCompletionMessage:
        if functions:
            tools_openai: List[ChatCompletionToolParam] = functions
        else:
            tools_openai = NOT_GIVEN

        # TODO :Check if it is multimodal and use vision.
        response = self.client.chat.completions.create(
            messages=conversation.messages,
            model=self.model_name,
            response_format={"type": response_format},
            temperature=temperature,
            tools=tools_openai,
            # stream=False,  # TODO: Address SET TO TRUE for specific cases - USER.
        )
        return response.choices[0].message

    def get_multi_modal_message(
        prompt: str,
        urls: Optional[List[str]] = [],
        paths: Optional[List[str]] = [],
        detail: Optional[str] = "low",
    ) -> Dict[str, Any]:
        content = [{"type": "text", "text": prompt}]
        image_urls = []

        # Fill image_urls with remote and local images
        for url in urls:
            image_urls.append(url)
        for path in paths:
            with open(path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            image_urls.append(
                {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": detail,
                }
            )
        # Fill completion_content with image_urls
        for image_url in image_urls:
            content.append(
                {
                    "type": "image_url",
                    "image_url": image_url,
                }
            )
        return content

    # A function to translate OpenAI types into Dict to encapsulate the logic and generalize with OS models.
    def get_tool_calls_dict(
        self, tools: List[ChatCompletionMessageToolCall]
    ) -> List[Dict[str, Any]]:
        tools_info = []
        for tool in tools:
            tools_info.append(
                {
                    "id": tool.id,
                    "arguments": tool.function.arguments,
                    "name": tool.function.name,
                }
            )
        return tools_info
