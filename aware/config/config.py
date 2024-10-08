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
        self.conversation_warning_threshold = 0.1  # 0.8  # TODO: Define this value.

        self.conversation_timeout_sec = 240
        self.task_timeout_sec = 600

        # Capabilities
        self.max_iterations = 10

        # Weaviate
        # Only local for now.
        self.local_weaviate_url = os.getenv(
            "LOCAL_WEAVIATE_URL", "localhost"
        )  # TODO: Remove after moving to cloud
        self.weaviate_port = os.getenv("WEAVIATE_PORT", 9090)

        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate")
        self.weaviate_key = os.getenv("WEAVIATE_KEY")

        # IPS
        self.system_ip = os.getenv("SYSTEM_IP", "127.0.0.1")
        self.assistant_ip = os.getenv("ASSISTANT_IP", "127.0.0.1")
        self.user_ip = os.getenv("USER_IP", "127.0.0.1")

        # Ports
        self.sub_port = os.getenv("SUB_PORT", 50001)
        self.pub_port = os.getenv("PUB_PORT", 50002)
        self.client_port = os.getenv("CLIENT_PORT", 50003)
        self.server_port = os.getenv("SERVER_PORT", 50004)
        self.action_client_port = os.getenv("ACTION_CLIENT_PORT", 50005)
        self.action_server_port = os.getenv("ACTION_SERVER_PORT", 50006)

        self.web_socket_port = os.getenv("WEB_SOCKET_PORT", 50010)

        # SUPABASE
        self.supabase_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        # REDIS
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = os.getenv("REDIS_PORT", 6379)

        # MODEL
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4-0125-preview")
        self.aware_model = os.getenv("AWARE_MODEL", "aware-1.0")
