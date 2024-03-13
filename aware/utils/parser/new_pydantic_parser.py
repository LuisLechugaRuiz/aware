import inspect
from pydantic import create_model
from typing import Any, Dict

from aware.utils.parser.json_pydantic_parser import JsonPydanticParser


class NewPydanticParser:
    @classmethod
    def get_openai_schema(cls, name: str, args: Dict[str, Any], description: str) -> Dict:
        callable = JsonPydanticParser.create_callable(name, args, description)
        params = {
            name: (param.annotation, ...)
            for name, param in inspect.signature(callable).parameters.items()
            if name != "self"  # Skip the 'self' parameter
        }
        model = create_model(f"{callable.__name__}", **params)
        schema = model.model_json_schema()
        schema = cls.clean_schema("title", "description")
        return schema

    @classmethod
    def clean_schema(cls, d: Dict, *args) -> Dict:
        """Recursively remove specified keys from a dictionary."""
        if isinstance(d, dict):
            return {
                k: cls.clean_schema(v, *args) for k, v in d.items() if k not in args
            }
        return d
