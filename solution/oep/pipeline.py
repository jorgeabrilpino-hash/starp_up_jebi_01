from __future__ import annotations

import json
import os

import numpy as np

from .advisor import get_ai_advice
from .config import AppConfig
from .imu import compute_fatigue, compute_jerk, compute_smoothness, compute_symmetry, detect_cycles, load_imu, split_cycle_sides
from .reporting import generate_dashboard, generate_report, plot_oep
from .scoring import build_recommendations, clamp_score, classify_profile, compute_economic_impact, compute_internal_index, estimate_percentile

TARGET_CYCLE_SECONDS = 50.0
TARGET_PASSES_PER_TRUCK = 4.5


def _kpi_scores(metrics: dict) -> dict[str, float]:
    cycle_time_score = clamp_score(100 - max(0.0, (metrics["cycle_time_avg_s"] - TARGET_CYCLE_SECONDS) * 2.5))
    consistency_score = clamp_score(100 - metrics["cycle_time_cv"] * 180 - metrics["outlier_cycle_ratio"] * 80)
    side_balance_score = clamp_score(100 - metrics["side_delta_pct"] * 6.0)
    smoothness_score = clamp_score(metrics["smoothness_index"] * 10)
    jerk_score = clamp_score(100 - max(0.0, metrics["jerk_p95"] - 120.0) / 3.5 - metrics["extreme_jerk_event_count"] * 2.0)
    stability_score = clamp_score((metrics["smoothness_blocks"][-1] / max(metrics["smoothness_blocks"][0], 0.1)) * 100 if metrics["smoothness_blocks"] else 70.0)
    return {
        "cycle_time_score": cycle_time_score,
        "consistency_score": consistency_score,
        "side_balance_score": side_balance_score,
        "smoothness_score": smoothness_score,
        "jerk_score": jerk_score,
        "stability_score": stability_score,
    }


