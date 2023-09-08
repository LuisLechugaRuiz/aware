from typing import Any, Callable, Dict, List, Optional
from logging import getLogger
from openai.types.chat import (
    ChatCompletionMessageToolCall,
)

from aware.chat.conversation import Conversation
from aware.chat.parser.pydantic_parser import PydanticParser
from aware.prompts.load import load_prompt
from aware.models.models_manager import ModelsManager
from aware.data.database.manager import DatabaseManager

# TODO: Create our own logger.
LOG = getLogger(__name__)


class Chat:
    """Main class to communicate with the models and update the conversation."""

    def __init__(
        self,
        module_name: str,
        system_prompt_kwargs: Dict[str, Any] = {},
        user_name: Optional[str] = None,
        memory_enabled: bool = True,
        register_database: bool = True,
    ):
        self.user_name = user_name
        self.model = None
        self.module_name = module_name
        self.memory_enabled = memory_enabled
        self.short_term_memory = "Empty, use update_short_term_memory to save relevant context and avoid loosing information."  # TODO: Get from permanent storage
        self.retrieved_data = "Empty"  # TODO: Get from permanent storage

        self.system_instruction_message = self.load_prompt(
            "system", self.module_name, system_prompt_kwargs
        )
        system_message = self.update_system()

        if user_name is not None:
            user = user_name
        else:
            user = module_name

        self.database = DatabaseManager(
            name=user,
            register=register_database,
        )
        self.conversation = Conversation(module_name, system_message)
        if memory_enabled:
            self.functions = [
                self.update_short_term_memory,
                self.store_on_long_term_memory,
                self.search_on_long_term_memory,
            ]
        else:
            self.functions = []

    def add_tool_feedback(self, id: str, message: str):
        self.conversation.add_tool_message(id=id, message=message)

    def call(
        self,
        functions: List[Callable] = [],
        add_default_functions=True,
        save_assistant_message=True,
    ):
        """Call the model to get a response."""

        if self.model is None:
            self.load_model()

        function_schemas = []
        if add_default_functions:
            functions.extend(self.functions)
        for function in functions:
            function_schemas.append(PydanticParser.get_function_schema(function))
        response = self.model.get_response(
            conversation=self.conversation,
            functions=function_schemas,
        )
        if function_schemas:
            tool_calls = response.tool_calls
            if tool_calls is not None:
                # In case we are sending tools we should save them in the traces as OpenAI doesn't include them on prompt.
                if save_assistant_message:
                    self.conversation.add_assistant_tool_message(tool_calls)
                return tool_calls

        response = response.content
        if save_assistant_message:
            self.conversation.add_assistant_message(response)
        return response

    def edit_system_message(self, system_prompt_kwargs: Dict[str, Any]):
        """Edit the system message."""
        self.system_instruction_message = self.load_prompt(
            "system", self.module_name, system_prompt_kwargs
        )
        system = self.update_system()
        self.conversation.edit_system_message(system)

    def update_system(self):
        if self.memory_enabled:
            self.system = self.load_prompt(
                "system_meta",
                args={
                    "instruction": self.system_instruction_message,
                    "short_term_memory": self.get_short_term_memory(),
                    "retrieved_data": self.retrieved_data,
                },
            )
        else:
            self.system = self.system_instruction_message
        return self.system

    def get_response(
        self,
        prompt_kwargs: Dict[str, Any],
        functions: List[Callable] = [],
        user_name: Optional[str] = None,
    ) -> str | List[ChatCompletionMessageToolCall]:
        """Get a reponse from the model, can be a single string or a list of tool call."""

        if self.model is None:
            self.load_model()

        # 1. Load user prompt.
        prompt = self.load_prompt("user", self.module_name, prompt_kwargs)
        # 2. Search the most relevant information at long term memory.
        self.retrieved_data = self.search_on_long_term_memory(prompt)
        # 3. Update system message with the new information.
        self.update_system()

        self.conversation.add_user_message(prompt, user_name)
        return self.call(functions)

    def load_model(self):
        self.model = ModelsManager().create_model(self.module_name)

    def load_prompt(
        self, prompt_name: str, path: Optional[str] = None, args: Dict[str, Any] = {}
    ):
        return load_prompt(prompt_name, path=path, **args)

    def get_short_term_memory(self):
        """Get the short-term memory of the system."""

        return self.short_term_memory

    def update_short_term_memory(self, info: str):
        """
        Updates the short-term memory of the system, which is the information displayed on the system message.
        This information is very useful to maintain a context that will be always displayed on the next prompt.
        Use this to save relevant information that might be relevant in the next prompts.
        """

        self.short_term_memory = info
        return "Succesfully updated short-term memory."

    # TODO: Store full conversation after it finishes.
    # We can do that and update them periodically extracting relevant data (Fine-tuning).
    def store_on_long_term_memory(self, info: str):
        """
        Interacts with the external database Weaviate to store information in real-time.
        This function stores information in the long-term memory, allowing the system to
        retrieve it later on by using the search_on_long_term_memory function.

        Args:
            info (str): The information to be stored in the database.

        Returns:
            str: A string confirming the information was stored successfully.
        """
        try:
            self.database.store(info)
            return "Succesfully stored on database."
        except Exception as e:
            print(f"Error storing information on database: {e}")
            return f"Error storing information on database: {e}"

    def search_on_long_term_memory(self, query: str):
        """
        Interacts with the external database Weaviate to retrieve information stored in real-time
        by using store_on_long_term_memory. This function searches the long-term memory,
        retrieving data based on similarity to the provided query, enhancing response relevance
        and accuracy with the most current data available.

        Args:
            query (str): The query used to search the database for similar information.

        Returns:
            str: The content most closely matching the query in terms of relevance and similarity from the database.
        """
        return self.database.search(query)
