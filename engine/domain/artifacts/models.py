import uuid
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, eq=False)
class Artifact:
    """
    Base abstraction for all addressable artifacts.
    """
    id: str
    stable_key: str
    kind: str
    file: str
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Artifact):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

