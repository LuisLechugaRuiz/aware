import json
from openai import OpenAI
import os
from pathlib import Path
from typing import List, Optional

import weaviate
import weaviate.classes as wvc

from aware.config.config import Config
from aware.data.database.weaviate.helpers import (
    WeaviateTool,
    WeaviateResult,
)


class WeaviateDB(object):
    def __init__(self):
        weaviate_key = Config().weaviate_key
        self.openai_client = OpenAI()

        if weaviate_key:
            # Run on weaviate cloud service
            self.client = weaviate.connect_to_wcs(
                cluster_url=Config().weaviate_url,
                auth_credentials=weaviate.auth.AuthApiKey(api_key=weaviate_key),
                headers={
                    "X-OpenAI-Api-Key": Config().openai_api_key,
                },
            )
        else:
            # Run locally
            print("Running on local Weaviate instance")
            print("DEBUG PORT: ", Config().weaviate_port)
            self.client = weaviate.connect_to_local(
                host=Config().local_weaviate_url, port=Config().weaviate_port
            )
        # self.client.collections.delete_all()  # TODO: START AGAIN
        schemas_path = os.path.join(Path(__file__).parent, "schemas", "schemas.json")
        self._create_schemas(schemas_path)

    def get_ada_embedding(self, text):
        text = text.replace("\n", " ")
        return (
            self.openai_client.embeddings.create(
                input=[text], model="text-embedding-ada-002"
            )
            .data[0]
            .embedding
        )

    def _create_schemas(self, schemas_path: str):
        """Create the schemas in the Weaviate instance

        Args:
            schemas_path (str): Path to the JSON schema
        """

        # Open path and get JSON schema
        with open(schemas_path) as json_file:
            json_schema = json.load(json_file)

        # Function to find the key in DataType enum by value
        def get_data_type_key(value):
            for data_type in wvc.DataType:
                if data_type.value == value:
                    return data_type
            return None

        # Iterate through the classes in the JSON schema
        for class_name, class_info in json_schema.items():
            if self.client.collections.exists(class_name):
                continue

            properties = []
            references = []
            for prop_name, prop_info in class_info["properties"].items():
                # Get the corresponding DataType enum key by value
                data_type_key = get_data_type_key(prop_info["type"])

                if data_type_key is not None:
                    # Add new property
                    properties.append(
                        wvc.Property(
                            name=prop_name,
                            data_type=data_type_key,
                            description=prop_info["description"],
                        )
                    )
                elif prop_info["type"] in json_schema:
                    # Add new cross-reference
                    references.append(
                        wvc.ReferenceProperty(
                            name=prop_name,
                            target_collection=prop_info["type"],
                            description=prop_info["description"],
                        )
                    )
            # Create collection
            print("Creating collection: ", class_name)
            self.client.collections.create(
                name=class_name,
                description=class_info["description"],
                properties=properties,
                references=references,
            )

    # TODO: FILTER BY UUID.
    def create_user(self, name: str) -> WeaviateResult:
        user_collection = self.client.collections.get("User")
        existing_users = user_collection.query.fetch_objects(
            filters=wvc.Filter("name").equal(name)
        )
        if len(existing_users.objects) > 0:
            return WeaviateResult(error="User already exists!!!")
        user_uuid = user_collection.data.insert(
            properties={
                "name": name,
            }
        )
        return WeaviateResult(data=user_uuid)

    def search_info(
        self,
        query: str,
        user_name: Optional[str] = None,
        num_relevant=2,
        certainty=0.7,
    ) -> WeaviateResult:
        try:
            filters = None
            if user_name is not None:
                filters = filter & wvc.Filter(["user", "User", "name"]).equal(user_name)

            query_vector = self.get_ada_embedding(query)
            info_collection = self.client.collections.get("Info")
            info = info_collection.query.near_vector(
                near_vector=query_vector,
                certainty=certainty,
                limit=num_relevant,
                filters=filters,
            )
            datapoints = [
                info_object.properties["data"] for info_object in info.objects
            ]
            return WeaviateResult(data=datapoints)
        except Exception as err:
            print(f"Unexpected error {err} when searching info")
            return WeaviateResult(error=str(err))

    # TODO: Return a specific class with Data, errors.. to differentiatate between string and error
    def store_info(
        self, user_name: str, data: str, potential_query: str
    ) -> WeaviateResult:
        try:
            user_collection = self.client.collections.get("User")
            user = user_collection.query.fetch_objects(
                filters=wvc.Filter("name").equal(user_name)
            )
            if len(user.objects) == 0:
                return WeaviateResult(error="User does not exist!")
            user_uuid = user.objects[0].uuid
            info_collection = self.client.collections.get("Info")
            info_uuid = info_collection.data.insert(
                properties={
                    "data": data,
                    "potential_query": potential_query,
                },
                references={
                    "user": wvc.Reference.to(uuids=user_uuid),
                },
                vector=self.get_ada_embedding(potential_query),
            )
            return WeaviateResult(data=info_uuid)
        except Exception as err:
            print(f"Unexpected error {err} when storing info")
            return WeaviateResult(error=str(err))

    # TODO: ADD UPDATE INFO TO MERGE NEW INFO WITH OLD ONE.
    # returned_objects.objects[0].metadata.last_update_time and creation_time!

    def search_tool(
        self, query: str, num_relevant=2, certainty=0.7
    ) -> List[WeaviateTool]:
        """Search for a tool in the database"""

        query_vector = self.get_ada_embedding(query)
        # Get the most similar content
        tool_collection = self.client.collections.get("Tool")
        tool_objects = tool_collection.query.near_vector(
            near_vector=query_vector, certainty=certainty, limit=num_relevant
        ).objects
        tools = [
            WeaviateTool(
                tool_object.properties["name"], tool_object.properties["description"]
            )
            for tool_object in tool_objects
        ]
        return tools

    def store_tool(self, name: str, description: str):
        """Store a tool in the database in case it doesn't exist yet"""

        try:
            # Search if the tool already exists
            tool_collection = self.client.collections.get("Tool")
            existing_tool = tool_collection.query.fetch_objects(
                filters=wvc.Filter("name").equal(name)
            )
            if len(existing_tool.objects) > 0:
                return existing_tool.objects[0].uuid

            tool_uuid = tool_collection.data.insert(
                properties={
                    "name": name,
                    "description": description,
                },
                # TODO: In the future we can add a reference to user, once we move to multi-agent.
                vector=self.get_ada_embedding(description),
            )
            return WeaviateResult(data=tool_uuid)
        except Exception as err:
            print(f"Unexpected error {err} when storing tool")
            return WeaviateResult(error=str(err))

    # TODO: Allow multiple users, references can be inserted as: https://weaviate.io/developers/weaviate/manage-data/cross-references#add-multiple-one-to-many-cross-references
    def search_conversation(
        self, query: str, user_name: Optional[str] = None, certainty=0.7, num_relevant=2
    ):
        try:
            filters = None
            if user_name is not None:
                filters = wvc.Filter(["user", "User", "name"]).equal(user_name)

            query_vector = self.get_ada_embedding(query)
            conversation_collection = self.client.collections.get("Conversation")
            conversations = conversation_collection.query.near_vector(
                near_vector=query_vector,
                certainty=certainty,
                limit=num_relevant,
                filters=filters,
            )
            summaries = [
                conversation_object.properties["summary"]
                for conversation_object in conversations.objects
            ]
            return WeaviateResult(data=summaries)
        except Exception as err:
            print(f"Unexpected error {err} when searching conversation")
            return WeaviateResult(error=str(err))

    def store_conversation(self, user_name: str, summary: str, potential_query: str):
        try:
            user_collection = self.client.collections.get("User")
            user_uuid = (
                user_collection.query.fetch_objects(
                    filters=wvc.Filter("name").equal(user_name)
                )
                .objects[0]
                .uuid
            )
            # Store the conversation
            conversation_collection = self.client.collections.get("Conversation")
            conversation_uuid = conversation_collection.data.insert(
                properties={
                    "summary": summary,
                    "potential_query": potential_query,
                },
                references={"User": wvc.Reference.to(uuids=user_uuid)},
                vector=self.get_ada_embedding(potential_query),
            )
            self.update_last_conversation_summary(conversation_uuid=conversation_uuid)
            return WeaviateResult(data=conversation_uuid)
        except Exception as err:
            print(f"Unexpected error {err} when storing conversation")
            return WeaviateResult(error=str(err))

    def get_last_conversation_summary(self):
        try:
            last_conversation_collection = self.client.collections.get(
                "LastConversation"
            )
            conversation_objects = last_conversation_collection.query.fetch_objects()
            if len(conversation_objects.objects) > 0:
                # Get the referenced conversation
                conversation_uuid = conversation_objects.objects[0].references[
                    "Conversation"
                ]
                print("DEBUG conversation_uuid: ", conversation_uuid)
                conversation_collection = self.client.collections.get("Conversation")
                conversation_object = conversation_collection.query.fetch_object_by_id(
                    uuid=conversation_uuid
                )
                summary = conversation_object.properties["summary"]
                return WeaviateResult(data=summary)
            return WeaviateResult(data="")
        except Exception as err:
            print(f"Unexpected error {err} when getting last conversation summary")
            return WeaviateResult(error=str(err))

    def update_last_conversation_summary(self, conversation_uuid: str):
        conversation_collection = self.client.collections.get("LastConversation")
        conversation_objects = conversation_collection.query.fetch_objects()
        references = {"Conversation": wvc.Reference.to(uuids=conversation_uuid)}
        if len(conversation_objects.objects) > 0:
            old_conversation_uuid = conversation_objects.objects[0].uuid
            # Update it
            conversation_collection.data.update(
                uuid=old_conversation_uuid,
                references=references,
            )
        else:
            conversation_collection.data.insert(references=references)
