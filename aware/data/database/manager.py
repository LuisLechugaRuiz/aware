from aware.architecture.helpers.topics import (
    DEF_SEARCH_DATABASE,
    DEF_STORE_DATABASE,
)
from aware.architecture.helpers.tmp_ips import (
    DEF_ASSISTANT_IP,
    DEF_SERVER_PORT,
)
from aware.data.database.weaviate import WeaviateDB
from aware.utils.communication_protocols import Server


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

    def search_tool(self, query: str):
        search_result = self.database.search_tool(query=query)
        if search_result is None:
            return None
        return search_result[0]

    def search(self, query: str):
        search_result = self.database.search(user_name=self.name, query=query)
        if search_result is None:
            return "No results found."
        # TODO: Process the data, rerank, synthesize....
        result = search_result[0]["info"]
        if result is None:
            return "No results found."
        return result

    def store(self, info: str):
        self.database.store(user_name=self.name, info=info)
        return "OK"

    def store_tool(self, name: str, description: str):
        self.database.store_tool(name=name, description=description)
        return "OK"
