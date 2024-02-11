from aware.data.database.client_handlers import ClientHandlers
from aware.process.process_ids import ProcessIds
from aware.server.celery_app import celery_app


# ENTRY POINT!
@celery_app.task(name="server.preprocess")
def preprocess(process_ids_str: str):
    process_ids = ProcessIds.from_json(process_ids_str)

    ClientHandlers().add_active_process(process_ids.process_id)
    process = ClientHandlers().get_process(process_ids.process_id)
    process.preprocess()
