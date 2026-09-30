"""
analisis/generar_tablas_bonferroni.py — Generador de Tablas Friedman y Bonferroni-Dunn (LaTeX + CSV)
====================================================================================================
Calcula el ranking global de Friedman y el procedimiento post-hoc de Bonferroni-Dunn
para comparar las 4 estrategias algorítmicas:
  1. Binary-Complex (A4: Hysteresis / Propuesto)
  2. Binary-Simple (A3: Simple DTW threshold)
  3. Vanilla-Exploration (Exploration-only baseline)
  4. Vanilla-Exploitation (Exploitation-only baseline)

Reproduce fielmente la plantilla de `results/tables/bonferroni/bonferroni_0.tex`:
  - Rango promedio sobre las combinaciones metaheurística--instancia (36 para una instancia
    a lo largo de los 9 problemas, o 108 para las 27 instancias completas).
  - Posición / Placement (1 = Mejor, menor rango promedio).
  - Estadístico chi-cuadrado de Friedman (chi^2) y p-valor asintótico.
  - Tabla complementaria de test post-hoc de Bonferroni-Dunn comparando el método
    de control (Binary-Complex) contra los baselines con el cálculo de Diferencia Crítica (CD).

Uso:
    python -m analisis.generar_tablas_bonferroni
    python -m analisis.generar_tablas_bonferroni --indices 0
    python -m analisis.generar_tablas_bonferroni --indices 0 15 29
    python -m analisis.generar_tablas_bonferroni --out-dir results/tables/bonferroni
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.stats import friedmanchisquare, norm, rankdata

ALL_MHS = ["PSO", "GA", "GWO", "DE"]

STRATEGIES = [
    ("binary_hysteresis", "Binary-Complex"),
    ("vanilla_exploracion", "Vanilla-Exploration"),
    ("binary_simple", "Binary-Simple"),
    ("vanilla_explotacion", "Vanilla-Exploitation"),
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


def load_strategy_mean_fitness(
    prob_name: str,
    idx: int,
    strategy_key: str,
    mh: str,
    results_root: Path,
) -> Optional[float]:
    """Carga el fitness promedio de las 31 corridas para una combinación dada."""
    inst_key = f"{prob_name}_{idx}"
    run_dir = find_latest_run_dir(strategy_folder=strategy_key, inst_key=inst_key, results_root=results_root)
    if not run_dir:
        return None

    json_file = run_dir / f"{mh}_{inst_key}.json"
    if not json_file.is_file():
        return None

    try:
        content = json.loads(json_file.read_text(encoding="utf-8"))
        fitness = content.get("fitness", [])
        if fitness:
            return float(np.mean(fitness))
    except Exception as exc:
        print(f"[WARN] Error leyendo {json_file}: {exc}")

    return None


def compute_friedman_and_bonferroni(
    blocks: List[List[float]],
    strategy_names: List[str],
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Calcula el ranking de Friedman y el test post-hoc de Bonferroni-Dunn.
    blocks: lista de N vectores, cada uno con k medias (una por estrategia).
    Para problemas de maximización, la mayor media recibe rango 1.
    """
    n_blocks = len(blocks)
    k = len(strategy_names)

    # Matriz de rangos (N filas x k columnas)
    ranks_matrix = []
    for b in blocks:
        # rankdata asigna rangos ascendentes; para maximización, usamos -b
        r = rankdata([-val for val in b], method="average")
        ranks_matrix.append(r)

    ranks_matrix = np.array(ranks_matrix)  # (N, k)
    mean_ranks = np.mean(ranks_matrix, axis=0)

    # Test de Friedman
    try:
        f_res = friedmanchisquare(*(ranks_matrix[:, i] for i in range(k)))
        stat_chi2 = float(f_res.statistic)
        p_val_friedman = float(f_res.pvalue)
    except Exception:
        stat_chi2 = 0.0
        p_val_friedman = 1.0

    # Ordenar estrategias por ranking medio (menor es mejor)
    ordered_indices = np.argsort(mean_ranks)
    ordered_strategies = [strategy_names[i] for i in ordered_indices]
    ordered_mean_ranks = [mean_ranks[i] for i in ordered_indices]

    # Cálculo post-hoc Bonferroni-Dunn
    # Error estándar de las diferencias de rango: SE = sqrt(k * (k + 1) / (6 * N))
    se_rank = math.sqrt((k * (k + 1)) / (6.0 * n_blocks)) if n_blocks > 0 else 1.0

    # Valor crítico z para Bonferroni-Dunn con (k - 1) comparaciones bilaterales
    num_comparisons = k - 1
    alpha_bonf = alpha / num_comparisons
    z_crit = norm.ppf(1.0 - alpha_bonf / 2.0)
    cd = z_crit * se_rank

    # Comparaciones frente al método de control (el de mejor ranking = índice 0 en ordenados)
    control_strat = ordered_strategies[0]
    control_rank = ordered_mean_ranks[0]

    posthoc_results = []
    for i in range(1, k):
        strat_i = ordered_strategies[i]
        rank_i = ordered_mean_ranks[i]
        diff = rank_i - control_rank
        z_val = diff / se_rank if se_rank > 0 else 0.0
        p_unadj = 2.0 * (1.0 - norm.cdf(abs(z_val)))
        p_bonf = min(1.0, p_unadj * num_comparisons)
        is_sig = diff > cd or p_bonf < alpha

        posthoc_results.append({
            "comparison": f"{control_strat} vs. {strat_i}",
            "strategy": strat_i,
            "rank": rank_i,
            "rank_diff": diff,
            "z_value": z_val,
            "p_unadj": p_unadj,
            "p_bonf": p_bonf,
            "significant": is_sig,
        })

    return {
        "n_blocks": n_blocks,
        "k": k,
        "se_rank": se_rank,
        "cd": cd,
        "chi2": stat_chi2,
        "p_friedman": p_val_friedman,
        "ordered_strategies": ordered_strategies,
        "ordered_mean_ranks": ordered_mean_ranks,
        "posthoc": posthoc_results,
    }


