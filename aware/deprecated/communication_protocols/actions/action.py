import abc


class Action(abc.ABC):
    @abc.abstractmethod
    def to_json(self):
        raise NotImplementedError("to_json must be implemented")

    @staticmethod
    @abc.abstractmethod
    def from_json(json_str):
        raise NotImplementedError("from_json must be implemented")
