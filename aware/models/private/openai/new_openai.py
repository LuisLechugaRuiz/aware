from typing import Any, Dict, List, Optional
import base64
from openai import AsyncOpenAI
from openai._types import NOT_GIVEN
from openai.types.chat import (
    ChatCompletionMessageToolCall,
    ChatCompletionToolParam,
    ChatCompletionMessage,
)
from dotenv import load_dotenv

from aware.config.config import Config
from aware.models.model import Model
from aware.models.private.openai.new_retry_handler import _OpenAIRetryHandler
from aware.utils.logger.file_logger import FileLogger

load_dotenv()


class OpenAIModel(Model):
    def __init__(self, api_key: str, logger: FileLogger):
        self.model_name = Config().openai_model  # TODO: Enable other models.
        self.logger = logger
        self.logger.info(f"OpenAI model: {self.model_name}, api_key: {api_key}")
        self.client = AsyncOpenAI(api_key=api_key)

        _retry_handler = _OpenAIRetryHandler(
            logger=self.logger, num_retries=Config().openai_num_retries
        )

        self._get_response_with_retries = _retry_handler(self._get_response)
        super().__init__()

    def get_name(self) -> str:
        return self.model_name

    async def get_response(
        self,
        messages: Dict[str, Any],
        functions: List[Dict[str, Any]] = [],
        temperature: float = 0.7,
    ) -> ChatCompletionMessage:
        try:
            return await self._get_response_with_retries(
                messages=messages,
                functions=functions,
                response_format="text",
                temperature=temperature,
            )
        # TODO: MANAGE THIS -> NOTIFIY TO USER OR SHUTDOWN SYSTEM TEMPORALLY, IN THE FUTURE CHANGE THE API PROVIDER.
        except Exception as e:
            self.logger.error(
                f"Error getting response from OpenAI: {e} after {Config().openai_num_retries} retries."
            )
            raise e

    # TODO: get temperature from cfg
    async def _get_response(
        self,
        messages: Dict[str, Any],
        functions: List[Dict[str, Any]] = [],
        response_format: str = "text",  # or json_object.
        temperature: float = 0.7,
    ) -> ChatCompletionMessage:
        if functions:
            tools_openai: List[ChatCompletionToolParam] = functions
        else:
            tools_openai = NOT_GIVEN

        # TODO :Check if it is multimodal and use vision.
        try:
            response = await self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                response_format={"type": response_format},
                temperature=temperature,
                tools=tools_openai,
                # stream=False,  # TODO: Address SET TO TRUE for specific cases - USER.
            )
        except Exception as e:
            self.logger.error(f"Error getting response from OpenAI 2: {e}")
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
