"""
Binary-Hysteresis — control con histéresis asimétrica sobre la señal A4 del monitor.
Corre todas las MHs, muestra métricas DTW en consola, y genera gráficos.

Uso (desde la raíz del proyecto):
    python -m binary_hysteresis.resultados
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
    is_entry_trigger,
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
    """Imprime fitness + DTW params por cada epoch."""
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

        ready = [h for h in res["historial_dtw"] if h.get("ready")]
        if ready:
            last = ready[-1]
            deltas = [h["delta"] for h in ready]
            print(
                f"    DTW  delta={np.mean(deltas):7.1f} (+-{np.std(deltas):.1f}) | "
                f"theta_delta={last['theta_delta']:.1f} | "
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
    "explore_bg": "#e74c3c",
    "optimum": "#7f8c8d",
    "delta": "#2980b9",
    "theta_delta": "#e67e22",
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


def _get_explore_state_entries(hist_mode):
    """Return iterations after an actual exploit-to-explore transition."""
    transitions = []
    for i in range(1, len(hist_mode)):
        if hist_mode[i] == "explore" and hist_mode[i - 1] != "explore":
            transitions.append(i)
    return transitions


def _get_entry_triggers(hist_dtw, hist_mode):
    """Return signal iterations that trigger a future explore state."""
    return [
        i
        for i, (dtw, mode) in enumerate(zip(hist_dtw, hist_mode))
        if is_entry_trigger(dtw, mode)
    ]


def generate_plots(resultados_por_mh: dict, inst: dict, save_dir: str):
    """
    Genera 2 paneles estilo paper:
      1. Fitness: explore-state lines + state-entry markers + optimum.
      2. A4 entry signal (trigger_streak vs patience) per MH.
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
        "legend.fontsize": 9,
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

    # =========================================================================
    # Panel 1: FITNESS SUPERPUESTO con líneas punteadas en explore
    # =========================================================================
    for nombre in nombres:
        res = mejores[nombre]
        hist_fit = res["historial_fitness"]
        hist_mode = res["historial_modos"]
        color = MH_COLORS.get(nombre, "#666666")

        explore_ranges = _get_explore_ranges(hist_mode)
        state_entries = _get_explore_state_entries(hist_mode)
        entry_triggers = _get_entry_triggers(res["historial_dtw"], hist_mode)

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

        # Mark state changes separately from the signal that caused them.
        if state_entries:
            state_fits = [hist_fit[i] for i in state_entries]
            ax1.scatter(
                state_entries, state_fits, color=COLORS["fire_marker"],
                marker="v", s=30, zorder=5,
                edgecolors="white", linewidths=0.3,
            )
        if entry_triggers:
            trigger_fits = [hist_fit[i] for i in entry_triggers]
            ax1.scatter(
                entry_triggers, trigger_fits, color=COLORS["theta_delta"],
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

    ax1.set_ylabel("Fitness")
    ax1.set_title(f"Binary-Hysteresis — All MHs (seed={SEMILLA})")
    ax1.legend(loc="lower right", framealpha=0.9)
    ax1.grid(True, alpha=0.2, linestyle=":")

    # =========================================================================
    # Panel 2: A4 entry signal — trigger_streak vs patience (per MH)
    # =========================================================================
    patience = DTW_CFG.patience
    for mh_idx, nombre in enumerate(nombres):
        res = mejores[nombre]
        hist_dtw = res["historial_dtw"]
        hist_mode = res["historial_modos"]
        color = MH_COLORS.get(nombre, "#666666")

        entry_triggers = _get_entry_triggers(hist_dtw, hist_mode)

        ready_iters, streak_vals, fire_flags = [], [], []
        for i, h in enumerate(hist_dtw):
            if h.get("ready"):
                ready_iters.append(i)
                streak_vals.append(h["trigger_streak"])
                fire_flags.append(bool(h["fire"]))

        if ready_iters:
            # Sustained-trigger signal
            ax2.step(
                ready_iters, streak_vals, where="mid", color=color,
                linewidth=1.3, label=rf"streak {nombre}", zorder=3,
            )

            # Fire zone: sustained A4 trigger while in exploit.
            fire_zone = [
                f and is_entry_trigger(hist_dtw[i], hist_mode[i])
                for i, f in zip(ready_iters, fire_flags)
            ]
            ax2.fill_between(
                ready_iters, streak_vals, patience,
                where=fire_zone,
                step="mid",
                color=COLORS["fire_marker"], alpha=0.08,
            )

            # Entry-trigger markers on the signal.
            for fi in entry_triggers:
                if fi in ready_iters:
                    idx = ready_iters.index(fi)
                    ax2.scatter(
                        fi, streak_vals[idx], color=color,
                        marker="^", s=35, zorder=5,
                        edgecolors="white", linewidths=0.5,
                    )

    ax2.axhline(
        y=patience, color="gray", linestyle="--",
        linewidth=1, alpha=0.7, label=f"patience ({patience})",
    )
    ax2.set_xlabel("Iteration")
    ax2.set_ylabel(r"$\mathrm{trigger\_streak}$")
    all_streaks = [
        h["trigger_streak"]
        for nombre in nombres
        for h in mejores[nombre]["historial_dtw"]
        if h.get("ready")
    ]
    ax2.set_ylim(-0.3, max(max(all_streaks, default=patience), patience) + 0.8)
    ax2.set_title(
        r"A4 entry signal — enter explore on sustained fire "
        r"(streak $\geq$ patience); exit on improvement"
    )
    ax2.legend(loc="upper left", framealpha=0.9, fontsize=7)
    ax2.grid(True, alpha=0.2, linestyle=":")

    plt.tight_layout(h_pad=1.5)

    # --- Guardar ---
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    # Derivar inst_name del save_dir (funciona tanto standalone como desde HPC)
    parts = Path(save_dir).parts
    inst_label = [p for p in parts if "_" in p and p.split("_")[0].startswith("mknapcb")]
    inst_name = inst_label[0].rsplit("_", 1)[0] if inst_label else Path(RUTA_INSTANCIA).stem
    for ext in ("png", "pdf"):
        path = f"{save_dir}/binary_hysteresis_{inst_name}.{ext}"
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
    print("  RESULTADOS MAESTRO — Binary-Hysteresis")
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
    save_dir = f"results/binary_hysteresis/todos/{inst_name}_{INDICE_INSTANCIA}/comparacion_mhs_{run_id}"
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
                "estrategia": "binary_hysteresis",
                "decision_rule": DECISION_RULE,
                "instancia": RUTA_INSTANCIA,
                "idx": INDICE_INSTANCIA,
                "poblacion": NUM_PARTICULAS,
                "iteraciones": NUM_ITERACIONES,
                **DTW_CFG.to_dict(),
            },
        )

    generate_plots(resultados_por_mh, inst, save_dir)


if __name__ == "__main__":
    main()
