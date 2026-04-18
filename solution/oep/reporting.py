from __future__ import annotations

from datetime import date
import json
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def plot_oep(scores: dict[str, float], oep_score: float, cycle_times: list[float], smoothness_blocks: list[float], output_path: str):
    fig = plt.figure(figsize=(18, 6))
    fig.suptitle(f"Operator Efficiency Profile (OEP) — Score: {oep_score}/100", fontsize=16, fontweight="bold")
    dims = list(scores.keys())
    vals = [scores[d] for d in dims] + [scores[dims[0]]]
    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]
    ax1 = fig.add_subplot(131, polar=True)
    ax1.plot(angles, vals, "b-o", linewidth=2)
    ax1.fill(angles, vals, alpha=0.2, color="blue")
    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels([d.upper() for d in dims], size=9)
    ax1.set_ylim(0, 100)
    ax1.set_title("Perfil 6 Dimensiones", pad=15)

    ax2 = fig.add_subplot(132)
    cycle_indices = list(range(1, len(cycle_times) + 1)) or [1]
    times = cycle_times or [0]
    colors = ["green" if t < 50 else "orange" if t < 55 else "red" for t in times]
    ax2.bar(cycle_indices, times, color=colors, alpha=0.8)
    if cycle_times:
        ax2.axhline(y=np.mean(cycle_times), color="blue", linestyle="--", label=f"Promedio: {np.mean(cycle_times):.1f}s")
    ax2.axhline(y=45, color="green", linestyle="--", alpha=0.5, label="Teórico: 45s")
    ax2.set_xlabel("Ciclo #")
    ax2.set_ylabel("Duración (s)")
    ax2.set_title("Duración de Ciclos Operativos")
    ax2.legend(handles=[mpatches.Patch(color="green", label="<50s"), mpatches.Patch(color="orange", label="50-55s"), mpatches.Patch(color="red", label=">55s")], fontsize=7)

    ax3 = fig.add_subplot(133)
    labels = [f"Bloque {i+1}" for i in range(len(smoothness_blocks))]
    bar_colors = ["#2ecc71" if s >= 7 else "#f39c12" if s >= 5.5 else "#e74c3c" for s in smoothness_blocks]
    ax3.bar(labels, smoothness_blocks, color=bar_colors, alpha=0.85)
    ax3.set_ylim(0, 10)
    ax3.axhline(y=7.5, color="green", linestyle="--", alpha=0.5, label="Óptimo: 7.5")
    ax3.set_ylabel("Smoothness Score (0-10)")
    ax3.set_title("Evolución de Suavidad (Fatiga)")
    ax3.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def generate_report(oep_data: dict, output_path: str, ai_advice: str | None = None):
    dims = oep_data["dimensions"]
    ov = oep_data["overall"]
    meta = oep_data["metadata"]
    recs = oep_data["recommendations"]
    econ = oep_data["economic_impact"]
    strengths = [f"{k.capitalize()} ({v['score']:.0f}/100)" for k, v in dims.items() if v.get("score", 0) >= 75]
    weaknesses = [f"{k.capitalize()} ({v['score']:.0f}/100)" for k, v in dims.items() if v.get("score", 0) < 70]
    recs_text = "\n".join(f"  {i}. [{r['priority']}] {r['action']} (ganancia estimada: +{r['expected_gain_pct']}%)" for i, r in enumerate(recs[:3], 1))
    ai_block = f"\n7. ASISTENTE IA\n{ai_advice}\n" if ai_advice else ""
    report = f"{'='*70}\nOPERATOR EFFICIENCY PROFILE (OEP) — REPORTE EJECUTIVO\nFecha de análisis: {date.today().isoformat()}\n{'='*70}\n\n1. RESUMEN EJECUTIVO\nEl operador obtuvo un OEP Score de {ov['oep_score']}/100, perfil {ov['profile_type']}, percentil {ov['percentile_estimate']}. Durante {meta['duration_seconds']:.0f}s se completaron {meta['total_cycles']} ciclos con promedio {dims['speed']['avg_cycle_seconds']:.1f}s y {dims['speed']['loads_per_hour']} cargas/hora.\n\n2. FORTALEZAS\n{', '.join(strengths) if strengths else 'No se identificaron fortalezas dominantes.'}\n\n3. AREAS CRITICAS\n{', '.join(weaknesses) if weaknesses else 'No se detectaron dimensiones críticas.'}\n\n4. TOP 3 RECOMENDACIONES\n{recs_text}\n\n5. TECNICA Y FATIGA\nSmoothness actual: {dims['technique'].get('smoothness_index',0):.2f}/10. Proyección 8h: {dims['fatigue'].get('projected_8h_smoothness',0):.2f}/10.\n\n6. IMPACTO ECONOMICO\nMejora anual estimada: +${econ['annual_improvement_usd']:,.0f} USD\n{ai_block}{'='*70}\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)


