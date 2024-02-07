from supabase import Client
from typing import Any, Dict, List, Optional

from aware.agent import AgentData
from aware.chat.conversation_schemas import ChatMessage, JSONMessage
from aware.config.config import Config
from aware.data.database.supabase_handler.messages_factory import MessagesFactory
from aware.process.process_data import ProcessData
from aware.process.process_ids import ProcessIds
from aware.process.prompt_data import PromptData
from aware.requests.request import Request, RequestData
from aware.requests.service import Service, ServiceData
from aware.tools.profile import Profile
from aware.utils.logger.file_logger import FileLogger


class SupabaseHandler:
    def __init__(self, client: Client):
        self.client = client

    def add_message(
        self,
        user_id: str,
        process_id: str,
        json_message: JSONMessage,
    ) -> ChatMessage:
        logger = FileLogger("migration_tests")
        invoke_options = {
            "p_user_id": user_id,
            "p_process_id": process_id,
            "p_model": Config().aware_model,
            "p_message_type": json_message.__class__.__name__,
        }
        # Add p_ to all the keys in json_message
        json_message_dict = json_message.to_openai_dict()
        json_message_dict = {
            "p_" + key: value for key, value in json_message_dict.items()
        }
        # Expand dictionary with json_message data
        invoke_options.update(json_message_dict)
        logger.info("DEBUG - PRE CALL")
        response = self.client.rpc("insert_new_message", invoke_options).execute().data
        logger.info(f"DEBUG - POST CALL: {response}")
        response = response[0]
        logger.info("DEBUG - AFTER RESPONSE")
        return ChatMessage(
            message_id=response["id"],
            timestamp=response["created_at"],
            message=json_message,
        )

    def create_agent(
        self,
        user_id: str,
        name: str,
        task: str,
        tools_class: str,
        instructions: Optional[str] = None,
    ):
        logger = FileLogger("migration_tests")
        logger.info(f"DEBUG - Creating agent {name}")
        response = (
            self.client.rpc(
                "create_agent",
                {
                    "p_user_id": user_id,
                    "p_name": name,
                    "p_task": task,
                    "p_tool_class": tools_class,
                    "p_instructions": instructions,
                },
            )
            .execute()
            .data
        )
        return AgentData(
            id=response["id"],
            name=response["name"],
            task=response["task"],
            instructions=response["instructions"],
            thought=response["thought"],
            context=response["context"],
        )

    def create_request(
        self,
        user_id: str,
        client_process_id: str,
        service_name: str,
        query: str,
        is_async: bool,
    ) -> Request:
        logger = FileLogger("migration_tests")
        logger.info(f"DEBUG - Creating request {service_name}")
        response = (
            self.client.rpc(
                "create_request",
                {
                    "p_user_id": user_id,
                    "p_client_process_id": client_process_id,
                    "p_service_name": service_name,
                    "p_query": query,
                    "p_is_async": is_async,
                },
            )
            .execute()
            .data
        )
        response = response[0]
        request_data = RequestData(
            query=response["query"],
            is_async=response["is_async"],
            feedback=response["feedback"],
            status=response["status"],
            response=response["response"],
            prompt_prefix=response["prompt_prefix"],
        )
        return Request(
            request_id=response["id"],
            service_id=response["service_id"],
            service_process_id=response["service_process_id"],
            client_process_id=client_process_id,
            timestamp=response["created_at"],
            request_data=request_data,
        )

    def create_service(
        self, user_id: str, tools_class: str, service_data: ServiceData
    ) -> Service:
        logger = FileLogger("migration_tests")
        logger.info(f"DEBUG - Creating service {service_data.name}")
        response = (
            self.client.rpc(
                "create_service",
                {
                    "p_user_id": user_id,
                    "p_tool_class": tools_class,
                    "p_name": service_data.name,
                    "p_description": service_data.description,
                    "p_prompt_prefix": service_data.prompt_prefix,
                },
            )
            .execute()
            .data
        )
        return (
            Service(
                service_id=response["returned_id"],
                process_id=response["returned_process_id"],
                data=service_data,
            ),
        )

    def create_topic(self, user_id: str, topic_name: str, topic_description: str):
        logger = FileLogger("migration_tests")
        existing_topic = (
            self.client.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", topic_name)
            .execute()
        ).data
        logger.info(f"DEBUG - Got existing topic: {existing_topic}")
        if not existing_topic:
            logger.info(f"DEBUG - Creating topic {topic_name}")
            self.client.table("topics").insert(
                {
                    "user_id": user_id,
                    "name": topic_name,
                    "content": "",
                    "description": topic_description,
                }
            ).execute()

    def delete_message(self, message_id):
        invoke_options = {"p_message_id": message_id}
        response = self.client.rpc("soft_delete_message", invoke_options).execute().data
        return response

    def get_active_messages(self, process_id: str) -> List[ChatMessage]:
        log = FileLogger("migration_tests")
        invoke_options = {"p_process_id": process_id}
        log.info(f"PRE INVOKE with id: {process_id}")
        ordered_messages = (
            self.client.rpc("get_active_messages", invoke_options).execute().data
        )
        log.info("POST INVOKE, response: " + str(ordered_messages))
        messages = []
        if ordered_messages:
            for row in ordered_messages:
                log.info(f"Row: {str(row)}")
                messages.append(MessagesFactory.create_message(row))
        return messages

    def get_buffered_messages(self, process_id: str) -> List[ChatMessage]:
        log = FileLogger("migration_tests")
        invoke_options = {"p_process_id": process_id}
        log.info(f"PRE INVOKE with id: {process_id}")
        ordered_messages = (
            self.client.rpc("get_buffered_messages", invoke_options).execute().data
        )
        log.info("POST INVOKE, response: " + str(ordered_messages))
        messages = []
        if ordered_messages:
            for row in ordered_messages:
                log.info(f"Row: {str(row)}")
                messages.append(MessagesFactory.create_message(row))
        return messages

    def get_agent_data(self, agent_id: str):
        data = self.client.table("agents").select("*").eq("id", agent_id).execute().data
        if not data:
            return None
        data = data[0]
        return AgentData(
            id=agent_id,
            name=data["name"],
            task=data["task"],
            thought=data["thought"],
            context=data["context"],
            # profile=Profile(profile=data["profile"]),
        )

    def get_agent_profile(self, agent_id: str) -> Optional[Profile]:
        data = self.client.table("agents").select("*").eq("id", agent_id).execute().data
        if not data:
            return None
        return Profile(profile=data[0]["profile"])

    def get_agent_process_id(self, agent_id: str, process_name: str) -> Optional[str]:
        data = (
            self.client.table("processes")
            .select("*")
            .eq("agent_id", agent_id)
            .eq("name", process_name)
            .execute()
            .data
        )
        if not data:
            return None
        return data[0]["id"]

    def get_tools_class(self, process_id: str) -> Optional[str]:
        data = (
            self.client.table("processes")
            .select("*")
            .eq("id", process_id)
            .execute()
            .data
        )
        if not data:
            return None
        return data[0]["tools_class"]

    def get_requests(self, service_id: str) -> List[Request]:
        data = (
            (
                self.client.table("requests")
                .select("*")
                .eq("service_id", service_id)
                .execute()
                .data
            )
            .execute()
            .data
        )
        requests = []
        if not data:
            return requests
        for row in data:
            request_data = RequestData(
                query=row["query"],
                status=row["status"],
                response=row["response"],
                prompt_prefix=row["prompt_prefix"],
            )
            requests.append(
                Request(
                    request_id=row["id"],
                    service_id=service_id,
                    client_process_id=row["client_process_id"],
                    request_data=request_data,
                )
            )
        return requests

    def get_process_service_requests(self, process_id: str) -> List[Request]:
        data = (
            (
                self.client.table("services")
                .select("*")
                .eq("process_id", process_id)
                .execute()
                .data
            )
            .execute()
            .data
        )
        requests = []
        if not data:
            return requests
        for row in data:
            requests.extend(self.get_requests(row["id"]))
        return requests

    def get_process_data(self, process_ids: ProcessIds) -> Optional[ProcessData]:
        data = (
            self.client.table("processes")
            .select("*")
            .eq("id", process_ids.process_id)
            .execute()
            .data
        )
        if not data:
            return None
        prompt_data = PromptData(
            module_name=data[0]["module_name"], prompt_name=data[0]["prompt_name"]
        )
        requests = self.get_process_service_requests(process_id=process_ids.process_id)
        return ProcessData(
            ids=process_ids,
            agent_data=self.get_agent_data(process_ids.agent_id),
            prompt_data=prompt_data,
            requests=requests,
            # TODO: Add events!
        )

    def get_user_profile(self, user_id: str):
        data = (
            self.client.table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
            .data
        )
        if not data:
            return None
        return data[0]

    def get_topic_content(self, user_id: str, name: str):
        data = (
            self.client.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", name)
            .execute()
            .data
        )
        if not data:
            return None
        data = data[0]
        return data["content"]

    def remove_frontend_message(self, message_id: str):
        self.client.table("frontend_messages").delete().eq("id", message_id).execute()

    def remove_new_user_notification(self, notification_id: str):
        self.client.table("new_user_notification").delete().eq(
            "id", notification_id
        ).execute()

    def send_message_to_user(
        self,
        user_id: str,
        process_id: str,
        message_type: str,
        role: str,
        name: str,
        content: str,
    ):
        logger = FileLogger("migration_tests")
        logger.info(f"DEBUG - Sending message to user {user_id}")
        invoke_options = {
            "p_user_id": user_id,
            "p_process_id": process_id,
            "p_model": Config().aware_model,
            "p_message_type": message_type,
            "p_role": role,
            "p_name": name,
            "p_content": content,
        }
        response = (
            self.client.rpc("send_message_to_user", invoke_options).execute().data
        )
        logger.info(f"DEBUG - Response: {response}")
        return response

    def set_active_process(self, process_id: str, active: bool):
        self.client.table("processes").update({"is_active": active}).eq(
            "id", process_id
        ).execute()

    def set_request_completed(self, request_id: str, response: str):
        self.client.table("requests").update(
            {"status": "completed", "response": response}
        ).eq("id", request_id).execute()

    def set_topic_content(self, user_id: str, name: str, content: str):
        data = (
            self.client.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", name)
            .execute()
            .data
        )
        if not data:
            raise Exception("Topic not found")
        else:
            self.client.table("topics").update({"content": content}).eq(
                "user_id", user_id
            ).eq("name", name).execute()

    def update_agent_data(self, agent_data: AgentData):
        self.client.table("agents").update(agent_data.to_dict()).eq(
            "id", agent_data.id
        ).execute()

    def update_agent_profile(self, agent_id: str, profile: Dict[str, Any]):
        self.client.table("agents").update({"profile": profile}).eq(
            "id", agent_id
        ).execute()

    def update_user_profile(self, user_id: str, profile: Dict[str, Any]):
        self.client.table("profiles").update(profile).eq("user_id", user_id).execute()
