from __future__ import annotations


def clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def compute_oep(scores: dict[str, float]):
    weights = {
        "cycle_efficiency": 0.24,
        "rhythm_consistency": 0.18,
        "motion_control": 0.20,
        "side_balance": 0.12,
        "endurance": 0.13,
        "operational_risk": 0.13,
    }
    total = sum(weights[k] * scores[k] for k in weights)
    return round(total, 1), weights


def classify_profile(oep_score: float) -> str:
    if oep_score >= 88:
        return "EXPERT — Alto rendimiento sostenido"
    if oep_score >= 75:
        return "PROFICIENT — Buen operador, mejoras menores disponibles"
    if oep_score >= 60:
        return "DEVELOPING — Operación usable, pero con pérdidas corregibles"
    return "NEEDS SUPPORT — Requiere intervención y supervisión"


def estimate_percentile(oep_score: float) -> int:
    if oep_score >= 90:
        return 95
    if oep_score >= 82:
        return 75
    if oep_score >= 71:
        return 50
    if oep_score >= 55:
        return 25
    return 10


def compute_economic_impact(cycles_per_hour: float, improvement_pct: float, value_per_truck_usd: float = 2500.0, target_passes_per_truck: float = 4.5, hours_per_day: int = 24, days_per_year: int = 300):
    trucks_per_hour = cycles_per_hour / target_passes_per_truck
    improved_trucks_per_hour = trucks_per_hour * (1 + improvement_pct / 100.0)
    current_hourly_value = trucks_per_hour * value_per_truck_usd
    improved_hourly_value = improved_trucks_per_hour * value_per_truck_usd
    annual_delta = (improved_hourly_value - current_hourly_value) * hours_per_day * days_per_year
    return round(current_hourly_value, 2), round(improved_hourly_value, 2), round(annual_delta, 2)


def build_recommendations(metrics: dict, scores: dict[str, float]):
    recs = []
    if scores["rhythm_consistency"] < 70:
        recs.append({
            "priority": "HIGH",
            "action": "Reducir la variabilidad de ciclo. Estandarizar la secuencia excavación-swing-descarga-retorno para eliminar ciclos lentos aislados.",
            "expected_gain_pct": 7,
        })
    if scores["motion_control"] < 72:
        recs.append({
            "priority": "HIGH",
            "action": "Corregir maniobras bruscas del brazo. Menos picos de jerk y menos correcciones finales mejoran control y vida útil del equipo.",
            "expected_gain_pct": 6,
        })
    if scores["side_balance"] < 75:
        recs.append({
            "priority": "MEDIUM",
            "action": "Entrenar el lado más lento de operación. La diferencia entre izquierda y derecha está penalizando el servicio por camión.",
            "expected_gain_pct": 4,
        })
    if scores["endurance"] < 75:
        recs.append({
            "priority": "MEDIUM",
            "action": "Monitorear deriva operativa por bloques y aplicar feedback temprano antes de que crezca la pérdida de consistencia en turno largo.",
            "expected_gain_pct": 4,
        })
    if scores["operational_risk"] < 75:
        recs.append({
            "priority": "HIGH",
            "action": "Atacar eventos extremos de operación. Los picos de jerk y ciclos atípicos son señales de riesgo y de pérdida de control operativo.",
            "expected_gain_pct": 5,
        })
    if scores["cycle_efficiency"] < 80:
        recs.append({
            "priority": "MEDIUM",
            "action": "Reducir segundos por pase en fases no productivas. Una mejora marginal por ciclo escala fuerte a nivel de turno y de año.",
            "expected_gain_pct": 3,
        })
    while len(recs) < 3:
        recs.append({
            "priority": "LOW",
            "action": "Revisar OEP periódicamente para comparar operadores, turnos y mejoras aplicadas.",
            "expected_gain_pct": 1,
        })
    return recs[:5]
