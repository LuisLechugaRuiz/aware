import json
from typing import Any, Dict

from aware.communications.requests.request import Request
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.process.process_handler import ProcessHandler


# TODO: Client should have an id from database so we can track it (Get it based on process ids and use it to schedule the specific request).
class RequestClient:
    def __init__(
        self, process_ids: ProcessIds, id: str, service_id: str, request_message_id: str
    ):
        self.process_ids = process_ids
        self.process_info = ClientHandlers().get_process_info(process_ids=process_ids)

        self.id = id
        self.service_id = service_id
        self.request_message_id = request_message_id
        self.process_handler = ProcessHandler()

    # TODO: This function should be called doing a translation at post model function call to specific request, accessing the right client.
    def create_request(
        self,
        request_message: Dict[str, Any],
        is_async: bool,
    ) -> Request:
        # - Save request in database
        result = ClientHandlers().create_request(
            client_process_ids=self.process_info.process_ids,
            client_process_name=self.process_info.process_data.name,
            service_id=self.service_id,
            request_message=request_message,
            is_async=is_async,
        )
        if result.error:
            return f"Error creating request: {result.error}"

        # - Start the service process if not running
        request = result.data
        service_process_ids = ClientHandlers().get_process_ids(
            process_id=request.service_process_id
        )
        self.process_handler.start(service_process_ids)
        return f"Request {request.id} created successfully"

    def to_dict(self):
        return {
            "process_ids": self.process_ids.to_dict(),
            "id": self.id,
            "service_id": self.service_id,
            "request_message_id": self.request_message_id,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def from_json(json_str: str):
        data = json.loads(json_str)
        data["process_ids"] = ProcessIds.from_json(data["process_ids"])
        return RequestClient(**data)
