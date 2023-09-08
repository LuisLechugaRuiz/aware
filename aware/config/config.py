import abc
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Singleton(abc.ABCMeta, type):
    """
    Singleton metaclass for ensuring only one instance of a class.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    """
    Configuration class to store the state of bools for different scripts access.
    """

    def __init__(self):
        # KEYS
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # Weaviate
        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate")
        self.local_weaviate_url = os.getenv(
            "LOCAL_WEAVIATE_URL", "http://localhost"
        )  # TODO: Remove after moving to cloud
        self.weaviate_port = os.getenv("WEAVIATE_PORT", "9090")
        self.weaviate_key = os.getenv("WEAVIATE_KEY")

        # TODO: Add here IPs and ports.
