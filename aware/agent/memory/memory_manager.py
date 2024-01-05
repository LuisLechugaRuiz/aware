from copy import copy
from typing import Callable, List

from aware.agent.agent import Agent
from aware.chat.chat import Chat
from aware.data.database.weaviate.weaviate import WeaviateDB
from aware.utils.logger.file_logger import FileLogger


class MemoryManager(Agent):
    """A class to manage the memory of the agent. It includes the main functions and can be extended by the inheriting class."""

    def __init__(
        self, user_name: str, chat: Chat, functions: List[Callable], logger: FileLogger
    ):
        self.user_name = user_name
        self.weaviate_db = WeaviateDB()

        self.default_functions = [
            self.find_categories,
            self.create_category,
            self.search_data,
            self.store_data,
        ]
        update_functions = copy(self.default_functions)
        update_functions.extend(functions)
        self.short_term_memory = "Short term memory is EMPTY!, use update_short_term_memory() to save relevant context and avoid loosing information."  # TODO: Get from permanent storage
        super().__init__(chat=chat, functions=update_functions, logger=logger)

    def create_user(self, name: str):
        self.weaviate_db.create_user(name=name)

    def create_category(self, name: str, description: str):
        """
        Create a new category.

        Args:
            name(str): The name of the category to create.
            description (str): A description of the content that will be stored in the category.

        Returns:
            str: Feedback message.
        """

        self.logger.info(f"Creating category: {name} with description {description}")
        category_object = self.weaviate_db.store_category(
            name=name, description=description
        )
        if category_object.error:
            return f"Error creating category: {category_object.error}"
        return "Category created."

    def find_categories(self, query: str):
        """
        Find a category given a query

        Args:
            query (str): The query to be searched.

        Returns:
            str: Feedback message.
        """
        self.logger.info(f"Searching categories with description {query}")
        categories = self.weaviate_db.search_category(query)
        return (
            "\n".join(
                [
                    f"- Category: {category.name}. Description: {category.description}"
                    for category in categories
                ]
            )
            or "No categories found."
        )

    # TODO: This function is useful to find related data so the model can merge both into a single datapoint.
    # Is also useful to find specific info that the parent agent might want to retrive, but it requires changing the logic.
    def search_data(self, category: str, query: str):
        """
        Interacts with the external database Weaviate to search information in real-time given a category and a query.

        Args:
            category (str): The category in which the data will be searched.
            query (str): The query to be searched.

        Returns:
            str: Feedback message.
        """

        self.logger.info(f"Searching data with category {category} and query {query}")
        datapoints = self.weaviate_db.search_info(category_name=category, query=query)
        # TODO: IN CASE CATEGORY DOESN'T EXIST WE CAN SEARCH BY NAME AND PROVIDE THE MOST SIMILAR ONES!!
        return (
            "\n\n".join([f"- Data: {datapoint}" for datapoint in datapoints.data])
            or "No data found."
        )

    def store_data(self, category: str, data: str, potential_query: str):
        """
        Store data in the external database Weaviate in real-time given a category and data.

        Args:
            category (str): The category in which the data will be stored.
            data (str): The data to be stored.
            potential_query (str): The potential query that might be used to search the data.

        Returns:
            str: Feedback message.
        """
        self.logger.info(
            f"Storing data with category {category} and data {data}, with potential query {potential_query}"
        )
        store_result = self.weaviate_db.store_info(
            user_name=self.user_name,
            category_name=category,
            data=data,
            potential_query=potential_query,
        )
        if store_result.error:
            return f"Error storing data: {store_result.error}"
        return "Data stored."

    def reset_agent_functions(self):
        self.update_functions(functions=self.default_functions)

    def update_agent_functions(self, functions: List[Callable]):
        updated_functions = copy(self.default_functions)
        updated_functions.extend(functions)
        self.update_functions(functions=updated_functions)
