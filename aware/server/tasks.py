from typing import Dict

from aware.data.database.client_handlers import ClientHandlers
from aware.process import Process, ProcessIds
from aware.server.celery_app import app


@app.task(name="handle_request")
def handle_request(user_id: str, process_id: str, service_name: str, query: str):
    redis_handler = ClientHandlers().get_redis_handler()
    server_process = redis_handler.get_server_process(user_id, service_name)

    # Now trigger server adding the specific request (This will add a set_request_completed tool to the process)
    server_process.add_request(
        user_id, process_id, service_name, query
    )  # TODO: CLARIFY THIS, IT SHOULD HAVE THIS INFO FOR LATER WHEN CALLED set_request_completed to be able to redirect it to the correct process

    # TODO: Define triggers - It should be general purpose function.
    server_process.trigger()


# ENTRY POINT!
@app.task(name="process")
def process(user_id: str, agent_id: str, process_id: str, extra_kwargs: Dict[str, str]):
    process_ids = ProcessIds(user_id=user_id, agent_id=agent_id, process_id=process_id)
    process_data = ClientHandlers().get_process_data(process_ids)
    process = Process(process_data=process_data)
    # 1. Verify if process has requests / events.
    # In case of requests adapt the tool with the possibility of set_request_completed - Should update the request status.
    # In case of event adapt the tool with the possibility of clear_event - Should update the event status.

    .preprocess(
        process_data=process_data, extra_kwargs=extra_kwargs
    )
