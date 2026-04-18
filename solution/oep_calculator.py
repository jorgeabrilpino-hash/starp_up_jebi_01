from __future__ import annotations


def compute_oep(speed: float, quality: float, technique: float, adaptability: float, fatigue: float, safety: float):
    weights = {
        "speed": 0.20,
        "quality": 0.20,
        "technique": 0.20,
        "adaptability": 0.15,
        "fatigue": 0.15,
        "safety": 0.10,
    }
    scores = {
        "speed": speed,
        "quality": quality,
        "technique": technique,
        "adaptability": adaptability,
        "fatigue": fatigue,
        "safety": safety,
    }
    oep = sum(weights[k] * scores[k] for k in weights)
    return round(oep, 1), scores


def classify_profile(oep_score: float) -> str:
    if oep_score >= 88:
        return "EXPERT — Alto rendimiento sostenido"
    if oep_score >= 75:
        return "PROFICIENT — Buen operador, mejoras menores disponibles"
    if oep_score >= 60:
        return "DEVELOPING — Operador en desarrollo, entrenamiento recomendado"
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


def compute_economic_impact(loads_per_15min: float, dark_mineral_pct: float, improved_loads: float | None = None, improved_dark_pct: float | None = None, value_per_load_usd: float = 500.0, days_per_year: int = 300):
    current = loads_per_15min * (dark_mineral_pct / 100.0) * value_per_load_usd
    improved_loads = improved_loads or loads_per_15min * 1.10
    improved_dark = improved_dark_pct or min(dark_mineral_pct + 10.0, 85.0)
    improved = improved_loads * (improved_dark / 100.0) * value_per_load_usd
    delta_15min = improved - current
    annual = delta_15min * (8 * 60 / 15) * days_per_year
    return round(current, 2), round(improved, 2), round(annual, 2)


def build_recommendations(scores: dict[str, float]):
    recs = []
    if scores["technique"] < 70:
        recs.append({
            "priority": "HIGH",
            "action": "Entrenar al operador en movimientos más suaves para reducir jerk y mejorar la consistencia del swing.",
            "expected_gain_pct": 8,
        })
    if scores["quality"] < 72:
        recs.append({
            "priority": "HIGH",
            "action": "Revisar el punto de descarga y el acceso al material para elevar la proporción de mineral oscuro útil.",
            "expected_gain_pct": 12,
        })
    if scores["fatigue"] < 70:
        recs.append({
            "priority": "HIGH",
            "action": "Introducir control de deriva operacional por bloques para detectar degradación de suavidad antes de que afecte todo el turno.",
            "expected_gain_pct": 6,
        })
    if scores["adaptability"] < 75:
        recs.append({
            "priority": "MEDIUM",
            "action": "Entrenar el patrón más lento de operación lateral para reducir la penalidad entre posiciones izquierda y derecha.",
            "expected_gain_pct": 4,
        })
    if scores["speed"] < 80:
        recs.append({
            "priority": "MEDIUM",
            "action": "Coordinar mejor el posicionamiento del camión para reducir microdemoras entre ciclos.",
            "expected_gain_pct": 3,
        })
    while len(recs) < 3:
        recs.append({
            "priority": "LOW",
            "action": "Revisar periódicamente el OEP para consolidar mejoras y seguir la tendencia del operador.",
            "expected_gain_pct": 1,
        })
    return recs[:5]
