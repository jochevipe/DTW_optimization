"""
run_benchmark_hpc.py — Wrapper para ejecutar las 9 instancias de Chu & Beasley en HPC.
====================================================================================
Ejecuta secuencialmente run_all_hpc.py para cada instancia (mknapcb1 a mknapcb9),
reutilizando el paralelismo masivo por CPU en cada instancia.

Uso:
    python run_benchmark_hpc.py
    python run_benchmark_hpc.py --cpus 40
    python run_benchmark_hpc.py --epochs 31
    python run_benchmark_hpc.py --instancias instances/mknapcb1.txt instances/mknapcb4.txt
    python run_benchmark_hpc.py --desde 1 --hasta 5
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Lista canónica de las 9 instancias de Chu & Beasley
DEFAULT_INSTANCES = [f"instances/mknapcb{i}.txt" for i in range(1, 10)]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ejecutor secuencial de las 9 instancias de benchmark en HPC"
    )
    p.add_argument(
        "--instancias",
        nargs="+",
        default=None,
        help="Rutas a instancias específicas (default: mknapcb1.txt a mknapcb9.txt)",
    )
    p.add_argument(
        "--desde",
        type=int,
        default=1,
        help="Número de instancia inicial (1 a 9, default: 1)",
    )
    p.add_argument(
        "--hasta",
        type=int,
        default=9,
        help="Número de instancia final (1 a 9, default: 9)",
    )
    p.add_argument(
        "--indice",
        type=int,
        default=0,
        help="Índice dentro de cada archivo de instancia (default: 0)",
    )
    p.add_argument(
        "--cpus",
        type=int,
        default=None,
        help="Número máximo de CPUs/workers por instancia (default: os.cpu_count())",
    )
    p.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Número de épocas por MH (default: tomado de mkp_common.config)",
    )
    p.add_argument(
        "--skip",
        nargs="*",
        default=[],
        help="Estrategias a omitir (ej: --skip vanilla_explotacion)",
    )
    p.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Detener el benchmark si alguna instancia falla",
    )
    return p.parse_args()


def resolve_instance_list(args: argparse.Namespace) -> List[str]:
    """Determina la lista de instancias a procesar según los argumentos."""
    if args.instancias:
        return args.instancias

    desde = max(1, min(args.desde, 9))
    hasta = max(desde, min(args.hasta, 9))
    return [f"instances/mknapcb{i}.txt" for i in range(desde, hasta + 1)]


def main() -> int:
    args = parse_args()
    instancias = resolve_instance_list(args)

    campaign_global_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.environ["MKP_CAMPAIGN_ID"] = campaign_global_id

    print("=" * 75)
    print("  HPC BENCHMARK RUNNER — 9 INSTANCIAS MKP")
    print("=" * 75)
    print(f"  Campaign Global ID: {campaign_global_id}")
    print(f"  Total de instancias: {len(instancias)}")
    for idx, inst_path in enumerate(instancias, 1):
        print(f"    [{idx:02d}] {inst_path} (idx={args.indice})")
    if args.cpus:
        print(f"  CPUs por instancia:  {args.cpus}")
    if args.epochs:
        print(f"  Épocas por MH:       {args.epochs}")
    if args.skip:
        print(f"  Estrategias omitidas:{', '.join(args.skip)}")
    print("=" * 75)
    print()

    t_global_start = time.perf_counter()
    reporte = []

    for i, inst_path in enumerate(instancias, 1):
        inst_name = Path(inst_path).stem
        banner_title = f"INSTANCIA {i}/{len(instancias)}: {inst_name}[{args.indice}]"

        print("\n" + "#" * 75)
        print(f"  >>> INICIANDO {banner_title}")
        print("#" * 75 + "\n")

        cmd = [
            sys.executable,
            "run_all_hpc.py",
            "--instancia", inst_path,
            "--indice", str(args.indice),
        ]
        if args.cpus:
            cmd.extend(["--cpus", str(args.cpus)])
        if args.epochs:
            cmd.extend(["--epochs", str(args.epochs)])
        if args.skip:
            cmd.extend(["--skip"] + args.skip)

        t0 = time.perf_counter()
        res = subprocess.run(cmd, env=os.environ.copy())
        t_elapsed = time.perf_counter() - t0
        elapsed_str = str(timedelta(seconds=round(t_elapsed)))

        status = "OK" if res.returncode == 0 else f"FAIL (código {res.returncode})"
        reporte.append({
            "instancia": f"{inst_name}[{args.indice}]",
            "tiempo": elapsed_str,
            "status": status,
            "exitoso": res.returncode == 0,
        })

        if res.returncode == 0:
            print(f"\n  [OK] {banner_title} finalizada con éxito en {elapsed_str}")
        else:
            print(f"\n  [FAIL] {banner_title} falló ({status}) en {elapsed_str}")
            if args.stop_on_error:
                print("\n  [STOP] Ejecución detenida por --stop-on-error.")
                break

    t_global_total = time.perf_counter() - t_global_start
    total_str = str(timedelta(seconds=round(t_global_total)))

    # ── Resumen Final ────────────────────────────────────────────────────────
    print("\n\n" + "=" * 75)
    print("  RESUMEN FINAL DEL BENCHMARK")
    print("=" * 75)
    print(f"  Tiempo total acumulado: {total_str}")
    print(f"  Instancias ejecutadas:  {len(reporte)}/{len(instancias)}")
    print("-" * 75)
    print(f"  {'Instancia':<25} {'Estado':<20} {'Tiempo':<15}")
    print("-" * 75)
    for r in reporte:
        print(f"  {r['instancia']:<25} {r['status']:<20} {r['tiempo']:<15}")
    print("=" * 75)

    todos_ok = all(r["exitoso"] for r in reporte)
    return 0 if (todos_ok and len(reporte) == len(instancias)) else 1


if __name__ == "__main__":
    sys.exit(main())
