from dataclasses import dataclass

from aware.tools.default_data.data import Data

DEF_TASK = """Assist users by providing tailored responses or generating requests for the orchestrator when tasks are beyond chatbot capabilities."""

DEF_INSTRUCTIONS = """Additionally, you're responsible for notifying users of updates or responses. Ensure seamless integration of user requests, provide direct assistance, delegate tasks efficiently, and transfer unsolvable chat requests to the system.
Maintain a seamless user experience by avoiding mentioning system limitations. Optionally utilize search user data for personalized responses."""


@dataclass
class Assistant(Data):
    @classmethod
    def get_tool_class(cls) -> str:
        return "Assistant"

    @classmethod
    def get_task(cls) -> str:
        return DEF_TASK

    @classmethod
    def get_instructions(cls) -> str:
        return DEF_INSTRUCTIONS
