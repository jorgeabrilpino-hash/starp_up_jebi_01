from __future__ import annotations

from datetime import date
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

KPI_SCORE_LABELS = {
    "cycle_time_score": "Cycle Time",
    "consistency_score": "Consistency",
    "side_balance_score": "Side Balance",
    "smoothness_score": "Smoothness",
    "jerk_score": "Jerk Control",
    "stability_score": "Temporal Stability",
}


def plot_oep(kpi_scores: dict[str, float], index_score: float, cycle_times: list[float], smoothness_blocks: list[float], output_path: str):
    fig = plt.figure(figsize=(18, 6))
    fig.suptitle(f"Internal Summary Index — Score: {index_score}/100", fontsize=16, fontweight="bold")

    dims = list(kpi_scores.keys())
    vals = [kpi_scores[d] for d in dims] + [kpi_scores[dims[0]]]
    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]
    ax1 = fig.add_subplot(131, polar=True)
    ax1.plot(angles, vals, "#38bdf8", linewidth=2)
    ax1.fill(angles, vals, alpha=0.25, color="#0ea5e9")
    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels([KPI_SCORE_LABELS[d] for d in dims], size=9)
    ax1.set_ylim(0, 100)
    ax1.set_title("KPI-based internal index", pad=15)

    ax2 = fig.add_subplot(132)
    cycle_indices = list(range(1, len(cycle_times) + 1)) or [1]
    times = cycle_times or [0]
    colors = ["#22c55e" if t <= 50 else "#f59e0b" if t <= 58 else "#ef4444" for t in times]
    ax2.bar(cycle_indices, times, color=colors, alpha=0.9)
    if cycle_times:
        ax2.axhline(y=np.mean(cycle_times), color="#38bdf8", linestyle="--", label=f"Promedio: {np.mean(cycle_times):.1f}s")
    ax2.axhline(y=50, color="#22c55e", linestyle="--", alpha=0.55, label="Target: 50s")
    ax2.set_xlabel("Cycle #")
    ax2.set_ylabel("Seconds")
    ax2.set_title("Cycle time distribution")
    ax2.legend(handles=[
        mpatches.Patch(color="#22c55e", label="<=50s"),
        mpatches.Patch(color="#f59e0b", label="51-58s"),
        mpatches.Patch(color="#ef4444", label=">58s"),
    ], fontsize=8)

    ax3 = fig.add_subplot(133)
    labels = [f"Block {i+1}" for i in range(len(smoothness_blocks))]
    bar_colors = ["#22c55e" if s >= 7 else "#f59e0b" if s >= 5.5 else "#ef4444" for s in smoothness_blocks]
    ax3.bar(labels, smoothness_blocks, color=bar_colors, alpha=0.9)
    ax3.set_ylim(0, 10)
    ax3.axhline(y=7.5, color="#22c55e", linestyle="--", alpha=0.5, label="Optimal")
    ax3.set_ylabel("Smoothness (0-10)")
    ax3.set_title("Temporal stability")
    ax3.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def generate_report(project_data: dict, output_path: str, ai_advice: str | None = None):
    meta = project_data["metadata"]
    kpis = project_data["standard_kpis"]
    idx = project_data["internal_summary_index"]
    recs = project_data["recommendations"]
    econ = project_data["economic_impact"]

    recs_text = "\n".join(f"  {i}. [{r['priority']}] {r['action']} (ganancia estimada: +{r['expected_gain_pct']}%)" for i, r in enumerate(recs[:3], 1))
    ai_block = f"\n7. SUGERENCIA ASISTIDA POR IA\n{ai_advice}\n" if ai_advice else ""

    methodology = (
        "Se detectaron ciclos desde gyro_roll del IMU. Sobre esa segmentación se calcularon KPIs estándar de tiempo de ciclo, "
        "variabilidad, diferencia entre lados, smoothness, jerk y estabilidad temporal. Luego se construyó un índice interno de resumen "
        "solo para visualización gerencial, no como métrica estándar de industria."
    )

    report = f"{'='*78}\nREPORTE OPERACIONAL DE PRODUCTIVIDAD DEL OPERADOR\nFecha de análisis: {date.today().isoformat()}\n{'='*78}\n\n1. CONTEXTO OPERACIONAL\nEquipo analizado: {meta['equipment_model']}\nFlota asociada: {', '.join(meta['truck_models'])}\nVentana evaluada: {meta['duration_seconds']:.0f}s\n\n2. QUE SE MIDIO Y COMO\n{methodology}\n\n3. STANDARD KPIs\n- cycle_time_avg_s: {kpis['cycle_time_avg_s']}\n- cycle_time_std_s: {kpis['cycle_time_std_s']}\n- cycle_time_cv: {kpis['cycle_time_cv']}\n- cycles_per_hour: {kpis['cycles_per_hour']}\n- estimated_trucks_per_hour: {kpis['estimated_trucks_per_hour']}\n- service_time_per_truck_min: {kpis['service_time_per_truck_min']}\n- left_cycle_time_avg_s: {kpis['left_cycle_time_avg_s']}\n- right_cycle_time_avg_s: {kpis['right_cycle_time_avg_s']}\n- side_delta_s: {kpis['side_delta_s']}\n- jerk_avg: {kpis['jerk_avg']}\n- jerk_p95: {kpis['jerk_p95']}\n- jerk_max: {kpis['jerk_max']}\n- smoothness_index: {kpis['smoothness_index']}\n- extreme_jerk_event_count: {kpis['extreme_jerk_event_count']}\n- smoothness_decay_per_block: {kpis['smoothness_decay_per_block']}\n\n4. HALLAZGOS CLAVE\n- Promedio de ciclo: {kpis['cycle_time_avg_s']}s\n- Variabilidad del ciclo (CV): {kpis['cycle_time_cv']}\n- Gap entre lados: {kpis['side_delta_s']}s\n- Jerk p95: {kpis['jerk_p95']}\n- Eventos extremos: {kpis['extreme_jerk_event_count']}\n- Proyección de smoothness a 8h: {kpis['projected_8h_smoothness']}\n\n5. INDICE INTERNO DE RESUMEN\nScore: {idx['score']}/100\nClasificación: {idx['label']}\nPercentil estimado: {idx['percentile_estimate']}\nNota: {idx['note']}\n\n6. TOP 3 RECOMENDACIONES\n{recs_text}\n\n7. IMPACTO ECONOMICO\nValor horario actual: ${econ['current_hourly_value_usd']:,.0f}\nValor horario mejorado: ${econ['improved_hourly_value_usd']:,.0f}\nMejora anual estimada: +${econ['annual_improvement_usd']:,.0f}\n{ai_block}{'='*78}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)


