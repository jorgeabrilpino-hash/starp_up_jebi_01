from __future__ import annotations

import json
import os
from datetime import date


def generate_dashboard(oep_data: dict, output_dir: str = "outputs/dashboard"):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "index.html")

    data_js = json.dumps(oep_data, ensure_ascii=False)
    dims = oep_data["dimensions"]
    ov = oep_data["overall"]
    meta = oep_data["metadata"]
    econ = oep_data["economic_impact"]
    recs = oep_data["recommendations"]
    blocks = dims["fatigue"].get("smoothness_blocks", [7, 6.5, 6])
    score = ov["oep_score"]
    percentile = ov["percentile_estimate"]
    profile_type = ov["profile_type"]
    score_color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 60 else "#ef4444"

    rec_rows = []
    priority_colors = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#22c55e"}
    for rec in recs[:3]:
        color = priority_colors.get(rec["priority"], "#94a3b8")
        rec_rows.append(
            f"<tr><td><span class='badge' style='background:{color}20;color:{color};border:1px solid {color}40'>{rec['priority']}</span></td><td>{rec['action']}</td><td class='gain'>+{rec['expected_gain_pct']}%</td></tr>"
        )

    block_rows = []
    for i, value in enumerate(blocks, start=1):
        color = "#22c55e" if value >= 7 else "#f59e0b" if value >= 5.5 else "#ef4444"
        width = max(0, min(100, value / 10 * 100))
        block_rows.append(
            f"<div class='fatigue-row'><span class='block-label'>Bloque {i}</span><div class='bar-track'><div class='bar-fill' style='width:{width}%;background:{color}'></div></div><span class='block-val' style='color:{color}'>{value:.1f}</span></div>"
        )

    html = f"""<!doctype html>
<html lang='es'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>OEP Dashboard</title>
<style>
:root{{--bg:#0a0c0f;--surface:#111418;--border:#1e2530;--amber:#f59e0b;--text:#cbd5e1;--muted:#64748b;--green:#22c55e;--red:#ef4444;}}
*{{box-sizing:border-box}}
body{{margin:0;padding:24px;background:var(--bg);color:var(--text);font-family:Arial,sans-serif;}}
.header{{display:grid;grid-template-columns:1fr auto;align-items:end;gap:16px;margin-bottom:24px;}}
.grid-main,.grid-bottom{{display:grid;gap:16px;}}
.grid-main{{grid-template-columns:280px 1fr 320px;margin-bottom:16px;}}
.grid-bottom{{grid-template-columns:1fr 1fr 1fr;}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px;}}
.title{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;margin-bottom:14px;}}
.meta{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px;}}
.pill{{padding:6px 10px;border:1px solid var(--border);border-radius:999px;color:var(--muted);font-size:12px;}}
.gauge{{width:180px;height:180px;border-radius:50%;display:grid;place-items:center;margin:0 auto;border:12px solid #1e2530;position:relative;}}
.gauge::after{{content:'';position:absolute;inset:-12px;border-radius:50%;border:12px solid {score_color};clip-path:inset(0 0 {100-score}% 0);}}
.gauge-inner{{position:relative;text-align:center;z-index:1;}}
.score{{font-size:42px;font-weight:700;color:{score_color};}}
.sub{{font-size:12px;color:var(--muted);}}
.dim-item{{margin-bottom:10px;}}
.dim-head{{display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;}}
.track{{height:6px;background:#1e2530;border-radius:999px;overflow:hidden;}}
.fill{{height:100%;}}
.cycles{{display:flex;align-items:flex-end;gap:3px;height:100px;}}
.bar{{flex:1;border-radius:3px 3px 0 0;min-height:4px;}}
.fatigue-row{{display:flex;align-items:center;gap:10px;margin-bottom:10px;}}
.block-label{{width:56px;font-size:12px;color:var(--muted);}}
.bar-track{{flex:1;height:8px;background:#1e2530;border-radius:999px;overflow:hidden;}}
.bar-fill{{height:100%;}}
.block-val{{font-size:12px;width:32px;text-align:right;}}
.badge{{padding:3px 6px;border-radius:4px;font-size:11px;font-weight:700;}}
table{{width:100%;border-collapse:collapse;}}
th,td{{padding:8px;text-align:left;border-bottom:1px solid #151922;font-size:13px;vertical-align:top;}}
th{{font-size:11px;color:var(--muted);text-transform:uppercase;}}
.gain{{color:var(--green);font-weight:700;}}
.small{{font-size:12px;color:var(--muted);}}
pre{{white-space:pre-wrap;word-break:break-word;font-size:12px;color:#dbeafe;}}
</style>
</head>
<body>
<div class='header'>
  <div><h1 style='margin:0;color:var(--amber)'>OEP Mining Dashboard</h1><div class='small'>JEBI Hackaton 2026 · Hitachi EX-5600</div></div>
  <div class='small' style='text-align:right'>{date.today().isoformat()}<br>{meta['video_left']} / {meta['video_right']}<br>{meta['imu_file']}</div>
</div>
<div class='meta'>
  <div class='pill'>Duración <strong>{meta['duration_seconds']:.0f}s</strong></div>
  <div class='pill'>Ciclos <strong>{meta['total_cycles']}</strong></div>
  <div class='pill'>Ciclo promedio <strong>{dims['speed']['avg_cycle_seconds']:.1f}s</strong></div>
  <div class='pill'>Cargas/hora <strong>{dims['speed']['loads_per_hour']}</strong></div>
</div>
<div class='grid-main'>
  <div class='card'><div class='title'>OEP Score</div><div class='gauge'><div class='gauge-inner'><div class='score'>{score}</div><div class='sub'>/100 · P{percentile}</div></div></div><div style='text-align:center;margin-top:14px'>{profile_type}</div></div>
  <div class='card'><div class='title'>Resumen de datos</div><pre id='radar'></pre></div>
  <div class='card'><div class='title'>Dimensiones</div><div id='dims'></div></div>
</div>
<div class='grid-bottom'>
  <div class='card'><div class='title'>Timeline de ciclos</div><div class='cycles' id='cycles'></div></div>
  <div class='card'><div class='title'>Fatiga / deriva</div>{''.join(block_rows)}<div class='small' style='margin-top:12px'>Proyección 8h: <strong>{dims['fatigue'].get('projected_8h_smoothness', 0):.2f}/10</strong></div></div>
  <div class='card'><div class='title'>Impacto económico</div><div style='font-size:28px;color:var(--amber);font-weight:700'>+${econ['annual_improvement_usd']:,.0f}</div><div class='small'>mejora anual estimada</div><div style='margin-top:14px' class='small'>Actual 15 min: ${econ['current_value_per_15min_usd']:,.0f}<br>Mejorado 15 min: ${econ['improved_value_per_15min_usd']:,.0f}</div></div>
</div>
<div class='card' style='margin-top:16px'><div class='title'>Top recomendaciones</div><table><thead><tr><th>Prioridad</th><th>Acción</th><th>Ganancia</th></tr></thead><tbody>{''.join(rec_rows)}</tbody></table></div>
<script>
const OEP = {data_js};
const dims = OEP.dimensions;
const dimKeys = ['speed','quality','technique','adaptability','fatigue','safety'];
const dimLabels = ['Speed','Quality','Technique','Adaptability','Fatigue','Safety'];
const dimsDiv = document.getElementById('dims');
dimKeys.forEach((k,i)=>{{const s=dims[k].score; const c=s>=75?'#22c55e':s>=60?'#f59e0b':'#ef4444'; dimsDiv.innerHTML += `<div class='dim-item'><div class='dim-head'><span>${{dimLabels[i]}}</span><strong style='color:${{c}}'>${{s.toFixed(0)}}</strong></div><div class='track'><div class='fill' style='width:${{s}}%;background:${{c}}'></div></div></div>`;}});
const cycles = dims.speed.cycle_times || [];
const cyclesDiv = document.getElementById('cycles');
(cycles.length?cycles:[dims.speed.avg_cycle_seconds]).forEach((t)=>{{const c=t<50?'#22c55e':t<55?'#f59e0b':'#ef4444'; const h=Math.max(8, Math.min(100, t/70*100)); const el=document.createElement('div'); el.className='bar'; el.style.height=h+'px'; el.style.background=c; el.title=t.toFixed(1)+'s'; cyclesDiv.appendChild(el);}});
document.getElementById('radar').textContent = JSON.stringify({{overall:OEP.overall, dimensions:Object.fromEntries(dimKeys.map(k=>[k,dims[k].score]))}}, null, 2);
</script>
</body></html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
