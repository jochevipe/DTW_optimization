"""
Binary-Diversity-Predictive — controlador A10 (diversidad + detección predictiva).
Corre todas las MHs, muestra métricas DTW + diversidad en consola, y genera gráficos.

Uso (desde la raíz del proyecto):
    python -m binary_diversity_predictive.resultados
"""

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

from mkp_common import BinaryPSO, GeneticAlgorithm, BinaryGWO, BinaryDE, cargar_instancia
from mkp_common.results import save_results

from .runner import run_epochs
from .config import (
    DECISION_RULE,
    DTW_CFG,
    INDICE_INSTANCIA,
    NUM_ITERACIONES,
    NUM_PARTICULAS,
    RUTA_INSTANCIA,
    EPOCHS,
    SEMILLA,
)

# MHs a comparar — agregar nuevas acá
MHS = {
    "PSO": BinaryPSO,
    "GA": GeneticAlgorithm,
    "GWO": BinaryGWO,
    "DE": BinaryDE,
}


# =============================================================================
# CONSOLA: métricas por epoch
# =============================================================================


def print_epoch_results(nombre: str, resultados: list, inst: dict):
    """Imprime fitness + DTW + diversidad por cada epoch."""
    optimo = inst["optimo"]

    print(f"\n{'=' * 70}")
    print(f"  {nombre}")
    print(f"{'=' * 70}")

    for res in resultados:
        gap = f"Gap={100 - res['ganancia']:.2f}%" if optimo > 0 else "Gap=N/A"
        print(
            f"\n  Epoch {res['epoch']:02d} | "
            f"Fitness={res['mejor_fitness']:.1f} | "
            f"Fires={res['fire_count']} | {gap} | "
            f"t={res['tiempo']:.2f}s"
        )

        div_states = [
            h["_diversity_state"]
            for h in res["historial_dtw"]
            if h.get("ready") and "_diversity_state" in h
        ]
        if div_states:
            divs = [s["hamming"] for s in div_states]
            last = div_states[-1]
            print(
                f"    DIV  hamming={np.mean(divs):.4f} (+-{np.std(divs):.4f}) | "
                f"th_low={last['theta_div_low']:.4f} | "
                f"th_high={last['theta_div_high']:.4f} | "
                f"Decision: {DECISION_RULE}"
            )

    fits = [r["mejor_fitness"] for r in resultados]
    print(f"\n  {'-' * 50}")
    print(f"  Mejor={np.max(fits):.1f}  Prom={np.mean(fits):.1f}  "
          f"Peor={np.min(fits):.1f}  Std={np.std(fits):.1f}")
    if optimo > 0:
        print(f"  Optimo={optimo:.0f}  Gap={100 - np.max(fits) / optimo * 100:.2f}%")


# Colores por MH
MH_COLORS = {
    "PSO": "#2196F3",
    "BinaryPSO": "#2196F3",
    "GA": "#E91E63",
    "GWO": "#4CAF50",
    "DE": "#FF9800",
}

# Colores comunes (estilo paper)
COLORS = {
    "fire_marker": "#c0392b",
    "exit_marker": "#e67e22",
    "explore_bg": "#e74c3c",
    "optimum": "#7f8c8d",
    "delta": "#2980b9",
}


def _get_explore_ranges(hist_mode):
    """Return inclusive ranges where the recorded fitness used explore."""
    ranges = []
    in_explore = False
    start = 0
    for i, m in enumerate(hist_mode):
        if m == "explore" and not in_explore:
            start = i
            in_explore = True
        elif m != "explore" and in_explore:
            ranges.append((start, i - 1))
            in_explore = False
    if in_explore:
        ranges.append((start, len(hist_mode) - 1))
    return ranges


def _get_state_entries(hist_mode):
    """Iteraciones con transición exploit -> explore (entradas a exploración)."""
    transitions = []
    for i in range(1, len(hist_mode)):
        if hist_mode[i] == "explore" and hist_mode[i - 1] != "explore":
            transitions.append(i)
    return transitions


def _get_state_exits(hist_mode):
    """Iteraciones con transición explore -> exploit (salidas de exploración)."""
    transitions = []
    for i in range(1, len(hist_mode)):
        if hist_mode[i] == "exploit" and hist_mode[i - 1] != "exploit":
            transitions.append(i)
    return transitions


def _div_series(hist_dtw):
    """(iters, diversity, theta_low, theta_high, delta, trend) en iteraciones listas."""
    iters, divs, lows, highs, deltas, trends = [], [], [], [], [], []
    for i, h in enumerate(hist_dtw):
        st = h.get("_diversity_state")
        if not st:
            continue
        iters.append(i)
        divs.append(st["hamming"])
        lows.append(st["theta_div_low"])
        highs.append(st["theta_div_high"])
        deltas.append(st["delta"])
        trends.append(st["trend_slope"])
    return iters, divs, lows, highs, deltas, trends


