import json
from typing import Any, Callable, cast, Dict, Generic, List, Optional, TypeVar, Type
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai.types.shared_params.function_definition import FunctionDefinition
from pydantic import create_model, BaseModel
import inspect
from logging import getLogger
import re

from aware.utils.parser.loggable_base_model import LoggableBaseModel
from aware.utils.parser.fix_format_prompt import (
    DEF_FIX_FORMAT_PROMPT,
)
from aware.models.model import Model
from aware.tool.decorators import RUN_REMOTE
from aware.tool.tool import Tool


T = TypeVar("T", bound=LoggableBaseModel)

# TODO: Create our own logger.
LOG = getLogger(__name__)


class ParseResult(Generic[T]):
    def __init__(
        self,
        result: Optional[T] = None,
        error_message: Optional[str] = None,
    ):
        self.result = result
        self.error_message = error_message


# TODO: Adapt and remove boiler plate -> Now we always use functions, no need for raw JSON anymore.
class PydanticParser(Generic[T]):
    def __init__(self, model: Model):
        self.model = model

    def parse_response(
        self,
        conversation: str,
        response: str,
        containers: List[Type[T]],
        retries=2,
        fix_retries=3,
    ) -> List[Type[T]]:
        output = []
        for container in containers:
            success = False
            for _ in range(retries):
                parsed_response = self._get_object(
                    response, container, fix_retries=fix_retries
                )
                if parsed_response.result:
                    LOG.info(str(parsed_response.result))
                    parsed_response = cast(container, parsed_response.result)
                    output.append(parsed_response)
                    success = True
                    break
                else:
                    LOG.error("Couldn't parse/fix response, getting new response.")
                    response = self.model.get_response(
                        conversation, response_format="json_object"
                    )
            if not success:
                LOG.critical(
                    f"Failed to get a valid response after {retries} retries and {fix_retries} fix retries. Returning None..."
                )
                output.append(None)
        return output

    def _get_object(
        self, response: str, pydantic_object: Type[T], fix_retries=3
    ) -> ParseResult[T]:
        parsed_response = self.parse(response, pydantic_object)
        if parsed_response.result:
            return parsed_response
        else:
            error_msg = parsed_response.error_message
            print(
                f"Failing parsing object: {pydantic_object.__name__}, trying to fix autonomously..."
            )
            print("Response:", response)
            # Just return, don't try to fix format YET!
            return ParseResult(error_message=error_msg)
        while fix_retries > 0:
            response_fix = self.try_to_fix_format(
                self.model, response, error_msg, pydantic_object
            )
            if response_fix.result:
                LOG.info("Response format was fixed.")
                return response_fix
            fix_retries -= 1
            LOG.error(
                f"Couldn't fix format... remaining attempts to fix: {fix_retries}"
            )
        return ParseResult(error_message=error_msg)

    @classmethod
    def parse(cls, text: str, pydantic_object: Type[BaseModel]):
        """Search for the first valid JSON object in the text and parse it into a pydantic object."""

        def preprocess(text: str) -> str:
            text = text.replace("True", "true").replace("False", "false")
            return text

        text = preprocess(text)
        pattern = rf'"{pydantic_object.__name__}"\s*:\s*'
        match = re.search(pattern, text)

        if not match:
            raise ValueError(f"{pydantic_object.__name__} not found in text")

        start = text.find("{", match.start())
        if start == -1:
            raise ValueError(
                f"JSON object start not found after {pydantic_object.__name__}"
            )

        decoder = json.JSONDecoder()

        while start < len(text):
            try:
                json_obj, index = decoder.raw_decode(text, start)
                # Ensure json_obj is a dictionary
                # if isinstance(json_obj, dict):
                # Check if the JSON object has the required keys
                if all(key in json_obj for key in pydantic_object.model_fields):
                    # Parse the JSON object and return the pydantic_object
                    result = pydantic_object.model_validate(json_obj)
                    return ParseResult(result=cast(T, result))
                start += index
            except json.JSONDecodeError:
                start += 1
            except Exception as e:
                print(f"Failing parsing with error: {e}")
                break

        name = pydantic_object.__name__
        msg = f"Failed to parse {name} from completion {text}."
        return ParseResult(error_message=msg)

    # TODO: TBD how to fix it and use properly with OS models - TODO: Fix this function to ask for the FULL JSON SCHEMA.
    def try_to_fix_format(
        self, response: str, error_msg: str, pydantic_object: Type[T]
    ) -> ParseResult[T]:
        schema = self.get_json_schema([pydantic_object])
        fix_prompt = DEF_FIX_FORMAT_PROMPT.format(
            response=response,
            schema=schema,
            error_msg=error_msg,
        )
        fix_response = self.model.get_response(
            system=fix_prompt,
        )
        result = self.parse(fix_response, pydantic_object)
        return result

    @classmethod
    def clean_schema(cls, d: Dict, *args) -> Dict:
        """Recursively remove specified keys from a dictionary."""
        if isinstance(d, dict):
            return {
                k: cls.clean_schema(v, *args) for k, v in d.items() if k not in args
            }
        return d

    @classmethod
    def get_json_schema(cls, objects: List[Type[BaseModel]]) -> str:
        """Get the JSON schema for a list of pydantic objects."""

        combined_schema = {}
        for obj in objects:
            combined_schema[obj.__name__] = obj.model_json_schema()
        # Ensure json in context is well-formed with double quotes.
        json_schema = json.dumps(combined_schema)

        return json_schema

    @classmethod
    def _get_json_schema(cls, object: Type[BaseModel]) -> str:
        """Get the JSON schema for a pydantic object and remove the title and description fields."""

        schema = object.model_json_schema()
        schema = cls.clean_schema(schema, "title", "description")
        # json_schema = json.dumps(schema)
        return schema

    # TODO: DEPRECATE IN FAVOR OF get_openai_tool
    @classmethod
    def get_function_schema(cls, fn: Callable) -> ChatCompletionToolParam:
        """Turn a function signature into a JSON schema.

        Every JSON object valid to the output JSON Schema can be passed
        to `fn` using the ** unpacking syntax.

        """

        params = {
            name: (param.annotation, ...)
            for name, param in inspect.signature(fn).parameters.items()
            if name != "self"  # Skip the 'self' parameter
        }

        model = create_model(f"{fn.__name__}Model", **params)
        schema = cls._get_json_schema(model)

        docstring = inspect.getdoc(fn) or "No docstring provided"
        function_definition = FunctionDefinition(
            name=fn.__name__, description=docstring, parameters=schema
        )
        chat_completion_param = ChatCompletionToolParam(
            type="function", function=function_definition
        )
        return chat_completion_param

    @classmethod
    def get_openai_tool(cls, fn: Callable) -> ChatCompletionToolParam:
        """Turn a function signature into a OpenAI ChatCompletionToolParam."""

        params = {
            name: (param.annotation, ...)
            for name, param in inspect.signature(fn).parameters.items()
            if name != "self"  # Skip the 'self' parameter
        }

        model = create_model(f"{fn.__name__}Model", **params)
        schema = cls._get_json_schema(model)

        docstring = inspect.getdoc(fn) or "No docstring provided"
        # As specified by -> from openai.types.shared_params.function_definition
        function_definition = FunctionDefinition(
            name=fn.__name__, description=docstring, parameters=schema
        )
        chat_completion_param = ChatCompletionToolParam(
            type="function", function=function_definition
        )
        return chat_completion_param

    @classmethod
    def get_tool(cls, callable: Callable, callback: Optional[Callable] = None) -> Tool:
        params = {
            name: (param.annotation, param.default is not inspect.Parameter.empty)
            for name, param in inspect.signature(callable).parameters.items()
            if name != "self"  # Skip the 'self' parameter
        }
        docstring = inspect.getdoc(callable) or "No docstring provided"

        if callback is None:
            callback = callable

        # Create and add the Tool object to the tools list
        return Tool(
            name=callable.__name__,
            params=params,
            description=docstring,
            callback=callback,
            run_remote=getattr(callback, RUN_REMOTE, False),
        )
