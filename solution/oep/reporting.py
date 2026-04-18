from __future__ import annotations

from datetime import date
import json
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

DIM_LABELS = {
    "cycle_efficiency": "Cycle Efficiency",
    "rhythm_consistency": "Rhythm Consistency",
    "motion_control": "Motion Control",
    "side_balance": "Side Balance",
    "endurance": "Endurance",
    "operational_risk": "Operational Risk",
}


def plot_oep(scores: dict[str, float], oep_score: float, cycle_times: list[float], smoothness_blocks: list[float], output_path: str):
    fig = plt.figure(figsize=(18, 6))
    fig.suptitle(f"Operator Efficiency Profile (OEP) — Score: {oep_score}/100", fontsize=16, fontweight="bold")

    dims = list(scores.keys())
    vals = [scores[d] for d in dims] + [scores[dims[0]]]
    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]
    ax1 = fig.add_subplot(131, polar=True)
    ax1.plot(angles, vals, "#38bdf8", linewidth=2)
    ax1.fill(angles, vals, alpha=0.25, color="#0ea5e9")
    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels([DIM_LABELS[d] for d in dims], size=9)
    ax1.set_ylim(0, 100)
    ax1.set_title("Perfil 6 Dimensiones", pad=15)

    ax2 = fig.add_subplot(132)
    cycle_indices = list(range(1, len(cycle_times) + 1)) or [1]
    times = cycle_times or [0]
    colors = ["#22c55e" if t <= 50 else "#f59e0b" if t <= 58 else "#ef4444" for t in times]
    ax2.bar(cycle_indices, times, color=colors, alpha=0.9)
    if cycle_times:
        ax2.axhline(y=np.mean(cycle_times), color="#38bdf8", linestyle="--", label=f"Promedio: {np.mean(cycle_times):.1f}s")
    ax2.axhline(y=50, color="#22c55e", linestyle="--", alpha=0.55, label="Target: 50s")
    ax2.set_xlabel("Ciclo #")
    ax2.set_ylabel("Duración (s)")
    ax2.set_title("Timeline de ciclos")
    ax2.legend(handles=[
        mpatches.Patch(color="#22c55e", label="<=50s"),
        mpatches.Patch(color="#f59e0b", label="51-58s"),
        mpatches.Patch(color="#ef4444", label=">58s"),
    ], fontsize=8)

    ax3 = fig.add_subplot(133)
    labels = [f"Bloque {i+1}" for i in range(len(smoothness_blocks))]
    bar_colors = ["#22c55e" if s >= 7 else "#f59e0b" if s >= 5.5 else "#ef4444" for s in smoothness_blocks]
    ax3.bar(labels, smoothness_blocks, color=bar_colors, alpha=0.9)
    ax3.set_ylim(0, 10)
    ax3.axhline(y=7.5, color="#22c55e", linestyle="--", alpha=0.5, label="Óptimo")
    ax3.set_ylabel("Smoothness (0-10)")
    ax3.set_title("Resistencia operacional")
    ax3.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def generate_report(oep_data: dict, output_path: str, ai_advice: str | None = None):
    dims = oep_data["dimensions"]
    ov = oep_data["overall"]
    meta = oep_data["metadata"]
    metrics = oep_data["metrics"]
    recs = oep_data["recommendations"]
    econ = oep_data["economic_impact"]

    strengths = [f"{DIM_LABELS[k]} ({v['score']:.0f}/100)" for k, v in dims.items() if v.get("score", 0) >= 75]
    weaknesses = [f"{DIM_LABELS[k]} ({v['score']:.0f}/100)" for k, v in dims.items() if v.get("score", 0) < 70]
    recs_text = "\n".join(f"  {i}. [{r['priority']}] {r['action']} (ganancia estimada: +{r['expected_gain_pct']}%)" for i, r in enumerate(recs[:3], 1))
    ai_block = f"\n7. SUGERENCIA ASISTIDA POR IA\n{ai_advice}\n" if ai_advice else ""

    methodology = (
        "Se detectaron ciclos desde gyro_roll del IMU, luego se calcularon métricas de duración, variabilidad, control del movimiento, "
        "balance entre lados, deriva temporal y eventos extremos. El modelo del equipo base es Hitachi EX-5600 y la referencia operativa se interpreta "
        "contra camiones CAT 793F / EH4000 AC-3 con una proxy de 4.5 pases por camión."
    )

    report = f"{'='*78}\nOPERATOR EFFICIENCY PROFILE (OEP) — REPORTE EJECUTIVO EMPRESARIAL\nFecha de análisis: {date.today().isoformat()}\n{'='*78}\n\n1. CONTEXTO OPERACIONAL\nEquipo analizado: {meta['equipment_model']}\nFlota asociada: {', '.join(meta['truck_models'])}\nVentana evaluada: {meta['duration_seconds']:.0f}s\nCiclos detectados: {meta['total_cycles']}\n\n2. QUE SE MIDIO Y COMO\n{methodology}\n\n3. RESUMEN EJECUTIVO\nEl operador obtuvo un OEP Score de {ov['oep_score']}/100, perfil {ov['profile_type']}, percentil {ov['percentile_estimate']}.\nSe estiman {metrics['cycles_per_hour']} ciclos por hora y {metrics['estimated_trucks_per_hour']} camiones servidos por hora, con {metrics['estimated_service_minutes']} min por camión.\n\n4. FORTALEZAS\n{', '.join(strengths) if strengths else 'No se identificaron fortalezas dominantes.'}\n\n5. AREAS CRITICAS\n{', '.join(weaknesses) if weaknesses else 'No se detectaron dimensiones críticas.'}\n\n6. HALLAZGOS CLAVE\n- Promedio de ciclo: {metrics['avg_cycle_seconds']}s\n- Variabilidad del ciclo (CV): {metrics['cycle_cv']}\n- Gap entre lados: {metrics['side_gap_seconds']}s\n- Jerk p95: {metrics['p95_jerk']}\n- Eventos extremos: {metrics['extreme_jerk_events']}\n- Proyección de smoothness a 8h: {metrics['projected_8h_smoothness']}\n\n7. TOP 3 RECOMENDACIONES\n{recs_text}\n\n8. IMPACTO ECONOMICO\nValor horario actual: ${econ['current_hourly_value_usd']:,.0f}\nValor horario mejorado: ${econ['improved_hourly_value_usd']:,.0f}\nMejora anual estimada: +${econ['annual_improvement_usd']:,.0f}\n{ai_block}{'='*78}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)


