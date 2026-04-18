from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def plot_oep(scores: dict[str, float], oep_score: float, cycle_times: list[float], smoothness_blocks: list[float], output_path: str):
    fig = plt.figure(figsize=(18, 6))
    fig.suptitle(f"Operator Efficiency Profile (OEP) — Score: {oep_score}/100", fontsize=16, fontweight="bold")

    dims = list(scores.keys())
    vals = [scores[d] for d in dims]
    vals += vals[:1]
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
    cycle_indices = list(range(1, len(cycle_times) + 1))
    colors = ["green" if t < 50 else "orange" if t < 55 else "red" for t in cycle_times] or ["orange"]
    times = cycle_times or [0]
    ax2.bar(cycle_indices or [1], times, color=colors, alpha=0.8)
    if cycle_times:
        ax2.axhline(y=np.mean(cycle_times), color="blue", linestyle="--", label=f"Promedio: {np.mean(cycle_times):.1f}s")
    ax2.axhline(y=45, color="green", linestyle="--", alpha=0.5, label="Teórico: 45s")
    ax2.set_xlabel("Ciclo #")
    ax2.set_ylabel("Duración (s)")
    ax2.set_title("Duración de Ciclos Operativos")
    green_p = mpatches.Patch(color="green", label="<50s (excelente)")
    orange_p = mpatches.Patch(color="orange", label="50-55s (normal)")
    red_p = mpatches.Patch(color="red", label=">55s (lento)")
    ax2.legend(handles=[green_p, orange_p, red_p], fontsize=7)

    ax3 = fig.add_subplot(133)
    block_labels = [f"Bloque {i + 1}" for i in range(len(smoothness_blocks))]
    bar_colors = ["#2ecc71" if s >= 7 else "#f39c12" if s >= 5.5 else "#e74c3c" for s in smoothness_blocks]
    ax3.bar(block_labels, smoothness_blocks, color=bar_colors, alpha=0.85)
    ax3.set_ylim(0, 10)
    ax3.axhline(y=7.5, color="green", linestyle="--", alpha=0.5, label="Óptimo: 7.5")
    ax3.set_ylabel("Smoothness Score (0-10)")
    ax3.set_title("Evolución de Suavidad (Fatiga)")
    ax3.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
