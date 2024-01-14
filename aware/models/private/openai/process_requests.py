import asyncio

from aware.data.database.client_handlers import ClientHandlers
from aware.models.private.openai.new_openai import OpenAIModel
from aware.server.tasks import process_response
from aware.utils.logger.file_logger import FileLogger


async def process_openai_call(call_id):
    redis_handlers = ClientHandlers().get_redis_handler()
    call_info = redis_handlers.get_call_info(call_id)
    logger = FileLogger(name=call_info.process_name)
    openai_model = OpenAIModel(api_key=call_info.get_api_key(), logger=logger)
    result = await openai_model.get_response(
        conversation=call_info.get_conversation(),
        functions=call_info.functions,
    )
    # Store the result back in the database
    redis_handlers.store_response(call_id, result.model_dump_json())
    # Initialize the celery task
    process_response(response=result.model_dump_json(), call_info=call_info)


async def get_pending_call_ids():
    while True:
        redis_handlers = ClientHandlers().get_redis_handler()
        message = redis_handlers.get_pending_call()

        if message is not None:
            _, call_id = message
            return call_id.decode()


async def main():
    while True:
        call_ids = await get_pending_call_ids()
        for call_id in call_ids:
            asyncio.create_task(process_openai_call(call_id))
        await asyncio.sleep(1)  # TODO: Verify this.


if __name__ == "__main__":
    asyncio.run(main())
