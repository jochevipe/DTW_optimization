"""
Visualiza la convergencia de una MH + DTW Fire Binario en una corrida.
Importa toda la config desde config.py.

Uso (desde la raíz del proyecto):
    python -m fire_binario.plot_experiment
"""

import matplotlib.pyplot as plt

from mkp_common import cargar_instancia

from .runner import run_experiment
from .config import (
    DTW_CFG,
    INDICE_INSTANCIA,
    MH_CLASS,
    NUM_ITERACIONES,
    NUM_PARTICULAS,
    RUTA_INSTANCIA,
    VERBOSE,
)


def plot_full_experiment(res: dict, title_prefix: str = "PSO+DTW"):
    """Genera un plot de 3 paneles: convergencia, D1/D2, delta."""
    hist_fit = res["historial_fitness"]
    hist_dtw = res["historial_dtw"]

    ready_iters = []
    d1s, d2s, deltas = [], [], []
    fire_iters = []

    for i, h in enumerate(hist_dtw):
        if h.get("ready"):
            ready_iters.append(i)
            d1s.append(h["D1_vs_ramp"])
            d2s.append(h["D2_vs_const"])
            deltas.append(h["delta"])
            if h.get("fire"):
                fire_iters.append(i)

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

    # --- Panel 1: Convergencia ---
    ax = axes[0]
    ax.plot(hist_fit, color="#2196F3", linewidth=1.5, label="gbest fitness")
    for fi in fire_iters:
        ax.axvline(x=fi, color="red", alpha=0.15, linewidth=1)
    fire_fits = [hist_fit[i] for i in fire_iters if i < len(hist_fit)]
    fire_x = [i for i in fire_iters if i < len(hist_fit)]
    ax.scatter(fire_x, fire_fits, color="red", s=20, zorder=5, label="DTW fire")
    ax.set_ylabel("Fitness")
    ax.set_title(f"{title_prefix} — Convergencia (fires={res['fire_count']})")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)

    # --- Panel 2: D1 vs D2 ---
    ax = axes[1]
    ax.plot(ready_iters, d1s, color="#FF9800", alpha=0.8, label="D1 (vs rampa)")
    ax.plot(ready_iters, d2s, color="#4CAF50", alpha=0.8, label="D2 (vs meseta)")
    for fi in fire_iters:
        ax.axvline(x=fi, color="red", alpha=0.15, linewidth=1)
    ax.set_ylabel("Distancia DTW")
    ax.set_title("Distancias DTW a patrones de referencia")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # --- Panel 3: Delta ---
    ax = axes[2]
    ax.plot(ready_iters, deltas, color="#9C27B0", alpha=0.8, label="delta (D1-D2)")
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    for fi in fire_iters:
        ax.axvline(x=fi, color="red", alpha=0.15, linewidth=1)
    ax.fill_between(ready_iters, deltas, 0, alpha=0.1, color="#9C27B0")
    ax.set_xlabel("Iteracion")
    ax.set_ylabel("Delta")
    ax.set_xticks(range(0, len(hist_fit) + 1, 5))
    ax.set_title("Delta (D1-D2) — positivo = estancamiento")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    save_path = "results/fire_binario/convergence.png"
    fig.savefig(save_path, dpi=150)
    print(f"  Guardado: {save_path}")
    plt.show()
    plt.close(fig)


def main():
    inst = cargar_instancia(RUTA_INSTANCIA, idx=INDICE_INSTANCIA)

    print(f"Config importada de fire_binario.config:")
    print(f"  Instancia: {RUTA_INSTANCIA}[{INDICE_INSTANCIA}]")
    print(f"  Particulas: {NUM_PARTICULAS}, Iteraciones: {NUM_ITERACIONES}")
    print(f"  DTW window={DTW_CFG.window}, patience={DTW_CFG.patience}")
    print()

    res = run_experiment(
        mh_class=MH_CLASS,
        inst=inst,
        monitor_cfg=DTW_CFG,
        num_particulas=NUM_PARTICULAS,
        num_iteraciones=NUM_ITERACIONES,
        semilla=3,
        verbose=VERBOSE,
    )

    print(f"\nFitness final: {res['mejor_fitness']:.1f}")
    print(f"Fires: {res['fire_count']}")

    mh_name = MH_CLASS.__name__
    plot_full_experiment(res, title_prefix=f"{mh_name} + DTW Fire (seed=3)")


if __name__ == "__main__":
    main()
