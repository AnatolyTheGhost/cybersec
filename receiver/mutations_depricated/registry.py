from __future__ import annotations

from typing import Iterable

from .adapters import MutationAdapter


class AdapterRegistry:
    """Registry for adapters that can be discovered without hardcoded wiring."""

    def __init__(self) -> None:
        self._adapters: dict[str, MutationAdapter] = {}

    def register(self, adapter: MutationAdapter) -> None:
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> MutationAdapter | None:
        return self._adapters.get(name)

    def remove(self, name: str) -> None:
        self._adapters.pop(name, None)

    def all(self) -> Iterable[MutationAdapter]:
        return self._adapters.values()

    @property
    def names(self) -> list[str]:
        return sorted(self._adapters.keys())