def run_pipeline(config: AppConfig) -> dict:
    os.makedirs(config.dashboard_dir, exist_ok=True)

    imu = load_imu(config.imu_file)
    cycle_info = detect_cycles(imu)
    cycle_times = cycle_info["cycle_times"]
    cycle_bounds = cycle_info["cycle_bounds"]
    jerk = compute_jerk(imu)
    smoothness_blocks, fatigue_slope = compute_fatigue(imu, jerk, n_blocks=3)
    left_cycles, right_cycles = split_cycle_sides(cycle_bounds)

    duration_seconds = float(imu["time_s"].iloc[-1])
    cycle_time_avg = float(np.mean(cycle_times)) if cycle_times else TARGET_CYCLE_SECONDS
    cycle_time_std = float(np.std(cycle_times)) if cycle_times else 5.0
    cycle_time_cv = cycle_time_std / max(cycle_time_avg, 1e-6)
    total_cycles = len(cycle_times)
    cycles_per_hour = round(total_cycles * (3600.0 / max(duration_seconds, 1.0)), 1)
    estimated_trucks_per_hour = round(cycles_per_hour / TARGET_PASSES_PER_TRUCK, 2)
    service_time_per_truck_min = round((TARGET_PASSES_PER_TRUCK * cycle_time_avg) / 60.0, 2)
    outlier_cycles = [t for t in cycle_times if t > cycle_time_avg + cycle_time_std or t < max(20.0, cycle_time_avg - cycle_time_std)]
    outlier_ratio = len(outlier_cycles) / max(len(cycle_times), 1)

    smoothness_index = compute_smoothness(jerk)
    jerk_avg = float(jerk.mean())
    jerk_p95 = float(np.percentile(jerk, 95))
    jerk_max = float(jerk.max())
    extreme_jerk_event_count = int((jerk > 500).sum())
    symmetry_index = compute_symmetry(imu)

    left_cycle_time_avg_s = float(np.mean(left_cycles)) if left_cycles else cycle_time_avg
    right_cycle_time_avg_s = float(np.mean(right_cycles)) if right_cycles else cycle_time_avg
    side_delta_s = abs(left_cycle_time_avg_s - right_cycle_time_avg_s)
    side_delta_pct = side_delta_s / max(cycle_time_avg, 1.0) * 100.0

    smoothness_decay_per_block = round(fatigue_slope, 4)
    blocks_duration_minutes = duration_seconds / 60.0 / max(len(smoothness_blocks), 1)
    smoothness_decay_per_minute = smoothness_decay_per_block / max(blocks_duration_minutes, 1e-6)
    projected_8h_smoothness = round(max(0.0, smoothness_blocks[0] + smoothness_decay_per_minute * (8 * 60)), 2) if smoothness_blocks else 0.0

    metrics = {
        "equipment_model": "Hitachi EX-5600",
        "truck_models": ["CAT 793F", "EH4000 AC-3"],
        "target_passes_per_truck": TARGET_PASSES_PER_TRUCK,
        "cycle_time_avg_s": round(cycle_time_avg, 2),
        "cycle_time_std_s": round(cycle_time_std, 2),
        "cycle_time_cv": round(cycle_time_cv, 3),
        "cycle_times_s": [round(x, 2) for x in cycle_times],
        "total_cycles": total_cycles,
        "cycles_per_hour": cycles_per_hour,
        "estimated_trucks_per_hour": estimated_trucks_per_hour,
        "service_time_per_truck_min": service_time_per_truck_min,
        "outlier_cycle_ratio": round(outlier_ratio, 3),
        "left_cycle_time_avg_s": round(left_cycle_time_avg_s, 2),
        "right_cycle_time_avg_s": round(right_cycle_time_avg_s, 2),
        "side_delta_s": round(side_delta_s, 2),
        "side_delta_pct": round(side_delta_pct, 2),
        "smoothness_index": smoothness_index,
        "smoothness_blocks": smoothness_blocks,
        "smoothness_decay_per_block": smoothness_decay_per_block,
        "smoothness_decay_per_minute": round(smoothness_decay_per_minute, 4),
        "projected_8h_smoothness": projected_8h_smoothness,
        "jerk_avg": round(jerk_avg, 2),
        "jerk_p95": round(jerk_p95, 2),
        "jerk_max": round(jerk_max, 2),
        "extreme_jerk_event_count": extreme_jerk_event_count,
        "symmetry_index": round(symmetry_index, 3),
    }

    recommendations = build_recommendations(metrics)
    kpi_scores = _kpi_scores(metrics)
    internal_index_score, internal_index_weights = compute_internal_index(kpi_scores)
    opportunity_pct = sum(r["expected_gain_pct"] for r in recommendations[:3])
    current_hourly_value, improved_hourly_value, annual_delta = compute_economic_impact(cycles_per_hour, opportunity_pct)

    project_data = {
        "metadata": {
            "duration_seconds": round(duration_seconds, 2),
            "video_left": os.path.basename(config.left_video),
            "video_right": os.path.basename(config.right_video),
            "imu_file": os.path.basename(config.imu_file),
            "equipment_model": metrics["equipment_model"],
            "truck_models": metrics["truck_models"],
        },
        "standard_kpis": metrics,
        "internal_summary_index": {
            "score": internal_index_score,
            "label": classify_profile(internal_index_score),
            "percentile_estimate": estimate_percentile(internal_index_score),
            "component_scores": kpi_scores,
            "weights": internal_index_weights,
            "note": "Internal summary index built from standard operational KPIs and IMU signal indicators. Not an industry standard metric.",
        },
        "recommendations": recommendations,
        "economic_impact": {
            "current_hourly_value_usd": current_hourly_value,
            "improved_hourly_value_usd": improved_hourly_value,
            "annual_improvement_usd": annual_delta,
        },
    }

    ai_advice = get_ai_advice(project_data, config)
    project_data["ai_advisor"] = {
        "enabled": bool(ai_advice),
        "provider": "openai" if (ai_advice and config.openai_api_key) else ("ollama" if ai_advice else None),
        "advice": ai_advice,
    }

    with open(os.path.join(config.outputs_dir, "oep_report.json"), "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2, ensure_ascii=False)
    plot_oep(kpi_scores, internal_index_score, cycle_times, smoothness_blocks, os.path.join(config.outputs_dir, "oep_visualization.png"))
    generate_dashboard(project_data, config.dashboard_dir)
    generate_report(project_data, os.path.join(config.outputs_dir, "oep_summary.txt"), ai_advice=ai_advice)
    return project_data
