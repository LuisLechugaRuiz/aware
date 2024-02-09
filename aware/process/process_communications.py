import json
from dataclasses import dataclass
from typing import List, Optional

from aware.communications.requests.request import Request
from aware.communications.events.event import Event
from aware.communications.subscriptions.subscription import Subscription


@dataclass
class ProcessCommunications:
    outgoing_requests: List[Request]
    incoming_request: Optional[Request]
    incoming_event: Optional[Event]
    subscriptions: List[Subscription]

    def to_dict(self):
        return {
            "outgoing_requests": [
                request.to_dict() for request in self.outgoing_requests
            ],
            "incoming_request": (
                self.incoming_request.to_dict() if self.incoming_request else None
            ),
            "incoming_event": (
                self.incoming_event.to_dict() if self.incoming_event else None
            ),
            "subscriptions": [
                subscription.to_dict() for subscription in self.subscriptions
            ],
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
        if data["incoming_event"]:
            data["incoming_event"] = Event(**data["incoming_event"])
        data["subscriptions"] = [
            Subscription(**subscription) for subscription in data["subscriptions"]
        ]
        return ProcessCommunications(**data)

    def to_prompt_kwargs(self):
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
        # TODO: Add events!
        if self.subscriptions:
            subscriptions_info = "\n".join(
                [subscription.to_string() for subscription in self.subscriptions]
            )
            prompt_kwargs.update({"subscriptions": subscriptions_info})
        return prompt_kwargs
