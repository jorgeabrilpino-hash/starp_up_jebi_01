from __future__ import annotations


def compute_internal_index(kpi_scores: dict[str, float]):
    weights = {
        "cycle_time_score": 0.28,
        "consistency_score": 0.20,
        "side_balance_score": 0.12,
        "smoothness_score": 0.20,
        "jerk_score": 0.10,
        "stability_score": 0.10,
    }
    total = sum(weights[k] * kpi_scores[k] for k in weights)
    return round(total, 1), weights


def clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def classify_profile(index_score: float) -> str:
    if index_score >= 88:
        return "EXPERT — Alto rendimiento sostenido"
    if index_score >= 75:
        return "PROFICIENT — Buen desempeño con pérdidas menores"
    if index_score >= 60:
        return "DEVELOPING — Operación usable, pero con pérdidas corregibles"
    return "NEEDS SUPPORT — Requiere intervención y supervisión"


def estimate_percentile(index_score: float) -> int:
    if index_score >= 90:
        return 95
    if index_score >= 82:
        return 75
    if index_score >= 71:
        return 50
    if index_score >= 55:
        return 25
    return 10


def compute_economic_impact(cycles_per_hour: float, improvement_pct: float, value_per_truck_usd: float = 2500.0, target_passes_per_truck: float = 4.5, hours_per_day: int = 24, days_per_year: int = 300):
    trucks_per_hour = cycles_per_hour / target_passes_per_truck
    improved_trucks_per_hour = trucks_per_hour * (1 + improvement_pct / 100.0)
    current_hourly_value = trucks_per_hour * value_per_truck_usd
    improved_hourly_value = improved_trucks_per_hour * value_per_truck_usd
    annual_delta = (improved_hourly_value - current_hourly_value) * hours_per_day * days_per_year
    return round(current_hourly_value, 2), round(improved_hourly_value, 2), round(annual_delta, 2)


def build_recommendations(metrics: dict):
    recs = []
    if metrics["cycle_time_cv"] > 0.18:
        recs.append({
            "priority": "HIGH",
            "action": "Reducir la variabilidad del tiempo de ciclo. Estandarizar la secuencia excavación-swing-descarga-retorno para eliminar pases lentos aislados.",
            "expected_gain_pct": 7,
        })
    if metrics["jerk_p95"] > 180 or metrics["extreme_jerk_event_count"] > 5:
        recs.append({
            "priority": "HIGH",
            "action": "Bajar brusquedad operacional. Disminuir jerk y correcciones finales mejora control, precisión y vida útil del equipo.",
            "expected_gain_pct": 6,
        })
    if metrics["side_delta_s"] > 2.0:
        recs.append({
            "priority": "MEDIUM",
            "action": "Entrenar el lado más lento de operación. La diferencia entre izquierda y derecha está penalizando el servicio por camión.",
            "expected_gain_pct": 4,
        })
    if metrics["smoothness_decay_per_block"] < -0.08:
        recs.append({
            "priority": "MEDIUM",
            "action": "Monitorear degradación temporal del smoothness y aplicar feedback temprano antes de que crezca la pérdida de consistencia.",
            "expected_gain_pct": 4,
        })
    if metrics["cycle_time_avg_s"] > 50:
        recs.append({
            "priority": "MEDIUM",
            "action": "Reducir segundos por pase en fases no productivas. Un recorte marginal por ciclo escala fuerte a nivel de turno y año.",
            "expected_gain_pct": 3,
        })
    while len(recs) < 3:
        recs.append({
            "priority": "LOW",
            "action": "Revisar periódicamente estos KPIs para comparar operadores, turnos y mejoras aplicadas.",
            "expected_gain_pct": 1,
        })
    return recs[:5]
