"""
Runner: orquesta MH + DTW + loop de iteraciones.
No sabe qué MH usa — solo llama la interfaz BaseMH.
"""

import time
from typing import Dict, List, Type

import numpy as np

from mkp_common.base import BaseMH
from mkp_common.monitor import StagnationConfig, StagnationMonitor


def run_experiment(
    mh_class: Type[BaseMH],
    inst: dict,
    monitor_cfg: StagnationConfig,
    num_particulas: int = 20,
    num_iteraciones: int = 100,
    semilla: int = 42,
    verbose: bool = False,
) -> dict:
    """
    Ejecuta UNA corrida de la MH con DTW auto-adaptativo.

    Args:
        mh_class:        Clase de la MH (ej: BinaryPSO)
        inst:            Instancia MKP cargada
        monitor_cfg:     Configuración del DTW
        num_particulas:  Tamaño de la población
        num_iteraciones: Presupuesto de iteraciones
        semilla:         Seed para reproducibilidad
        verbose:         Imprimir diagnóstico del DTW

    Returns:
        dict con resultados de la corrida
    """
    rng = np.random.default_rng(semilla)
    mh = mh_class(inst, rng, num_particulas=num_particulas)
    monitor = StagnationMonitor(cfg=monitor_cfg)

    mh.initialize()

    historial_fitness: List[float] = []
    historial_dtw: List[Dict] = []
    fire_count = 0

    for it in range(num_iteraciones):
        fitness = mh.step()

        out = monitor.update(fitness)
        historial_dtw.append(out)

        prev_mode = mh.mode
        if out.get("ready"):
            mh.adapt(out["fire"])

        if mh.mode == "explore" and prev_mode != "explore":
            fire_count += 1
            if verbose:
                print(
                    f"  [DTW FIRE] iter={it:03d} | "
                    f"no_imp={out['no_improve_len']} | "
                    f"streak={out['trigger_streak']} | "
                    f"D1={out['D1_vs_ramp']:.1f} D2={out['D2_vs_const']:.1f} "
                    f"delta={out['delta']:+.1f} >> EXPLORE"
                )
        elif mh.mode == "exploit" and prev_mode == "explore":
            if verbose:
                print(
                    f"  [DTW COOL] iter={it:03d} | "
                    f"no_imp={out['no_improve_len']} >> EXPLOIT"
                )

        historial_fitness.append(fitness)

    sol, fit = mh.get_best()
    optimo = inst["optimo"]

    return {
        "mejor_fitness": fit,
        "mejor_solucion": sol,
        "optimo_conocido": optimo,
        "historial_fitness": historial_fitness,
        "historial_dtw": historial_dtw,
        "fire_count": fire_count,
        "ganancia": (fit / optimo * 100) if optimo > 0 else 0,
    }


def run_epochs(
    mh_class: Type[BaseMH],
    inst: dict,
    monitor_cfg: StagnationConfig,
    num_particulas: int = 20,
    num_iteraciones: int = 100,
    epochs: int = 10,
    verbose: bool = False,
) -> List[dict]:
    """
    Ejecuta múltiples corridas (epochs) y retorna lista de resultados.
    Cada epoch usa semilla = epoch_index + 1.
    """
    resultados = []
    for ep in range(epochs):
        semilla = ep + 1
        t0 = time.perf_counter()
        res = run_experiment(
            mh_class, inst, monitor_cfg,
            num_particulas=num_particulas,
            num_iteraciones=num_iteraciones,
            semilla=semilla,
            verbose=verbose,
        )
        t1 = time.perf_counter()
        res["tiempo"] = t1 - t0
        res["epoch"] = ep + 1
        res["semilla"] = semilla
        resultados.append(res)
    return resultados
