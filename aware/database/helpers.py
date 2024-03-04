from typing import Generic, TypeVar, Optional, Union
from dataclasses import dataclass, field

T = TypeVar("T")


@dataclass
class DatabaseResult(Generic[T]):
    _data: Optional[T] = field(default=None, repr=False, init=False)
    _error: Optional[str] = field(default=None, repr=False, init=False)
    value: Union[T, str]

    def __post_init__(self):
        if self._data is not None and self._error is not None:
            raise ValueError("Both data and error cannot be set.")
        elif self._data is None and self._error is None:
            raise ValueError("Either data or error must be set.")
        self.value = self._data if self._data is not None else self._error

    @property
    def data(self) -> Optional[T]:
        return self._data if self._data is not None else None

    @data.setter
    def data(self, value: T):
        if self._error is not None:
            raise ValueError("Cannot set data because error is already set.")
        self._data = value
        self.value = value

    @property
    def error(self) -> Optional[str]:
        return self._error if self._error is not None else None

    @error.setter
    def error(self, value: str):
        if self._data is not None:
            raise ValueError("Cannot set error because data is already set.")
        self._error = value
        self.value = value
