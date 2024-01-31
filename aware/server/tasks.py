from typing import Dict

from aware.data.database.client_handlers import ClientHandlers
from aware.process.process import Process
from aware.process.process_ids import ProcessIds
from aware.server.celery_app import app


# ENTRY POINT!
# TODO: HOW TO SERIALIZE - DESERIALIZE EXTRA KWARGS?
@app.task(name="trigger_process")
def trigger_process(process_ids_str: str, extra_kwargs: Dict[str, str] = {}):
    process_ids = ProcessIds.from_json(process_ids_str)
    process_data = ClientHandlers().get_process_data(process_ids)
    Process(process_data=process_data).preprocess(extra_kwargs=extra_kwargs)