def generate_friedman_table_latex(results: Dict[str, Any], table_label: str = "tab:friedman_ranking") -> str:
    """Genera la tabla LaTeX principal de ranking de Friedman idéntica a bonferroni_0.tex."""
    n_blocks = results["n_blocks"]
    chi2 = results["chi2"]
    p_val = results["p_friedman"]

    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        f"  \\caption{{Global Friedman ranking across the {n_blocks} metaheuristic--instance combinations.}}",
        f"  \\label{{{table_label}}}",
        r"  \begin{tabular}{lcc}",
        r"    \toprule",
        r"    \textbf{Strategy} &",
        r"    \textbf{Mean Rank (1=Best)} &",
        r"    \textbf{Placement} \\",
        r"    \midrule",
    ]

    for place, (strat, m_rank) in enumerate(zip(results["ordered_strategies"], results["ordered_mean_ranks"]), start=1):
        if place == 1:
            strat_str = f"\\textbf{{{strat}}}"
            rank_str = f"\\textbf{{{m_rank:.2f}}}"
            place_str = f"\\textbf{{{place}}}"
        else:
            strat_str = f"{strat:<22}"
            rank_str = f"{m_rank:.2f}"
            place_str = f"{place}"

        lines.append(f"    {strat_str:<32} & {rank_str:>6} & {place_str:>2} \\\\")

    lines.extend([
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{1ex}",
        "",
        r"  \footnotesize Friedman statistic:",
        f"  $\\chi^2={chi2:.2f}$, $p={p_val:.4f}$.",
        r"\end{table}",
    ])

    return "\n".join(lines)


