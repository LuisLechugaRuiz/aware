from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class WeaviateCategory:
    name: str
    description: str


@dataclass
class WeaviateTool:
    name: str
    description: str


@dataclass
class WeaviateResult:
    data: Optional[Any] = None
    error: Optional[str] = None
