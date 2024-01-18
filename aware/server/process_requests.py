import asyncio

from aware.data.database.client_handlers import ClientHandlers
from aware.models.private.openai.new_openai import OpenAIModel
from aware.system.tasks import process_response
from aware.utils.logger.file_logger import FileLogger


async def process_openai_call(call_id):
    logger = FileLogger(name="migration_tests")
    redis_handlers = ClientHandlers().get_async_redis_handler()
    call_info = await redis_handlers.get_call_info(call_id)
    # logger = FileLogger(name=call_info.process_name)
    logger.info("Getting response...")
    try:
        openai_model = OpenAIModel(api_key=call_info.get_api_key(), logger=logger)
        result = await openai_model.get_response(
            messages=call_info.get_conversation_messages(),
            functions=call_info.functions,
        )
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Error getting response from OpenAI: {e}")
        raise e
    # Store the result back in the database TODO: MOVE TO PROCESS_REQUEST TO DO THIS PROPERLY.
    await redis_handlers.store_response(call_id, result.model_dump_json())
    # Initialize the celery task
    process_response.delay(result.model_dump_json(), call_info.to_json())


async def get_pending_call_id():
    while True:
        redis_handlers = ClientHandlers().get_async_redis_handler()
        message = await redis_handlers.get_pending_call()

        if message is not None:
            _, call_id = message
            return call_id


async def main():
    task_queue = asyncio.Queue()
    workers = []

    async def worker():
        while True:
            call_id = await task_queue.get()
            try:
                await process_openai_call(call_id)
            except Exception as e:
                # handle exceptions
                print(f"Error processing call {call_id}: {e}")
            finally:
                task_queue.task_done()

    async def manage_workers():
        while True:
            # Adjust these numbers based on your system's capabilities and task characteristics
            max_workers = 100
            target_queue_size_per_worker = 10

            # Scale workers based on queue size
            desired_workers = min(
                max_workers, max(1, task_queue.qsize() // target_queue_size_per_worker)
            )
            current_workers = len(workers)

            if current_workers < desired_workers:
                for _ in range(desired_workers - current_workers):
                    new_worker = asyncio.create_task(worker())
                    workers.append(new_worker)
            elif current_workers > desired_workers:
                for _ in range(current_workers - desired_workers):
                    worker_to_cancel = workers.pop()
                    worker_to_cancel.cancel()

            await asyncio.sleep(5)  # Check periodically

    async def enqueue_pending_calls():
        while True:
            call_id = await get_pending_call_id()
            await task_queue.put(call_id)
            await asyncio.sleep(0.1)  # Prevent tight loop, adjust as needed

    worker_manager = asyncio.create_task(manage_workers())
    enqueuer = asyncio.create_task(enqueue_pending_calls())

    await asyncio.gather(worker_manager, enqueuer)


if __name__ == "__main__":
    asyncio.run(main())
