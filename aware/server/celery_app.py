from celery import Celery

# Configure Celery application TODO: Add backend?
app = Celery("assistant_tasks", broker="pyamqp://guest@localhost//")

app.conf.update(
    task_routes={
        "assistant.*": {"queue": "assistant_queue"},
        "server.*": {"queue": "server_queue"},
    }
)
app.autodiscover_tasks(["aware.assistant"])
app.autodiscover_tasks(["aware.server"])
