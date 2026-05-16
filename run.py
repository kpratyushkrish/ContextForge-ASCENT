"""Repository-root benchmark entrypoint.

Kept at the root so the public benchmark command remains:
`python run.py --adapter adapters.myteam:Engine --out l3_report.json`.
"""
from __future__ import annotations

import os
import sys


_SRC_ROOT = os.path.join(os.path.dirname(__file__), "src")
if _SRC_ROOT not in sys.path:
    sys.path.insert(0, _SRC_ROOT)

from anvil_benchmark.run import main


if __name__ == "__main__":
    sys.exit(main())
