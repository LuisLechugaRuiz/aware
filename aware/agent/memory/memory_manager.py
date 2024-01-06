from typing import Dict, List

from aware.data.database.weaviate.weaviate import WeaviateDB
from aware.utils.logger.file_logger import FileLogger


class MemoryManager:
    """A class to manage the memory of the agent"""

    def __init__(self, user_name: str, logger: FileLogger):
        self.user_name = user_name
        self.logger = logger
        self.weaviate_db = WeaviateDB()
        self.register_user()

    def create_user(self, name: str):
        self.weaviate_db.create_user(name=name)

    # TODO: This function is useful to find related data so the model can merge both into a single datapoint.
    # Is also useful to find specific info that the parent agent might want to retrive, but it requires changing the logic.
    def search_data(self, queries: List[str]):
        """
        Interacts with the external database Weaviate to search information in real-time for different queries.

        Args:
            query (List[str]): A list of queries to be searched.

        Returns:
            str: Feedback message.
        """
        datapoints: Dict[str, List[str]] = {}
        for query in queries:
            results = self.weaviate_db.search_info(query=query).data
            datapoints[query].append(results)
        response = ""
        for query, data in datapoints.items():
            data_str = "\n".join(data)
            response += f"- Query: {query}\n-Data: {data_str}\n"
        return response

    def store_data(self, data: str, potential_query: str):
        """
        Stores data in the Weaviate database with an associated potential query for future retrieval.

        Args:
            data (str): The data to be stored.
            potential_query (str): A related query for future data retrieval.

        Returns:
            str: Feedback message.
        """
        self.logger.info(f"Storing data {data}, with potential query {potential_query}")
        store_result = self.weaviate_db.store_info(
            user_name=self.user_name,
            data=data,
            potential_query=potential_query,
        )
        if store_result.error:
            return f"Error storing data: {store_result.error}"
        return "Data stored."

    def register_user(self):
        """
        Registers the user in the Weaviate database.

        Returns:
            str: Feedback message.
        """
        self.logger.info(f"Registering user {self.user_name}")
        if not self.weaviate_db.user_exists(name=self.user_name):
            self.logger.info(f"User {self.user_name} does not exist. Creating it.")
            self.weaviate_db.create_user(name=self.user_name)
