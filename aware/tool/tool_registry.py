from typing import Dict, List, Optional
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam


from aware.chat.parser.pydantic_parser import PydanticParser
from aware.tool.tool import Tool


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def get_openai_tools(self) -> List[ChatCompletionToolParam]:
        return [
            PydanticParser.get_openai_tool(tool.callback)
            for tool in self.tools.values()
        ]

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name, None)

    def get_tools(self) -> List[Tool]:
        return self.tools.values()

    def register_tools(self, tools: List[Tool]):
        for tool in tools:
            self.tools[tool.name] = tool
