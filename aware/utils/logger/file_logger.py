import logging
import os

from aware.permanent_storage.permanent_storage import get_permanent_storage_path


class FileLogger(logging.Logger):
    _instances = {}  # A class-level attribute used to store unique instances

    def __new__(cls, name, *args, **kwargs):
        # If an instance with this name exists, return it
        if name in cls._instances:
            return cls._instances[name]

        # Create a new instance because one doesn't exist
        instance = super(FileLogger, cls).__new__(cls)
        cls._instances[name] = instance
        return instance

    def __init__(self, name, should_print=True, level=logging.NOTSET):
        # If we have already initialized this instance, we don't want to do it again
        if getattr(self, "_initialized", False):
            return

        super().__init__(name, level)
        self.should_print = should_print

        # File handler setup
        logger_path = os.path.join(get_permanent_storage_path(), "logs", f"{name}.log")
        os.makedirs(os.path.dirname(logger_path), exist_ok=True)
        file_handler = logging.FileHandler(logger_path)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        self.addHandler(file_handler)

        # TODO: ADD CONSOLE LOGGER!
        # self.console_logger = ConsoleLogger(name)

        self._initialized = True

    # TODO: Remove hack when printing by console, might be more relevant when adding the UI.
    def info(self, msg, should_print_local=True, *args, **kwargs):
        super().info(msg, *args, **kwargs)  # This logs to the file
        if self.should_print and should_print_local:
            print(msg)

    def debug(self, msg, *args, **kwargs):
        super().debug(msg, *args, **kwargs)
        if self.should_print:
            print(msg)

    def warning(self, msg, *args, **kwargs):
        super().warning(msg, *args, **kwargs)
        if self.should_print:
            print(msg)

    def error(self, msg, *args, **kwargs):
        super().error(msg, *args, **kwargs)
        if self.should_print:
            print(msg)

    def critical(self, msg, *args, **kwargs):
        super().critical(msg, *args, **kwargs)
        if self.should_print:
            print(msg)
