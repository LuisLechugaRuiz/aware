from typing import Callable, Dict, Optional


class TaskExecutor:
    _instance: Optional["TaskExecutor"] = None
    _services: Dict[str, Callable]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskExecutor, cls).__new__(cls)
            cls._instance._services = {}
        return cls._instance

    def register_task(self, task_name, task_func):
        self._services[task_name] = task_func

    def execute_task(self, task_name, *args, **kwargs):
        if task_name in self._services:
            task_func = self._services[task_name]
            # Call celery task.
            task_func.delay(*args, **kwargs)
        else:
            raise ValueError(f"Task {task_name} not registered")
