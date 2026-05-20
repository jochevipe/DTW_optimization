"""
Entry point: ejecuta una MH + DTW Fire Binario sobre una instancia MKP.

Uso (desde la raíz del proyecto):
    python -m fire_binario.run
"""

from pathlib import Path

from mkp_common import cargar_instancia
from mkp_common.results import diagnosticar_dtw, print_summary, save_results

from .config import (
    DTW_CFG,
    INDICE_INSTANCIA,
    MH_CLASS,
    NUM_ITERACIONES,
    NUM_PARTICULAS,
    RUTA_INSTANCIA,
    EPOCHS,
    VERBOSE,
)
from .runner import run_epochs


def main():
    print("=" * 60)
    print("  MH + DTW Fire Binario para MKP")
    print("=" * 60)

    inst = cargar_instancia(RUTA_INSTANCIA, INDICE_INSTANCIA)

    archivo_nombre = Path(RUTA_INSTANCIA).stem
    print(f"\nInstancia: {archivo_nombre}[{INDICE_INSTANCIA}]")
    print(f"  n={inst['n']}, m={inst['m']}")
    if inst["optimo"] > 0:
        print(f"  Optimo conocido: {inst['optimo']:.0f}")
    else:
        print(f"  Optimo: desconocido")

    resultados = run_epochs(
        mh_class=MH_CLASS,
        inst=inst,
        monitor_cfg=DTW_CFG,
        num_particulas=NUM_PARTICULAS,
        num_iteraciones=NUM_ITERACIONES,
        epochs=EPOCHS,
        verbose=VERBOSE,
    )

    for res in resultados:
        if inst["optimo"] > 0:
            gap = 100 - res["ganancia"]
            gap_str = f"Gap={gap:.2f}%"
        else:
            gap_str = "Gap=N/A"
        print(
            f"\n--- Epoch {res['epoch']}/{EPOCHS} (semilla={res['semilla']}) ---\n"
            f"  Fitness={res['mejor_fitness']:.1f} | "
            f"Fires={res['fire_count']} | {gap_str} | "
            f"Tiempo={res['tiempo']:.2f}s"
        )
        diagnosticar_dtw(res["historial_dtw"])

    print_summary(resultados, inst)

    carpeta_salida = f"results/fire_binario/{archivo_nombre}_{INDICE_INSTANCIA}"
    mh_name = MH_CLASS.__name__
    ruta_json = f"{carpeta_salida}/{mh_name}.json"

    save_results(
        resultados,
        path=ruta_json,
        mh_name=mh_name,
        optimo_conocido=inst["optimo"] if inst["optimo"] > 0 else None,
        extra_info={
            "estrategia": "fire_binario",
            "instancia": RUTA_INSTANCIA,
            "archivo": archivo_nombre,
            "idx": INDICE_INSTANCIA,
            "n": inst["n"],
            "m": inst["m"],
            "particulas": NUM_PARTICULAS,
            "iteraciones": NUM_ITERACIONES,
            "dtw_window": DTW_CFG.window,
            "dtw_band": DTW_CFG.band,
            "dtw_patience": DTW_CFG.patience,
            "dtw_plateau_max": DTW_CFG.plateau_max,
            "dtw_min_slope": DTW_CFG.min_slope,
            "dtw_use_ddtw": DTW_CFG.use_ddtw,
        },
    )


if __name__ == "__main__":
    main()
