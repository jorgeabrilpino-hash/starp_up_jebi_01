from __future__ import annotations

from datetime import date


def _score_label(score: float) -> str:
    if score >= 85:
        return "Excelente"
    if score >= 75:
        return "Bueno"
    if score >= 60:
        return "Regular"
    return "Crítico"


def _strengths(dimensions: dict) -> list[str]:
    return [f"{dim.capitalize()} ({data['score']:.0f}/100)" for dim, data in dimensions.items() if data.get("score", 0) >= 75]


def _weaknesses(dimensions: dict) -> list[str]:
    return [f"{dim.capitalize()} ({data['score']:.0f}/100)" for dim, data in dimensions.items() if data.get("score", 0) < 70]


def generate_report(oep_data: dict, output_path: str):
    meta = oep_data["metadata"]
    dims = oep_data["dimensions"]
    ov = oep_data["overall"]
    recs = oep_data["recommendations"]
    econ = oep_data["economic_impact"]

    oep_score = ov["oep_score"]
    profile_type = ov["profile_type"]
    percentile = ov["percentile_estimate"]
    strengths = _strengths(dims)
    weaknesses = _weaknesses(dims)
    speed_dim = dims["speed"]
    tech_dim = dims["technique"]
    fatigue_dim = dims["fatigue"]
    econ_delta = econ["annual_improvement_usd"]

    exec_summary = (
        f"El operador obtuvo un OEP Score de {oep_score}/100, clasificado como {profile_type}. "
        f"Se ubica en el percentil {percentile}. Durante {meta['duration_seconds']:.0f} segundos de sesión "
        f"se completaron {meta['total_cycles']} ciclos con un tiempo promedio de {speed_dim['avg_cycle_seconds']:.1f}s por ciclo "
        f"({speed_dim['loads_per_hour']} cargas/hora)."
    )

    strengths_text = (
        "Las dimensiones con mejor desempeño son: " + ", ".join(strengths) + "."
        if strengths
        else "No se identificaron dimensiones con desempeño destacado en esta sesión."
    )
    weaknesses_text = (
        "Las dimensiones que requieren atención prioritaria son: " + ", ".join(weaknesses) + "."
        if weaknesses
        else "No se detectaron dimensiones críticas."
    )

    recs_text = "\n".join(
        f"  {i}. [{r['priority']}] {r['action']} (ganancia estimada: +{r['expected_gain_pct']}%)"
        for i, r in enumerate(recs[:3], 1)
    )

    smoothness = tech_dim.get("smoothness_index", 0)
    decay = fatigue_dim.get("decay_per_block", 0)
    proj_8h = fatigue_dim.get("projected_8h_smoothness", smoothness)
    tech_text = (
        f"El índice de suavidad actual es {smoothness:.2f}/10. "
        + (
            f"Se detecta una degradación de {abs(decay):.3f} puntos por bloque, proyectando {proj_8h:.2f}/10 al final de 8 horas."
            if decay < -0.1
            else "La suavidad se mantiene relativamente estable durante la sesión."
        )
    )

    top_gain = sum(r["expected_gain_pct"] for r in recs[:3])
    projected_oep = min(100, round(oep_score * (1 + top_gain / 100), 1))
    projection_text = (
        f"Si se aplican las 3 principales recomendaciones, el OEP podría subir a {projected_oep}/100 "
        f"({_score_label(projected_oep)}), con un impacto anual estimado de +${econ_delta:,.0f} USD."
    )

    separator = "=" * 70
    report = f"""{separator}
OPERATOR EFFICIENCY PROFILE (OEP) — REPORTE EJECUTIVO
JEBI Mining Productivity 2.0 | Hackaton 2026
Fecha de análisis: {date.today().isoformat()}
{separator}

1. RESUMEN EJECUTIVO
{exec_summary}

2. FORTALEZAS DEL OPERADOR
{strengths_text}

3. AREAS CRITICAS DE MEJORA
{weaknesses_text}

4. TOP 3 RECOMENDACIONES ACCIONABLES
{recs_text}

5. TECNICA Y FATIGA
{tech_text}

6. PROYECCION DE MEJORA
{projection_text}

{separator}
OEP Score:           {oep_score}/100
Perfil:              {profile_type}
Percentil estimado:  {percentile}%
Impacto anual:       +${econ_delta:,.0f} USD
{separator}
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
