"""
Resultados: visualización, diagnóstico, guardado y comparación.
Pensado para comparar múltiples MHs sobre las mismas instancias.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# matplotlib es opcional — si no está, las funciones de plot avisan
try:
    import matplotlib.pyplot as plt
    HAS_PLT = True
except ImportError:
    HAS_PLT = False


# =============================================================================
# DIAGNOSTICO DTW (texto)
# =============================================================================


def diagnosticar_dtw(historial_dtw: List[Dict]) -> None:
    """Imprime resumen del comportamiento del DTW durante una corrida."""
    ready = [h for h in historial_dtw if h.get("ready")]
    fires = [h for h in ready if h.get("fire")]

    if not ready:
        print("  [DTW] No alcanzó el warm-up")
        return

    deltas = [h["delta"] for h in ready]
    d1s = [h["D1_vs_ramp"] for h in ready]
    d2s = [h["D2_vs_const"] for h in ready]

    print(f"  [DTW] Iteraciones activas: {len(ready)}")
    print(f"  [DTW] Fires disparados:   {len(fires)}")
    print(f"  [DTW] Delta promedio:      {np.mean(deltas):.1f}")
    print(f"  [DTW] Delta min/max:       {np.min(deltas):.1f} / {np.max(deltas):.1f}")
    print(f"  [DTW] D1 promedio:         {np.mean(d1s):.1f}")
    print(f"  [DTW] D2 promedio:         {np.mean(d2s):.1f}")


def print_summary(resultados: List[dict], inst: dict) -> None:
    """Imprime resumen final de múltiples epochs."""
    fits = [r["mejor_fitness"] for r in resultados]
    optimo = inst["optimo"]

    print("\n" + "=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    print(f"  Mejor:      {np.max(fits):.1f}")
    print(f"  Promedio:   {np.mean(fits):.1f}")
    print(f"  Peor:       {np.min(fits):.1f}")
    print(f"  Desv. Est.: {np.std(fits):.1f}")
    if optimo > 0:
        print(f"  Optimo:     {optimo:.0f}")
        print(f"  Gap:        {100 - np.max(fits) / optimo * 100:.2f}%")
    print(f"  Epochs:     {len(resultados)}")


# =============================================================================
# GRAFICOS
# =============================================================================


def _check_plt():
    if not HAS_PLT:
        print("[results] matplotlib no instalado. Instalar con: pip install matplotlib")
        return False
    return True


def plot_convergence(
    historial_fitness: List[float],
    title: str = "Convergencia",
    optimo: Optional[float] = None,
    save_path: Optional[str] = None,
) -> None:
    """Grafica la curva de convergencia (fitness vs iteración)."""
    if not _check_plt():
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(historial_fitness, linewidth=1.5, label="gbest fitness")
    if optimo and optimo > 0:
        ax.axhline(y=optimo, color="r", linestyle="--", alpha=0.7, label=f"Óptimo ({optimo:.0f})")
    ax.set_xlabel("Iteración")
    ax.set_ylabel("Fitness")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  Guardado: {save_path}")
    else:
        plt.show()
    plt.close(fig)


def plot_dtw_metrics(
    historial_dtw: List[Dict],
    title: str = "Métricas DTW",
    save_path: Optional[str] = None,
) -> None:
    """Grafica D1, D2 y delta del monitor DTW."""
    if not _check_plt():
        return

    ready = [h for h in historial_dtw if h.get("ready")]
    if not ready:
        print("  [DTW] Sin datos para graficar")
        return

    iters = list(range(len(ready)))
    d1s = [h["D1_vs_ramp"] for h in ready]
    d2s = [h["D2_vs_const"] for h in ready]
    deltas = [h["delta"] for h in ready]

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    axes[0].plot(iters, d1s, label="D1 (vs rampa)", alpha=0.8)
    axes[0].plot(iters, d2s, label="D2 (vs meseta)", alpha=0.8)
    axes[0].set_ylabel("Distancia DTW")
    axes[0].set_title(title)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(iters, deltas, color="purple", label="delta (D1-D2)", alpha=0.8)
    axes[1].axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    axes[1].set_xlabel("Iteración (desde warm-up)")
    axes[1].set_ylabel("Delta")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  Guardado: {save_path}")
    else:
        plt.show()
    plt.close(fig)


def plot_comparison(
    resultados_por_mh: Dict[str, List[dict]],
    title: str = "Comparación de MHs",
    save_path: Optional[str] = None,
) -> None:
    """
    Box plot comparando fitness de múltiples MHs.

    Args:
        resultados_por_mh: {"PSO": [resultados...], "GA": [resultados...]}
    """
    if not _check_plt():
        return

    nombres = list(resultados_por_mh.keys())
    datos = [
        [r["mejor_fitness"] for r in resultados_por_mh[n]]
        for n in nombres
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(datos, label=nombres)
    ax.set_ylabel("Mejor Fitness")
    ax.set_title(title)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        print(f"  Guardado: {save_path}")
    else:
        plt.show()
    plt.close(fig)


# =============================================================================
# GUARDADO / CARGA
# =============================================================================


def save_results(
    resultados: List[dict],
    path: str,
    mh_name: str = "PSO",
    extra_info: Optional[dict] = None,
    optimo_conocido: Optional[float] = None,
) -> None:
    """
    Guarda resultados a JSON (sin numpy arrays, solo metricas).

    Args:
        resultados:       Lista de dicts de run_experiment/run_epochs
        path:             Ruta del archivo .json
        mh_name:          Nombre de la MH para identificacion
        extra_info:       Info adicional (config, instancia, etc.)
        optimo_conocido:  Valor optimo conocido de la literatura (si existe)
    """
    fits = [r["mejor_fitness"] for r in resultados]
    mejor = float(np.max(fits))

    stats = {
        "mejor": mejor,
        "promedio": float(np.mean(fits)),
        "peor": float(np.min(fits)),
        "std": float(np.std(fits)),
    }

    if optimo_conocido and optimo_conocido > 0:
        stats["optimo_conocido"] = optimo_conocido
        stats["gap_al_optimo"] = round(100 - mejor / optimo_conocido * 100, 4)

    salida = {
        "mh": mh_name,
        "epochs": len(resultados),
        "optimo_conocido": optimo_conocido if optimo_conocido and optimo_conocido > 0 else None,
        "fitness": fits,
        "fire_counts": [r["fire_count"] for r in resultados],
        "ganancias": [r["ganancia"] for r in resultados],
        "tiempos": [r.get("tiempo", 0) for r in resultados],
        "stats": stats,
    }
    if extra_info:
        salida["info"] = extra_info

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(salida, f, indent=2)
    print(f"  Resultados guardados: {path}")


def load_results(path: str) -> dict:
    """Carga resultados desde JSON."""
    with open(path) as f:
        return json.load(f)
