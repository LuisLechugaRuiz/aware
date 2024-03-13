import typing
from typing import Callable, Dict

from aware.utils.parser.pydantic_parser import PydanticParser
from aware.tool.tool import Tool


class DynamicFunctionHolder:
    def __init__(self, name, args, description):
        function_str = self.create_function(name, args, description)
        self.add_function(function_str, args)

    def add_function(self, function_str, args):
        exec_globals = globals().copy()  # Copy current globals

        # Dynamically import types from 'typing' module used in 'args'
        for arg_type in set(args.values()):  # Use set to avoid duplicates
            if "[" in arg_type:  # Check for generic types like 'List[str]'
                base_type = arg_type.split("[", 1)[0]  # Extract 'List' from 'List[str]'
                if hasattr(typing, base_type):
                    exec_globals[base_type] = getattr(typing, base_type)
            else:
                if hasattr(typing, arg_type):
                    exec_globals[arg_type] = getattr(typing, arg_type)

        local_namespace = {}
        exec(function_str, exec_globals, local_namespace)

        for name, value in local_namespace.items():
            if callable(value):
                setattr(self, name, value)

    def create_function(self, name: str, args: Dict[str, str], description: str):
        function_str = f"def {name}(self"
        for arg_name, arg_type in args.items():
            function_str += f", {arg_name}: {arg_type}"
        function_str += f'):\n    """\n    {description}\n    """\n'
        function_str += "    pass\n"
        return function_str


class JsonPydanticParser:
    @staticmethod
    def create_callable(name, args, description) -> Callable:
        # Retrieve the dynamically added function using its name
        dynamic_holder = DynamicFunctionHolder(name, args, description)

        return getattr(dynamic_holder, name)

    @staticmethod
    def get_tool(name: str, args: Dict[str, str], description: str, callback: Callable) -> Tool:
        callable = JsonPydanticParser.create_callable(name, args, description)
        return PydanticParser.get_tool(callable=callable, callback=callback)


def main():
    args = {
        "agent_name": "str",
        "state_name": "str",
        "task": "str",
        "instructions": "str",
        "tools": "List[str]",
    }
    print(
        JsonPydanticParser.get_tool(
            "example_function", args, "This is an example function"
        ).params
    )


if __name__ == "__main__":
    main()
