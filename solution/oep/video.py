from __future__ import annotations

import cv2
import numpy as np

DEFAULT_DARK_PCT = 60.0
DEFAULT_SPILL_PCT = 3.0


def _open_video(video_path: str):
    cap = cv2.VideoCapture(video_path)
    return cap if cap.isOpened() else None


def analyze_mineral_quality(video_path: str, sample_every_n: int = 30) -> float:
    cap = _open_video(video_path)
    if cap is None:
        return DEFAULT_DARK_PCT
    dark_count = 0
    total_count = 0
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every_n == 0:
            roi = frame[frame.shape[0] // 2 :, :]
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            dark_mask = cv2.inRange(hsv, (0, 20, 0), (180, 255, 110))
            dark_count += int(np.sum(dark_mask > 0))
            total_count += int(roi.shape[0] * roi.shape[1])
        frame_idx += 1
    cap.release()
    return round(dark_count / total_count * 100, 2) if total_count else DEFAULT_DARK_PCT


def detect_spillage(video_path: str, sample_every_n: int = 30) -> float:
    cap = _open_video(video_path)
    if cap is None:
        return DEFAULT_SPILL_PCT
    prev_frame = None
    spill_events = 0
    sampled_frames = 0
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every_n == 0:
            sampled_frames += 1
            if prev_frame is not None:
                left_zone = frame[:, : frame.shape[1] // 5]
                right_zone = frame[:, 4 * frame.shape[1] // 5 :]
                prev_left = prev_frame[:, : prev_frame.shape[1] // 5]
                prev_right = prev_frame[:, 4 * prev_frame.shape[1] // 5 :]
                diff_left = cv2.absdiff(left_zone, prev_left)
                diff_right = cv2.absdiff(right_zone, prev_right)
                if float(diff_left.mean()) > 15 or float(diff_right.mean()) > 15:
                    spill_events += 1
            prev_frame = frame.copy()
        frame_idx += 1
    cap.release()
    return round(min(spill_events / sampled_frames * 100, 100), 2) if sampled_frames else DEFAULT_SPILL_PCT
