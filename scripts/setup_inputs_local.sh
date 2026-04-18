#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INPUTS_DIR="$ROOT_DIR/inputs"
mkdir -p "$INPUTS_DIR"

LEFT_SRC="/data/.openclaw/workspace/hackathon/inbound_videos/left_13Deu2vxds0QTg3gdnvA3JhHo5k9KXZqK.mp4"
RIGHT_SRC="/data/.openclaw/workspace/hackathon/inbound_videos/right_1y0XQNrRGRupVeQRPJAzj8kA5iW7tWpvw.mp4"
IMU_SRC="/data/.openclaw/media/inbound/40343737_20260313_110600_to_112100_imu---0a7e8599-b95b-4ed0-a0cf-37e7f2ef4469"

for f in "$LEFT_SRC" "$RIGHT_SRC" "$IMU_SRC"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: no se encontró $f"
    exit 1
  fi
done

ln -sfn "$LEFT_SRC" "$INPUTS_DIR/shovel_left.mp4"
ln -sfn "$RIGHT_SRC" "$INPUTS_DIR/shovel_right.mp4"
ln -sfn "$IMU_SRC" "$INPUTS_DIR/imu_data.npy"

echo "Inputs enlazados correctamente en $INPUTS_DIR"
ls -lh "$INPUTS_DIR"
