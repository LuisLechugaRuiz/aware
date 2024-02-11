import json
from dataclasses import dataclass
from typing import List, Optional

from aware.communications.requests.request import Request
from aware.communications.topics.subscription import TopicSubscription


@dataclass
class ProcessCommunications:
    outgoing_requests: List[Request]
    incoming_request: Optional[Request]
    topic_subscriptions: List[TopicSubscription]

    def to_dict(self):
        return {
            "outgoing_requests": [
                request.to_dict() for request in self.outgoing_requests
            ],
            "incoming_request": (
                self.incoming_request.to_dict() if self.incoming_request else None
            ),
            "topic_subscriptions": [
                topic_subscriptions.to_dict()
                for topic_subscriptions in self.topic_subscriptions
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
        data["topic_subscriptions"] = [
            TopicSubscription(**topic_subscriptions)
            for topic_subscriptions in data["topic_subscriptions"]
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
        if self.topic_subscriptions:
            topic_subscriptions_info = "\n".join(
                [
                    topic_subscriptions.to_string()
                    for topic_subscriptions in self.topic_subscriptions
                ]
            )
            prompt_kwargs.update({"topic_subscriptions": topic_subscriptions_info})
        return prompt_kwargs