def generate_bonferroni_posthoc_latex(results: Dict[str, Any], table_label: str = "tab:bonferroni_posthoc") -> str:
    """Genera la tabla complementaria de comparaciones post-hoc de Bonferroni-Dunn."""
    n_blocks = results["n_blocks"]
    cd = results["cd"]
    se = results["se_rank"]
    control_name = results["ordered_strategies"][0]

    lines = [
        "% --- Bonferroni-Dunn Post-Hoc Comparison Table ---",
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \small",
        f"  \\caption{{Bonferroni-Dunn Post-Hoc Test ($N={n_blocks}$, Control: \\textbf{{{control_name}}}, $\\alpha=0.05$, $CD={cd:.3f}$).}}",
        f"  \\label{{{table_label}}}",
        r"  \begin{tabular}{lcccc}",
        r"    \toprule",
        r"    \textbf{Comparison} & \textbf{Rank Diff.} & \textbf{$z$-statistic} & \textbf{$p_{\text{unadj}}$} & \textbf{$p_{\text{Bonf}}$} \\",
        r"    \midrule",
    ]

    for p_info in results["posthoc"]:
        comp_str = p_info["comparison"]
        diff_str = f"{p_info['rank_diff']:.2f}"
        z_str = f"{p_info['z_value']:.2f}"
        p_unadj_str = f"{p_info['p_unadj']:.4f}"
        p_bonf_str = f"{p_info['p_bonf']:.4f}"

        if p_info["significant"]:
            diff_str = f"\\textbf{{{diff_str}}}"
            p_bonf_str = f"\\textbf{{{p_bonf_str}}}"

        lines.append(f"    {comp_str:<38} & {diff_str:>6} & {z_str:>5} & {p_unadj_str:>7} & {p_bonf_str:>7} \\\\")

    lines.extend([
        r"    \bottomrule",
        r"  \end{tabular}",
        r"  \vspace{1ex}",
        "",
        f"  \\footnotesize Standard Error: $SE={se:.4f}$, Critical Difference: $CD={cd:.3f}$.",
        r"\end{table}",
    ])

    return "\n".join(lines)


def export_bonferroni_csv(results: Dict[str, Any], out_csv: Path) -> None:
    """Exporta el ranking de Friedman y los tests post-hoc a CSV."""
    with open(out_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Section", "Item", "Value", "Notes"])
        writer.writerow(["Friedman", "Statistic_Chi2", f"{results['chi2']:.4f}", ""])
        writer.writerow(["Friedman", "p_value", f"{results['p_friedman']:.4e}", ""])
        writer.writerow(["Friedman", "N_blocks", f"{results['n_blocks']}", ""])
        writer.writerow(["Friedman", "k_strategies", f"{results['k']}", ""])
        writer.writerow([])

        writer.writerow(["Ranking", "Placement", "Strategy", "Mean_Rank"])
        for place, (strat, m_rank) in enumerate(zip(results["ordered_strategies"], results["ordered_mean_ranks"]), start=1):
            writer.writerow(["Ranking", place, strat, f"{m_rank:.4f}"])
        writer.writerow([])

        writer.writerow(["PostHoc", "Comparison", "Rank_Diff", "z_value", "p_unadjusted", "p_bonferroni", "Significant"])
        for p_info in results["posthoc"]:
            writer.writerow([
                "PostHoc", p_info["comparison"], f"{p_info['rank_diff']:.4f}",
                f"{p_info['z_value']:.4f}", f"{p_info['p_unadj']:.4e}",
                f"{p_info['p_bonf']:.4e}", "Yes" if p_info["significant"] else "No"
            ])


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generador de Tablas Friedman y Bonferroni-Dunn (LaTeX + CSV)"
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
        default=Path("results/tables/bonferroni"),
        help="Directorio de destino (default: results/tables/bonferroni)",
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
        help=f"Índices de instancias a incluir (default: {DEFAULT_INDICES})",
    )
    return p.parse_args()


def collect_blocks_for_index(
    problemas: List[str],
    idx: int,
    results_root: Path,
) -> Tuple[List[List[float]], List[str]]:
    """Recolecta los bloques de medias para un índice de instancia (típicamente 36 bloques)."""
    blocks: List[List[float]] = []
    strat_keys = [s[0] for s in STRATEGIES]
    strat_labels = [s[1] for s in STRATEGIES]

    for prob in problemas:
        for mh in ALL_MHS:
            row_means = []
            for s_key in strat_keys:
                m_fit = load_strategy_mean_fitness(prob, idx, s_key, mh, results_root)
                if m_fit is not None:
                    row_means.append(m_fit)

            if len(row_means) == len(strat_keys):
                blocks.append(row_means)

    return blocks, strat_labels


