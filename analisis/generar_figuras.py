"""
analisis/generar_figuras.py — Generador de Boxplots para el Paper (Chu & Beasley MKP)
====================================================================================
Genera figuras científicas en alta resolución (PDF vectorial + PNG 300 DPI) para
comparar las 4 versiones algorítmicas en las subsecciones del paper:

    1. V-Explotación (Exploitation-only baseline)
    2. V-Exploración (Exploration-only baseline)
    3. Binary-Simple (A3: Fire D2)
    4. Binary-Complex (A4: Fire Binario / Hysteresis)

Estructura de figuras:
  - Figuras consolidadas por problema (3 filas x 4 columnas):
      Muestra las 3 instancias (0, 15, 29) y las 4 metaheurísticas (PSO, GA, GWO, DE).
      Ideal para una figura principal por subsección de problema (mknapcb1, 2, ..., 9).
  - Figuras individuales por instancia (1 fila x 4 columnas):
      Guardadas en results/figuras/individuales/ para uso como subfiguras en LaTeX.
  - Figuras de Gap al óptimo (%) por problema:
      Muestra el error relativo porcentual respecto al óptimo teórico conocido.

Uso:
    python -m analisis.generar_figuras
    python -m analisis.generar_figuras --problemas mknapcb1 mknapcb4
    python -m analisis.generar_figuras --desde 1 --hasta 3
    python -m analisis.generar_figuras --indices 0 15 29 --dpi 300
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Configuración de tipografía estándar para publicaciones académicas (MDPI / IEEE / Elsevier)
# fonttype 42 asegura que el texto se incruste como fuentes vectoriales TrueType en el PDF
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans", "Helvetica", "Arial"]

# ═══════════════════════════════════════════════════════════════════════════
# Metadata de problemas y estrategias
# ═══════════════════════════════════════════════════════════════════════════

PROBLEM_METADATA: Dict[str, Dict[str, Any]] = {
    "mknapcb1": {"m": 5, "n": 100, "label": "mknapcb1 (5 × 100)"},
    "mknapcb2": {"m": 5, "n": 250, "label": "mknapcb2 (5 × 250)"},
    "mknapcb3": {"m": 5, "n": 500, "label": "mknapcb3 (5 × 500)"},
    "mknapcb4": {"m": 10, "n": 100, "label": "mknapcb4 (10 × 100)"},
    "mknapcb5": {"m": 10, "n": 250, "label": "mknapcb5 (10 × 250)"},
    "mknapcb6": {"m": 10, "n": 500, "label": "mknapcb6 (10 × 500)"},
    "mknapcb7": {"m": 30, "n": 100, "label": "mknapcb7 (30 × 100)"},
    "mknapcb8": {"m": 30, "n": 250, "label": "mknapcb8 (30 × 250)"},
    "mknapcb9": {"m": 30, "n": 500, "label": "mknapcb9 (30 × 500)"},
}

ALL_MHS = ["PSO", "GA", "GWO", "DE"]
DEFAULT_INDICES = [0, 15, 29]

# Paleta ColorBrewer adaptada para publicaciones científicas (alto contraste y daltonismo-amigable)
VERSION_CONFIG: List[Dict[str, str]] = [
    {
        "key": "vanilla_explotacion",
        "short_label": "V-Explot.",
        "full_label": "Vanilla-Explotación",
        "color": "#2b5c8f",     # Azul sobrio
        "edge_color": "#1a3959",
    },
    {
        "key": "vanilla_exploracion",
        "short_label": "V-Explor.",
        "full_label": "Vanilla-Exploración",
        "color": "#d95f02",     # Naranja cálido
        "edge_color": "#8c3d00",
    },
    {
        "key": "binary_simple",
        "short_label": "B-Simple",
        "full_label": "Binary-Simple (A3)",
        "color": "#1b9e77",     # Verde esmeralda / Teal
        "edge_color": "#11634b",
    },
    {
        "key": "binary_hysteresis",
        "short_label": "B-Complex",
        "full_label": "Binary-Complex (A4)",
        "color": "#7570b3",     # Púrpura / Violeta
        "edge_color": "#48456f",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# Carga de datos experimentales desde JSON
# ═══════════════════════════════════════════════════════════════════════════

def find_latest_run_dir(strategy_folder: str, inst_key: str, results_root: Path) -> Optional[Path]:
    """Localiza el directorio de resultados más reciente para una estrategia e instancia."""
    base_dir = results_root / strategy_folder / "todos" / inst_key
    if not base_dir.is_dir():
        return None

    run_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("comparacion_mhs_")]
    if not run_dirs:
        return None

    # Ordenar por timestamp para tomar la ejecución más reciente
    return max(run_dirs, key=lambda d: d.name)


def load_instance_data(
    prob_name: str,
    idx: int,
    results_root: Path,
) -> Tuple[Dict[str, Dict[str, List[float]]], Optional[float]]:
    """
    Carga los resultados de las 4 estrategias y las 4 MHs para una (instancia, índice).

    Retorna:
      - data[mh][strat_key] = lista de 31 fitness
      - optimo_conocido: float
    """
    inst_key = f"{prob_name}_{idx}"
    data: Dict[str, Dict[str, List[float]]] = {mh: {} for mh in ALL_MHS}
    optimo_conocido: Optional[float] = None

    for v_info in VERSION_CONFIG:
        strat_key = v_info["key"]
        run_dir = find_latest_run_dir(strat_key, inst_key, results_root)
        if not run_dir:
            continue

        for mh in ALL_MHS:
            json_file = run_dir / f"{mh}_{inst_key}.json"
            if not json_file.is_file():
                continue

            try:
                content = json.loads(json_file.read_text(encoding="utf-8"))
                fitness_list = content.get("fitness", [])
                data[mh][strat_key] = fitness_list
                if optimo_conocido is None and "optimo_conocido" in content:
                    optimo_conocido = float(content["optimo_conocido"])
            except Exception as exc:
                print(f"[WARN] Error leyendo {json_file}: {exc}")

    return data, optimo_conocido


# ═══════════════════════════════════════════════════════════════════════════
# Funciones de graficado
# ═══════════════════════════════════════════════════════════════════════════

def _apply_boxplot_style(
    bp: dict,
    colors: List[str],
    edge_colors: List[str],
) -> None:
    """Aplica formato visual estilizado y publication-ready a los boxplots."""
    for patch, color, edge in zip(bp["boxes"], colors, edge_colors):
        patch.set_facecolor(color)
        patch.set_edgecolor(edge)
        patch.set_linewidth(1.2)
        patch.set_alpha(0.85)

    for median in bp["medians"]:
        median.set_color("#111111")
        median.set_linewidth(2.0)

    for whisker in bp["whiskers"]:
        whisker.set_color("#333333")
        whisker.set_linewidth(1.1)
        whisker.set_linestyle("-")

    for cap in bp["caps"]:
        cap.set_color("#333333")
        cap.set_linewidth(1.1)

    for flier in bp["fliers"]:
        flier.set_marker("o")
        flier.set_markersize(3.5)
        flier.set_markerfacecolor("#666666")
        flier.set_markeredgecolor("none")
        flier.set_alpha(0.6)


def _safe_boxplot(ax, plot_data: list, tick_labels: list, widths: float = 0.6) -> dict:
    """Invoca ax.boxplot compatible con versiones antiguas (labels) y nuevas (tick_labels) de matplotlib."""
    try:
        return ax.boxplot(plot_data, tick_labels=tick_labels, patch_artist=True, widths=widths)
    except TypeError:
        return ax.boxplot(plot_data, labels=tick_labels, patch_artist=True, widths=widths)


def plot_problem_composite(
    prob_name: str,
    indices: List[int],
    data_by_idx: Dict[int, Dict[str, Dict[str, List[float]]]],
    optima_by_idx: Dict[int, Optional[float]],
    output_dir: Path,
    complex_label: str = "Binary-Complex",
    dpi: int = 300,
) -> Tuple[Path, Path]:
    """
    Genera la figura de panel consolidado para la subsección del problema en el paper.
    Matriz de 3 filas (instancias 0, 15, 29) x 4 columnas (PSO, GA, GWO, DE).
    """
    prob_meta = PROBLEM_METADATA.get(prob_name, {"m": "?", "n": "?", "label": prob_name})
    n_rows = len(indices)
    n_cols = len(ALL_MHS)

    fig, axes = plt.subplots(
        nrows=n_rows,
        ncols=n_cols,
        figsize=(15.5, 3.2 * n_rows + 0.8),
        sharey=False,
    )

    if n_rows == 1:
        axes = [axes]

    colors = [v["color"] for v in VERSION_CONFIG]
    edge_colors = [v["edge_color"] for v in VERSION_CONFIG]
    tick_labels = [
        complex_label if v["key"] == "binary_hysteresis" else v["short_label"]
        for v in VERSION_CONFIG
    ]

    for row_idx, inst_idx in enumerate(indices):
        inst_data = data_by_idx.get(inst_idx, {})
        optimo = optima_by_idx.get(inst_idx)

        for col_idx, mh in enumerate(ALL_MHS):
            ax = axes[row_idx][col_idx]
            mh_data = inst_data.get(mh, {})

            plot_data: List[List[float]] = []
            present_colors: List[str] = []
            present_edges: List[str] = []
            present_ticks: List[str] = []

            for v_idx, v_info in enumerate(VERSION_CONFIG):
                f_list = mh_data.get(v_info["key"], [])
                if f_list:
                    plot_data.append(f_list)
                    present_colors.append(colors[v_idx])
                    present_edges.append(edge_colors[v_idx])
                    present_ticks.append(tick_labels[v_idx])

            if plot_data:
                bp = _safe_boxplot(ax, plot_data, present_ticks, widths=0.6)
                _apply_boxplot_style(bp, present_colors, present_edges)

            # Línea horizontal del óptimo teórico
            if optimo and optimo > 0:
                ax.axhline(
                    optimo,
                    color="#27ae60",
                    linestyle="--",
                    linewidth=1.4,
                    alpha=0.9,
                    zorder=3,
                )

            # Estilo de ejes y cuadrícula
            ax.yaxis.grid(True, linestyle="--", linewidth=0.7, alpha=0.5, color="#c8c8c8")
            ax.set_axisbelow(True)
            ax.tick_params(axis="x", labelsize=8.5, rotation=15)
            ax.tick_params(axis="y", labelsize=8.5)

            # Título de columnas en la primera fila
            if row_idx == 0:
                ax.set_title(mh, fontsize=12, fontweight="bold", pad=8)

            # Título lateral de fila en la primera columna
            if col_idx == 0:
                opt_str = f"opt={optimo:.0f}" if optimo else ""
                ax.set_ylabel(
                    f"{prob_name}[{inst_idx}]\n({opt_str})\nFitness",
                    fontsize=9.5,
                    fontweight="bold",
                )

    # Título superior del panel de la subsección
    dim_str = f"m = {prob_meta['m']}, n = {prob_meta['n']}"
    fig.suptitle(
        f"Comparative Performance across Instances — {prob_name} ({dim_str})\n"
        f"31 Independent Runs per Metaheuristic Variant (W=200, percentiles 40/60)",
        fontsize=13,
        fontweight="bold",
        y=0.995,
    )

    # Leyenda unificada superior
    legend_patches = [
        mpatches.Patch(
            facecolor=v["color"],
            edgecolor=v["edge_color"],
            label=(complex_label if v["key"] == "binary_hysteresis" else v["full_label"]),
        )
        for v in VERSION_CONFIG
    ]
    legend_patches.append(
        matplotlib.lines.Line2D(
            [0], [0],
            color="#27ae60",
            linestyle="--",
            linewidth=1.5,
            label="Theoretical Optimum",
        )
    )

    fig.legend(
        handles=legend_patches,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.94),
        ncol=len(legend_patches),
        fontsize=9,
        frameon=True,
        facecolor="#fcfcfc",
        edgecolor="#d0d0d0",
    )

    fig.tight_layout(rect=[0, 0, 1, 0.92])

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{prob_name}_boxplot.pdf"
    png_path = output_dir / f"{prob_name}_boxplot.png"

    fig.savefig(pdf_path, format="pdf", dpi=dpi, bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return pdf_path, png_path


def plot_instance_individual(
    prob_name: str,
    idx: int,
    inst_data: Dict[str, Dict[str, List[float]]],
    optimo: Optional[float],
    output_dir: Path,
    complex_label: str = "Binary-Complex",
    dpi: int = 300,
) -> Tuple[Path, Path]:
    """
    Genera una figura individual para una instancia específica (1 fila x 4 columnas de MHs).
    Útil para subfiguras individuales en LaTeX.
    """
    prob_meta = PROBLEM_METADATA.get(prob_name, {"m": "?", "n": "?", "label": prob_name})
    n_cols = len(ALL_MHS)

    fig, axes = plt.subplots(
        nrows=1,
        ncols=n_cols,
        figsize=(14.5, 3.8),
        sharey=False,
    )

    colors = [v["color"] for v in VERSION_CONFIG]
    edge_colors = [v["edge_color"] for v in VERSION_CONFIG]
    tick_labels = [
        complex_label if v["key"] == "binary_hysteresis" else v["short_label"]
        for v in VERSION_CONFIG
    ]

    for col_idx, mh in enumerate(ALL_MHS):
        ax = axes[col_idx]
        mh_data = inst_data.get(mh, {})

        plot_data: List[List[float]] = []
        present_colors: List[str] = []
        present_edges: List[str] = []
        present_ticks: List[str] = []

        for v_idx, v_info in enumerate(VERSION_CONFIG):
            f_list = mh_data.get(v_info["key"], [])
            if f_list:
                plot_data.append(f_list)
                present_colors.append(colors[v_idx])
                present_edges.append(edge_colors[v_idx])
                present_ticks.append(tick_labels[v_idx])

        if plot_data:
            bp = _safe_boxplot(ax, plot_data, present_ticks, widths=0.6)
            _apply_boxplot_style(bp, present_colors, present_edges)

        if optimo and optimo > 0:
            ax.axhline(
                optimo,
                color="#27ae60",
                linestyle="--",
                linewidth=1.4,
                alpha=0.9,
            )

        ax.yaxis.grid(True, linestyle="--", linewidth=0.7, alpha=0.5, color="#c8c8c8")
        ax.set_axisbelow(True)
        ax.set_title(mh, fontsize=11, fontweight="bold")
        ax.tick_params(axis="x", labelsize=8.5, rotation=15)
        ax.tick_params(axis="y", labelsize=8.5)

        if col_idx == 0:
            ax.set_ylabel("Fitness", fontsize=10, fontweight="bold")

    dim_str = f"m = {prob_meta['m']}, n = {prob_meta['n']}"
    opt_str = f" (Optimum: {optimo:.0f})" if optimo else ""
    fig.suptitle(
        f"{prob_name}[{idx}] — {dim_str}{opt_str}",
        fontsize=12,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()

    indiv_dir = output_dir / "individuales"
    indiv_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = indiv_dir / f"{prob_name}_inst{idx}_boxplot.pdf"
    png_path = indiv_dir / f"{prob_name}_inst{idx}_boxplot.png"

    fig.savefig(pdf_path, format="pdf", dpi=dpi, bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return pdf_path, png_path


# ═══════════════════════════════════════════════════════════════════════════
# CLI y orquestación
# ═══════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generador de Boxplots para el Paper (Chu & Beasley MKP)"
    )
    p.add_argument(
        "--problemas",
        nargs="+",
        default=None,
        help="Nombres de problemas específicos a procesar (ej: mknapcb1 mknapcb4)",
    )
    p.add_argument(
        "--desde",
        type=int,
        default=1,
        help="Número inicial de problema (1 a 9, default: 1)",
    )
    p.add_argument(
        "--hasta",
        type=int,
        default=9,
        help="Número final de problema (1 a 9, default: 9)",
    )
    p.add_argument(
        "--indices",
        nargs="+",
        type=int,
        default=DEFAULT_INDICES,
        help=f"Índices de instancias por problema (default: {DEFAULT_INDICES})",
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
        default=Path("results/figuras"),
        help="Directorio de destino de las figuras (default: results/figuras)",
    )
    p.add_argument(
        "--complex-label",
        type=str,
        default="Binary-Complex",
        help="Etiqueta para la estrategia A4 (default: Binary-Complex)",
    )
    p.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolución DPI para exportación PNG (default: 300)",
    )
    p.add_argument(
        "--skip-individuales",
        action="store_true",
        help="Omitir la generación de figuras individuales por instancia",
    )
    return p.parse_args()


def resolve_problem_list(args: argparse.Namespace) -> List[str]:
    """Determina la lista de problemas a procesar."""
    if args.problemas:
        return args.problemas
    desde = max(1, min(args.desde, 9))
    hasta = max(desde, min(args.hasta, 9))
    return [f"mknapcb{i}" for i in range(desde, hasta + 1)]


def main() -> int:
    args = parse_args()
    problemas = resolve_problem_list(args)
    indices = sorted(args.indices)
    results_root = args.results_dir
    output_dir = args.out_dir

    print("=" * 75)
    print("  GENERADOR DE BOXPLOTS PARA EL PAPER — REVISIÓN ROUND 1 (MKP)")
    print("=" * 75)
    print(f"  Problemas:        {', '.join(problemas)} ({len(problemas)})")
    print(f"  Índices:          {indices}")
    print(f"  Estrategias:      {[v['full_label'] for v in VERSION_CONFIG]}")
    print(f"  Metaheurísticas:  {ALL_MHS}")
    print(f"  Directorio salida:{output_dir}")
    print(f"  Resolución:       {args.dpi} DPI (PDF vectorial + PNG)")
    print("=" * 75)
    print()

    generadas_panel: List[Tuple[str, Path, Path]] = []
    generadas_indiv: List[Tuple[str, int, Path]] = []

    for prob_name in problemas:
        print(f"-> Procesando {prob_name} (índices {indices})...")
        data_by_idx: Dict[int, Dict[str, Dict[str, List[float]]]] = {}
        optima_by_idx: Dict[int, Optional[float]] = {}

        for idx in indices:
            inst_data, optimo = load_instance_data(prob_name, idx, results_root)
            data_by_idx[idx] = inst_data
            optima_by_idx[idx] = optimo

            # Generar figura individual si está habilitado
            if not args.skip_individuales:
                pdf_ind, _ = plot_instance_individual(
                    prob_name=prob_name,
                    idx=idx,
                    inst_data=inst_data,
                    optimo=optimo,
                    output_dir=output_dir,
                    complex_label=args.complex_label,
                    dpi=args.dpi,
                )
                generadas_indiv.append((prob_name, idx, pdf_ind))

        # Generar figura de panel consolidado de la subsección
        pdf_panel, png_panel = plot_problem_composite(
            prob_name=prob_name,
            indices=indices,
            data_by_idx=data_by_idx,
            optima_by_idx=optima_by_idx,
            output_dir=output_dir,
            complex_label=args.complex_label,
            dpi=args.dpi,
        )
        generadas_panel.append((prob_name, pdf_panel, png_panel))
        print(f"   [OK] Panel consolidado: {pdf_panel.name} y {png_panel.name}")

    print()
    print("=" * 75)
    print("  RESUMEN DE FIGURAS GENERADAS EXITOSAMENTE")
    print("=" * 75)
    print(f"  Figuras consolidadas de subsección ({len(generadas_panel)} problemas):")
    for prob_name, pdf_p, _ in generadas_panel:
        print(f"    - {prob_name:<10}: {pdf_p}")

    if not args.skip_individuales:
        print(f"\n  Figuras individuales ({len(generadas_indiv)} instancias):")
        print(f"    - Guardadas en: {output_dir / 'individuales'}/")
        print(f"    - Total archivos: {len(generadas_indiv)} PDFs + {len(generadas_indiv)} PNGs")

    print("=" * 75)
    print("Listo para incluir en las subsecciones del manuscrito LaTeX.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
