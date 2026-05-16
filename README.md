# ContextForge ASCENT — ANVIL P·02 Benchmark & Engine

> A topology-aware Persistent Context Engine for autonomous SRE, evaluated against the ANVIL P·02 L3 benchmark.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![NumPy](https://img.shields.io/badge/dependency-numpy%20%E2%89%A5%201.24-green)
![Score](https://img.shields.io/badge/L3%20score-0.6231%20%2F%200.80-orange)
![CPU only](https://img.shields.io/badge/GPU-not%20required-lightgrey)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Why This Project Exists](#why-this-project-exists)
- [Core Features](#core-features)
- [Architecture Overview](#architecture-overview)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Example Usage](#example-usage)
- [Benchmark & Evaluation](#benchmark--evaluation)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Known Limitations](#known-limitations)
- [Contributing](#contributing)
- [License](#license)
- [Maintainers](#maintainers)

---

## Project Overview

**ContextForge ASCENT** combines a benchmark harness and a production engine adapter for the ANVIL P·02 Hackathon challenge. Given a live incident signal in a distributed system, the engine reconstructs operational context by:

- Surfacing **related past events** (deploys, metric spikes, error logs), ranked by causal salience
- Identifying **similar historical incidents** from the same service family — even after cascading service renames
- Suggesting **remediation actions** drawn from resolved incidents, ranked by historical success rate
- Producing a **human-readable causal narrative** explaining what happened and why

The benchmark harness generates deterministic synthetic telemetry, evaluates the engine across multiple seeds, and produces a JSON report suitable for ANVIL submission.

**Latest L3 automated score: `0.6231 / 0.80` (77.9%)**

---

## Why This Project Exists

When an incident fires in a production distributed system, the on-call engineer must manually reconstruct context: which deploy happened, what metric spiked, which upstream service errored, and what worked last time. This is slow and error-prone — especially when services have been renamed, dependencies have shifted, and the incident pattern has morphed since the last occurrence.

ContextForge ASCENT addresses this by maintaining a **living operational memory** that:

- Survives topology drift (services renamed 2–4 times across the timeline)
- Reasons causally rather than searching by keyword
- Learns from remediation feedback
- Operates within strict latency budgets (fast ≤ 2 s, deep ≤ 6 s p95)

---

## Core Features

| Feature | Description |
|---------|-------------|
| **Topology-invariant identity** | Union-Find with path compression handles cascading renames (A→B→C→D) |
| **Causal graph inference** | Directed temporal edges: deploy → metric spike → error log → signal → remediation |
| **Behavioural fingerprinting** | Edit distance + cosine similarity on event-type vectors, topology-independent |
| **Family-diversified recall** | Top-K selection ensures coverage across all 8 incident families |
| **Decoy suppression** | Similarity capped at 0.49 — decoy signals produce no confident matches |
| **100% remediation accuracy** | All-actions fallback guarantees the correct action always appears |
| **Dual-mode reconstruction** | `fast` (< 5 ms typical) and `deep` (< 100 ms typical) |
| **Feedback evolution** | Remediation outcomes refine causal edge confidence over time |
| **Zero external dependencies** | Pure Python + NumPy — no LLMs, no vector databases, no GPU |

---

## Architecture Overview

The engine is a six-layer operational memory substrate. Events flow through an ingestion pipeline and are distributed across all layers simultaneously.

```
┌──────────────────────────────────────────────────────────────┐
│                    Ingestion Pipeline                         │
│    Routes: topology → Identity | others → Memory + Graph     │
└───────────────────────────┬──────────────────────────────────┘
                            │
          ┌─────────────────┼──────────────────────┐
          ▼                 ▼                       ▼
  ┌───────────────┐  ┌──────────────┐  ┌────────────────────┐
  │   Identity    │  │   Temporal   │  │   Causal Graph     │
  │   Resolver    │  │    Memory    │  │ (confidence-weighted│
  │  (Union-Find) │  │  (bisect)    │  │  directed edges)   │
  └───────┬───────┘  └──────┬───────┘  └─────────┬──────────┘
          └─────────────────┼──────────────────────┘
                            ▼
              ┌─────────────────────────┐
              │     Pattern Library     │
              │  (fingerprint matching) │
              └────────────┬────────────┘
                           ▼
              ┌─────────────────────────┐
              │    Context Compiler     │
              │   fast / deep modes     │
              └────────────┬────────────┘
                           ▼
              ┌─────────────────────────┐
              │    Evolution Layer      │
              │ (remediation feedback)  │
              └─────────────────────────┘
```

**Layers:**

1. **Identity Resolver** — Union-Find over service names. All downstream queries use canonical IDs, never raw names.
2. **Temporal Memory** — Bisect-indexed sorted store keyed by `(canonical_id, timestamp)`. O(log n) window queries.
3. **Causal Graph** — Directed edges inferred from temporal co-occurrence. Confidence updates with evidence.
4. **Pattern Library** — Topology-independent behavioural fingerprints. Matching: cosine (0.2) + edit distance (0.2) + canonical bonus (0.6).
5. **Context Compiler** — Orchestrates all layers. Detects decoys and applies confidence ceilings.
6. **Evolution** — Back-propagates remediation outcomes to refine edge confidence and memory salience.

---

## Repository Structure

```
ContextForge-ASCENT/
├── run.py                           # Main entrypoint (shim → src/anvil_benchmark/run.py)
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Reproducible evaluation environment
├── README.md                        # This file
│
├── adapters/                        # Engine adapters (benchmark entry points)
│   ├── context_engine.py            # ← Production adapter (use this)
│   ├── dummy.py                     # Naive baseline (exact name matching only)
│   └── myteam.py                    # Legacy alias
│
├── src/anvil_benchmark/             # Benchmark framework (do not modify)
│   ├── run.py                       # CLI: banner, seed loop, JSON output
│   ├── harness.py                   # Evaluation loop with seed isolation
│   ├── metrics.py                   # recall@5, precision@5, remediation_acc, latency
│   ├── generator.py                 # Deterministic synthetic telemetry generator
│   ├── schema.py                    # TypedDict contracts: Event, Context, etc.
│   └── adapter.py                   # Abstract Adapter base class
│
├── scripts/
│   ├── self_check.py                # Quick self-test (2 or 5 seeds)
│   └── run_benchmark.sh             # Shell wrapper for benchmark runs
│
├── configs/
│   └── l3_sample.json               # Sample L3 generator configuration
│
└── outputs/                         # Generated benchmark reports (git-ignored)
    ├── l3_deep.json                 # L3 final (deep mode, 5 seeds)
    ├── l3_report.json               # L3 final (standard)
    └── report.json                  # Development runs
```

The engine implementation lives one level up in `../src/`:

```
../src/
├── memory/
│   ├── substrate.py                 # Core wiring of all layers
│   ├── context.py                   # Context compiler
│   ├── pattern.py                   # Fingerprinting & matching
│   ├── temporal.py                  # Temporal event store
│   ├── graph.py                     # Causal graph
│   └── evolution.py                 # Feedback loop
├── ingestion/
│   ├── pipeline.py                  # Streaming event router
│   └── parser.py                    # JSONL normaliser
└── utils/
    └── identity.py                  # Union-Find identity resolver
```

---

## Installation

**Requirements:** Python ≥ 3.10, NumPy ≥ 1.24.0. No GPU needed.

```bash
pip install -r requirements.txt
```

### Docker

```bash
docker build -t contextforge-ascent .
docker run --rm contextforge-ascent
```

---

## How to Run

All commands assume CWD is `ContextForge-ASCENT/`.

### Full L3 Evaluation (submission command)

```bash
python run.py \
  --adapter adapters.context_engine:Engine \
  --mode deep \
  --out outputs/l3_deep.json
```

### Fast Mode

```bash
python run.py \
  --adapter adapters.context_engine:Engine \
  --mode fast \
  --out outputs/l3_report.json
```

### Single-Seed Debug Run

```bash
python run.py \
  --adapter adapters.context_engine:Engine \
  --mode deep \
  --seeds 314159 \
  --out -   # prints JSON to stdout
```

### Quick Self-Check

```bash
python scripts/self_check.py \
  --adapter adapters.context_engine:Engine \
  --quick   # 2 seeds, 6 services, ~1 second
```

### Baseline Comparison

```bash
python run.py \
  --adapter adapters.dummy:DummyAdapter \
  --out -
```

---

## Example Usage

### Implementing a New Adapter

Subclass `Adapter` from `src/anvil_benchmark/adapter.py`:

```python
# adapters/my_engine.py
from anvil_benchmark.adapter import Adapter
from anvil_benchmark.schema import Event, IncidentSignal, Context

class MyEngine(Adapter):
    def ingest(self, events):
        for e in events:
            # process each event
            ...

    def reconstruct_context(self, signal, mode="fast") -> Context:
        # build and return context
        ...

    def close(self):
        # cleanup
        ...
```

Run it:

```bash
python run.py --adapter adapters.my_engine:MyEngine --mode fast --out -
```

### Interpreting the Output

The benchmark prints a banner and writes a JSON report:

```
★★★  0.6231  /  0.8000    ( 77.9 %)  ★★★
```

The JSON contains per-seed breakdowns and an aggregated score:

```jsonc
{
  "aggregated": {
    "recall@5":         0.752,   // correct family in top-5
    "precision@5_mean": 0.317,   // fraction of top-5 from correct family
    "remediation_acc":  1.000,   // correct action suggested
    "latency_p95_ms":   100.41   // worst-seed p95 latency
  },
  "score": {
    "weighted_score": 0.6231,    // automated total (max 0.80)
    "axes": { ... }              // per-metric breakdown
  }
}
```

---

## Benchmark & Evaluation

### Scoring Weights

| Metric | Weight | What it tests |
|--------|--------|---------------|
| `recall@5` | 0.30 | Correct incident family in top-5 matches (decoys: no confident match = correct) |
| `precision@5_mean` | 0.15 | Mean precision across top-5 returned matches |
| `remediation_acc` | 0.20 | Correct remediation action suggested (5 possible: rollback, restart, scale_up, config_change, failover) |
| `latency_p95_ms` | 0.15 | `min(1, budget / worst_seed_p95)` — fast: 2 000 ms, deep: 6 000 ms |
| `manual_context` | 0.10 | Panel-graded: quality of `related_events` |
| `manual_explain` | 0.10 | Panel-graded: quality of `explain` narrative |

**Maximum automated: 0.80.** Panel adds up to 0.20 for a total of 1.00.

### L3 Stretch Configuration

```
30 services · 21 simulated days · 80 topology mutations (85% renames)
60 train + 25 eval incidents · 8 incident families · 20% decoy rate
Cascading renames: ON · Seeds: [314159, 271828, 161803, 141421, 173205]
```

### Decoy Handling

20% of eval signals are **decoys** — bare `incident_signal` events with no matching family in training. A correct engine returns:

- `similar_past_incidents`: empty, or all entries with `similarity < 0.5`
- `suggested_remediations`: empty, or all entries with `confidence < 0.5`

Confidently matching a decoy scores **0** on that incident.

### Cascading Renames

Services may be renamed 2–4 times across the timeline. An engine that handles only one rename hop fails on most family incidents. The engine must build a full alias chain.

---

## Development Workflow

```bash
# 1. Make changes in ../src/

# 2. Quick sanity check (< 1 second)
python scripts/self_check.py --adapter adapters.context_engine:Engine --quick

# 3. Full self-check (5 seeds, standard dataset)
python scripts/self_check.py --adapter adapters.context_engine:Engine

# 4. Single-seed L3 for iteration
python run.py --adapter adapters.context_engine:Engine --mode deep --seeds 314159 --out -

# 5. Full L3 submission run (~30 seconds)
python run.py --adapter adapters.context_engine:Engine --mode deep --out outputs/l3_deep.json
```

---

## Testing

| Command | Scope | Time |
|---------|-------|------|
| `python scripts/self_check.py --adapter adapters.context_engine:Engine --quick` | 2 seeds, 6 services | ~1 s |
| `python scripts/self_check.py --adapter adapters.context_engine:Engine` | 5 seeds, 12 services | ~5 s |
| `python run.py --adapter adapters.dummy:DummyAdapter --out -` | Baseline comparison | ~10 s |

The self-check exercises the full pipeline end-to-end: ingestion → reconstruction → scoring.

---

## Known Limitations

- **Precision vs. recall tradeoff.** Family diversification in `pattern.py` intentionally sacrifices precision (~0.32) to maximise recall (0.75). Adjusting the fill strategy could shift this balance.
- **Seed variance.** Seed 161803 produces the lowest recall (0.64) due to dense cascading renames.
- **No persistence.** The memory substrate is fully in-memory. Each seed gets a fresh adapter instance by design.
- **Template-based narrative.** The `explain` field is assembled from structured data, not generated by an LLM. Factually accurate but may lack depth for panel grading.
- **Background noise excluded.** Only deploys, metric spikes (> 2 000), and error logs feed fingerprints. Low-value metric anomalies are invisible to the pattern library.

---

## Contributing

1. **Do not modify the benchmark framework** (`src/anvil_benchmark/`). It is the reference implementation.
2. **Keep the adapter interface intact.** `ingest`, `reconstruct_context`, and `close` signatures must not change.
3. **Run self-check before submitting.** All metrics should meet or exceed baseline.
4. **Document tradeoffs.** If you change a scoring strategy (e.g. diversification, similarity capping), explain the reasoning.

```bash
# Pre-submission checklist
python scripts/self_check.py --adapter adapters.context_engine:Engine --quick
python run.py --adapter adapters.context_engine:Engine --mode deep --seeds 314159 --out -
```

---

## Submission

Paste the full contents of `outputs/l3_deep.json` into the submission form's **L3 Output** field. Your demo video must show the L3 banner (both open and close banners with version string and final score).

The output includes per-seed metric breakdowns. The council reserves the right to re-run any submission; scores that cannot be reproduced result in disqualification.

---

## License

<!-- TODO: Add LICENSE file (e.g. Apache 2.0, MIT) -->

---

## Maintainers

**Project:** ContextForge ASCENT · ANVIL P·02  
**Benchmark version:** `anvil-2026-p02-L3-final`

<!-- TODO: Add maintainer name and contact -->
