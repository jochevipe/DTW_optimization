"""
Script maestro de resultados — Fire Binario.
Corre todas las MHs, muestra métricas DTW en consola, y genera gráficos.

Uso (desde la raíz del proyecto):
    python -m fire_binario.resultados
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from mkp_common import BinaryPSO, GeneticAlgorithm, BinaryGWO, cargar_instancia
from mkp_common.results import save_results

from .runner import run_epochs
from .config import (
    DTW_CFG,
    INDICE_INSTANCIA,
    NUM_ITERACIONES,
    NUM_PARTICULAS,
    RUTA_INSTANCIA,
    EPOCHS,
)

# MHs a comparar — agregar nuevas acá
MHS = {
    "BinaryPSO": BinaryPSO,
    "GA": GeneticAlgorithm,
    "GWO": BinaryGWO,
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
            d1s = [h["D1_vs_ramp"] for h in ready]
            d2s = [h["D2_vs_const"] for h in ready]
            deltas = [h["delta"] for h in ready]
            print(
                f"    DTW  D1={np.mean(d1s):7.1f} (+-{np.std(d1s):.1f}) | "
                f"D2={np.mean(d2s):7.1f} (+-{np.std(d2s):.1f}) | "
                f"delta={np.mean(deltas):+7.1f} | "
                f"th_c={last['theta_c']:.1f}  th_r={last['theta_r']:.1f}  "
                f"th_d={last['theta_delta']:.1f}"
            )

    fits = [r["mejor_fitness"] for r in resultados]
    print(f"\n  {'-' * 50}")
    print(f"  Mejor={np.max(fits):.1f}  Prom={np.mean(fits):.1f}  "
          f"Peor={np.min(fits):.1f}  Std={np.std(fits):.1f}")
    if optimo > 0:
        print(f"  Optimo={optimo:.0f}  Gap={100 - np.max(fits) / optimo * 100:.2f}%")


# Colores por MH
MH_COLORS = {
    "BinaryPSO": "#2196F3",
    "GA": "#E91E63",
    "GWO": "#4CAF50",
}


def _get_explore_segments(hist_dtw: list) -> list:
    """Detecta los rangos de iteraciones donde la MH está en modo explore."""
    segments = []
    in_fire = False
    start = 0
    for i, h in enumerate(hist_dtw):
        if h.get("fire") and not in_fire:
            start = i
            in_fire = True
        elif not h.get("fire") and in_fire:
            segments.append((start, i))
            in_fire = False
    if in_fire:
        segments.append((start, len(hist_dtw) - 1))
    return segments


def generate_plots(resultados_por_mh: dict):
    """
    Genera 2 paneles:
      1. Fitness: ambas MHs superpuestas, línea punteada durante explore
      2. Delta: delta de cada MH con theta_delta como referencia
    """
    nombres = list(resultados_por_mh.keys())

    mejores = {}
    for nombre in nombres:
        resultados = resultados_por_mh[nombre]
        idx = int(np.argmax([r["mejor_fitness"] for r in resultados]))
        mejores[nombre] = resultados[idx]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # =========================================================================
    # Panel 1: FITNESS SUPERPUESTO
    # =========================================================================
    ax = axes[0]
    for nombre in nombres:
        res = mejores[nombre]
        hist_fit = res["historial_fitness"]
        color = MH_COLORS.get(nombre, "#666666")
        segments = _get_explore_segments(res["historial_dtw"])

        iters = list(range(len(hist_fit)))
        ax.plot(iters, hist_fit, color=color, linewidth=1.5, alpha=0.3)

        if not segments:
            ax.plot(iters, hist_fit, color=color, linewidth=1.5,
                    label=f"{nombre} (fires={res['fire_count']})")
        else:
            ax.plot([], [], color=color, linewidth=1.5, linestyle="-",
                    label=f"{nombre} (fires={res['fire_count']})")

            is_explore = [False] * len(hist_fit)
            for s, e in segments:
                for j in range(s, min(e + 1, len(hist_fit))):
                    is_explore[j] = True

            prev_type = is_explore[0]
            seg_start = 0
            for k in range(1, len(hist_fit)):
                if is_explore[k] != prev_type:
                    style = "--" if prev_type else "-"
                    ax.plot(range(seg_start, k + 1),
                            hist_fit[seg_start:k + 1],
                            color=color, linewidth=1.5, linestyle=style)
                    seg_start = k
                    prev_type = is_explore[k]
            style = "--" if prev_type else "-"
            ax.plot(range(seg_start, len(hist_fit)),
                    hist_fit[seg_start:],
                    color=color, linewidth=1.5, linestyle=style)

    ax.plot([], [], color="gray", linestyle="-", linewidth=1, label="Exploit (solido)")
    ax.plot([], [], color="gray", linestyle="--", linewidth=1, label="Explore (punteado)")
    ax.set_ylabel("Fitness")
    ax.set_title("Convergencia - Todas las MHs (Fire Binario)")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xticks(range(0, NUM_ITERACIONES + 1, 5))
    ax.grid(True, alpha=0.3)

    # =========================================================================
    # Panel 2: DELTA con theta_delta
    # =========================================================================
    ax = axes[1]
    for nombre in nombres:
        res = mejores[nombre]
        hist_dtw = res["historial_dtw"]
        color = MH_COLORS.get(nombre, "#666666")

        ready_iters, deltas, thetas = [], [], []
        for i, h in enumerate(hist_dtw):
            if h.get("ready"):
                ready_iters.append(i)
                deltas.append(h["delta"])
                thetas.append(h["theta_delta"])

        if ready_iters:
            ax.plot(ready_iters, deltas, color=color, linewidth=1.2,
                    alpha=0.8, label=f"delta {nombre}")
            ax.plot(ready_iters, thetas, color=color, linewidth=1,
                    linestyle=":", alpha=0.5, label=f"th_delta {nombre}")

    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.4)
    ax.set_xlabel("Iteracion")
    ax.set_ylabel("Delta (D1-D2)")
    ax.set_title("Delta vs Theta_delta (positivo = estancamiento)")
    ax.set_xticks(range(0, NUM_ITERACIONES + 1, 5))
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    save_path = "results/fire_binario/comparacion_mhs.png"
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150)
    print(f"\n  Grafico guardado: {save_path}")
    plt.show()
    plt.close(fig)


# =============================================================================
# MAIN
# =============================================================================


def main():
    inst = cargar_instancia(RUTA_INSTANCIA, idx=INDICE_INSTANCIA)

    print("=" * 70)
    print("  RESULTADOS MAESTRO — Fire Binario")
    print("=" * 70)
    print(f"  Instancia: {RUTA_INSTANCIA}[{INDICE_INSTANCIA}]")
    print(f"  n={inst['n']}, m={inst['m']}")
    print(f"  Particulas/Pop: {NUM_PARTICULAS}, Iteraciones: {NUM_ITERACIONES}, "
          f"Epochs: {EPOCHS}")
    print(f"  DTW: window={DTW_CFG.window}, patience={DTW_CFG.patience}, "
          f"ddtw={DTW_CFG.use_ddtw}")

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
            path=f"results/fire_binario/{nombre}_{inst_name}_{INDICE_INSTANCIA}.json",
            mh_name=nombre,
            optimo_conocido=inst["optimo"] if inst["optimo"] > 0 else None,
            extra_info={
                "estrategia": "fire_binario",
                "instancia": RUTA_INSTANCIA,
                "idx": INDICE_INSTANCIA,
                "poblacion": NUM_PARTICULAS,
                "iteraciones": NUM_ITERACIONES,
                "dtw_window": DTW_CFG.window,
                "dtw_patience": DTW_CFG.patience,
            },
        )

    generate_plots(resultados_por_mh)


if __name__ == "__main__":
    main()
