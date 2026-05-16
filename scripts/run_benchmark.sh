#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python run.py --adapter adapters.myteam:Engine --mode fast --seeds 9999 31415 --out outputs/report.json
echo "Report written to outputs/report.json"
