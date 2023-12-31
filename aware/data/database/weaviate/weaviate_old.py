import weaviate
import weaviate.classes as wvc
from openai import OpenAI
from typing import Optional

from aware.config.config import Config


# TODO: Define more schemas -> User info, tool, episode (previous tasks)...
# {
#     "class": "User",
#     "description": "User",
#     "properties": [
#         {
#             "name": "name",
#             "dataType": ["text"],
#             "description": "The name of the user",
#         },
#         {
#             "name": "id",
#             "dataType": ["text"],
#             "description": "The user id",
#         },
#     ],
# },

DEF_SCHEMA = {
    "classes": [
        {
            "class": "Category",
            "description": "A category to classify data",
            "properties": [
                {
                    "name": "name",
                    "dataType": ["text"],
                    "description": "The category name",
                },
            ],
        },
        {
            "class": "Conversation",
            "description": "A conversation between users and the assistant",
            "properties": [
                {
                    # TODO: Cross reference to user.
                    "name": "users",
                    "dataType": ["text[]"],
                    "description": "The name of the tool",
                },
                {
                    "name": "summary",
                    "dataType": ["text"],
                    "description": "The conversation summary",
                },
            ],
        },
        {
            "class": "Info",
            "description": "Information from a certain category",
            "properties": [
                {
                    "name": "user_name",
                    "dataType": ["text"],
                    "description": "The name of the user",
                },
                {
                    "name": "category",
                    "dataType": ["Category"],
                    "description": "The category of the information",
                },
                {
                    "name": "info",
                    "dataType": ["text"],
                    "description": "The information of the user",
                },
            ],
        },
        {
            "class": "Tool",
            "description": "Tool information",
            "properties": [
                {
                    "name": "name",
                    "dataType": ["text"],
                    "description": "The name of the tool",
                },
                {
                    "name": "description",
                    "dataType": ["text"],
                    "description": "The description of the tool",
                },
            ],
        },
    ]
}


