"""
Engine adapter — thin shim between the benchmark harness and the
Persistent Context Engine.
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, Literal

# Add project root to path so `src` is importable
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from adapter import Adapter
from schema import Context, Event, IncidentSignal
from src.memory.substrate import MemorySubstrate


class Engine(Adapter):
    """ANVIL P-02 Persistent Context Engine adapter."""

    def __init__(self) -> None:
        self.store = MemorySubstrate()

    def ingest(self, events: Iterable[Event]) -> None:
        for e in events:
            self.store.consume(e)

    def reconstruct_context(
        self,
        signal: IncidentSignal,
        mode: Literal["fast", "deep"] = "fast",
    ) -> Context:
        return self.store.reconstruct(signal, mode=mode)  # type: ignore[return-value]

    def close(self) -> None:
        self.store.shutdown()