def generate_dashboard(project_data: dict, output_dir: str = "outputs/dashboard"):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "index.html")
    meta = project_data["metadata"]
    kpis = project_data["standard_kpis"]
    idx = project_data["internal_summary_index"]
    econ = project_data["economic_impact"]
    score = idx["score"]
    score_color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 60 else "#ef4444"

    score_cards = []
    for key, label in KPI_SCORE_LABELS.items():
        value = idx["component_scores"][key]
        color = "#22c55e" if value >= 75 else "#f59e0b" if value >= 60 else "#ef4444"
        score_cards.append(f"<div class='metric-card'><div class='metric-name'>{label}</div><div class='metric-score' style='color:{color}'>{value:.0f}</div><div class='bar'><div class='fill' style='width:{value}%;background:{color}'></div></div></div>")

    cycle_bars = []
    for t in kpis["cycle_times_s"]:
        color = "#22c55e" if t <= 50 else "#f59e0b" if t <= 58 else "#ef4444"
        h = max(10, min(120, (t / 70.0) * 110))
        cycle_bars.append(f"<div class='cycle-wrap'><div class='cycle-bar' style='height:{h}px;background:{color}' title='{t}s'></div></div>")

    suggestions_html = "".join(f"<li><strong>[{r['priority']}]</strong> {r['action']} <span class='gain'>+{r['expected_gain_pct']}%</span></li>" for r in project_data["recommendations"][:3])
    ai_html = f"<div class='card'><h3>Sugerencia empresarial asistida por IA</h3><p>{project_data['ai_advisor']['advice']}</p></div>" if project_data.get("ai_advisor", {}).get("advice") else ""

    html = f"""<!doctype html>
<html lang='es'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Operator Productivity Dashboard</title>
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
      <h1 style='margin:0;color:var(--amber)'>Operator Productivity Dashboard</h1>
      <div class='muted'>KPIs estándar de productividad para {meta['equipment_model']}</div>
      <div class='muted' style='margin-top:6px'>Flota observada: {', '.join(meta['truck_models'])}</div>
    </div>
    <div class='muted' style='text-align:right'>Fecha {date.today().isoformat()}<br>{meta['video_left']} · {meta['video_right']}<br>{meta['imu_file']}</div>
  </div>

  <div class='hero'>
    <div class='card'>
      <div class='muted'>Internal summary index</div>
      <div class='score'>{score}</div>
      <div>{idx['label']}</div>
      <div class='subscore' style='margin-top:8px'>Nota: índice interno, no estándar de industria</div>
    </div>
    <div class='card'>
      <div class='kpis'>
        <div class='kpi'><div class='name'>Cycle time avg</div><div class='val'>{kpis['cycle_time_avg_s']}s</div></div>
        <div class='kpi'><div class='name'>Cycles/hour</div><div class='val'>{kpis['cycles_per_hour']}</div></div>
        <div class='kpi'><div class='name'>Trucks/hour</div><div class='val'>{kpis['estimated_trucks_per_hour']}</div></div>
        <div class='kpi'><div class='name'>Service/truck</div><div class='val'>{kpis['service_time_per_truck_min']}m</div></div>
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
    <h3 style='margin-top:0'>KPI score components</h3>
    <div class='metrics-grid'>{''.join(score_cards)}</div>
  </div>

  <div style='display:grid;grid-template-columns:1.2fr .8fr;gap:18px'>
    <div class='card'>
      <h3 style='margin-top:0'>Cycle time by pass</h3>
      <div class='timeline'>{''.join(cycle_bars)}</div>
      <div class='muted' style='margin-top:8px'>Target operativo de referencia: 50s por pase</div>
    </div>
    <div class='card'>
      <h3 style='margin-top:0'>Temporal stability</h3>
      <div class='blocks'>
        {''.join(f"<div class='block'><div class='muted'>Block {i+1}</div><div class='val'>{v:.2f}</div></div>" for i,v in enumerate(kpis['smoothness_blocks']))}
      </div>
      <div class='muted' style='margin-top:12px'>Projected 8h smoothness: {kpis['projected_8h_smoothness']} · Side delta: {kpis['side_delta_s']}s</div>
    </div>
  </div>

  <div style='display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px'>
    <div class='card'>
      <h3 style='margin-top:0'>Standard KPIs</h3>
      <pre>{chr(10).join([f'{k}: {v}' for k,v in kpis.items() if k != 'cycle_times_s'])}</pre>
    </div>
    <div class='card'>
      <h3 style='margin-top:0'>Recomendaciones empresariales</h3>
      <ul>{suggestions_html}</ul>
    </div>
  </div>
  {ai_html}
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