def generate_dashboard(oep_data: dict, output_dir: str = "outputs/dashboard"):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "index.html")
    dims = oep_data["dimensions"]
    ov = oep_data["overall"]
    meta = oep_data["metadata"]
    metrics = oep_data["metrics"]
    econ = oep_data["economic_impact"]
    score = ov["oep_score"]
    score_color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 60 else "#ef4444"

    dim_cards = []
    for key in DIM_LABELS:
        value = dims[key]["score"]
        color = "#22c55e" if value >= 75 else "#f59e0b" if value >= 60 else "#ef4444"
        dim_cards.append(
            f"<div class='metric-card'><div class='metric-name'>{DIM_LABELS[key]}</div><div class='metric-score' style='color:{color}'>{value:.0f}</div><div class='bar'><div class='fill' style='width:{value}%;background:{color}'></div></div></div>"
        )

    cycle_bars = []
    for t in metrics["cycle_times"]:
        color = "#22c55e" if t <= 50 else "#f59e0b" if t <= 58 else "#ef4444"
        h = max(10, min(120, (t / 70.0) * 110))
        cycle_bars.append(f"<div class='cycle-wrap'><div class='cycle-bar' style='height:{h}px;background:{color}' title='{t}s'></div></div>")

    suggestions_html = "".join(
        f"<li><strong>[{r['priority']}]</strong> {r['action']} <span class='gain'>+{r['expected_gain_pct']}%</span></li>"
        for r in oep_data["recommendations"][:3]
    )
    ai_html = f"<div class='card'><h3>Sugerencia empresarial asistida por IA</h3><p>{oep_data['ai_advisor']['advice']}</p></div>" if oep_data.get("ai_advisor", {}).get("advice") else ""

    html = f"""<!doctype html>
<html lang='es'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>OEP Dashboard</title>
<style>
:root{{--bg:#0a0f16;--card:#111827;--border:#263446;--text:#dbe7f3;--muted:#94a3b8;--amber:#f59e0b;--green:#22c55e;--red:#ef4444;--blue:#38bdf8}}
body{{margin:0;padding:24px;background:linear-gradient(180deg,#081019,#0b1220);color:var(--text);font-family:Inter,Arial,sans-serif}}
.container{{max-width:1320px;margin:0 auto}} .card{{background:rgba(17,24,39,.95);border:1px solid var(--border);border-radius:14px;padding:18px;margin-bottom:18px;box-shadow:0 10px 30px rgba(0,0,0,.18)}}
.header{{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}} .muted{{color:var(--muted)}} .hero{{display:grid;grid-template-columns:280px 1fr 340px;gap:18px;margin-top:18px}}
.score{{font-size:64px;font-weight:800;color:{score_color};line-height:1}} .subscore{{font-size:13px;color:var(--muted)}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}} .kpi{{background:#0c1522;border:1px solid var(--border);border-radius:12px;padding:14px}} .kpi .name{{font-size:12px;color:var(--muted)}} .kpi .val{{font-size:28px;font-weight:700;margin-top:6px}}
.metrics-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}} .metric-card{{background:#0c1522;border:1px solid var(--border);border-radius:12px;padding:14px}} .metric-name{{font-size:13px;color:var(--muted)}} .metric-score{{font-size:30px;font-weight:800;margin:8px 0}} .bar{{height:8px;background:#1e293b;border-radius:999px;overflow:hidden}} .fill{{height:100%}}
.timeline{{display:flex;align-items:flex-end;gap:4px;height:150px;padding-top:10px}} .cycle-wrap{{flex:1;display:flex;align-items:flex-end}} .cycle-bar{{width:100%;border-radius:6px 6px 0 0}}
.blocks{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}} .block{{background:#0c1522;border:1px solid var(--border);border-radius:12px;padding:12px}} .block .val{{font-size:26px;font-weight:700}}
ul{{margin:0;padding-left:18px}} li{{margin:10px 0;line-height:1.45}} .gain{{color:var(--green);font-weight:700;margin-left:8px}} pre{{white-space:pre-wrap;color:#cfe6ff;background:#0c1522;border:1px solid var(--border);border-radius:10px;padding:12px}}
</style>
</head>
<body>
<div class='container'>
  <div class='card header'>
    <div>
      <h1 style='margin:0;color:var(--amber)'>Operator Efficiency Profile</h1>
      <div class='muted'>Proyecto empresarial de evaluación de operador para {meta['equipment_model']}</div>
      <div class='muted' style='margin-top:6px'>Flota observada: {', '.join(meta['truck_models'])}</div>
    </div>
    <div class='muted' style='text-align:right'>Fecha {date.today().isoformat()}<br>{meta['video_left']} · {meta['video_right']}<br>{meta['imu_file']}</div>
  </div>

  <div class='hero'>
    <div class='card'>
      <div class='muted'>OEP Score Global</div>
      <div class='score'>{score}</div>
      <div>{ov['profile_type']}</div>
      <div class='subscore' style='margin-top:8px'>Percentil estimado: {ov['percentile_estimate']}</div>
    </div>
    <div class='card'>
      <div class='kpis'>
        <div class='kpi'><div class='name'>Ciclos/hora</div><div class='val'>{metrics['cycles_per_hour']}</div></div>
        <div class='kpi'><div class='name'>Camiones/hora</div><div class='val'>{metrics['estimated_trucks_per_hour']}</div></div>
        <div class='kpi'><div class='name'>Min/camión</div><div class='val'>{metrics['estimated_service_minutes']}</div></div>
        <div class='kpi'><div class='name'>CV ciclo</div><div class='val'>{metrics['cycle_cv']}</div></div>
      </div>
    </div>
    <div class='card'>
      <div class='muted'>Impacto económico</div>
      <div class='score' style='font-size:42px;color:var(--amber)'>+${econ['annual_improvement_usd']:,.0f}</div>
      <div class='subscore'>Valor horario actual: ${econ['current_hourly_value_usd']:,.0f}</div>
      <div class='subscore'>Valor horario mejorado: ${econ['improved_hourly_value_usd']:,.0f}</div>
    </div>
  </div>

  <div class='card'>
    <h3 style='margin-top:0'>Dimensiones del operador</h3>
    <div class='metrics-grid'>{''.join(dim_cards)}</div>
  </div>

  <div style='display:grid;grid-template-columns:1.2fr .8fr;gap:18px'>
    <div class='card'>
      <h3 style='margin-top:0'>Timeline de ciclos</h3>
      <div class='timeline'>{''.join(cycle_bars)}</div>
      <div class='muted' style='margin-top:8px'>Target operativo de referencia: 50s por pase</div>
    </div>
    <div class='card'>
      <h3 style='margin-top:0'>Deriva y resistencia operacional</h3>
      <div class='blocks'>
        {''.join(f"<div class='block'><div class='muted'>Bloque {i+1}</div><div class='val'>{v:.2f}</div></div>" for i,v in enumerate(metrics['smoothness_blocks']))}
      </div>
      <div class='muted' style='margin-top:12px'>Proyección 8h: {metrics['projected_8h_smoothness']} · Gap entre lados: {metrics['side_gap_seconds']}s</div>
    </div>
  </div>

  <div style='display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px'>
    <div class='card'>
      <h3 style='margin-top:0'>Recomendaciones empresariales</h3>
      <ul>{suggestions_html}</ul>
    </div>
    <div class='card'>
      <h3 style='margin-top:0'>Método resumido</h3>
      <pre>1. Detectar ciclos desde gyro_roll.
2. Medir duración, variabilidad y outliers.
3. Evaluar control con smoothness y jerk.
4. Comparar equilibrio izquierda/derecha.
5. Medir deriva temporal por bloques.
6. Traducir métricas a riesgo, coaching e impacto económico.</pre>
    </div>
  </div>
  {ai_html}
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
