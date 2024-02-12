from supabase import Client
from typing import Any, Dict, List, Optional

from aware.agent.agent_data import AgentData, AgentState, ThoughtGeneratorMode
from aware.chat.conversation_schemas import ChatMessage, JSONMessage
from aware.communications.events.event import Event
from aware.communications.requests.request import Request, RequestData
from aware.communications.requests.service import Service, ServiceData
from aware.communications.topics.subscription import TopicSubscription
from aware.config.config import Config
from aware.data.database.supabase_handler.messages_factory import MessagesFactory
from aware.process.process_data import ProcessData
from aware.process.process_communications import ProcessCommunications
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
        tools_class: str,
        identity: str,
        task: str,
        instructions: str,
        thought_generator_mode: str,
    ) -> AgentData:
        logger = FileLogger("migration_tests")
        logger.info(f"DEBUG - Creating agent {name}")
        data = (
            self.client.table("agents")
            .insert(
                {
                    "user_id": user_id,
                    "name": name,
                    "tools_class": tools_class,
                    "identity": identity,
                    "task": task,
                    "instructions": instructions,
                    "thought_generator_mode": thought_generator_mode,
                }
            )
            .execute()
            .data
        )

        return AgentData(
            id=data["id"],
            name=data["name"],
            context=data["context"],
            tools_class=data["tools_class"],
            identity=data["identity"],
            task=data["task"],
            instructions=data["instructions"],
            state=AgentState(data["state"]),
            thought_generator_mode=ThoughtGeneratorMode(data["thought_generator_mode"]),
        )

    def create_process(
        self,
        user_id: str,
        agent_id: str,
        name: str,
        tools_class: str,
        identity: str,
        task: str,
        instructions: str,
    ) -> ProcessData:
        logger = FileLogger("migration_tests")
        logger.info(f"DEBUG - Creating process {name}")
        data = (
            self.client.table("processes")
            .insert(
                {
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "name": name,
                    "tools_class": tools_class,
                    "identity": identity,
                    "task": task,
                    "instructions": instructions,
                }
            )
            .execute()
            .data
        )
        return ProcessData(
            id=data["id"],
            name=data["name"],
            tools_class=data["tools"],
            identity=data["identity"],
            task=data["task"],
            instructions=data["instructions"],
        )

    def create_event(self, user_id: str, event_name: str, content: str) -> Event:
        logger = FileLogger("migration_tests")
        logger.info(f"DEBUG - Creating event {event_name} for user {user_id}")
        response = (
            self.client.table("events")
            .insert(
                {
                    "user_id": user_id,
                    "name": event_name,
                    "content": content,
                }
            )
            .execute()
            .data
        )
        return Event(
            id=response["id"],
            name=event_name,
            content=content,
            timestamp=response["created_at"],
        )

    def create_event_subscription(self, user_id: str, process_id: str, event_name: str):
        logger = FileLogger("migration_tests")
        logger.info(
            f"DEBUG - Creating subscription to event: {event_name} for user: {user_id} and process: {process_id}"
        )
        self.client.rpc(
            "create_event_subscription",
            {
                "p_user_id": user_id,
                "p_process_id": process_id,
                "p_event_name": event_name,
            },
        ).execute()

    def create_topic_subscription(
        self,
        process_id: str,
        topic_name: str,
    ):
        logger = FileLogger("migration_tests")
        logger.info(f"DEBUG - Creating topic subscription for process {process_id}")
        self.client.rpc(
            "create_topic_subscription",
            {
                "p_process_id": process_id,
                "p_topic_name": topic_name,
            },
        ).execute()

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
            context=data["context"],
            state=AgentState(data["state"]),
            thought_generator_mode=ThoughtGeneratorMode(data["thought_generator_mode"]),
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

    def get_topic_subscriptions(self, process_id: str) -> List[TopicSubscription]:
        data = (
            self.client.rpc("get_subscribed_data", {"p_process_id": process_id})
            .execute()
            .data
        )
        if not data:
            return None
        subscriptions: List[TopicSubscription] = []
        for row in data:
            subscriptions.append(
                TopicSubscription(
                    id=row["topic_id"],
                    topic_name=row["name"],
                    content=row["content"],
                    description=row["description"],
                    timestamp=row["updated_at"],
                )
            )
        return subscriptions

    def get_requests(self, key_process_id: str, process_id: str) -> List[Request]:
        data = (
            self.client.table("requests")
            .select("*")
            .eq(key_process_id, process_id)
            .execute()
            .data
        )
        requests = []
        if not data:
            return requests
        for row in data:
            request_data = RequestData(
                query=row["query"],
                is_async=row["is_async"],
                feedback=row["feedback"],
                status=row["status"],
                response=row["response"],
            )
            requests.append(
                Request(
                    request_id=row["id"],
                    service_id=row["service_id"],
                    service_process_id=row["service_process_id"],
                    client_process_id=row["client_process_id"],
                    timestamp=row["created_at"],
                    data=request_data,
                )
            )
        return requests

    def get_process_service_requests(self, process_id: str) -> List[Request]:
        data = (
            self.client.table("services")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        requests = []
        if not data:
            return requests
        for row in data:
            requests.extend(
                self.get_requests(
                    key_process_id="service_process_id", process_id=row["id"]
                )
            )
        return requests

    def get_process_communications(self, process_id: str) -> ProcessCommunications:
        outgoing_requests = self.get_requests(
            key_process_id="client_process_id", process_id=process_id
        )
        incoming_requests = self.get_requests(
            key_process_id="service_process_id", process_id=process_id
        )
        if len(incoming_requests) > 0:
            incoming_request = incoming_requests[0]
        else:
            incoming_request = None
        topic_subscriptions = self.get_topic_subscriptions(process_id)
        return ProcessCommunications(
            outgoing_requests=outgoing_requests,
            incoming_request=incoming_request,
            subscriptions=topic_subscriptions,
        )

    def get_process_data(self, process_id: str) -> Optional[ProcessData]:
        data = (
            self.client.table("processes")
            .select("*")
            .eq("id", process_id)
            .execute()
            .data
        )
        if not data:
            return None
        data = data[0]
        return ProcessData(
            name=data["name"],
            tools_class=data["tools_class"],
            identity=data["identity"],
            task=data["task"],
            instructions=data["instructions"],
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
