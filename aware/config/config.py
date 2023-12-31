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
        # OPENAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_num_retries = os.getenv("OPENAI_NUM_RETRIES", 3)

        self.assistant_name = os.getenv("ASSISTANT_NAME", "Aware")

        # Memory
        self.max_conversation_tokens = 2000  # TODO: Define this value.
        self.conversation_warning_threshold = 0.8  # TODO: Define this value.

        self.max_short_term_memory_tokens = 2000  # TODO: Define this value.
        self.max_long_term_memory_tokens = 1000  # TODO: Define this value.

        # Weaviate
        # Only local for now.
        self.local_weaviate_url = os.getenv(
            "LOCAL_WEAVIATE_URL", "localhost"
        )  # TODO: Remove after moving to cloud
        self.weaviate_port = os.getenv("WEAVIATE_PORT", 9090)

        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate")
        self.weaviate_key = os.getenv("WEAVIATE_KEY")

        # TODO: Add here IPs and ports.
