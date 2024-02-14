from celery import Celery

app = Celery("aware", broker="pyamqp://guest@localhost//")

app.conf.update(
    task_routes={
        "server.*": {"queue": "server_queue"},
    }
)
app.autodiscover_tasks(["aware.server"])
