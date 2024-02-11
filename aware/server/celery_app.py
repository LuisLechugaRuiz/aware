from celery import Celery

# Import the tasks to register them
from aware.server.tasks.postprocess import postprocess, process_tool_feedback
from aware.server.tasks.preprocess import preprocess

# Configure Celery application TODO: Add backend?
app = Celery("aware", broker="pyamqp://guest@localhost//")

app.conf.update(
    task_routes={
        "server.*": {"queue": "server_queue"},
    }
)
