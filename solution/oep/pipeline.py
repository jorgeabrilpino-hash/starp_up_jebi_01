from __future__ import annotations

import json
import os

import numpy as np

from .advisor import get_ai_advice
from .config import AppConfig
from .imu import compute_fatigue, compute_jerk, compute_smoothness, compute_symmetry, detect_cycles, load_imu, split_cycle_sides
from .reporting import generate_dashboard, generate_report, plot_oep
from .scoring import build_recommendations, classify_profile, compute_economic_impact, compute_oep, estimate_percentile
from .video import analyze_mineral_quality, detect_spillage


def run_pipeline(config: AppConfig) -> dict:
    os.makedirs(config.dashboard_dir, exist_ok=True)

    imu = load_imu(config.imu_file)
    cycle_info = detect_cycles(imu)
    cycle_times = cycle_info["cycle_times"]
    cycle_bounds = cycle_info["cycle_bounds"]
    jerk = compute_jerk(imu)
    smoothness_blocks, fatigue_slope = compute_fatigue(imu, jerk, n_blocks=3)
    symmetry = compute_symmetry(imu)
    left_cycles, right_cycles = split_cycle_sides(cycle_bounds)

    avg_cycle = float(np.mean(cycle_times)) if cycle_times else 55.0
    std_cycle = float(np.std(cycle_times)) if cycle_times else 5.0
    loads_per_window = len(cycle_times)
    loads_per_hour = round(loads_per_window * (3600.0 / max(float(imu["time_s"].iloc[-1]), 1.0)), 1)
    smoothness_score = compute_smoothness(jerk)
    max_jerk = float(jerk.max())
    avg_jerk = float(jerk.mean())

    dark_pct_left = analyze_mineral_quality(config.left_video)
    spill_pct_left = detect_spillage(config.left_video)
    dark_pct_right = analyze_mineral_quality(config.right_video)
    spill_pct_right = detect_spillage(config.right_video)
    dark_pct_avg = (dark_pct_left + dark_pct_right) / 2.0
    spill_pct_avg = (spill_pct_left + spill_pct_right) / 2.0

    speed_score = min(100.0, round(100.0 * 45.0 / avg_cycle, 1)) if avg_cycle > 0 else 0.0
    quality_score = round(min(100.0, max(0.0, (dark_pct_avg - 30.0) / 40.0 * 100.0)), 1)
    smoothness_pct = smoothness_score * 10.0
    symmetry_penalty = max(0.0, (symmetry - 0.3) / 0.3 * 20.0)
    technique_score = round(max(0.0, smoothness_pct - symmetry_penalty), 1)
    left_avg = float(np.mean(left_cycles)) if left_cycles else avg_cycle
    right_avg = float(np.mean(right_cycles)) if right_cycles else avg_cycle
    position_penalty_pct = abs(left_avg - right_avg) / max(avg_cycle, 1.0) * 100.0
    adaptability_score = round(max(0.0, 100.0 - position_penalty_pct * 5.0), 1)
    fatigue_score = round(min(100.0, (smoothness_blocks[-1] / smoothness_blocks[0]) * 100.0), 1) if len(smoothness_blocks) >= 2 and smoothness_blocks[0] > 0 else 70.0
    risk_events = int((jerk > 500).sum())
    safety_score = round(max(0.0, 100.0 - (risk_events / max(len(jerk), 1) * 1000.0) - spill_pct_avg * 2.0), 1)
    oep_score, scores_dict = compute_oep(speed_score, quality_score, technique_score, adaptability_score, fatigue_score, safety_score)

    blocks_duration_minutes = float(imu["time_s"].iloc[-1]) / 60.0 / max(len(smoothness_blocks), 1)
    decay_per_minute = fatigue_slope / max(blocks_duration_minutes, 1e-6)
    projected_8h = round(max(0.0, smoothness_blocks[0] + decay_per_minute * (8 * 60)), 2) if smoothness_blocks else 0.0
    current_val, improved_val, annual_delta = compute_economic_impact(loads_per_window, dark_pct_avg)

    oep_data = {
        "metadata": {
            "duration_seconds": round(float(imu["time_s"].iloc[-1]), 2),
            "total_cycles": loads_per_window,
            "video_left": os.path.basename(config.left_video),
            "video_right": os.path.basename(config.right_video),
            "imu_file": os.path.basename(config.imu_file),
        },
        "dimensions": {
            "speed": {"score": speed_score, "loads_per_hour": loads_per_hour, "avg_cycle_seconds": round(avg_cycle, 2), "std_cycle_seconds": round(std_cycle, 2), "cycle_times": [round(x, 2) for x in cycle_times]},
            "quality": {"score": quality_score, "dark_mineral_pct": round(dark_pct_avg, 2), "spillage_pct": round(spill_pct_avg, 2)},
            "technique": {"score": technique_score, "avg_jerk": round(avg_jerk, 2), "max_jerk": round(max_jerk, 2), "smoothness_index": smoothness_score, "symmetry_index": symmetry},
            "adaptability": {"score": adaptability_score, "left_avg_cycle_s": round(left_avg, 2), "right_avg_cycle_s": round(right_avg, 2), "position_penalty_pct": round(position_penalty_pct, 2)},
            "fatigue": {"score": fatigue_score, "smoothness_block1": smoothness_blocks[0] if smoothness_blocks else 0.0, "smoothness_block2": smoothness_blocks[1] if len(smoothness_blocks) > 1 else 0.0, "smoothness_blocks": smoothness_blocks, "decay_per_block": round(fatigue_slope, 4), "decay_per_minute": round(decay_per_minute, 4), "projected_8h_smoothness": projected_8h},
            "safety": {"score": safety_score, "risk_events_count": risk_events, "load_stability_index": round(max(0.0, 1.0 - min(symmetry, 1.0)), 3)},
        },
        "overall": {"oep_score": oep_score, "profile_type": classify_profile(oep_score), "percentile_estimate": estimate_percentile(oep_score)},
        "recommendations": build_recommendations(scores_dict),
        "economic_impact": {"current_value_per_15min_usd": current_val, "improved_value_per_15min_usd": improved_val, "annual_improvement_usd": annual_delta},
    }

    ai_advice = get_ai_advice(oep_data, config)
    if ai_advice:
        oep_data["ai_advisor"] = {"enabled": True, "provider": "openai" if config.openai_api_key else "ollama", "advice": ai_advice}
    else:
        oep_data["ai_advisor"] = {"enabled": False, "provider": None, "advice": None}

    with open(os.path.join(config.outputs_dir, "oep_report.json"), "w", encoding="utf-8") as f:
        json.dump(oep_data, f, indent=2, ensure_ascii=False)
    plot_oep(scores_dict, oep_score, cycle_times, smoothness_blocks, os.path.join(config.outputs_dir, "oep_visualization.png"))
    generate_dashboard(oep_data, config.dashboard_dir)
    generate_report(oep_data, os.path.join(config.outputs_dir, "oep_summary.txt"), ai_advice=ai_advice)
    return oep_data
