"""
analisis/generar_tablas_tiempo.py — Generador de Tablas de Tiempo Computacional (LaTeX + CSV)
=============================================================================================
Genera tablas de tiempo de ejecución computacional en formato LaTeX y CSV siguiendo la
plantilla predefinida en `results/tables/tiempo/costo_computacional.tex`.

Compara las 4 variantes algorítmicas a lo largo de los 9 problemas (mknapcb1..9) y sus
instancias (0, 15, 29) sobre las 31 corridas independientes:
  1. V-Exploit   (Vanilla Exploitation)
  2. V-Explore   (Vanilla Exploration)
  3. Bin-Simple  (Binary-Simple / A3)
  4. Bin-Complex (Binary-Complex / A4 Hysteresis)

Métricas calculadas:
  - Tiempo medio (Mean) y desviación estándar muestral (Std, ddof=1) en segundos [s].
  - Resalta en negrita (\\mathbf{...}) el menor tiempo de cómputo por metaheurística.
  - Genera tablas específicas por índice de instancia (0, 15, 29), la tabla consolidada
    principal (`costo_computacional.tex`), el desglose completo de 27 instancias (`costo_computacional_all.tex`)
    y archivos CSV con métricas de sobrecosto relativo (Delta t%).

Uso:
    python -m analisis.generar_tablas_tiempo
    python -m analisis.generar_tablas_tiempo --indices 0
    python -m analisis.generar_tablas_tiempo --indices 0 15 29
    python -m analisis.generar_tablas_tiempo --results-dir results_old/results-200-40-60
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ALL_MHS = ["PSO", "GA", "GWO", "DE"]
MH_DISPLAY_NAMES = {
    "PSO": "BPSO",
    "GA": "GA",
    "GWO": "BGWO",
    "DE": "BDE",
}

STRATEGIES = [
    ("vanilla_explotacion", "V-Exploit"),
    ("vanilla_exploracion", "V-Explore"),
    ("binary_simple", "Bin-Simple"),
    ("binary_hysteresis", "Bin-Complex"),
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


def load_instance_times(
    prob_name: str,
    idx: int,
    results_root: Path,
) -> Dict[str, Dict[str, List[float]]]:
    """Carga los vectores de 'tiempos' de ejecución [s] para las 4 estrategias y las 4 MHs."""
    inst_key = f"{prob_name}_{idx}"
    data: Dict[str, Dict[str, List[float]]] = {mh: {} for mh in ALL_MHS}

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
                tiempos = content.get("tiempos", [])
                if tiempos:
                    data[mh][strat_key] = [float(t) for t in tiempos]
                elif "stats" in content and "tiempo_promedio" in content["stats"]:
                    # Fallback si solo están los escalares estadísticos
                    data[mh][strat_key] = [float(content["stats"]["tiempo_promedio"])]
            except Exception as exc:
                print(f"[WARN] Error leyendo tiempos en {json_file}: {exc}")

    return data


def compute_time_stats(times: List[float]) -> Tuple[float, float, int]:
    """Retorna (mean, std_sample, n)."""
    if not times:
        return 0.0, 0.0, 0
    arr = np.array(times, dtype=float)
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    return mean_val, std_val, len(arr)


def generate_computational_cost_table_latex(
    rows_data: List[Dict[str, Any]],
    caption_text: str = "Computational Execution Time [s] (Mean $\\pm$ Std) across 31 Independent Runs",
    table_label: str = "tab:computational_cost",
) -> str:
    """Genera el código LaTeX para la tabla de costo computacional."""
    lines = [
        "% --- Computational Execution Time Table ---",
        r"\begin{table*}[htbp]",
        r"  \centering",
        r"  \small",
        f"  \\caption{{{caption_text}}}",
        f"  \\label{{{table_label}}}",
        r"  \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llcccc@{}}",
        r"    \toprule",
        r"    \textbf{Instance} & \textbf{Algorithm} & \textbf{V-Exploit} & \textbf{V-Explore} & \textbf{Bin-Simple} & \textbf{Bin-Complex} \\",
    ]

    current_group = ""

    for row in rows_data:
        group_id = row["group_id"]
        if group_id != current_group:
            lines.append(r"    \midrule")
            inst_label = f"\\textbf{{{row['display_instance']}}}"
            current_group = group_id
        else:
            inst_label = ""

        mh_label = row["mh_display"]

        # Identificar el menor tiempo medio para resaltarlo en negrita
        valid_means = [
            row[strat_key]["mean"]
            for strat_key, _ in STRATEGIES
            if row[strat_key]["count"] > 0
        ]
        min_mean = min(valid_means) if valid_means else None

        cells = []
        for strat_key, _ in STRATEGIES:
            info = row[strat_key]
            if info["count"] == 0:
                cells.append("--")
                continue

            m_val = info["mean"]
            s_val = info["std"]

            val_str = f"{m_val:.1f} \\pm {s_val:.1f}"
            is_fastest = min_mean is not None and abs(m_val - min_mean) < 1e-4

            if is_fastest:
                cells.append(f"$\\mathbf{{{val_str}}}$")
            else:
                cells.append(f"${val_str}$")

        cells_str = " & ".join(f"{c:>24}" for c in cells)
        lines.append(f"    {inst_label:<18} & {mh_label:<5} & {cells_str} \\\\")

    lines.extend([
        r"    \bottomrule",
        r"  \end{tabular*}",
        r"\end{table*}",
    ])

    return "\n".join(lines)


def export_time_csv(rows_data: List[Dict[str, Any]], out_csv: Path) -> None:
    """Exporta las estadísticas de tiempo computacional y sobrecosto a CSV."""
    with open(out_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Instance", "Algorithm",
            "V_Exploit_Mean", "V_Exploit_Std",
            "V_Explore_Mean", "V_Explore_Std",
            "Bin_Simple_Mean", "Bin_Simple_Std",
            "Bin_Complex_Mean", "Bin_Complex_Std",
            "Overhead_Complex_vs_Exploit_Pct",
            "Overhead_Complex_vs_Explore_Pct",
        ])

        for r in rows_data:
            ve = r["vanilla_explotacion"]["mean"]
            vx = r["vanilla_exploracion"]["mean"]
            bc = r["binary_hysteresis"]["mean"]

            ov_exp = ((bc - ve) / ve * 100.0) if ve > 0 else 0.0
            ov_xpr = ((bc - vx) / vx * 100.0) if vx > 0 else 0.0

            writer.writerow([
                r["display_instance"], r["mh_display"],
                f"{r['vanilla_explotacion']['mean']:.2f}", f"{r['vanilla_explotacion']['std']:.2f}",
                f"{r['vanilla_exploracion']['mean']:.2f}", f"{r['vanilla_exploracion']['std']:.2f}",
                f"{r['binary_simple']['mean']:.2f}", f"{r['binary_simple']['std']:.2f}",
                f"{r['binary_hysteresis']['mean']:.2f}", f"{r['binary_hysteresis']['std']:.2f}",
                f"{ov_exp:+.2f}%", f"{ov_xpr:+.2f}%"
            ])


def collect_rows_for_index(
    problemas: List[str],
    idx: int,
    results_root: Path,
) -> List[Dict[str, Any]]:
    """Recolecta datos de tiempo computacional para un índice de instancia a lo largo de los problemas."""
    rows: List[Dict[str, Any]] = []

    for prob in problemas:
        data = load_instance_times(prob, idx, results_root)

        for mh in ALL_MHS:
            mh_disp = MH_DISPLAY_NAMES.get(mh, mh)
            row_dict: Dict[str, Any] = {
                "group_id": prob,
                "display_instance": prob,
                "mh_display": mh_disp,
            }

            for strat_key, _ in STRATEGIES:
                t_list = data.get(mh, {}).get(strat_key, [])
                m, s, n = compute_time_stats(t_list)
                row_dict[strat_key] = {"mean": m, "std": s, "count": n}

            rows.append(row_dict)

    return rows


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generador de Tablas de Tiempo Computacional (LaTeX + CSV)"
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
        default=Path("results/tables/tiempo"),
        help="Directorio de salida (default: results/tables/tiempo)",
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
    print("  GENERADOR DE TABLAS DE TIEMPO COMPUTACIONAL (LATEX + CSV)")
    print("=" * 75)
    print(f"  Resultados: {results_root}")
    print(f"  Salida:     {output_dir}")
    print(f"  Problemas:  {', '.join(problemas)}")
    print(f"  Instancias: {indices}")
    print("=" * 75)
    print()

    # 1. Generar tabla de tiempo por cada índice de instancia (0, 15, 29)
    for idx in indices:
        rows = collect_rows_for_index(problemas, idx, results_root)
        if not rows:
            continue

        tex_content = generate_computational_cost_table_latex(
            rows_data=rows,
            caption_text=f"Computational Execution Time [s] (Mean $\\pm$ Std) across 31 Independent Runs (Instance {idx})",
            table_label=f"tab:computational_cost_inst{idx}",
        )

        tex_file = output_dir / f"costo_computacional_{idx}.tex"
        csv_file = output_dir / f"costo_computacional_{idx}.csv"

        tex_file.write_text(tex_content + "\n", encoding="utf-8")
        export_time_csv(rows, csv_file)
        print(f"  [OK] Tabla generada: {tex_file.name} y {csv_file.name}")

    # Si se procesó la instancia 0, también actualizar/asegurar costo_computacional.tex
    if 0 in indices:
        rows_0 = collect_rows_for_index(problemas, 0, results_root)
        if rows_0:
            tex_main = generate_computational_cost_table_latex(
                rows_data=rows_0,
                caption_text="Computational Execution Time [s] (Mean $\\pm$ Std) across 31 Independent Runs",
                table_label="tab:computational_cost",
            )
            main_file = output_dir / "costo_computacional.tex"
            main_file.write_text(tex_main + "\n", encoding="utf-8")
            print(f"  [OK] Tabla principal actualizada: {main_file.name}")

    # 2. Generar tabla consolidada con las 27 instancias individuales
    if len(indices) > 1:
        all_rows: List[Dict[str, Any]] = []
        for prob in problemas:
            for idx in indices:
                data = load_instance_times(prob, idx, results_root)
                inst_label = f"{prob}[{idx}]"

                for mh in ALL_MHS:
                    mh_disp = MH_DISPLAY_NAMES.get(mh, mh)
                    row_dict: Dict[str, Any] = {
                        "group_id": f"{prob}_{idx}",
                        "display_instance": inst_label,
                        "mh_display": mh_disp,
                    }

                    for strat_key, _ in STRATEGIES:
                        t_list = data.get(mh, {}).get(strat_key, [])
                        m, s, n = compute_time_stats(t_list)
                        row_dict[strat_key] = {"mean": m, "std": s, "count": n}

                    all_rows.append(row_dict)

        tex_all = generate_computational_cost_table_latex(
            rows_data=all_rows,
            caption_text="Computational Execution Time [s] (Mean $\\pm$ Std) across All 27 Benchmark Instances",
            table_label="tab:computational_cost_all_instances",
        )
        all_tex_file = output_dir / "costo_computacional_all.tex"
        all_csv_file = output_dir / "costo_computacional_all.csv"

        all_tex_file.write_text(tex_all + "\n", encoding="utf-8")
        export_time_csv(all_rows, all_csv_file)
        print(f"  [OK] Tabla consolidada 27 instancias: {all_tex_file.name} y {all_csv_file.name}")

    print()
    print("=" * 75)
    print("  PROCESO DE TIEMPOS COMPUTACIONALES FINALIZADO CON ÉXITO")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(main())
