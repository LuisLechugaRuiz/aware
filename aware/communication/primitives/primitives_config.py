from dataclasses import dataclass
import json
from typing import List

from aware.communication.primitives import (
    ActionConfig,
    EventConfig,
    RequestConfig,
    TopicConfig
)


@dataclass
class CommunicationPrimitivesConfig:
    action_configs: List[ActionConfig]
    event_configs: List[EventConfig]
    request_configs: List[RequestConfig]
    topic_configs: List[TopicConfig]

    def to_json(self):
        return {
            "action_configs": [action_config.to_json() for action_config in self.action_configs],
            "event_configs": [event_config.to_json() for event_config in self.event_configs],
            "request_configs": [request_config.to_json() for request_config in self.request_configs],
            "topic_configs": [topic_config.to_json() for topic_config in self.topic_configs],
        }

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        data["action_configs"] = [
            ActionConfig.from_json(action_config) for action_config in data["action_configs"]
        ]
        data["event_configs"] = [
            EventConfig.from_json(event_config) for event_config in data["event_configs"]
        ]
        data["request_configs"] = [
            RequestConfig.from_json(request_config) for request_config in data["request_configs"]
        ]
        data["topic_configs"] = [
            TopicConfig.from_json(topic_config) for topic_config in data["topic_configs"]
        ]
        return cls(**data)
