from typing import List

from aware.architecture.helpers.topics import (
    DEF_SEARCH_DATABASE,
    DEF_STORE_DATABASE,
)
from aware.architecture.helpers.tmp_ips import (
    DEF_ASSISTANT_IP,
    DEF_SERVER_PORT,
)
from aware.data.database.weaviate.weaviate import WeaviateDB
from aware.data.database.weaviate.helpers import WeaviateTool
from aware.utils.communication_protocols import Server


# TODO: REMOVE ME!
class DatabaseManager:
    def __init__(self, name: str, register: bool = True):
        self.database = WeaviateDB()
        self.name = name
        if register:
            self.search_user_info_server = Server(
                address=f"tcp://{DEF_ASSISTANT_IP}:{DEF_SERVER_PORT}",
                topics=[f"{name}_{DEF_SEARCH_DATABASE}"],
                callback=self.search,
            )
            self.store_user_info_server = Server(
                address=f"tcp://{DEF_ASSISTANT_IP}:{DEF_SERVER_PORT}",
                topics=[f"{name}_{DEF_STORE_DATABASE}"],
                callback=self.store,
            )

    def search_tool(self, query: str) -> List[WeaviateTool]:
        return self.database.search_tool(query=query)

    def search(self, query: str):
        search_result = self.database.search_info(user_name=self.name, query=query)
        if search_result is None:
            return "No results found."
        # TODO: Process the data, rerank, synthesize....
        result = search_result[0]["info"]
        if result is None:
            return "No results found."
        return result

    def store_info(self, info: str):
        self.database.store(user_name=self.name, info=info)
        return "OK"

    def store_conversation(self, summary: str):
        self.database.store_conversation_summary(user_name=self.name, summary=summary)
        return "OK"

    def store_tool(self, name: str, description: str):
        self.database.store_tool(name=name, description=description)
        return "OK"