def main() -> int:
    args = parse_args()
    results_root = args.results_dir
    output_dir = args.out_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    problemas = args.problemas or [f"mknapcb{i}" for i in range(1, 10)]
    indices = sorted(args.indices)

    print("=" * 75)
    print("  GENERADOR DE TABLAS FRIEDMAN Y BONFERRONI-DUNN (LATEX + CSV)")
    print("=" * 75)
    print(f"  Resultados: {results_root}")
    print(f"  Salida:     {output_dir}")
    print(f"  Problemas:  {', '.join(problemas)}")
    print(f"  Instancias: {indices}")
    print("=" * 75)
    print()

    # 1. Generar tablas para cada índice específico de instancia (ej. bonferroni_0.tex, 15, 29)
    for idx in indices:
        blocks, strat_names = collect_blocks_for_index(problemas, idx, results_root)
        if not blocks:
            continue

        res = compute_friedman_and_bonferroni(blocks, strat_names)

        # Tabla principal de Friedman (idéntica a bonferroni_0.tex)
        tex_main = generate_friedman_table_latex(res, table_label=f"tab:friedman_inst{idx}")
        tex_main_file = output_dir / f"bonferroni_{idx}.tex"
        tex_main_file.write_text(tex_main + "\n", encoding="utf-8")

        # Tabla complementaria de post-hoc Bonferroni-Dunn
        tex_posthoc = generate_bonferroni_posthoc_latex(res, table_label=f"tab:bonferroni_posthoc_inst{idx}")
        tex_posthoc_file = output_dir / f"bonferroni_posthoc_{idx}.tex"
        tex_posthoc_file.write_text(tex_posthoc + "\n", encoding="utf-8")

        # Exportación CSV
        csv_file = output_dir / f"bonferroni_{idx}.csv"
        export_bonferroni_csv(res, csv_file)

        print(f"  [OK] Generada tabla Friedman:  {tex_main_file.name}")
        print(f"       Generada tabla Post-Hoc:  {tex_posthoc_file.name}")
        print(f"       Generado archivo CSV:     {csv_file.name}")

    # 2. Generar tabla global consolidada con todas las 27 instancias (N = 108 bloques)
    if len(indices) > 1:
        all_blocks: List[List[float]] = []
        strat_names = [s[1] for s in STRATEGIES]
        for idx in indices:
            b_idx, _ = collect_blocks_for_index(problemas, idx, results_root)
            all_blocks.extend(b_idx)

        res_global = compute_friedman_and_bonferroni(all_blocks, strat_names)

        tex_glob_main = generate_friedman_table_latex(res_global, table_label="tab:friedman_all_instances")
        tex_glob_file = output_dir / "bonferroni_all.tex"
        tex_glob_file.write_text(tex_glob_main + "\n", encoding="utf-8")

        tex_glob_posthoc = generate_bonferroni_posthoc_latex(res_global, table_label="tab:bonferroni_posthoc_all")
        tex_glob_posthoc_file = output_dir / "bonferroni_posthoc_all.tex"
        tex_glob_posthoc_file.write_text(tex_glob_posthoc + "\n", encoding="utf-8")

        csv_glob_file = output_dir / "bonferroni_all.csv"
        export_bonferroni_csv(res_global, csv_glob_file)

        print(f"\n  [OK] Tabla global Friedman:   {tex_glob_file.name}")
        print(f"       Tabla global Post-Hoc:   {tex_glob_posthoc_file.name}")
        print(f"       Archivo global CSV:      {csv_glob_file.name}")

    print()
    print("=" * 75)
    print("  PROCESO FRIEDMAN / BONFERRONI FINALIZADO CON ÉXITO")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(main())
