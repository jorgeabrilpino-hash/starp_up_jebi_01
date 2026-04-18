from __future__ import annotations

import json
import os

import numpy as np

from .advisor import get_ai_advice
from .config import AppConfig
from .imu import compute_fatigue, compute_jerk, compute_smoothness, compute_symmetry, detect_cycles, load_imu, split_cycle_sides
from .reporting import generate_dashboard, generate_report, plot_oep
from .scoring import build_recommendations, clamp_score, classify_profile, compute_economic_impact, compute_oep, estimate_percentile
from .video import analyze_mineral_quality, detect_spillage


TARGET_CYCLE_SECONDS = 50.0
TARGET_PASSES_PER_TRUCK = 4.5


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

    duration_seconds = float(imu["time_s"].iloc[-1])
    avg_cycle = float(np.mean(cycle_times)) if cycle_times else TARGET_CYCLE_SECONDS
    std_cycle = float(np.std(cycle_times)) if cycle_times else 5.0
    cycle_cv = std_cycle / max(avg_cycle, 1e-6)
    loads_per_window = len(cycle_times)
    cycles_per_hour = round(loads_per_window * (3600.0 / max(duration_seconds, 1.0)), 1)
    estimated_trucks_per_hour = round(cycles_per_hour / TARGET_PASSES_PER_TRUCK, 2)
    estimated_service_minutes = round((TARGET_PASSES_PER_TRUCK * avg_cycle) / 60.0, 2)
    outlier_cycles = [t for t in cycle_times if t > avg_cycle + std_cycle or t < max(20.0, avg_cycle - std_cycle)]
    outlier_ratio = len(outlier_cycles) / max(len(cycle_times), 1)

    smoothness_score = compute_smoothness(jerk)
    avg_jerk = float(jerk.mean())
    p95_jerk = float(np.percentile(jerk, 95))
    max_jerk = float(jerk.max())
    extreme_jerk_events = int((jerk > 500).sum())

    left_avg = float(np.mean(left_cycles)) if left_cycles else avg_cycle
    right_avg = float(np.mean(right_cycles)) if right_cycles else avg_cycle
    side_gap_seconds = abs(left_avg - right_avg)
    side_gap_pct = side_gap_seconds / max(avg_cycle, 1.0) * 100.0

    dark_pct_left = analyze_mineral_quality(config.left_video)
    spill_pct_left = detect_spillage(config.left_video)
    dark_pct_right = analyze_mineral_quality(config.right_video)
    spill_pct_right = detect_spillage(config.right_video)
    visual_load_darkness = round((dark_pct_left + dark_pct_right) / 2.0, 2)
    spill_proxy_pct = round((spill_pct_left + spill_pct_right) / 2.0, 2)

    blocks_duration_minutes = duration_seconds / 60.0 / max(len(smoothness_blocks), 1)
    decay_per_minute = fatigue_slope / max(blocks_duration_minutes, 1e-6)
    projected_8h = round(max(0.0, smoothness_blocks[0] + decay_per_minute * (8 * 60)), 2) if smoothness_blocks else 0.0
    endurance_delta = (smoothness_blocks[-1] - smoothness_blocks[0]) if len(smoothness_blocks) >= 2 else 0.0

    cycle_efficiency_score = clamp_score(100 - max(0.0, (avg_cycle - TARGET_CYCLE_SECONDS) * 2.2) + min(10.0, cycles_per_hour / 10.0))
    rhythm_consistency_score = clamp_score(100 - cycle_cv * 100 - outlier_ratio * 120)
    motion_control_score = clamp_score((smoothness_score * 10) - max(0.0, (p95_jerk - 120.0) / 8.0) - extreme_jerk_events * 1.5)
    side_balance_score = clamp_score(100 - side_gap_pct * 4.0 - abs(symmetry - 0.35) * 80.0)
    endurance_score = clamp_score((smoothness_blocks[-1] / max(smoothness_blocks[0], 0.1)) * 100 if smoothness_blocks else 70.0)
    operational_risk_score = clamp_score(100 - extreme_jerk_events * 3.0 - outlier_ratio * 80.0 - max(0.0, spill_proxy_pct - 20.0) * 0.3)

    scores = {
        "cycle_efficiency": cycle_efficiency_score,
        "rhythm_consistency": rhythm_consistency_score,
        "motion_control": motion_control_score,
        "side_balance": side_balance_score,
        "endurance": endurance_score,
        "operational_risk": operational_risk_score,
    }
    oep_score, weights = compute_oep(scores)

    opportunity_pct = sum(r["expected_gain_pct"] for r in build_recommendations({}, scores)[:3])
    current_hourly_value, improved_hourly_value, annual_delta = compute_economic_impact(cycles_per_hour, opportunity_pct)

    metrics = {
        "avg_cycle_seconds": round(avg_cycle, 2),
        "std_cycle_seconds": round(std_cycle, 2),
        "cycle_cv": round(cycle_cv, 3),
        "cycle_times": [round(x, 2) for x in cycle_times],
        "cycles_per_hour": cycles_per_hour,
        "estimated_trucks_per_hour": estimated_trucks_per_hour,
        "estimated_service_minutes": estimated_service_minutes,
        "outlier_cycle_ratio": round(outlier_ratio, 3),
        "left_avg_cycle_seconds": round(left_avg, 2),
        "right_avg_cycle_seconds": round(right_avg, 2),
        "side_gap_seconds": round(side_gap_seconds, 2),
        "side_gap_pct": round(side_gap_pct, 2),
        "smoothness_blocks": smoothness_blocks,
        "smoothness_index": smoothness_score,
        "avg_jerk": round(avg_jerk, 2),
        "p95_jerk": round(p95_jerk, 2),
        "max_jerk": round(max_jerk, 2),
        "extreme_jerk_events": extreme_jerk_events,
        "decay_per_block": round(fatigue_slope, 4),
        "decay_per_minute": round(decay_per_minute, 4),
        "projected_8h_smoothness": projected_8h,
        "endurance_delta": round(endurance_delta, 3),
        "visual_load_darkness": visual_load_darkness,
        "spill_proxy_pct": spill_proxy_pct,
        "symmetry_index": symmetry,
        "equipment_model": "Hitachi EX-5600",
        "truck_models": ["CAT 793F", "EH4000 AC-3"],
        "target_passes_per_truck": TARGET_PASSES_PER_TRUCK,
    }

    recommendations = build_recommendations(metrics, scores)
    oep_data = {
        "metadata": {
            "duration_seconds": round(duration_seconds, 2),
            "total_cycles": loads_per_window,
            "video_left": os.path.basename(config.left_video),
            "video_right": os.path.basename(config.right_video),
            "imu_file": os.path.basename(config.imu_file),
            "equipment_model": metrics["equipment_model"],
            "truck_models": metrics["truck_models"],
        },
        "dimensions": {
            "cycle_efficiency": {
                "score": cycle_efficiency_score,
                "avg_cycle_seconds": metrics["avg_cycle_seconds"],
                "cycles_per_hour": metrics["cycles_per_hour"],
                "estimated_trucks_per_hour": metrics["estimated_trucks_per_hour"],
                "estimated_service_minutes": metrics["estimated_service_minutes"],
                "cycle_times": metrics["cycle_times"],
            },
            "rhythm_consistency": {
                "score": rhythm_consistency_score,
                "std_cycle_seconds": metrics["std_cycle_seconds"],
                "cycle_cv": metrics["cycle_cv"],
                "outlier_cycle_ratio": metrics["outlier_cycle_ratio"],
            },
            "motion_control": {
                "score": motion_control_score,
                "smoothness_index": metrics["smoothness_index"],
                "avg_jerk": metrics["avg_jerk"],
                "p95_jerk": metrics["p95_jerk"],
                "max_jerk": metrics["max_jerk"],
            },
            "side_balance": {
                "score": side_balance_score,
                "left_avg_cycle_seconds": metrics["left_avg_cycle_seconds"],
                "right_avg_cycle_seconds": metrics["right_avg_cycle_seconds"],
                "side_gap_seconds": metrics["side_gap_seconds"],
                "side_gap_pct": metrics["side_gap_pct"],
            },
            "endurance": {
                "score": endurance_score,
                "smoothness_blocks": metrics["smoothness_blocks"],
                "decay_per_block": metrics["decay_per_block"],
                "decay_per_minute": metrics["decay_per_minute"],
                "projected_8h_smoothness": metrics["projected_8h_smoothness"],
            },
            "operational_risk": {
                "score": operational_risk_score,
                "extreme_jerk_events": metrics["extreme_jerk_events"],
                "spill_proxy_pct": metrics["spill_proxy_pct"],
                "symmetry_index": metrics["symmetry_index"],
                "outlier_cycle_ratio": metrics["outlier_cycle_ratio"],
            },
        },
        "metrics": metrics,
        "overall": {
            "oep_score": oep_score,
            "profile_type": classify_profile(oep_score),
            "percentile_estimate": estimate_percentile(oep_score),
            "weights": weights,
        },
        "recommendations": recommendations,
        "economic_impact": {
            "current_hourly_value_usd": current_hourly_value,
            "improved_hourly_value_usd": improved_hourly_value,
            "annual_improvement_usd": annual_delta,
        },
    }

    ai_advice = get_ai_advice(oep_data, config)
    oep_data["ai_advisor"] = {
        "enabled": bool(ai_advice),
        "provider": "openai" if (ai_advice and config.openai_api_key) else ("ollama" if ai_advice else None),
        "advice": ai_advice,
    }

    with open(os.path.join(config.outputs_dir, "oep_report.json"), "w", encoding="utf-8") as f:
        json.dump(oep_data, f, indent=2, ensure_ascii=False)
    plot_oep(scores, oep_score, cycle_times, smoothness_blocks, os.path.join(config.outputs_dir, "oep_visualization.png"))
    generate_dashboard(oep_data, config.dashboard_dir)
    generate_report(oep_data, os.path.join(config.outputs_dir, "oep_summary.txt"), ai_advice=ai_advice)
    return oep_data