def generate_dashboard(oep_data: dict, output_dir: str = "outputs/dashboard"):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "index.html")
    dims = oep_data["dimensions"]
    ov = oep_data["overall"]
    meta = oep_data["metadata"]
    econ = oep_data["economic_impact"]
    score = ov["oep_score"]
    score_color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 60 else "#ef4444"
    dim_html = []
    for key in ["speed", "quality", "technique", "adaptability", "fatigue", "safety"]:
        value = dims[key]["score"]
        color = "#22c55e" if value >= 75 else "#f59e0b" if value >= 60 else "#ef4444"
        dim_html.append(f"<div><div style='font-size:12px;color:#94a3b8'>{key.upper()} <strong style='color:{color}'>{value:.0f}</strong></div><div style='height:8px;background:#1e2530;border-radius:999px;overflow:hidden;margin:6px 0 12px'><div style='height:100%;width:{value}%;background:{color}'></div></div></div>")
    summary_json = json.dumps({"overall": ov, "speed": dims["speed"], "technique": dims["technique"]}, ensure_ascii=False, indent=2)
    html = f"""<!doctype html>
<html lang='es'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>OEP Dashboard</title>
</head>
<body style='margin:0;padding:24px;background:#0a0c0f;color:#cbd5e1;font-family:Arial,sans-serif'>
  <div style='background:#111418;border:1px solid #1e2530;border-radius:8px;padding:18px;margin-bottom:16px'>
    <h1 style='margin:0;color:#f59e0b'>OEP Mining Dashboard</h1>
    <div style='font-size:12px;color:#94a3b8;margin-top:6px'>Fecha {date.today().isoformat()} · {meta['video_left']} · {meta['imu_file']}</div>
    <div style='margin-top:10px;font-size:12px;color:#94a3b8'>Duración <strong>{meta['duration_seconds']:.0f}s</strong> · Ciclos <strong>{meta['total_cycles']}</strong> · Cargas/hora <strong>{dims['speed']['loads_per_hour']}</strong></div>
  </div>
  <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px'>
    <div style='background:#111418;border:1px solid #1e2530;border-radius:8px;padding:18px'>
      <div style='font-size:12px;color:#94a3b8'>OEP SCORE</div>
      <div style='font-size:56px;font-weight:700;color:{score_color}'>{score}</div>
      <div>{ov['profile_type']}</div>
    </div>
    <div style='background:#111418;border:1px solid #1e2530;border-radius:8px;padding:18px'>
      <div style='font-size:12px;color:#94a3b8'>IMPACTO ANUAL</div>
      <div style='font-size:34px;font-weight:700;color:#f59e0b'>+${econ['annual_improvement_usd']:,.0f}</div>
      <div style='font-size:12px;color:#94a3b8'>Mejorado 15 min: ${econ['improved_value_per_15min_usd']:,.0f}</div>
    </div>
    <div style='background:#111418;border:1px solid #1e2530;border-radius:8px;padding:18px'>
      <div style='font-size:12px;color:#94a3b8'>RESUMEN</div>
      <pre style='white-space:pre-wrap;color:#dbeafe;font-size:12px'>{summary_json}</pre>
    </div>
  </div>
  <div style='background:#111418;border:1px solid #1e2530;border-radius:8px;padding:18px;margin-top:16px'>
    <h3 style='margin-top:0'>Dimensiones</h3>
    {''.join(dim_html)}
  </div>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
