from typing import Any, Dict

from aware.communications.requests.request import Request
from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.process.process_handler import ProcessHandler


class Client:
    def __init__(self, process_ids: ProcessIds):
        self.process_info = ClientHandlers().get_process_info(process_ids=process_ids)
        self.process_handler = ProcessHandler()

    def create_request(
        self,
        service_name: str,
        request_message: Dict[str, Any],
        is_async: bool,
    ) -> Request:
        # - Save request in database
        request = ClientHandlers().create_request(
            process_ids=self.process_info.process_ids,
            client_process_name=self.process_info.process_data.name,
            service_name=service_name,
            request_message=request_message,
            is_async=is_async,
        )
        # - Start the service process if not running
        service_process_ids = ClientHandlers().get_process_ids(
            process_id=request.service_process_id
        )
        self.process_handler.start(service_process_ids)
        return request
