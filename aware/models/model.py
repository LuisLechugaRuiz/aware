import abc
from openai.types.chat import ChatCompletionMessage


class Model(abc.ABC):
    """Simple interface for models."""

    @abc.abstractmethod
    def get_response(self, *args, **kwargs) -> ChatCompletionMessage:
        """Get a response from the model with variable arguments."""
        pass
