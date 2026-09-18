"""
Script maestro — Ejecuta etapas secuenciales de pruebas y resultados.
Cada etapa es un módulo Python que se ejecuta via subprocess.

Uso (desde la raíz del proyecto):
    python run_all.py
    python run_all.py --instancia instances/mknapcb1.txt
    python run_all.py --instancia instances/mknapcb1.txt --indice 2

Para agregar/quitar etapas, modificá la lista ETAPAS abajo.
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN: definí acá las etapas a ejecutar (orden secuencial)
# ═══════════════════════════════════════════════════════════════════════════

ETAPAS = [
    # (nombre, módulo_a_ejecutar, args_extra)
    # -- Líneas base sin DTW --
    ("Vanilla-Exploitation",     "vanilla_explotacion.resultados",  []),
    ("Vanilla-Exploration",     "vanilla_exploracion.resultados",  []),
    # -- DTW: Binary --
    ("Binary-Simple",           "binary_simple.resultados",  []),
    ("Binary-Complex",        "binary_complex.resultados", []),
    ("Binary-Patient",          "binary_patient.resultados", []),
]

# ═══════════════════════════════════════════════════════════════════════════
# Si True, para al primer error. Si False, continúa.
STOP_ON_ERROR = False

# ═══════════════════════════════════════════════════════════════════════════


def parse_args():
    parser = argparse.ArgumentParser(
        description="Script maestro — ejecuta todas las versiones sobre la misma instancia"
    )
    parser.add_argument(
        "--instancia",
        default=None,
        help="Ruta a la instancia MKP (ej: instances/mknapcb1.txt). "
             "Si no se especifica, cada versión usa su default.",
    )
    parser.add_argument(
        "--indice",
        type=int,
        default=None,
        help="Índice de la instancia (default: 0). Solo se usa si --instancia está presente.",
    )
    return parser.parse_args()


def build_env(
    instancia: str | None,
    indice: int | None,
    campaign_id: str | None = None,
) -> dict:
    """Construye un environment dict con las variables MKP si se especificaron."""
    env = os.environ.copy()
    if instancia is not None:
        env["MKP_INSTANCIA"] = instancia
    if indice is not None:
        env["MKP_INDICE"] = str(indice)
    if campaign_id is not None:
        env["MKP_CAMPAIGN_ID"] = campaign_id
    return env


def run_stage(name: str, module: str, extra_args: list[str] = None, env: dict = None) -> bool:
    """Ejecuta una etapa y retorna True si fue exitosa."""
    extra_args = extra_args or []
    cmd = [sys.executable, "-m", module] + extra_args

    print(f"\n{'=' * 70}")
    print(f"  ETAPA: {name}")
    print(f"  Comando: python -m {module} {' '.join(extra_args)}")
    print(f"{'=' * 70}")

    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=False, text=True, env=env)
    elapsed = time.perf_counter() - t0
    elapsed_str = str(timedelta(seconds=round(elapsed)))

    if result.returncode == 0:
        print(f"\n  [OK] {name} — completado en {elapsed_str}")
        return True
    else:
        print(f"\n  [FAIL] {name} — FALLO (codigo {result.returncode}) en {elapsed_str}")
        return False


def main():
    args = parse_args()
    campaign_id = os.environ.get("MKP_CAMPAIGN_ID") or datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    env = build_env(args.instancia, args.indice, campaign_id=campaign_id)

    root = Path(__file__).parent
    print("=" * 70)
    print("  SCRIPT MAESTRO — Cola de experimentos")
    print("=" * 70)
    print(f"  Proyecto: {root}")
    print(f"  Etapas: {len(ETAPAS)}")
    print(f"  Stop on error: {STOP_ON_ERROR}")
    if args.instancia:
        print(f"  Instancia: {args.instancia}")
        print(f"  Índice:    {args.indice if args.indice is not None else 0}")
    else:
        print(f"  Instancia: (default de cada versión)")
    print()

    t_total_start = time.perf_counter()
    ok, fail = 0, 0
    failed_stages = []

    for i, (name, module, extra_args) in enumerate(ETAPAS, 1):
        print(f"\n  [{i}/{len(ETAPAS)}] {name}")
        success = run_stage(name, module, extra_args, env=env)

        if success:
            ok += 1
        else:
            fail += 1
            failed_stages.append(name)
            if STOP_ON_ERROR:
                print(f"\n  ⛔ Detenido por error en etapa {i}")
                break

    t_total = time.perf_counter() - t_total_start
    total_str = str(timedelta(seconds=round(t_total)))

    # Resumen final
    print(f"\n{'=' * 70}")
    print(f"  RESUMEN FINAL")
    print(f"{'=' * 70}")
    print(f"  [OK] Completadas: {ok}/{len(ETAPAS)}")
    print(f"  [FAIL] Fallidas:  {fail}/{len(ETAPAS)}")
    print(f"  [TIME] Total:     {total_str}")
    if failed_stages:
        print(f"  Etapas fallidas:")
        for fs in failed_stages:
            print(f"    - {fs}")
    print(f"{'=' * 70}")

    # ── Análisis estadístico post-experimentos ──────────────────────────
    analysis_ok = True
    if ok >= 1:
        print(f"\n{'=' * 70}")
        print(f"  ANÁLISIS ESTADÍSTICO")
        print(f"{'=' * 70}")

        analysis_cmd = [sys.executable, "-m", "analisis.estadistico"]
        if args.instancia:
            analysis_cmd += ["--instancia", args.instancia]
        if args.indice is not None:
            analysis_cmd += ["--indice", str(args.indice)]

        print(f"  Comando: {' '.join(analysis_cmd)}")
        print()

        t_analysis = time.perf_counter()
        result = subprocess.run(analysis_cmd, capture_output=False, text=True, env=env)
        analysis_elapsed = time.perf_counter() - t_analysis
        analysis_str = str(timedelta(seconds=round(analysis_elapsed)))

        if result.returncode == 0:
            print(f"\n  [OK] Análisis estadístico completado en {analysis_str}")
        else:
            print(f"\n  [FAIL] Análisis estadístico fallo (codigo {result.returncode}) en {analysis_str}")
            analysis_ok = False
    else:
        print(f"\n  [SKIP] Análisis estadístico omitido — ninguna etapa completada con exito.")
        analysis_ok = False

    return 0 if (fail == 0 and analysis_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
