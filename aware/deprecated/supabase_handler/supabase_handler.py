from supabase import Client
from typing import Any, Dict, List, Optional

from aware.agent.agent_data import (
    AgentData,
    AgentMemoryMode,
    AgentState,
    ThoughtGeneratorMode,
)
from aware.chat.conversation_schemas import ChatMessage, JSONMessage
from aware.agent.agent_communication import Communications
from aware.communication.events.event import Event, EventStatus
from aware.communication.events.event_type import EventType
from aware.communication.events.event_subscriber import EventSubscriber
from aware.communication.events.event_publisher import EventPublisher
from aware.communication.requests.request import Request, RequestData, RequestStatus
from aware.communication.requests.request_service import (
    RequestService,
    RequestServiceData,
)
from aware.communication.requests.request_client import RequestClient
from aware.communication.topics.topic import Topic
from aware.communication.topics.topic_subscriber import TopicSubscriber
from aware.communication.topics.topic_publisher import TopicPublisher
from aware.config.config import Config
from aware.data.database.supabase_handler.messages_factory import MessagesFactory
from aware.memory.user.user_data import UserData
from aware.process.process_data import ProcessData, ProcessFlowType
from aware.process.process_ids import ProcessIds
from aware.process.state_machine.state import ProcessState
from aware.tool.capability import Capability
from aware.agent.agent_profile import Profile
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
        capability_class: str,
        memory_mode: str,
        modalities: List[str],
        thought_generator_mode: str,
    ) -> AgentData:
        self.logger.info(f"Creating agent {name}")
        data = (
            self.client.table("agents")
            .insert(
                {
                    "user_id": user_id,
                    "name": name,
                    "capability_class": capability_class,
                    "memory_mode": memory_mode,
                    "modalities": modalities,
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
            capability_class=data["capability_class"],
            state=AgentState(data["state"]),
            memory_mode=AgentMemoryMode(data["memory_mode"]),
            modalities=data["modalities"],
            thought_generator_mode=ThoughtGeneratorMode(data["thought_generator_mode"]),
        )

    def create_current_process_state(
        self, user_id: str, process_id: str, process_state_id: str
    ) -> ProcessState:
        self.logger.info(f"Creating current process state for process: {process_id}")
        response = (
            self.client.table("current_process_states")
            .insert(
                {
                    "user_id": user_id,
                    "process_id": process_id,
                    "current_state_id": process_state_id,
                }
            )
            .execute()
            .data
        )
        self.logger.info(
            f"Current process state created for process: {process_id}. Response: {response}"
        )

    def create_process(
        self,
        user_id: str,
        agent_id: str,
        name: str,
        capability_class: str,
        flow_type: ProcessFlowType,
        type=ProcessType,
    ) -> ProcessData:
        self.logger.info(f"Creating process {name}")
        data = (
            self.client.table("processes")
            .insert(
                {
                    "user_id": user_id,
                    "agent_id": agent_id,
                    "name": name,
                    "capability_class": capability_class,
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
            capability_class=data["capability_class"],
            flow_type=ProcessFlowType(data["flow_type"]),
        )

    def create_process_state(
        self,
        user_id: str,
        process_id: str,
        name: str,
        task: str,
        instructions: str,
        tools: Dict[str, str],
    ) -> ProcessState:
        self.logger.info(f"Creating process state {name}")
        data = (
            self.client.table("process_states")
            .insert(
                {
                    "user_id": user_id,
                    "process_id": process_id,
                    "name": name,
                    "task": task,
                    "instructions": instructions,
                }
            )
            .execute()
            .data
        )
        data = data[0]
        process_state_id = data["id"]
        self.logger.info(f"Process state: {name}, created.")
        self.logger.info(f"Creating tools for process state: {name}")
        for tool_name, transition_state_name in tools.items():
            data = (
                # TODO: tools is not the right name, should be a transition
                self.client.table("tools")
                .insert(
                    {
                        "user_id": user_id,
                        "process_state_id": process_state_id,
                        "name": tool_name,
                        "transition_state_name": transition_state_name,
                    }
                )
                .execute()
                .data
            )
        return ProcessState(
            id=process_state_id,
            name=name,
            tools=tools,
            task=task,
            instructions=instructions,
        )

    def create_event_type(
        self,
        user_id: str,
        event_name: str,
        event_description: str,
        message_format: Dict[str, Any],
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
                    "message_format": message_format,
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
            message_format=message_format,
        )

    def create_event(self, publisher_id: str, event_message: Dict[str, Any]) -> Event:
        self.logger.info(
            f"Creating event using publisher: {publisher_id} with message: {event_message}"
        )
        response = (
            self.client.rpc(
                "create_event",
                {
                    "p_publisher_id": publisher_id,
                    "p_event_message": event_message,
                },
            )
            .execute()
            .data
        )
        response = response[0]
        return Event(
            id=response["id"],
            user_id=response["user_id"],
            event_type_id=response["event_type_id"],
            event_name=response["event_name"],
            event_description=response["event_description"],
            event_message=event_message,
            event_format=response["message_format"],
            status=EventStatus(response["status"]),
            timestamp=response["created_at"],
        )

    def create_event_subscriber(
        self, user_id: str, process_id: str, event_name: str
    ) -> EventSubscriber:
        self.logger.info(
            f"Creating subscriber to event_type: {event_name} process: {process_id}"
        )
        response = (
            self.client.rpc(
                "create_event_subscriber",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_event_name": event_name,
                },
            )
            .execute()
            .data[0]
        )
        return EventSubscriber(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            event_type_id=response["_event_type_id"],
            event_name=event_name,
            event_description=response["_event_description"],
            event_format=response["_event_format"],
        )

    def create_event_publisher(
        self, user_id: str, process_id: str, event_name: str
    ) -> EventSubscriber:
        self.logger.info(
            f"Creating publisher to event_type: {event_name} process: {process_id}"
        )
        response = (
            self.client.rpc(
                "create_event_publisher",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_event_name": event_name,
                },
            )
            .execute()
            .data[0]
        )
        return EventPublisher(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            event_type_id=response["_event_type_id"],
            event_name=event_name,
            event_description=response["_event_description"],
            event_format=response["_event_format"],
        )

    def create_request(
        self,
        user_id: str,
        service_id: str,
        client_id: str,
        client_process_id: str,
        client_process_name: str,
        request_message: Dict[str, Any],
        priority: int,
        is_async: bool,
    ) -> Request:
        self.logger.info(
            f"Creating request from client process: {client_process_name} to service: {service_id}"
        )
        response = (
            self.client.rpc(
                "create_request",
                {
                    "p_user_id": user_id,
                    "p_service_id": service_id,
                    "p_client_id": client_id,
                    "p_client_process_id": client_process_id,
                    "p_client_process_name": client_process_name,
                    "p_request_message": request_message,
                    "p_priority": priority,
                    "p_is_async": is_async,
                },
            )
            .execute()
            .data
        )
        request_data = RequestData(
            request=response["request"],
            feedback=response["feedback"],
            response=response["response"],
            priority=response["priority"],
            is_async=response["is_async"],
            status=RequestStatus(response["status"]),
        )
        return Request(
            request_id=response["id"],
            service_id=service_id,
            service_process_id=response["service_process_id"],
            client_id=client_id,
            client_process_id=client_process_id,
            client_process_name=client_process_name,
            timestamp=response["created_at"],
            data=request_data,
        )

    def create_request_client(self, user_id: str, process_id: str, service_name: str):
        self.logger.info(f"Creating client for process: {process_id}")
        response = (
            self.client.rpc(
                "create_request_client",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_service_name": service_name,
                },
            )
            .execute()
            .data[0]
        )
        self.logger.info(
            f"Client created for process: {process_id}. Response: {response}"
        )
        return RequestClient(
            user_id=user_id,
            process_id=process_id,
            process_name=["_process_name"],
            client_id=response["_id"],
            service_id=response["_service_id"],
            service_name=service_name,
            service_description=response["_service_description"],
            request_format=response["_request_format"],
        )

    def create_request_service(
        self,
        user_id: str,
        process_id: str,
        service_name: str,
        service_description: str,
        request_name: str,
        tool_name: Optional[str],
    ) -> RequestService:
        self.logger.info(f"Creating request service {service_name}")
        response = (
            self.client.rpc(
                "create_request_service",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_name": service_name,
                    "p_description": service_description,
                    "p_request_name": request_name,
                    "p_tool_name": tool_name,
                },
            )
            .execute()
            .data
        )
        service_data = RequestServiceData(
            service_name=service_name,
            service_description=service_description,
            request_format=response["_request_format"],
            feedback_format=response["_feedback_format"],
            response_format=response["_response_format"],
            tool_name=tool_name,
        )
        service_id = response["_id"]
        self.logger.info(
            f"New service created at supabase. Name: {service_name}, id: {service_id}"
        )
        return RequestService(
            user_id=user_id,
            process_id=process_id,
            service_id=service_id,
            data=service_data,
            requests=[],
        )

    def create_request_type(
        self,
        user_id: str,
        request_name: str,
        request_format: Dict[str, str],
        feedback_format: Dict[str, str],
        response_format: Dict[str, str],
    ):
        self.logger.info(f"Creating request type {request_name}")
        response = (
            self.client.table("request_types")
            .insert(
                {
                    "user_id": user_id,
                    "name": request_name,
                    "request_format": request_format,
                    "feedback_format": feedback_format,
                    "response_format": response_format,
                }
            )
            .execute()
            .data
        )
        response = response[0]
        return response

    # TODO: call it properly to initialize topics.
    def create_topic(
        self,
        user_id: str,
        topic_name: str,
        topic_description: str,
        message_format: Dict[str, str],
        agent_id: Optional[str] = None,
        is_private: bool = False,
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
            if agent_id is not None:
                new_topic_dict = {
                    "agent_id": agent_id,
                }
            else:
                new_topic_dict = {}

            self.logger.info(f"Creating topic {topic_name}")
            new_topic_dict.update(
                {
                    "user_id": user_id,
                    "name": topic_name,
                    "description": topic_description,
                    "message_format": message_format,
                    "is_private": is_private,
                }
            )

            existing_topic = (
                self.client.table("topics").insert(new_topic_dict).execute().data
            )
        existing_topic = existing_topic[0]
        return Topic(
            id=existing_topic["id"],
            user_id=user_id,
            name=topic_name,
            description=topic_description,
            message=existing_topic["message"],
            message_format=message_format,
            timestamp=existing_topic["updated_at"],
        )

    def create_topic_publisher(
        self,
        user_id: str,
        process_id: str,
        topic_name: str,
    ) -> TopicPublisher:
        self.logger.info(f"Creating topic publisher for process {process_id}")
        response = (
            self.client.rpc(
                "create_topic_publisher",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_topic_name": topic_name,
                },
            )
            .execute()
            .data[0]
        )
        self.logger.info(f"Process {process_id} published to topic {topic_name}.")
        return TopicPublisher(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            topic_id=response["_topic_id"],
            topic_name=topic_name,
            topic_description=response["_topic_description"],
            message_format=response["_message_format"],
        )

    def create_topic_subscriber(
        self,
        user_id: str,
        process_id: str,
        topic_name: str,
    ) -> TopicSubscriber:
        self.logger.info(f"Creating topic subscription for process {process_id}")
        response = (
            self.client.rpc(
                "create_topic_subscriber",
                {
                    "p_user_id": user_id,
                    "p_process_id": process_id,
                    "p_topic_name": topic_name,
                },
            )
            .execute()
            .data[0]
        )
        self.logger.info(f"Process {process_id} subscribed to topic {topic_name}.")
        return TopicSubscriber(
            id=response["_id"],
            user_id=user_id,
            process_id=process_id,
            topic_id=response["_topic_id"],
            topic_name=topic_name,
            topic_description=response["_topic_description"],
            message_format=response["_message_format"],
            topic=self.get_topic(user_id, topic_name),
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

    def get_current_process_state(self, process_id: str) -> ProcessState:
        current_process_state = (
            self.client.rpc("get_current_process_state", {"p_process_id": process_id})
            .execute()
            .data
        )
        tools = (
            self.client.rpc("get_tools", {"p_process_id": process_id}).execute().data
        )
        process_tools = {}
        for tool in tools:
            process_tools[tool["name"]] = tool["transition_state_name"]

        return ProcessState(
            name=current_process_state["name"],
            tools=process_tools,
            task=current_process_state["task"],
            instructions=current_process_state["instructions"],
        )

    # def get_process_service_requests(self, process_id: str) -> List[Request]:
    #     data = (
    #         self.client.table("services")
    #         .select("*")
    #         .eq("process_id", process_id)
    #         .execute()
    #         .data
    #     )
    #     requests = []
    #     if not data:
    #         return requests
    #     for row in data:
    #         requests.extend(
    #             self.get_requests(
    #                 key_process_id="service_process_id", process_id=row["id"]
    #             )
    #         )
    #     return requests

    def get_communications(self, process_id: str) -> Communications:
        return Communications(
            topic_publishers=self.get_topic_publishers(process_id),
            topic_subscribers=self.get_topic_subscribers(process_id),
            request_clients=self.get_request_clients(process_id),
            request_services=self.get_request_services(process_id),
            event_subscribers=self.get_event_subscribers(process_id),
        )

        # TODO: Refactor request system instead of client_process_id and service_process_id.
        # outgoing_requests = self.get_requests(
        #     key_process_id="client_process_id", process_id=process_id
        # )
        # incoming_requests = self.get_requests(
        #     key_process_id="service_process_id", process_id=process_id
        # )
        # if len(incoming_requests) > 0:
        #     incoming_request = incoming_requests[0]
        # else:
        #     incoming_request = None
        # topics = self.get_subscribed_topics(process_id)
        # return Communications(
        #     outgoing_requests=outgoing_requests,
        #     incoming_request=incoming_request,
        #     topics=topics,
        # )

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
            capability_class=data["capability_class"],
            flow_type=ProcessFlowType(data["flow_type"]),
            type=data["type"],
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

    def get_process_states(self, process_id: str) -> List[ProcessState]:
        data = (
            self.client.table("process_states")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        process_states = []
        if not data:
            return process_states
        for row in data:
            process_states.append(
                ProcessState(
                    name=row["name"],
                    tools=row["tools"],
                    task=row["task"],
                    instructions=row["instructions"],
                )
            )
        return process_states

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
                request=row["request"],
                feedback=row["feedback"],
                response=row["response"],
                is_async=row["is_async"],
                status=RequestStatus(row["status"]),
            )
            requests.append(
                # TODO: define if we need tool again.
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

    def get_event_subscribers(self, process_id: str) -> List[EventSubscriber]:
        data = (
            self.client.table("event_subscribers")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        event_subscribers = []
        if not data:
            return event_subscribers
        for row in data:
            event_type_id = row["event_type_id"]
            # TODO: implement me!
            events = self.get_events(event_type_id)
            event_subscribers.append(
                EventSubscriber(
                    id=row["id"],
                    user_id=row["user_id"],
                    process_id=process_id,
                    event_type_id=row["event_type_id"],
                    event_name=row["event_name"],
                    event_description=row["event_description"],
                    event_format=row["event_format"],
                ).add_events(events)
            )
        return event_subscribers

    def get_request_clients(self, process_id: str) -> Dict[str, RequestClient]:
        data = (
            self.client.table("request_clients")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        request_clients = {}
        if not data:
            return request_clients
        for row in data:
            service_name = row["service_name"]
            requests = self.get_requests(
                key_process_id="client_process_id", process_id=process_id
            )
            request_clients[service_name] = RequestClient(
                user_id=row["user_id"],
                process_id=process_id,
                process_name=row["name"],
                client_id=row["id"],
                service_id=row["service_id"],
                service_name=service_name,
                service_description=row["service_description"],
                request_format=row["request_format"],
            ).add_requests(requests)
        return request_clients

    def get_request_services(self, process_id: str) -> Dict[str, RequestService]:
        data = (
            self.client.table("request_services")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        request_services = {}
        if not data:
            return request_services
        for row in data:
            service_name = row["name"]
            requests = self.get_requests(
                key_process_id="service_process_id", process_id=process_id
            )
            request_services[service_name] = RequestService(
                user_id=row["user_id"],
                process_id=process_id,
                service_id=row["id"],
                data=RequestServiceData(
                    service_name=service_name,
                    service_description=row["description"],
                    request_format=row["request_format"],
                    feedback_format=row["feedback_format"],
                    response_format=row["response_format"],
                    tool_name=row["tool_name"],
                ),
            ).add_requests(requests)
        return request_services

    def get_topic_publishers(self, process_id: str) -> Dict[str, TopicPublisher]:
        data = (
            self.client.table("topic_publishers")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        topic_publishers = {}
        if not data:
            return topic_publishers
        for row in data:
            topic_name = row["topic_name"]
            topic_publishers[topic_name] = TopicPublisher(
                id=row["id"],
                user_id=row["user_id"],
                process_id=process_id,
                topic_id=row["topic_id"],
                topic_name=topic_name,
                topic_description=row["topic_description"],
                message_format=row["message_format"],
            )
        return topic_publishers

    def get_topic_subscribers(self, process_id: str) -> Dict[str, TopicSubscriber]:
        data = (
            self.client.table("topic_subscribers")
            .select("*")
            .eq("process_id", process_id)
            .execute()
            .data
        )
        topic_subscribers = {}
        if not data:
            return topic_subscribers
        for row in data:
            topic_name = row["topic_name"]
            topic_subscribers[topic_name] = TopicSubscriber(
                id=row["id"],
                user_id=row["user_id"],
                process_id=process_id,
                topic_id=row["topic_id"],
                topic_name=topic_name,
                topic_description=row["topic_description"],
                message_format=row["message_format"],
                topic=self.get_topic(row["user_id"], topic_name),
            )
        return topic_subscribers

    # def get_request_service(self, service_id: str) -> RequestService:
    #     data = (
    #         self.client.table("request_services")
    #         .select("*")
    #         .eq("id", service_id)
    #         .execute()
    #         .data
    #     )
    #     if not data:
    #         return None
    #     data = data[0]
    #     return RequestService(
    #         user_id=data["user_id"],
    #         process_id=data["process_id"],
    #         service_id=service_id,
    #         data=RequestServiceData(
    #             service_name=data["name"],
    #             service_description=data["description"],
    #             request_format=data["request_format"],
    #             feedback_format=data["feedback_format"],
    #             response_format=data["response_format"],
    #             tool_name=data["tool_name"],
    #         ),
    #     )

    # TODO: refactor, get topics from subscribers.
    def get_subscribed_topics(self, process_id: str) -> List[Topic]:
        data = (
            self.client.rpc("get_subscribed_topics", {"p_process_id": process_id})
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
                    message_id=row["topic_message_id"],
                    name=row["name"],
                    description=row["description"],
                    message=row["message"],
                    timestamp=row["updated_at"],
                )
            )
        return topics

    def get_topic(self, user_id: str, name: str):
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
        return Topic(
            id=data["id"],
            user_id=user_id,
            name=name,
            description=data["description"],
            message=data["message"],
            message_format=data["message_format"],
            timestamp=data["updated_at"],
        )

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

    def update_current_process_state(self, process_id: str, process_state_id: str):
        self.client.table("current_process_states").update(
            {"current_state_id": process_state_id}
        ).eq("process_id", process_id).execute()

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
