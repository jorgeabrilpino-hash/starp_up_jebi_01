from __future__ import annotations

import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "inputs"
INPUTS.mkdir(parents=True, exist_ok=True)

FILES = {
    "shovel_left.mp4": "13Deu2vxds0QTg3gdnvA3JhHo5k9KXZqK",
    "shovel_right.mp4": "1y0XQNrRGRupVeQRPJAzj8kA5iW7tWpvw",
}
IMU_LOCAL = Path("/data/.openclaw/media/inbound/40343737_20260313_110600_to_112100_imu---0a7e8599-b95b-4ed0-a0cf-37e7f2ef4469")


def _get_confirm_and_uuid(file_id: str) -> tuple[str, str]:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", "ignore")
    confirm = re.search(r'name="confirm" value="([^"]+)"', html)
    uuid = re.search(r'name="uuid" value="([^"]+)"', html)
    if not confirm or not uuid:
        raise RuntimeError(f"No se pudo resolver confirm/uuid para {file_id}")
    return confirm.group(1), uuid.group(1)


def _download_drive_file(file_id: str, output_path: Path):
    confirm, uuid = _get_confirm_and_uuid(file_id)
    url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm={confirm}&uuid={uuid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, output_path.open("wb") as f:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


for name, file_id in FILES.items():
    out = INPUTS / name
    if out.exists() and out.stat().st_size > 0:
        print(f"[skip] {name} ya existe")
    else:
        print(f"[download] {name}")
        _download_drive_file(file_id, out)

imu_out = INPUTS / "imu_data.npy"
if not imu_out.exists():
    if IMU_LOCAL.exists():
        os.symlink(IMU_LOCAL, imu_out)
        print("[link] imu_data.npy enlazado desde entorno local")
    else:
        print("[warn] IMU local no encontrado, copia imu_data.npy manualmente a inputs/")

print("Listo. Ahora puedes ejecutar: bash run.sh")
