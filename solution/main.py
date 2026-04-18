from __future__ import annotations

from oep.config import CONFIG
from oep.pipeline import run_pipeline


if __name__ == "__main__":
    print("[1/1] Ejecutando pipeline OEP...")
    result = run_pipeline(CONFIG)
    kpis = result["standard_kpis"]
    idx = result["internal_summary_index"]
    print("=" * 60)
    print(f"INTERNAL SUMMARY INDEX: {idx['score']} / 100")
    print(f"LABEL: {idx['label']}")
    print(f"CYCLE TIME AVG: {kpis['cycle_time_avg_s']:.1f}s")
    print(f"CYCLES/HOUR: {kpis['cycles_per_hour']}")
    print(f"TRUCKS/HOUR: {kpis['estimated_trucks_per_hour']}")
    print(f"SIDE DELTA: {kpis['side_delta_s']}s")
    print(f"SMOOTHNESS: {kpis['smoothness_index']}/10")
    print(f"ANNUAL IMPACT: +${result['economic_impact']['annual_improvement_usd']:,.0f} USD")
    if result.get('ai_advisor', {}).get('enabled'):
        print(f"AI ADVISOR: {result['ai_advisor']['provider']}")
    print("=" * 60)
