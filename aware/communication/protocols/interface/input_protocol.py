from abc import abstractmethod
from typing import List, Optional

from aware.communication.primitives.interface.input import Input
from aware.communication.protocols.interface.protocol import Protocol


class InputProtocol(Protocol):
    def __init__(self, id: str):
        super().__init__(id=id)

    def get_highest_priority_input(self) -> Optional[Input]:
        highest_priority_input: Optional[Input] = None
        for input in self.get_inputs():
            if (
                highest_priority_input is None
                or input.priority > highest_priority_input.priority
            ):
                highest_priority_input = input
        return highest_priority_input

    @abstractmethod
    def get_inputs(self) -> List[Input]:
        """
        Derived classes must implement this method to return the primitives that will be used in the protocol.
        """
        pass

    @abstractmethod
    def set_input_completed(self):
        """
        Derived classes must implement this method to set the input as completed.
        """
        pass
