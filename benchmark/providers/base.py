"""Abstract provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewResult:
    provider: str
    case_id: str
    review_text: str
    metadata: dict


class Provider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def review(self, prompt: str, case_id: str) -> ReviewResult: ...

    @abstractmethod
    def is_available(self) -> bool: ...
