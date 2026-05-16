"""
Engine adapter — thin shim between the benchmark harness and the
Persistent Context Engine.
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, Literal

# Add repository roots to path so both `anvil_benchmark` and any
# implementation package under `src.*` remain importable.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_ROOT = os.path.join(_PROJECT_ROOT, "src")
for _path in (_PROJECT_ROOT, _SRC_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from anvil_benchmark.adapter import Adapter
from anvil_benchmark.schema import Context, Event, IncidentSignal
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