class WeaviateDB(object):
    def __init__(self):
        weaviate_key = Config().weaviate_key
        self.openai_client = OpenAI()

        if weaviate_key:
            # Run on weaviate cloud service
            auth = weaviate.auth.AuthApiKey(api_key=weaviate_key)
            self.client = weaviate.Client(
                url=Config().weaviate_url,
                auth_client_secret=auth,
                additional_headers={
                    "X-OpenAI-Api-Key": Config().openai_api_key,
                },
            )
        else:
            # Run locally"
            self.client = weaviate.connect_to_local(
                host=Config().local_weaviate_url, port=Config().weaviate_port
            )
        # self.client.schema.delete_all()
        self._create_schema()

    def _create_schema(self):
        # Check if classes in the schema already exist in Weaviate
        for class_definition in DEF_SCHEMA["classes"]:
            class_name = class_definition["class"]
            print("Creating class: ", class_name)
            try:
                if not self.client.schema.contains(class_definition):
                    # Class doesn't exist, so we attempt to create it
                    self.client.schema.create_class(class_definition)
            except Exception as err:
                print(f"Unexpected error {err=}, {type(err)=}")

    def get_ada_embedding(self, text):
        text = text.replace("\n", " ")
        return (
            self.openai_client.embeddings.create(
                input=[text], model="text-embedding-ada-002"
            )
            .data[0]
            .embedding
        )

    def _get_relevant(
        self,
        vector,
        class_name,
        fields,
        where_filter=None,
        num_relevant=2,
    ):
        try:
            query = (
                self.client.query.get(class_name, fields)
                .with_near_vector(vector)
                .with_limit(num_relevant)
                .with_additional(["certainty", "id"])
            )
            if where_filter:
                query.with_where(where_filter)
            results = query.do()

            if len(results["data"]["Get"][class_name]) > 0:
                return results["data"]["Get"][class_name]
            else:
                return None

        except Exception as err:
            print(f"Unexpected error {err=}, {type(err)=}")
            return None

    def searchNEW(
        self,
        category: str,
        query: str,
        class_name: str = "UserInfo",
        name: Optional[str] = None,
        num_relevant=2,
        certainty=0.7,
    ):
        query_vector = self.get_ada_embedding(query)
        # Get the most similar content
        filter = None
        if name:
            filter = {
                "path": ["name"],
                "operator": "Equal",
                "valueText": name,
            }
        most_similar_contents = self._get_relevant(
            vector=({"vector": query_vector}),  # TODO: add "certainty": certainty
            class_name=class_name,
            fields=["user_name", "info"],  # TODO: ADJUST!!
            where_filter=filter,
            num_relevant=num_relevant,
        )
        return most_similar_contents

    def search(self, user_name: str, query: str, num_relevant=2, certainty=0.7):
        query_vector = self.get_ada_embedding(query)
        # Get the most similar content
        user_filter = {
            "path": ["user_name"],
            "operator": "Equal",
            "valueText": user_name,
        }
        most_similar_contents = self._get_relevant(
            vector=({"vector": query_vector}),  # TODO: add "certainty": certainty
            class_name="UserInfo",
            fields=["user_name", "info"],
            where_filter=user_filter,
            num_relevant=num_relevant,
        )
        return most_similar_contents

    def search_tool(self, query: str, num_relevant=2, certainty=0.7):
        query_vector = self.get_ada_embedding(query)
        # Get the most similar content
        most_similar_contents = self._get_relevant(
            vector=({"vector": query_vector}),  # TODO: add "certainty": certainty
            class_name="Tool",
            fields=["name", "description"],
            num_relevant=num_relevant,
        )
        return most_similar_contents

    def store_tool(self, name: str, description: str):
        """Store a tool in the database in case it doesn't exist yet"""

        try:
            query = (
                self.client.query.get("Tool", ["name", "description"])
                .with_limit(1)
                .with_additional(["certainty", "id"])
            )
            tool_name_filter = {
                "path": ["name"],
                "operator": "Equal",
                "valueText": name,
            }
            query.with_where(tool_name_filter)
            results = query.do()

            if len(results["data"]["Get"]["Tool"]) > 0:
                return results["data"]["Get"]["Tool"][0]["_additional"]["id"]
            else:
                info_vector = self.get_ada_embedding(description)
                tool_uuid = self.client.data_object.create(
                    data_object={
                        "name": name,
                        "description": description,
                    },
                    class_name="Tool",
                    vector=info_vector,
                )
                return tool_uuid
        except Exception as err:
            print(f"Unexpected error {err=}, {type(err)=}")
            return None

    def store(
        self,
        user_name: str,
        info: str,
    ):
        # TODO: If the object doesn't exist, proceed with creating a new one
        info_vector = self.get_ada_embedding(info)
        user_info_uuid = self.client.data_object.create(
            data_object={
                "user_name": user_name,
                "info": info,
            },
            class_name="UserInfo",
            vector=info_vector,
        )
        return user_info_uuid

    # TODO: ADJUST!
    def searchNew(self, category: str, query: str, num_relevant=2, certainty=0.7):
        # 1. search for data where category.name == name
        category_filter = {
            "path": ["category", "Category", "name"],
            "operator": "Equal",
            "valueText": category,
        }

        query_vector = self.get_ada_embedding(query)
        # Get the most similar content
        most_similar_contents = self._get_relevant(
            vector=({"vector": query_vector}),  # TODO: add "certainty": certainty
            class_name="Info",
            fields=["name", "info"],
            num_relevant=num_relevant,
        )
        return most_similar_contents

    # Two types of store:
    def storeNEW(
        self,
        category: str,
        data: str,
        name: str = "default",
    ):
        info_vector = self.get_ada_embedding(data)
        user_info_uuid = self.client.data_object.create(
            data_object={
                "name": name,
                "info": data,
            },
            class_name="Info",
            vector=info_vector,
        )
        return user_info_uuid

    def test(self):
        # NEWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
        # Add the reference to JeopardyQuestion, after it was created
        category = self.client.collections.get("Category")

        data_object = wvc.DataObject(
            properties=properties,
            references={"hasCategory": wvc.Reference.to(uuids=target_uuid)},
            uuid=generate_uuid5(properties),
        )

        # category.config.add_reference(
        category.config.add_property(
            wvc.ReferenceProperty(
                name="hasQuestion", target_collection="JeopardyQuestion"
            )
        )
