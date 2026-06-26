"""
Script maestro — Ejecuta etapas secuenciales de pruebas y resultados.
Cada etapa es un módulo Python que se ejecuta via runpy.

Uso (desde la raíz del proyecto):
    python run_all.py

Para agregar/quitar etapas, modificá la lista ETAPAS abajo.
"""

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
    #("Vanilla",    "vanilla.run",         []),
    ("Vanilla (Todos)",     "vanilla.resultados",  []),
    #("Fire Binary",    "fire_binario.run",         []),
    ("Fire Binary (Todos)",     "fire_binario.resultados",  []),
    #("Fire D2",  "fire_d2.run",        []),
    ("Fire D2 (Todos)",   "fire_d2.resultados", []),
    #("Sigmoid Delta",  "sigmoid_delta.run",        []),
    ("Sigmoid Delta (Todos)",   "sigmoid_delta.resultados", []),
]

# ═══════════════════════════════════════════════════════════════════════════
# Si True, para al primer error. Si False, continúa.
STOP_ON_ERROR = False

# ═══════════════════════════════════════════════════════════════════════════


def run_stage(name: str, module: str, extra_args: list[str] = None) -> bool:
    """Ejecuta una etapa y retorna True si fue exitosa."""
    extra_args = extra_args or []
    cmd = [sys.executable, "-m", module] + extra_args

    print(f"\n{'=' * 70}")
    print(f"  ETAPA: {name}")
    print(f"  Comando: python -m {module} {' '.join(extra_args)}")
    print(f"{'=' * 70}")

    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=False, text=True)
    elapsed = time.perf_counter() - t0
    elapsed_str = str(timedelta(seconds=round(elapsed)))

    if result.returncode == 0:
        print(f"\n  [OK] {name} — completado en {elapsed_str}")
        return True
    else:
        print(f"\n  [FAIL] {name} — FALLO (codigo {result.returncode}) en {elapsed_str}")
        return False


def main():
    root = Path(__file__).parent
    print("=" * 70)
    print("  SCRIPT MAESTRO — Cola de experimentos")
    print("=" * 70)
    print(f"  Proyecto: {root}")
    print(f"  Etapas: {len(ETAPAS)}")
    print(f"  Stop on error: {STOP_ON_ERROR}")
    print()

    t_total_start = time.perf_counter()
    ok, fail = 0, 0
    failed_stages = []

    for i, (name, module, args) in enumerate(ETAPAS, 1):
        print(f"\n  [{i}/{len(ETAPAS)}] {name}")
        success = run_stage(name, module, args)

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

    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