def generate_plots(resultados_por_mh: dict, inst: dict, save_dir: str):
    """
    Genera 2 paneles estilo paper:
      1. Fitness: explore-state lines + entry/exit markers + optimum.
      2. Señal A10: delta + tendencia (eje izq.) y diversidad vs umbrales
         P20/P50 (eje der.) por MH.
    """
    nombres = list(resultados_por_mh.keys())

    # Seleccionar el mejor epoch de cada MH
    mejores = {}
    for nombre in nombres:
        resultados = resultados_por_mh[nombre]
        idx = int(np.argmax([r["mejor_fitness"] for r in resultados]))
        mejores[nombre] = resultados[idx]

    optimo = inst["optimo"]

    # --- Estilo paper ---
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "legend.fontsize": 8,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 6.5), sharex=True,
        gridspec_kw={"height_ratios": [1.3, 1]},
    )
    ax2_twin = ax2.twinx()

    # =========================================================================
    # Panel 1: FITNESS SUPERPUESTO con líneas punteadas en explore
    # =========================================================================
    for nombre in nombres:
        res = mejores[nombre]
        hist_fit = res["historial_fitness"]
        hist_mode = res["historial_modos"]
        color = MH_COLORS.get(nombre, "#666666")

        explore_ranges = _get_explore_ranges(hist_mode)
        state_entries = _get_state_entries(hist_mode)
        state_exits = _get_state_exits(hist_mode)

        # Crear máscara de explore
        is_explore = [False] * len(hist_fit)
        for s, e in explore_ranges:
            for j in range(s, min(e + 1, len(hist_fit))):
                is_explore[j] = True

        # Dibujar segmentos con diferentes estilos
        prev_type = is_explore[0]
        seg_start = 0
        for k in range(1, len(hist_fit)):
            if is_explore[k] != prev_type:
                style = "--" if prev_type else "-"
                ax1.plot(
                    range(seg_start, k + 1),
                    hist_fit[seg_start:k + 1],
                    color=color, linewidth=1.5, linestyle=style,
                    zorder=3,
                )
                seg_start = k
                prev_type = is_explore[k]
        # Último segmento
        style = "--" if prev_type else "-"
        ax1.plot(
            range(seg_start, len(hist_fit)),
            hist_fit[seg_start:],
            color=color, linewidth=1.5, linestyle=style,
            zorder=3,
        )

        # Leyenda (una sola entrada por MH)
        ax1.plot(
            [], [], color=color, linewidth=1.5, linestyle="-",
            label=f"{nombre} (max={res['mejor_fitness']:.1f}, fires={res['fire_count']})",
        )

        # Entry markers (exploit -> explore)
        if state_entries:
            entry_fits = [hist_fit[i] for i in state_entries]
            ax1.scatter(
                state_entries, entry_fits, color=COLORS["fire_marker"],
                marker="v", s=30, zorder=5,
                edgecolors="white", linewidths=0.3,
            )
        # Exit markers (explore -> exploit)
        if state_exits:
            exit_fits = [hist_fit[i] for i in state_exits]
            ax1.scatter(
                state_exits, exit_fits, color=COLORS["exit_marker"],
                marker="^", s=28, zorder=5,
                edgecolors="white", linewidths=0.3,
            )

    # Óptimo
    if optimo > 0:
        ax1.axhline(
            y=optimo, color=COLORS["optimum"], linestyle="--",
            linewidth=1, alpha=0.7, label=f"Known optimum ({optimo})",
        )

    # Leyenda de estilos de línea
    ax1.plot([], [], color="gray", linewidth=1.5, linestyle="-", label="Exploit")
    ax1.plot([], [], color="gray", linewidth=1.5, linestyle="--", label="Explore")
    ax1.scatter(
        [], [], color=COLORS["fire_marker"], marker="v", s=30, label="Enter explore"
    )
    ax1.scatter(
        [], [], color=COLORS["exit_marker"], marker="^", s=28, label="Exit explore"
    )

    ax1.set_ylabel("Fitness")
    ax1.set_title(f"Binary-Diversity-Predictive — All MHs (seed={SEMILLA})")
    ax1.legend(loc="lower right", framealpha=0.9)
    ax1.grid(True, alpha=0.2, linestyle=":")

    # =========================================================================
    # Panel 2: señal A10 — delta + tendencia (izq.) y diversidad vs umbrales (der.)
    # =========================================================================
    for nombre in nombres:
        res = mejores[nombre]
        hist_dtw = res["historial_dtw"]
        color = MH_COLORS.get(nombre, "#666666")

        iters, divs, lows, highs, deltas, trends = _div_series(hist_dtw)
        if not iters:
            continue

        # Eje izquierdo: delta (sólida) + tendencia (dashed)
        ax2.plot(
            iters, deltas, color=color, linewidth=1.3,
            label=rf"$\delta$ {nombre}", zorder=3,
        )
        trend_ok = [(i, t) for i, t in zip(iters, trends) if t is not None]
        if trend_ok:
            t_iters = [i for i, _ in trend_ok]
            t_vals = [t for _, t in trend_ok]
            ax2.plot(
                t_iters, t_vals, color=color, linewidth=0.9,
                linestyle="--", alpha=0.6, zorder=2,
                label=rf"trend {nombre}",
            )

        # Eje derecho: diversidad (sólida) + umbrales P20/P50 (punteada)
        ax2_twin.plot(
            iters, divs, color=color, linewidth=1.0, linestyle="-",
            alpha=0.9, zorder=3, label=rf"div {nombre}",
        )
        ax2_twin.plot(
            iters, lows, color=color, linewidth=0.8, linestyle=":",
            alpha=0.5, zorder=2,
        )
        ax2_twin.plot(
            iters, highs, color=color, linewidth=0.8, linestyle=":",
            alpha=0.9, zorder=2,
        )

    # Referencia cero para la pendiente (rama predictiva)
    ax2.axhline(y=0.0, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)

    ax2.set_xlabel("Iteration")
    ax2.set_ylabel(r"$\delta$ (solid) / trend slope (dashed)")
    ax2_twin.set_ylabel("Hamming diversity / P20-P50 thresholds (dotted)")
    ax2.set_title(
        "A10 signal — delta + rising-delta trend (left), "
        "diversity vs P20/P50 thresholds (right)"
    )
    ax2.legend(loc="upper left", framealpha=0.9, fontsize=7)
    ax2_twin.legend(loc="upper right", framealpha=0.9, fontsize=6)
    ax2.grid(True, alpha=0.2, linestyle=":")

    plt.tight_layout(h_pad=1.5)

    # --- Guardar ---
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    # Derivar inst_name del save_dir (funciona tanto standalone como desde HPC)
    parts = Path(save_dir).parts
    inst_label = [p for p in parts if "_" in p and p.split("_")[0].startswith("mknapcb")]
    inst_name = inst_label[0].rsplit("_", 1)[0] if inst_label else Path(RUTA_INSTANCIA).stem
    for ext in ("png", "pdf"):
        path = f"{save_dir}/binary_diversity_predictive_{inst_name}.{ext}"
        fig.savefig(path)
        print(f"  Saved: {path}")

    if "ipykernel" in sys.modules:
        plt.show()
    plt.close(fig)


