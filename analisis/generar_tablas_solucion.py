"""
analisis/generar_tablas_solucion.py — Generador de Tablas de Calidad de Solución (LaTeX + CSV)
=============================================================================================
Genera tablas de calidad de solución en formato LaTeX siguiendo la plantilla predefinida
de `results/tables/solucion/mknapcb1_0.tex` para cada uno de los problemas (mknapcb1..9)
y sus instancias (0, 15, 29).

Métricas calculadas sobre 31 corridas independientes por variante:
  - Best Fitness (máximo alcanzado)
  - Average (media muestral)
  - Std. (desviación estándar muestral con ddof=1)
  - Gap (%) respecto al óptimo teórico conocido: (f* - Average) / f* * 100

Destaca automáticamente en negrita (\\textbf{...}) los mejores valores por metaheurística.
Exporta también archivos CSV y una tabla resumen consolidada multi-instancia.

Uso:
    python -m analisis.generar_tablas_solucion
    python -m analisis.generar_tablas_solucion --indices 0
    python -m analisis.generar_tablas_solucion --indices 0 15 29
    python -m analisis.generar_tablas_solucion --results-dir results
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Metadata de problemas Chu & Beasley MKP
PROBLEM_METADATA: Dict[str, Dict[str, Any]] = {
    "mknapcb1": {"m": 5, "n": 100, "label": "mknapcb1"},
    "mknapcb2": {"m": 5, "n": 250, "label": "mknapcb2"},
    "mknapcb3": {"m": 5, "n": 500, "label": "mknapcb3"},
    "mknapcb4": {"m": 10, "n": 100, "label": "mknapcb4"},
    "mknapcb5": {"m": 10, "n": 250, "label": "mknapcb5"},
    "mknapcb6": {"m": 10, "n": 500, "label": "mknapcb6"},
    "mknapcb7": {"m": 30, "n": 100, "label": "mknapcb7"},
    "mknapcb8": {"m": 30, "n": 250, "label": "mknapcb8"},
    "mknapcb9": {"m": 30, "n": 500, "label": "mknapcb9"},
}

ALL_MHS = ["PSO", "GA", "GWO", "DE"]
MH_DISPLAY_NAMES = {
    "PSO": "BPSO",
    "GA": "GA",
    "GWO": "BGWO",
    "DE": "BDE",
}

STRATEGIES = [
    ("vanilla_explotacion", "Vanilla Exploitation"),
    ("vanilla_exploracion", "Vanilla Exploration"),
    ("binary_simple", "Binary-Simple"),
    ("binary_hysteresis", "Binary-Complex"),
]

DEFAULT_INDICES = [0, 15, 29]


def find_latest_run_dir(strategy_folder: str, inst_key: str, results_root: Path) -> Optional[Path]:
    """Localiza el directorio de corrida más reciente para una estrategia e instancia."""
    base_dir = results_root / strategy_folder / "todos" / inst_key
    if not base_dir.is_dir():
        return None

    run_dirs = [
        d for d in base_dir.iterdir()
        if d.is_dir() and d.name.startswith("comparacion_mhs_")
    ]
    if not run_dirs:
        return None

    return max(run_dirs, key=lambda d: d.name)


def load_instance_fitness(
    prob_name: str,
    idx: int,
    results_root: Path,
) -> Tuple[Dict[str, Dict[str, List[float]]], Optional[float]]:
    """
    Carga los vectores de fitness para una instancia y las 4 estrategias.
    Retorna data[mh][strat_key] = List[float] y el óptimo conocido f*.
    """
    inst_key = f"{prob_name}_{idx}"
    data: Dict[str, Dict[str, List[float]]] = {mh: {} for mh in ALL_MHS}
    optimo_conocido: Optional[float] = None

    for strat_key, _ in STRATEGIES:
        run_dir = find_latest_run_dir(strat_key, inst_key, results_root)
        if not run_dir:
            continue

        for mh in ALL_MHS:
            json_file = run_dir / f"{mh}_{inst_key}.json"
            if not json_file.is_file():
                continue

            try:
                content = json.loads(json_file.read_text(encoding="utf-8"))
                fitness = content.get("fitness", [])
                if fitness:
                    data[mh][strat_key] = [float(x) for x in fitness]
                if optimo_conocido is None and "optimo_conocido" in content:
                    optimo_conocido = float(content["optimo_conocido"])
            except Exception as exc:
                print(f"[WARN] Error leyendo {json_file}: {exc}")

    return data, optimo_conocido


def format_latex_number(value: float, is_int: bool = False) -> str:
    """Formatea números para LaTeX con separador de miles con espacio delgado si corresponde."""
    if is_int:
        return f"{int(round(value)):,}".replace(",", r"\,")
    return f"{value:.2f}"


def generate_single_instance_table(
    prob_name: str,
    idx: int,
    data: Dict[str, Dict[str, List[float]]],
    optimo: Optional[float],
    prob_meta: Dict[str, Any],
) -> str:
    """Genera el código LaTeX para una tabla de solución individual de una instancia."""
    n = prob_meta.get("n", "?")
    m = prob_meta.get("m", "?")
    f_star_str = format_latex_number(optimo, is_int=True) if optimo else "?"

    lines = [
        f"% --- Solution Quality: {prob_name} (Instance {idx}) ---",
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \small",
        f"  \\caption{{Solution quality on \\textbf{{{prob_name}}} (inst. {idx}, $n={n}$, $m={m}$, $f^*={f_star_str}$).}}",
        f"  \\label{{tab:calidad_{prob_name}_{idx}}}",
        r"  \begin{tabular}{lrrrr}",
        r"    \toprule",
        r"    \textbf{MH -- Variant} &",
        r"    \textbf{Best Fitness} &",
        r"    \textbf{Average} &",
        r"    \textbf{Std.} &",
        r"    \textbf{Gap (\%)} \\",
    ]

    for mh_idx, mh in enumerate(ALL_MHS):
        lines.append(r"    \midrule")
        mh_disp = MH_DISPLAY_NAMES.get(mh, mh)

        # Precalcular métricas de las 4 variantes para determinar los mejores
        strat_metrics = []
        for strat_key, strat_label in STRATEGIES:
            fits = data.get(mh, {}).get(strat_key, [])
            if not fits:
                strat_metrics.append((strat_key, strat_label, None, None, None, None))
                continue
            arr = np.array(fits, dtype=float)
            best_val = float(np.max(arr))
            avg_val = float(np.mean(arr))
            std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
            gap_val = ((optimo - avg_val) / optimo * 100.0) if optimo and optimo > 0 else 0.0
            strat_metrics.append((strat_key, strat_label, best_val, avg_val, std_val, gap_val))

        # Encontrar valores óptimos entre las variantes evaluadas
        valid_bests = [m[2] for m in strat_metrics if m[2] is not None]
        valid_avgs = [m[3] for m in strat_metrics if m[3] is not None]
        valid_gaps = [m[5] for m in strat_metrics if m[5] is not None]

        max_best = max(valid_bests) if valid_bests else None
        max_avg = max(valid_avgs) if valid_avgs else None
        min_gap = min(valid_gaps) if valid_gaps else None

        for strat_key, strat_label, best_val, avg_val, std_val, gap_val in strat_metrics:
            row_label = f"{mh_disp} -- {strat_label}"

            if best_val is None:
                lines.append(f"    {row_label:<28} & -- & -- & -- & -- \\\\")
                continue

            # Formateo con negrita para los mejores valores
            is_best_hit = max_best is not None and abs(best_val - max_best) < 1e-6
            best_str = f"\\textbf{{{int(round(best_val))}}}" if is_best_hit else f"{int(round(best_val))}"

            is_avg_hit = max_avg is not None and abs(avg_val - max_avg) < 1e-4
            avg_str = f"\\textbf{{{avg_val:.2f}}}" if is_avg_hit else f"{avg_val:.2f}"

            std_str = f"{std_val:.2f}"

            is_gap_hit = min_gap is not None and abs(gap_val - min_gap) < 1e-4
            gap_str = f"\\textbf{{{gap_val:.2f}}}" if is_gap_hit else f"{gap_val:.2f}"

            lines.append(
                f"    {row_label:<28} & {best_str:>14} & {avg_str:>16} & {std_str:>6} & {gap_str:>12} \\\\"
            )

    lines.extend([
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{table}",
    ])

    return "\n".join(lines)


def export_csv_table(
    prob_name: str,
    idx: int,
    data: Dict[str, Dict[str, List[float]]],
    optimo: Optional[float],
    prob_meta: Dict[str, Any],
    out_csv: Path,
) -> None:
    """Exporta los datos de calidad de solución a un archivo CSV."""
    with open(out_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Problem", "Dim_m", "Dim_n", "Instance_Idx", "Optimum",
            "Algorithm", "Strategy", "Best_Fitness", "Average", "Std", "Gap_Pct"
        ])

        for mh in ALL_MHS:
            mh_disp = MH_DISPLAY_NAMES.get(mh, mh)
            for strat_key, strat_label in STRATEGIES:
                fits = data.get(mh, {}).get(strat_key, [])
                if not fits:
                    continue
                arr = np.array(fits, dtype=float)
                best_val = float(np.max(arr))
                avg_val = float(np.mean(arr))
                std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
                gap_val = ((optimo - avg_val) / optimo * 100.0) if optimo and optimo > 0 else 0.0

                writer.writerow([
                    prob_name, prob_meta.get("m"), prob_meta.get("n"), idx,
                    optimo if optimo else "", mh_disp, strat_label,
                    f"{best_val:.0f}", f"{avg_val:.2f}", f"{std_val:.2f}", f"{gap_val:.4f}"
                ])


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generador de Tablas de Calidad de Solución (LaTeX + CSV)"
    )
    p.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Directorio raíz de resultados (default: results)",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/tables/solucion"),
        help="Directorio destino de tablas LaTeX (default: results/tables/solucion)",
    )
    p.add_argument(
        "--problemas",
        nargs="+",
        default=None,
        help="Problemas a procesar (default: mknapcb1..9)",
    )
    p.add_argument(
        "--indices",
        nargs="+",
        type=int,
        default=DEFAULT_INDICES,
        help=f"Índices de instancias (default: {DEFAULT_INDICES})",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    results_root = args.results_dir
    output_dir = args.out_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    problemas = args.problemas or [f"mknapcb{i}" for i in range(1, 10)]
    indices = sorted(args.indices)

    print("=" * 75)
    print("  GENERADOR DE TABLAS DE CALIDAD DE SOLUCIÓN (LATEX + CSV)")
    print("=" * 75)
    print(f"  Resultados: {results_root}")
    print(f"  Salida:     {output_dir}")
    print(f"  Problemas:  {', '.join(problemas)}")
    print(f"  Instancias: {indices}")
    print("=" * 75)
    print()

    generated_count = 0
    all_rows = []

    for prob_name in problemas:
        prob_meta = PROBLEM_METADATA.get(prob_name, {"m": "?", "n": "?"})

        for idx in indices:
            data, optimo = load_instance_fitness(prob_name, idx, results_root)

            # Verificar si se cargaron datos
            has_data = any(len(data[mh]) > 0 for mh in ALL_MHS)
            if not has_data:
                continue

            # 1. Generar tabla LaTeX individual
            tex_content = generate_single_instance_table(prob_name, idx, data, optimo, prob_meta)
            tex_file = output_dir / f"{prob_name}_{idx}.tex"
            tex_file.write_text(tex_content + "\n", encoding="utf-8")

            # 2. Generar CSV individual
            csv_file = output_dir / f"{prob_name}_{idx}.csv"
            export_csv_table(prob_name, idx, data, optimo, prob_meta, csv_file)

            generated_count += 1
            print(f"  [OK] Generada tabla: {tex_file.name} (CSV: {csv_file.name})")

    print()
    print("=" * 75)
    print(f"  TOTAL TABLAS GENERADAS: {generated_count} archivos .tex y .csv")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(main())
