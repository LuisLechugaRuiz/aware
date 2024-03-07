import json


class CurrentInputMetadata:
    def __init__(self, input_type: str, input_id: str, protocol_id: str):
        self.input_type = input_type
        self.input_id = input_id
        self.protocol_id = protocol_id

    def to_json(self) -> str:
        """Serializes the object to a JSON string."""
        return json.dumps(
            {
                "input_type": self.input_type,
                "input_id": self.input_id,
                "protocol_id": self.protocol_id,
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "CurrentInputMetadata":
        """Deserializes a JSON string to a CurrentInputMetadata object."""
        data = json.loads(json_str)
        return cls(
            input_type=data["input_type"],
            input_id=data["input_id"],
            protocol_id=data["protocol_id"],
        )
