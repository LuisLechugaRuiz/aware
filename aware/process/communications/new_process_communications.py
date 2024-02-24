import json
from dataclasses import dataclass
from typing import List, Optional

from aware.communications.events.event import Event
from aware.communications.requests.request import Request
from aware.communications.topics.topic import Topic


# "publisher": [],
# "subscriber": [],
# "clients": ["create_team"], //, "assign_task", "talk_to_user" as part of assistant tool.
# "server": [
#     {
#         "name": "inform_user", -> name of service
#         "description": "Send a request to assistant to inform the user about an important event", -> description of service
#         "request": "inform_user", -> name of the request (the structured data)
#         "tool": "inform_user", -> name of the tool to be called, by default NONE for any new agent, but used to call internal tools for some requests.
#     }
# ],
# "event_subscriber": ["user_message"]


# TODO: REFACTOR ME!!! ADD PUBLISHER/SUBSCRIBER/CLIENTS/SERVERS/EVENTS. NOT DEFINED BY THE KIND OF REQUESTS!!!
@dataclass
class ProcessCommunications:
    outgoing_requests: List[Request]
    incoming_request: Optional[Request]
    event: Optional[Event]
    topics: List[Topic]

    def to_dict(self):
        return {
            "outgoing_requests": [
                request.to_dict() for request in self.outgoing_requests
            ],
            "incoming_request": (
                self.incoming_request.to_dict() if self.incoming_request else None
            ),
            "event": self.event.to_dict() if self.event else None,
            "topics": [topic.to_dict() for topic in self.topics],
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        data["outgoing_requests"] = [
            Request(**request) for request in data["outgoing_requests"]
        ]
        if data["incoming_request"]:
            data["incoming_request"] = Request(**data["incoming_request"])
        if data["event"]:
            data["event"] = Event(**data["event"])
        data["topics"] = [Topic(**topic) for topic in data["topics"]]
        return ProcessCommunications(**data)

    def to_prompt_kwargs(self):
        """Show permanent info on the prompt. Don't show event as it will be part of conversation."""
        prompt_kwargs = {}
        if self.outgoing_requests:
            # Add the feedback of all the outgoing requests
            requests_feedback = "\n".join(
                [request.feedback_to_string() for request in self.outgoing_requests]
            )
            prompt_kwargs.update({"outgoing_requests": requests_feedback})
        if self.incoming_request is not None:
            # Add the query of the incoming request
            prompt_kwargs.update(
                {"incoming_request": self.incoming_request.query_to_string()}
            )
        if self.topics:
            topics_info = "\n".join([topic.to_string() for topic in self.topics])
            prompt_kwargs.update({"topics": topics_info})
        return prompt_kwargs
