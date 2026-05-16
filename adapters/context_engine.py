"""
Engine adapter — thin shim between the benchmark harness and the
Persistent Context Engine.
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, Literal

# ── Path setup ───────────────────────────────────────────────────────────────
# ContextForge-ASCENT/adapters/ -> one up = ContextForge-ASCENT/ (bench root)
#                               -> two up = Anvil-P-E/          (engine root)
_BENCH_ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ENGINE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_BENCH_SRC   = os.path.join(_BENCH_ROOT,  "src")   # has anvil_benchmark/
_ENGINE_SRC  = os.path.join(_ENGINE_ROOT, "src")   # has memory/, ingestion/, utils/

# The old run-shim may have already loaded ContextForge-ASCENT/src as 'src',
# caching it before we get here. Evict it so src.memory resolves correctly.
_cached_src = sys.modules.get("src")
if _cached_src is not None:
    _cached_src_path = "".join(getattr(_cached_src, "__path__", [""]))
    if _ENGINE_SRC not in _cached_src_path:
        for _k in [k for k in list(sys.modules) if k == "src" or k.startswith("src.")]:
            del sys.modules[_k]

# Insert engine root first so 'src' resolves to Anvil-P-E/src/ (has memory).
# Keep bench src on path too so 'anvil_benchmark' remains importable.
for _p in (_ENGINE_ROOT, _BENCH_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ─────────────────────────────────────────────────────────────────────────────

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