# =============================================================================
# MAIN
# =============================================================================


def main():
    inst = cargar_instancia(RUTA_INSTANCIA, idx=INDICE_INSTANCIA)

    print("=" * 70)
    print("  RESULTADOS MAESTRO — Binary-Diversity-Predictive")
    print("=" * 70)
    print(f"  Decision rule: {DECISION_RULE}")
    print(f"  Instancia: {RUTA_INSTANCIA}[{INDICE_INSTANCIA}]")
    print(f"  n={inst['n']}, m={inst['m']}")
    print(f"  Particulas/Pop: {NUM_PARTICULAS}, Iteraciones: {NUM_ITERACIONES}, "
          f"Epochs: {EPOCHS}")
    print(f"  DTW: window={DTW_CFG.window}, ddtw={DTW_CFG.use_ddtw}")

    # Crear carpeta de salida con timestamp
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    inst_name = Path(RUTA_INSTANCIA).stem
    save_dir = f"results/binary_diversity_predictive/todos/{inst_name}_{INDICE_INSTANCIA}/comparacion_mhs_{run_id}"
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    resultados_por_mh = {}

    for nombre, mh_class in MHS.items():
        print(f"\n  Ejecutando {nombre}...")
        resultados = run_epochs(
            mh_class=mh_class,
            inst=inst,
            monitor_cfg=DTW_CFG,
            num_particulas=NUM_PARTICULAS,
            num_iteraciones=NUM_ITERACIONES,
            epochs=EPOCHS,
            verbose=False,
        )
        resultados_por_mh[nombre] = resultados
        print_epoch_results(nombre, resultados, inst)

        inst_name = Path(RUTA_INSTANCIA).stem
        save_results(
            resultados,
            path=f"{save_dir}/{nombre}_{inst_name}_{INDICE_INSTANCIA}.json",
            mh_name=nombre,
            optimo_conocido=inst["optimo"] if inst["optimo"] > 0 else None,
            extra_info={
                "estrategia": "binary_diversity_predictive",
                "decision_rule": DECISION_RULE,
                "instancia": RUTA_INSTANCIA,
                "idx": INDICE_INSTANCIA,
                "poblacion": NUM_PARTICULAS,
                "iteraciones": NUM_ITERACIONES,
                "dtw_window": DTW_CFG.window,
            },
        )

    generate_plots(resultados_por_mh, inst, save_dir)


if __name__ == "__main__":
    main()
