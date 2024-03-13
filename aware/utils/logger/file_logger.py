import logging
import os


class FileLogger(logging.Logger):
    _instances = {}

    def __new__(cls, file_name, *args, **kwargs):
        if file_name in cls._instances:
            return cls._instances[file_name]

        instance = super(FileLogger, cls).__new__(cls)
        cls._instances[file_name] = instance
        return instance

    def __init__(self, file_path, should_print=True, level=logging.NOTSET):
        if getattr(self, "_initialized", False):
            return

        name = os.path.basename(file_path).split(".")[0]  # Extract name from file_path
        super().__init__(name, level)
        self.should_print = should_print

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        self.addHandler(file_handler)

        self._initialized = True

    # TODO: Remove hack when printing by console, might be more relevant when adding the UI.
    def info(self, msg, should_print_local=True, *args, **kwargs):
        super().info(msg, *args, **kwargs)  # This logs to the file
        if self.should_print and should_print_local:
            print(msg)

    def debug(self, msg, should_print_local=True, *args, **kwargs):
        super().debug(msg, *args, **kwargs)
        if self.should_print and should_print_local:
            print(msg)

    def warning(self, msg, should_print_local=True, *args, **kwargs):
        super().warning(msg, *args, **kwargs)
        if self.should_print and should_print_local:
            print(msg)

    def error(self, msg, should_print_local=True, *args, **kwargs):
        super().error(msg, *args, **kwargs)
        if self.should_print and should_print_local:
            print(msg)

    def critical(self, msg, should_print_local=True, *args, **kwargs):
        super().critical(msg, *args, **kwargs)
        if self.should_print and should_print_local:
            print(msg)
