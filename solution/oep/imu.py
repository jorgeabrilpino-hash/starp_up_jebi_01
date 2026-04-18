from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

IMU_COLUMNS = [
    "timestamp_ns", "accel_x", "accel_y", "accel_z",
    "gyro_roll", "gyro_pitch", "gyro_yaw",
    "quat_w", "quat_x", "quat_y", "quat_z",
]


def load_imu(path: str) -> pd.DataFrame:
    arr = np.load(path)
    df = pd.DataFrame(arr, columns=IMU_COLUMNS)
    df["time_s"] = (df["timestamp_ns"] - df["timestamp_ns"].iloc[0]) / 1e9
    return df


def detect_cycles(df: pd.DataFrame, threshold: float = 30.0, min_distance_samples: int = 300) -> dict:
    roll = df["gyro_roll"].to_numpy()
    pos_peaks, pos_props = find_peaks(roll, height=threshold, distance=min_distance_samples)
    neg_peaks, neg_props = find_peaks(-roll, height=threshold, distance=min_distance_samples)
    cycle_times, cycle_bounds = [], []
    for start_idx, end_idx in zip(pos_peaks.tolist(), pos_peaks.tolist()[1:]):
        duration = float(df["time_s"].iloc[end_idx] - df["time_s"].iloc[start_idx])
        if 30.0 <= duration <= 90.0:
            cycle_times.append(duration)
            cycle_bounds.append((int(start_idx), int(end_idx), duration))
    return {
        "cycle_times": cycle_times,
        "cycle_bounds": cycle_bounds,
        "positive_peaks": pos_peaks,
        "negative_peaks": neg_peaks,
        "positive_peak_heights": pos_props.get("peak_heights", np.array([])),
        "negative_peak_heights": neg_props.get("peak_heights", np.array([])),
    }


def compute_jerk(df: pd.DataFrame) -> pd.Series:
    dt = df["time_s"].diff().replace(0, np.nan).fillna(1 / 15)
    jerk_x = df["accel_x"].diff().fillna(0) / dt
    jerk_y = df["accel_y"].diff().fillna(0) / dt
    jerk_z = df["accel_z"].diff().fillna(0) / dt
    return np.sqrt(jerk_x**2 + jerk_y**2 + jerk_z**2).fillna(0)


def compute_smoothness(jerk_series: pd.Series, max_jerk: float = 650.0) -> float:
    avg_jerk = float(jerk_series.mean())
    score = 10 * (1 - min(avg_jerk / max_jerk, 1))
    return round(score, 2)


def compute_fatigue(df: pd.DataFrame, jerk_series: pd.Series, n_blocks: int = 3):
    if len(df) == 0:
        return [0.0] * n_blocks, 0.0
    block_size = max(1, len(df) // n_blocks)
    blocks = []
    for i in range(n_blocks):
        start = i * block_size
        end = len(df) if i == n_blocks - 1 else (i + 1) * block_size
        blocks.append(compute_smoothness(jerk_series.iloc[start:end]))
    slope = (blocks[-1] - blocks[0]) / (len(blocks) - 1) if len(blocks) > 1 else 0.0
    return blocks, round(float(slope), 4)


def compute_symmetry(df: pd.DataFrame) -> float:
    lateral = float(df["accel_x"].abs().mean())
    vertical = float((df["accel_y"].abs() - 9.81).abs().mean()) + 1e-3
    return round(lateral / vertical, 3)


def split_cycle_sides(cycle_bounds: list[tuple[int, int, float]]):
    left_cycles = [dur for idx, (_, _, dur) in enumerate(cycle_bounds) if idx % 2 == 0]
    right_cycles = [dur for idx, (_, _, dur) in enumerate(cycle_bounds) if idx % 2 == 1]
    return left_cycles, right_cycles
