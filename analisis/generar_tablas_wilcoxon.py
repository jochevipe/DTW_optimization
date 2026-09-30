"""
analisis/generar_tablas_wilcoxon.py — Generador de Tablas Wilcoxon (LaTeX + CSV)
================================================================================
Genera tablas de validación estadística no paramétrica mediante el test de rangos
con signo de Wilcoxon (Wilcoxon Signed-Rank Test, R=31 corridas apareadas, alpha=0.05).
Compara la variante propuesta (Binary-Complex) frente a:
  1. Vanilla Exploitation (baseline explotación pura)
  2. Vanilla Exploration (baseline exploración pura)
  3. Binary-Simple (control DTW simple sin histéresis)

Reproduce fielmente la plantilla de `results/tables/wilcoxon/wilcoxon_0.tex`:
  - P-valores formateados con notación científica para p < 0.001 (ej. 5.726e-06)
    o 4 decimales para p >= 0.001 (ej. 0.1610).
  - Veredictos estadísticos:
      '+' : Binary-Complex estadísticamente superior (p < 0.05 y mayor rendimiento).
      '~' : Sin diferencia estadísticamente significativa (p >= 0.05).
      '-' : Baseline estadísticamente superior (p < 0.05 y mayor rendimiento).
  - Fila inferior de conteos consolidados: Total (+ / ~ / -).
  - Genera tablas por índice de instancia (0, 15, 29) y una tabla consolidada global.

Uso:
    python -m analisis.generar_tablas_wilcoxon
    python -m analisis.generar_tablas_wilcoxon --indices 0 15 29
    python -m analisis.generar_tablas_wilcoxon --out-dir results/tables/wilcoxon
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.stats import wilcoxon

ALL_MHS = ["PSO", "GA", "GWO", "DE"]
MH_DISPLAY_NAMES = {
    "PSO": "BPSO",
    "GA": "GA",
    "GWO": "BGWO",
    "DE": "BDE",
}

BASELINES = [
    ("vanilla_explotacion", "Vanilla (Exploit)"),
    ("vanilla_exploracion", "Vanilla (Explore)"),
    ("binary_simple", "Binary-Simple"),
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
) -> Dict[str, Dict[str, List[float]]]:
    """Carga los vectores de fitness para las 4 estrategias y las 4 MHs."""
    inst_key = f"{prob_name}_{idx}"
    data: Dict[str, Dict[str, List[float]]] = {mh: {} for mh in ALL_MHS}

    strats_to_load = ["binary_hysteresis"] + [b[0] for b in BASELINES]
    for strat in strats_to_load:
        run_dir = find_latest_run_dir(strat, inst_key, results_root)
        if not run_dir:
            continue

        for mh in ALL_MHS:
            json_file = run_dir / f"{mh}_{inst_key}.json"
            if not json_file.is_file():
                continue

            try:
                content = json.loads(json_file.read_text(encoding="utf-8"))
                fits = content.get("fitness", [])
                if fits:
                    data[mh][strat] = [float(x) for x in fits]
            except Exception as exc:
                print(f"[WARN] Error leyendo {json_file}: {exc}")

    return data


def format_p_value(p: float) -> str:
    """Formatea el p-valor: notación científica si p < 0.001, o 4 decimales si p >= 0.001."""
    if p < 0.001:
        # Notación científica con 3 decimales en la mantisa (ej. 5.726e-06)
        formatted = f"{p:.3e}"
        # Normalizar exponente a 2 dígitos si la plataforma añade 3 (ej. e-006 -> e-06)
        parts = formatted.split("e")
        exp = int(parts[1])
        sign = "-" if exp < 0 else "+"
        return f"{parts[0]}e{sign}{abs(exp):02d}"
    return f"{p:.4f}"


def run_pairwise_wilcoxon(
    focal_runs: List[float],
    baseline_runs: List[float],
    alpha: float = 0.05,
) -> Tuple[float, str, float]:
    """
    Ejecuta el test de Wilcoxon de dos colas sobre pares de observaciones.
    Retorna (p_value, sign, mean_diff).
    """
    if len(focal_runs) == 0 or len(baseline_runs) == 0:
        return 1.0, r"$\approx$", 0.0

    arr_focal = np.array(focal_runs, dtype=float)
    arr_base = np.array(baseline_runs, dtype=float)

    # Si todas las diferencias son cero, p=1.0 y sin diferencia
    diffs = arr_focal - arr_base
    if np.all(diffs == 0):
        return 1.0, r"$\approx$", 0.0

    try:
        res = wilcoxon(arr_focal, arr_base, zero_method="wilcox", alternative="two-sided")
        p_val = float(res.pvalue)
    except Exception:
        return 1.0, r"$\approx$", 0.0

    mean_diff = float(np.mean(diffs))

    if p_val < alpha:
        if mean_diff > 0:
            sign = r"$+$"
        else:
            sign = r"$-$"
    else:
        sign = r"$\approx$"

    return p_val, sign, mean_diff


def generate_wilcoxon_table_latex(
    wilcoxon_rows: List[Dict[str, Any]],
    instance_title: str,
    table_label: str = "tab:wilcoxon_tests",
) -> str:
    """Genera el código LaTeX para la tabla de tests de Wilcoxon en formato tabular*."""
    lines = [
        "% --- Non-Parametric Wilcoxon Signed-Rank Test Table ---",
        r"\begin{table*}[htbp]",
        r"  \centering",
        r"  \small",
        f"  \\caption{{Pairwise Wilcoxon Signed-Rank Test: Proposed \\textbf{{Binary-Complex}} vs. Baselines ($\\alpha=0.05$, $R=31$, {instance_title}). Verdict signs: $+$ indicates Binary-Complex is statistically superior ($p < 0.05$); $\\approx$ indicates no significant difference ($p \\ge 0.05$); $-$ indicates baseline is superior.}}",
        f"  \\label{{{table_label}}}",
        r"  \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llcccccc@{}}",
        r"    \toprule",
        r"    & & \multicolumn{2}{c}{\textbf{vs. Vanilla (Exploit)}} & \multicolumn{2}{c}{\textbf{vs. Vanilla (Explore)}} & \multicolumn{2}{c}{\textbf{vs. Binary-Simple}} \\",
        r"    \cmidrule(lr){3-4} \cmidrule(lr){5-6} \cmidrule(lr){7-8}",
        r"    \textbf{Instance} & \textbf{Algorithm} & $p$-value & Sign & $p$-value & Sign & $p$-value & Sign \\",
    ]

    total_counts = {
        "vanilla_explotacion": {"+": 0, "~": 0, "-": 0},
        "vanilla_exploracion": {"+": 0, "~": 0, "-": 0},
        "binary_simple": {"+": 0, "~": 0, "-": 0},
    }

    current_group = ""

    for row in wilcoxon_rows:
        group_id = row["group_id"]
        if group_id != current_group:
            lines.append(r"    \midrule")
            inst_label = f"\\textbf{{{row['display_instance']}}}"
            current_group = group_id
        else:
            inst_label = ""

        mh_label = row["mh_display"]

        row_tokens = [f"    {inst_label:<18} & {mh_label:<5}"]

        for strat_key, _ in BASELINES:
            p_val = row[strat_key]["p_value"]
            sign = row[strat_key]["sign"]

            p_str = format_p_value(p_val)
            row_tokens.append(f"& {p_str:>9} & {sign}")

            if "+" in sign:
                total_counts[strat_key]["+"] += 1
            elif "-" in sign:
                total_counts[strat_key]["-"] += 1
            else:
                total_counts[strat_key]["~"] += 1

        lines.append(" ".join(row_tokens) + r" \\")

    # Fila de totales
    lines.append(r"    \midrule")
    tot_tokens = [r"    \multicolumn{2}{l}{\textbf{Total ($+ / \approx / -$)}}"]
    for strat_key, _ in BASELINES:
        cnt = total_counts[strat_key]
        str_val = f"{cnt['+']} / {cnt['~']} / {cnt['-']}"
        tot_tokens.append(f"& \\multicolumn{{2}}{{c}}{{\\textbf{{{str_val}}}}} ")

    lines.append(" ".join(tot_tokens) + r"\\")
    lines.extend([
        r"    \bottomrule",
        r"  \end{tabular*}",
        r"  \vspace{1ex}",
        r"\end{table*}",
    ])

    return "\n".join(lines)


def export_wilcoxon_csv(wilcoxon_rows: List[Dict[str, Any]], out_csv: Path) -> None:
    """Exporta los resultados detallados a CSV."""
    with open(out_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Instance", "MH",
            "p_vs_exploit", "sign_vs_exploit", "diff_vs_exploit",
            "p_vs_explore", "sign_vs_explore", "diff_vs_explore",
            "p_vs_simple", "sign_vs_simple", "diff_vs_simple",
        ])

        for r in wilcoxon_rows:
            e = r["vanilla_explotacion"]
            x = r["vanilla_exploracion"]
            s = r["binary_simple"]

            clean_sign = lambda s_raw: "+" if "+" in s_raw else ("-" if "-" in s_raw else "~")

            writer.writerow([
                r["display_instance"], r["mh_display"],
                f"{e['p_value']:.4e}", clean_sign(e["sign"]), f"{e['diff']:.2f}",
                f"{x['p_value']:.4e}", clean_sign(x["sign"]), f"{x['diff']:.2f}",
                f"{s['p_value']:.4e}", clean_sign(s["sign"]), f"{s['diff']:.2f}",
            ])


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generador de Tablas Wilcoxon (LaTeX + CSV)"
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
        default=Path("results/tables/wilcoxon"),
        help="Directorio de destino (default: results/tables/wilcoxon)",
    )
    p.add_argument(
        "--problemas",
        nargs="+",
        default=None,
        help="Problemas a incluir (default: mknapcb1..9)",
    )
    p.add_argument(
        "--indices",
        nargs="+",
        type=int,
        default=DEFAULT_INDICES,
        help=f"Índices de instancias a evaluar (default: {DEFAULT_INDICES})",
    )
    return p.parse_args()


def process_instance_index(
    problemas: List[str],
    idx: int,
    results_root: Path,
) -> List[Dict[str, Any]]:
    """Procesa una lista de filas para un índice específico de instancia a lo largo de los 9 problemas."""
    rows: List[Dict[str, Any]] = []

    for prob in problemas:
        data = load_instance_fitness(prob, idx, results_root)

        for mh in ALL_MHS:
            mh_disp = MH_DISPLAY_NAMES.get(mh, mh)
            focal_runs = data.get(mh, {}).get("binary_hysteresis", [])

            row_dict: Dict[str, Any] = {
                "group_id": prob,
                "display_instance": prob,
                "mh_display": mh_disp,
            }

            for strat_key, _ in BASELINES:
                base_runs = data.get(mh, {}).get(strat_key, [])
                p_val, sign, diff = run_pairwise_wilcoxon(focal_runs, base_runs)
                row_dict[strat_key] = {
                    "p_value": p_val,
                    "sign": sign,
                    "diff": diff,
                }

            rows.append(row_dict)

    return rows


def main() -> int:
    args = parse_args()
    results_root = args.results_dir
    output_dir = args.out_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    problemas = args.problemas or [f"mknapcb{i}" for i in range(1, 10)]
    indices = sorted(args.indices)

    print("=" * 75)
    print("  GENERADOR DE TABLAS WILCOXON (LATEX + CSV)")
    print("=" * 75)
    print(f"  Resultados: {results_root}")
    print(f"  Salida:     {output_dir}")
    print(f"  Problemas:  {', '.join(problemas)}")
    print(f"  Instancias: {indices}")
    print("=" * 75)
    print()

    # 1. Generar tabla Wilcoxon por cada índice de instancia (ej. wilcoxon_0.tex, 15, 29)
    for idx in indices:
        rows = process_instance_index(problemas, idx, results_root)
        if not rows:
            continue

        tex_table = generate_wilcoxon_table_latex(
            wilcoxon_rows=rows,
            instance_title=f"Representative Instance {idx}",
            table_label=f"tab:wilcoxon_inst{idx}",
        )

        tex_file = output_dir / f"wilcoxon_{idx}.tex"
        csv_file = output_dir / f"wilcoxon_{idx}.csv"

        tex_file.write_text(tex_table + "\n", encoding="utf-8")
        export_wilcoxon_csv(rows, csv_file)

        print(f"  [OK] Tabla generada: {tex_file.name} y {csv_file.name}")

    # 2. Generar tabla consolidada con todas las 27 instancias individuales
    if len(indices) > 1:
        all_rows: List[Dict[str, Any]] = []
        for prob in problemas:
            for idx in indices:
                inst_label = f"{prob}[{idx}]"
                data = load_instance_fitness(prob, idx, results_root)
                for mh in ALL_MHS:
                    mh_disp = MH_DISPLAY_NAMES.get(mh, mh)
                    focal_runs = data.get(mh, {}).get("binary_hysteresis", [])
                    row_dict: Dict[str, Any] = {
                        "group_id": f"{prob}_{idx}",
                        "display_instance": inst_label,
                        "mh_display": mh_disp,
                    }
                    for strat_key, _ in BASELINES:
                        base_runs = data.get(mh, {}).get(strat_key, [])
                        p_val, sign, diff = run_pairwise_wilcoxon(focal_runs, base_runs)
                        row_dict[strat_key] = {
                            "p_value": p_val,
                            "sign": sign,
                            "diff": diff,
                        }
                    all_rows.append(row_dict)

        tex_global = generate_wilcoxon_table_latex(
            wilcoxon_rows=all_rows,
            instance_title="All 27 Benchmark Instances",
            table_label="tab:wilcoxon_all_instances",
        )
        global_tex_file = output_dir / "wilcoxon_all.tex"
        global_csv_file = output_dir / "wilcoxon_all.csv"
        global_tex_file.write_text(tex_global + "\n", encoding="utf-8")
        export_wilcoxon_csv(all_rows, global_csv_file)
        print(f"  [OK] Tabla consolidada generada: {global_tex_file.name} y {global_csv_file.name}")

    print()
    print("=" * 75)
    print("  PROCESO WILCOXON FINALIZADO CON ÉXITO")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(main())
