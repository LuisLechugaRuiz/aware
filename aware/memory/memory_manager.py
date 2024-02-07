from typing import Dict, List

from aware.data.database.weaviate.weaviate import WeaviateDB, WeaviateResult
from aware.utils.logger.file_logger import FileLogger


class MemoryManager:
    """A class to manage the memory of the agent"""

    def __init__(self, user_id: str, logger: FileLogger):
        self.user_id = user_id
        self.logger = logger
        self.weaviate_db = WeaviateDB()

    def create_user(self, user_id: str, user_name: str) -> WeaviateResult:
        return self.weaviate_db.create_user(user_id=user_id, user_name=user_name)

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
            search_results = self.weaviate_db.search_info(
                query=query, user_id=self.user_id
            )
            if search_results.error:
                return f"Error searching for query {query}: {search_results.error}"
            results = search_results.data
            self.logger.info(f"Searching for query {query}, results: {results}")
            datapoints[query] = results
        response = ""
        for query, data in datapoints.items():
            data_str = "Not found."
            for index, datapoint in enumerate(data):
                data_str += f"- Data {index}: {datapoint}\n"
            response += f"- Query: {query}\n{data_str}"
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
            user_id=self.user_id,
            data=data,
            potential_query=potential_query,
        )
        if store_result.error:
            return f"Error storing data: {store_result.error}"
        return "Data stored."

    def store_conversation(self, summary: str, potential_query: str):
        """
        Stores a conversation summary in the Weaviate database with an associated potential query for future retrieval.

        Args:
            summary (str): The conversation summary to be stored.
            potential_query (str): A related query for future data retrieval.

        Returns:
            str: Feedback message.
        """
        self.logger.info(
            f"Storing conversation summary with potential query: {potential_query}"
        )
        store_result = self.weaviate_db.store_conversation(
            user_id=self.user_id,
            summary=summary,
            potential_query=potential_query,
        )
        if store_result.error:
            return f"Error storing data: {store_result.error}"
        return "Data stored."