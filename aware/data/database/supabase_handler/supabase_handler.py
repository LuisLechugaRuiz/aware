from supabase import Client
from typing import Any, Dict, List, Optional

from aware.agent.agent_data import AgentData, AgentState, ThoughtGeneratorMode
from aware.chat.conversation_schemas import ChatMessage, JSONMessage
from aware.communications.events.event import Event, EventStatus
from aware.communications.events.event_type import EventType
from aware.communications.events.event_subscription import EventSubscription
from aware.communications.requests.request import Request, RequestData, RequestStatus
from aware.communications.requests.service import Service, ServiceData
from aware.communications.topics.topic import Topic
from aware.communications.topics.topic_subscription import TopicSubscription
from aware.config.config import Config
from aware.data.database.supabase_handler.messages_factory import MessagesFactory
from aware.memory.user.user_data import UserData
from aware.process.process_data import ProcessData, ProcessFlowType
from aware.process.process_ids import ProcessIds
from aware.process.process_communications import ProcessCommunications
from aware.tools.profile import Profile
from aware.utils.logger.file_logger import FileLogger


class SupabaseHandler:
    def __init__(self, client: Client):
        self.client = client
        self.logger = FileLogger("supabase_handler")

    def add_message(
        self,
        user_id: str,
        process_id: str,
        json_message: JSONMessage,
    ) -> ChatMessage:
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
        self.logger.info("Adding message to database")
        response = self.client.rpc("insert_new_message", invoke_options).execute().data
        self.logger.info(f"Database acknowledge {response}")
        response = response[0]
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
        task: str,
        instructions: str,
        thought_generator_mode: str,
    ) -> AgentData:
        self.logger.info(f"Creating agent {name}")
        data = (
            self.client.table("agents")
            .insert(
                {
                    "user_id": user_id,
                    "name": name,
                    "tools_class": tools_class,
                    "task": task,
                    "instructions": instructions,
                    "thought_generator_mode": thought_generator_mode,
                }
            )
            .execute()
            .data
        )
        data = data[0]
        self.logger.info(f"Agent: {name}, created. Initializing agent data")
        return AgentData(
            id=data["id"],
            name=data["name"],
            context=data["context"],
            tools_class=data["tools_class"],
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
        task: str,
        instructions: str,
        flow_type: ProcessFlowType,
    ) -> ProcessData:
        self.logger.info(f"Creating process {name}")
        data = (
            self.client.table("processes")
            .insert(
                {
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "name": name,
                    "tools_class": tools_class,
                    "task": task,
                    "instructions": instructions,
                    "flow_type": flow_type.value,
                }
            )
            .execute()
            .data
        )
        data = data[0]
        self.logger.info(f"Process: {name}, created. Initializing process data")
        return ProcessData(
            id=data["id"],
            name=data["name"],
            tools_class=data["tools_class"],
            task=data["task"],
            instructions=data["instructions"],
            flow_type=ProcessFlowType(data["flow_type"]),
        )

    def create_event_type(
        self, user_id: str, event_name: str, event_description: str
    ) -> Event:
        self.logger.info(
            f"Creating event type {event_name} with description: {event_description} for user: {user_id}"
        )
        response = (
            self.client.table("event_types")
            .insert(
                {
                    "user_id": user_id,
                    "name": event_name,
                    "description": event_description,
                }
            )
            .execute()
            .data
        )
        response = response[0]
        return EventType(
            id=response["id"],
            user_id=user_id,
            name=event_name,
            description=event_description,
        )

    def create_event(
        self, user_id: str, event_name: str, message_name: str, content: str
    ) -> Event:
        self.logger.info(
            f"Creating event {event_name} with content: {content} for user {user_id}"
        )
        response = (
            self.client.rpc(
                "create_event",
                {
                    "p_user_id": user_id,
                    "p_event_name": event_name,
                    "p_message_name": message_name,
                    "p_content": content,
                },
            )
            .execute()
            .data
        )
        response = response[0]
        return Event(
            id=response["id"],
            user_id=user_id,
            name=event_name,
            message_name=message_name,
            content=content,
            status=EventStatus(response["status"]),
            timestamp=response["created_at"],
        )

    def create_event_subscription(
        self, process_id: str, event_name: str
    ) -> EventSubscription:
        self.logger.info(
            f"Creating subscription to event_type: {event_name} process: {process_id}"
        )
        response = (
            self.client.rpc(
                "create_event_subscription",
                {
                    "p_process_id": process_id,
                    "p_event_name": event_name,
                },
            )
            .execute()
            .data[0]
        )
        return EventSubscription(
            user_id=response["returned_user_id"],
            process_id=process_id,
            event_type_id=response["returned_event_type_id"],
            event_name=event_name,
        )

    def create_topic_subscription(
        self,
        process_id: str,
        topic_name: str,
    ) -> TopicSubscription:
        self.logger.info(f"Creating topic subscription for process {process_id}")
        response = (
            self.client.rpc(
                "create_topic_subscription",
                {
                    "p_process_id": process_id,
                    "p_topic_name": topic_name,
                },
            )
            .execute()
            .data[0]
        )
        self.logger.info(
            f"Process {process_id} subscribed to topic {topic_name}. Subscription: {response}"
        )
        return TopicSubscription(
            user_id=response["returned_user_id"],
            process_id=process_id,
            topic_id=response["returned_topic_id"],
            topic_name=topic_name,
        )

    def create_request(
        self,
        user_id: str,
        client_process_id: str,
        client_process_name: str,
        service_name: str,
        query: str,
        is_async: bool,
    ) -> Request:
        self.logger.info(f"Creating request {service_name}")
        response = (
            self.client.rpc(
                "create_request",
                {
                    "p_user_id": user_id,
                    "p_client_process_id": client_process_id,
                    "p_client_process_name": client_process_name,
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
            status=RequestStatus(response["status"]),
            response=response["response"],
        )
        return Request(
            request_id=response["id"],
            service_id=response["service_id"],
            service_process_id=response["service_process_id"],
            client_process_id=client_process_id,
            client_process_name=client_process_name,
            timestamp=response["created_at"],
            data=request_data,
        )

    def create_service(
        self, user_id: str, process_id: str, service_data: ServiceData
    ) -> Service:
        self.logger.info(f"Creating service {service_data.name}")
        service_id = (
            self.client.rpc(
                "create_service",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_name": service_data.name,
                    "p_description": service_data.description,
                },
            )
            .execute()
            .data
        )
        self.logger.info(
            f"New service created at supabase. Name: {service_data.name}, id: {service_id}"
        )
        return Service(service_id=service_id, process_id=process_id, data=service_data)

    def create_topic(
        self, user_id: str, topic_name: str, topic_description: str
    ) -> Topic:
        existing_topic = (
            self.client.table("topics")
            .select("*")
            .eq("user_id", user_id)
            .eq("name", topic_name)
            .execute()
        ).data
        self.logger.info(f"Got existing topic: {existing_topic}")
        if not existing_topic:
            self.logger.info(f"Creating topic {topic_name}")
            existing_topic = (
                self.client.table("topics")
                .insert(
                    {
                        "user_id": user_id,
                        "name": topic_name,
                        "description": topic_description,
                        "content": "",
                    }
                )
                .execute()
                .data
            )
        existing_topic = existing_topic[0]
        return Topic(
            id=existing_topic["id"],
            user_id=user_id,
            topic_name=topic_name,
            description=topic_description,
            content=existing_topic["content"],
            timestamp=existing_topic["updated_at"],
        )

    def clear_conversation_buffer(self, process_id: str):
        response = self.client.rpc(
            "clear_conversation_buffer", {"p_process_id": process_id}
        ).execute()
        return response

    def delete_message(self, message_id):
        response = (
            self.client.rpc("soft_delete_message", {"p_message_id": message_id})
            .execute()
            .data
        )
        return response

    def get_active_messages(self, process_id: str) -> List[ChatMessage]:
        self.logger.info(f"Getting active messages for: {process_id}")
        ordered_messages = (
            self.client.rpc("get_active_messages", {"p_process_id": process_id})
            .execute()
            .data
        )
        self.logger.info(f"Active messages: {str(ordered_messages)}")
        messages = []
        if ordered_messages:
            for row in ordered_messages:
                messages.append(MessagesFactory.create_message(row))
        return messages

    def get_buffered_messages(self, process_id: str) -> List[ChatMessage]:
        self.logger.info(f"Getting buffered messages for: {process_id}")
        ordered_messages = (
            self.client.rpc("get_buffered_messages", {"p_process_id": process_id})
            .execute()
            .data
        )
        self.logger.info(f"Buffered messages: {str(ordered_messages)}")
        messages = []
        if ordered_messages:
            for row in ordered_messages:
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
        topics = self.get_topic_subscriptions(process_id)
        return ProcessCommunications(
            outgoing_requests=outgoing_requests,
            incoming_request=incoming_request,
            topics=topics,
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
            id=data["id"],
            name=data["name"],
            tools_class=data["tools_class"],
            task=data["task"],
            instructions=data["instructions"],
            flow_type=ProcessFlowType(data["flow_type"]),
        )

    def get_process_ids(self, process_id: str) -> Optional[ProcessIds]:
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
        return ProcessIds(
            user_id=data["user_id"],
            agent_id=data["agent_id"],
            process_id=process_id,
        )

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
                status=RequestStatus(row["status"]),
                response=row["response"],
            )
            requests.append(
                Request(
                    request_id=row["id"],
                    service_id=row["service_id"],
                    service_process_id=row["service_process_id"],
                    client_process_id=row["client_process_id"],
                    client_process_name=row["client_process_name"],
                    timestamp=row["created_at"],
                    data=request_data,
                )
            )
        return requests

    def get_topic_subscriptions(self, process_id: str) -> List[Topic]:
        data = (
            self.client.rpc("get_topic_subscriptions", {"p_process_id": process_id})
            .execute()
            .data
        )
        if not data:
            return None
        topics: List[Topic] = []
        for row in data:
            topics.append(
                Topic(
                    id=row["topic_id"],
                    user_id=row["user_id"],
                    topic_name=row["name"],
                    description=row["description"],
                    content=row["content"],
                    timestamp=row["updated_at"],
                )
            )
        return topics

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

    def get_user_data(self, user_id: str) -> Optional[UserData]:
        data = (
            self.client.table("users_data")
            .select("*")
            .eq("user_id", user_id)
            .execute()
            .data
        )
        if not data:
            return None
        user_data = data[0]
        return UserData(
            user_id=user_id,
            user_name=user_data["name"],
            api_key=user_data["api_key"],
        )

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
        self.logger.info(f"Sending message: {content} to user {user_id}")
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
        self.logger.info(f"Database acknowledge: {response}")
        return response

    def set_active_agent(self, agent_id: str, active: bool):
        self.client.table("agents").update({"is_active": active}).eq(
            "id", agent_id
        ).execute()

    def set_request_completed(self, request: Request):
        self.client.table("requests").update(
            {"status": request.data.status.value, "response": request.data.response}
        ).eq("id", request.id).execute()

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

    def update_event(self, event: Event):
        self.client.table("events").update({"status": event.status.value}).eq(
            "id", event.id
        ).execute()

    def update_agent_profile(self, agent_id: str, profile: Dict[str, Any]):
        self.client.table("agents").update({"profile": profile}).eq(
            "id", agent_id
        ).execute()

    def update_request_feedback(self, request: Request):
        self.client.table("requests").update({"feedback": request.data.feedback}).eq(
            "id", request.id
        ).execute()

    def update_request_status(self, request: Request):
        self.client.table("requests").update({"status": request.data.status.value}).eq(
            "id", request.id
        ).execute()

    def update_user_profile(self, user_id: str, profile: Dict[str, Any]):
        self.client.table("profiles").update(profile).eq("user_id", user_id).execute()
