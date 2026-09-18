"""
run_benchmark_hpc.py — Wrapper para ejecutar instancias de Chu & Beasley en HPC.
====================================================================================
Ejecuta secuencialmente run_all_hpc.py para cada (instancia, índice),
reutilizando el paralelismo masivo por CPU en cada instancia.

Uso:
    python run_benchmark_hpc.py
    python run_benchmark_hpc.py --cpus 40
    python run_benchmark_hpc.py --epochs 31
    python run_benchmark_hpc.py --instancias instances/mknapcb1.txt instances/mknapcb4.txt
    python run_benchmark_hpc.py --desde 1 --hasta 5

Modo multi-índice (Frente 2 de la revisión MDPI):
    python run_benchmark_hpc.py --k 3 --sample-seed 1000
        → 3 índices fijos por archivo (27 instancias en total).
          idx=0 siempre incluido (comparabilidad con el paper) y los k-1
          restantes muestreados sin reposición con semilla derivada
          (seed_base + número de archivo). Selección determinista y
          documentada: se guarda en results/campaign_<id>/instance_selection.json.

    python run_benchmark_hpc.py --indices 0 5 10
        → lista explícita de índices aplicada a todos los archivos.

    python run_benchmark_hpc.py --k 3 --no-include-zero
        → muestreo puro sin forzar idx=0.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Lista canónica de las 9 instancias de Chu & Beasley
DEFAULT_INSTANCES = [f"instances/mknapcb{i}.txt" for i in range(1, 10)]

# Valores por defecto del modo multi-índice (documentados en la revisión)
DEFAULT_SAMPLE_SEED = 1000
DEFAULT_K = 3


def _instance_count(inst_path: str) -> int:
    """Lee el primer token del archivo OR-Library: número de instancias."""
    with open(inst_path, encoding="utf-8") as stream:
        for line in stream:
            stripped = line.strip()
            if stripped:
                return int(stripped.split()[0])
    raise ValueError(f"{inst_path}: archivo vacío, no se pudo leer el conteo")


def sample_indices(
    inst_path: str,
    file_number: int,
    k: int,
    seed_base: int,
    include_zero: bool,
) -> List[int]:
    """
    Selección determinista de k índices para un archivo.

    - include_zero=True (default): idx=0 siempre incluido; los k-1 restantes
      se muestrean sin reposición de [1, num_instancias).
    - include_zero=False: muestreo uniforme de k índices de [0, num_instancias).
    """
    num = _instance_count(inst_path)
    if k < 1:
        raise ValueError("k debe ser >= 1")
    if k > num:
        raise ValueError(f"{inst_path}: k={k} excede las {num} instancias disponibles")

    rng = np.random.default_rng(seed_base + file_number)
    if include_zero and k > 1:
        picks = [0] + rng.choice(
            np.arange(1, num), size=k - 1, replace=False
        ).tolist()
    elif include_zero and k == 1:
        picks = [0]
    else:
        picks = rng.choice(np.arange(num), size=k, replace=False).tolist()
    return sorted(picks)


def build_work_plan(
    args: argparse.Namespace, instancias: List[str]
) -> Tuple[List[Tuple[str, int]], str, Dict[str, List[int]]]:
    """Devuelve la lista ordenada de (instancia, índice) a ejecutar."""
    if args.indices is not None:
        indices_by_file: Dict[str, List[int]] = {
            path: list(args.indices) for path in instancias
        }
        sampling_mode = "explicit"
    elif args.k is not None:
        sampling_mode = "sampled"
        indices_by_file = {
            path: sample_indices(
                path,
                file_number=i,
                k=args.k,
                seed_base=args.sample_seed,
                include_zero=args.include_zero,
            )
            for i, path in enumerate(instancias, 1)
        }
    else:
        sampling_mode = "single"
        indices_by_file = {path: [args.indice] for path in instancias}

    plan = [(path, idx) for path in instancias for idx in indices_by_file[path]]
    return plan, sampling_mode, indices_by_file


def save_selection_manifest(
    campaign_global_id: str,
    indices_by_file: Dict[str, List[int]],
    sampling_mode: str,
    args: argparse.Namespace,
) -> Path:
    """Guarda la tabla de selección de instancias para trazabilidad académica."""
    out_dir = Path("results") / f"campaign_{campaign_global_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "campaign_id": campaign_global_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "sampling_mode": sampling_mode,
        "k": args.k,
        "sample_seed": args.sample_seed,
        "include_zero": args.include_zero,
        "instances": {
            path: {"indices": indices, "count": len(indices)}
            for path, indices in sorted(indices_by_file.items())
        },
        "total": sum(len(v) for v in indices_by_file.values()),
    }
    path = out_dir / "instance_selection.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ejecutor secuencial de instancias de benchmark en HPC"
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
        help="Índice dentro de cada archivo de instancia (modo single-index, default: 0)",
    )
    p.add_argument(
        "--indices",
        nargs="+",
        type=int,
        default=None,
        help="Lista explícita de índices aplicada a todos los archivos (modo multi-índice)",
    )
    p.add_argument(
        "--k",
        type=int,
        default=None,
        help=f"Número de índices por archivo en modo multi-índice (default: {DEFAULT_K} si se combina con --sample-seed)",
    )
    p.add_argument(
        "--sample-seed",
        type=int,
        default=DEFAULT_SAMPLE_SEED,
        help=f"Semilla base del muestreo por archivo (seed = base + nº de archivo, default: {DEFAULT_SAMPLE_SEED})",
    )
    p.add_argument(
        "--include-zero",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Incluir siempre idx=0 en el muestreo (default: sí; --no-include-zero lo desactiva)",
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
    """Determina la lista de archivos de instancia a procesar."""
    if args.instancias:
        return args.instancias

    desde = max(1, min(args.desde, 9))
    hasta = max(desde, min(args.hasta, 9))
    return [f"instances/mknapcb{i}.txt" for i in range(desde, hasta + 1)]


def main() -> int:
    args = parse_args()
    instancias = resolve_instance_list(args)

    if args.k is not None and args.k < 1:
        print("ERROR: --k debe ser >= 1.")
        return 1

    plan, sampling_mode, indices_by_file = build_work_plan(args, instancias)

    campaign_global_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.environ["MKP_CAMPAIGN_ID"] = campaign_global_id

    print("=" * 75)
    print("  HPC BENCHMARK RUNNER — INSTANCIAS MKP (CHU & BEASLEY)")
    print("=" * 75)
    print(f"  Campaign Global ID: {campaign_global_id}")
    print(f"  Modo de selección:  {sampling_mode}")
    if sampling_mode == "sampled":
        print(f"  Muestreo:           k={args.k}, seed_base={args.sample_seed}, "
              f"include_zero={args.include_zero}")
    print(f"  Total de unidades:  {len(plan)}")
    for idx, (inst_path, inst_idx) in enumerate(plan, 1):
        print(f"    [{idx:02d}] {inst_path}[{inst_idx}]")
    if args.cpus:
        print(f"  CPUs por instancia:  {args.cpus}")
    if args.epochs:
        print(f"  Épocas por MH:       {args.epochs}")
    if args.skip:
        print(f"  Estrategias omitidas:{', '.join(args.skip)}")
    print("=" * 75)
    print()

    if sampling_mode != "single":
        manifest_path = save_selection_manifest(
            campaign_global_id, indices_by_file, sampling_mode, args
        )
        print(f"  Manifiesto de selección guardado en: {manifest_path}")
        print()

    t_global_start = time.perf_counter()
    reporte = []

    for i, (inst_path, inst_idx) in enumerate(plan, 1):
        inst_name = Path(inst_path).stem
        banner_title = f"INSTANCIA {i}/{len(plan)}: {inst_name}[{inst_idx}]"

        print("\n" + "#" * 75)
        print(f"  >>> INICIANDO {banner_title}")
        print("#" * 75 + "\n")

        cmd = [
            sys.executable,
            "run_all_hpc.py",
            "--instancia", inst_path,
            "--indice", str(inst_idx),
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
            "instancia": f"{inst_name}[{inst_idx}]",
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
    print(f"  Unidades ejecutadas:    {len(reporte)}/{len(plan)}")
    print("-" * 75)
    print(f"  {'Instancia':<25} {'Estado':<20} {'Tiempo':<15}")
    print("-" * 75)
    for r in reporte:
        print(f"  {r['instancia']:<25} {r['status']:<20} {r['tiempo']:<15}")
    print("=" * 75)

    todos_ok = all(r["exitoso"] for r in reporte)
    return 0 if (todos_ok and len(reporte) == len(plan)) else 1


if __name__ == "__main__":
    sys.exit(main())
