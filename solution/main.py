from __future__ import annotations

from oep.config import CONFIG
from oep.pipeline import run_pipeline


if __name__ == "__main__":
    print("[1/1] Ejecutando pipeline OEP...")
    result = run_pipeline(CONFIG)
    print("=" * 60)
    print(f"OEP SCORE FINAL: {result['overall']['oep_score']} / 100")
    print(f"PERFIL: {result['overall']['profile_type']}")
    print(f"CICLOS DETECTADOS: {result['metadata']['total_cycles']}")
    print(f"CICLO PROMEDIO: {result['dimensions']['cycle_efficiency']['avg_cycle_seconds']:.1f}s")
    print(f"CICLOS/HORA: {result['dimensions']['cycle_efficiency']['cycles_per_hour']}")
    print(f"GAP ENTRE LADOS: {result['dimensions']['side_balance']['side_gap_seconds']}s")
    print(f"SMOOTHNESS: {result['dimensions']['motion_control']['smoothness_index']}/10")
    print(f"IMPACTO ANUAL: +${result['economic_impact']['annual_improvement_usd']:,.0f} USD")
    if result.get('ai_advisor', {}).get('enabled'):
        print(f"AI ADVISOR: {result['ai_advisor']['provider']}")
    print("=" * 60)
