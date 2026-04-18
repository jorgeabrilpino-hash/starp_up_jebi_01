#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "=== JEBI Hackaton 2026 — OEP Mining Productivity MVP v2 ==="

for f in inputs/shovel_left.mp4 inputs/shovel_right.mp4 inputs/imu_data.npy; do
  if [ ! -f "$f" ]; then
    echo "ERROR: Falta archivo de entrada: $f"
    exit 1
  fi
done

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

mkdir -p outputs outputs/dashboard
export PYTHONPATH="$ROOT_DIR/solution:${PYTHONPATH:-}"
python solution/main.py

echo "=== COMPLETADO ==="
echo "Outputs disponibles en ./outputs"
if [ -f outputs/dashboard/index.html ]; then
  echo "Dashboard: outputs/dashboard/index.html"
fi
