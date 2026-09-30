"""
analisis/generar_figura_activaciones.py — Visualización de Activaciones DTW (Paper MKP)
========================================================================================
Genera figuras científicas en alta resolución (PDF vectorial + PNG 300 DPI) para
analizar el promedio de activaciones del controlador DTW (s_t = 1, conmutaciones
a exploración) a lo largo de los 9 problemas (mknapcb1..9) y sus respectivas instancias
(0, 15, 29) para las 4 metaheurísticas (BPSO, GA, BGWO, BDE).

Reproduce fielmente y extiende la figura histórica de `results_old/fig_dtw_activations_grid.pdf`:
  - Panel 2x2 por metaheurística (BPSO, GA, BGWO, BDE).
  - Comparativa de barras agrupadas: Binary-Simple vs Binary-Complex.
  - Barras de error (desviación estándar sobre las corridas independientes).
  - Opciones de agregación:
      1. Grid consolidado por problema (promediando las instancias 0, 15, 29).
      2. Grid por índice específico de instancia (ej. instancia 0, 15, 29).
      3. Grid detallado con todas las 27 instancias individuales.
      4. Paneles individuales por problema (desglose de instancias 0, 15, 29).
  - Exportación complementaria de tablas en formato LaTeX y CSV.

Uso:
    python -m analisis.generar_figura_activaciones
    python -m analisis.generar_figura_activaciones --results-dir results_old/results-200-40-60
    python -m analisis.generar_figura_activaciones --indice 0
    python -m analisis.generar_figura_activaciones --dpi 300 --out-dir results/figuras/activaciones
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Configuración de tipografía estándar para publicaciones académicas (IEEE / MDPI / Elsevier)
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans", "Helvetica", "Arial"]

# ═══════════════════════════════════════════════════════════════════════════
# Metadata de problemas, metaheurísticas y estrategias
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
MH_DISPLAY_NAMES = {
    "PSO": "BPSO",
    "GA": "GA",
    "GWO": "BGWO",
    "DE": "BDE",
}

DEFAULT_INDICES = [0, 15, 29]

STRATEGY_CONFIG = {
    "binary_simple": {
        "key": "binary_simple",
        "default_label": "Binary-Simple",
        "color": "#f0a34b",       # Ámbar / Naranja cálido (idéntico al paper de referencia)
        "edge_color": "#8c5310",  # Borde contrastante
    },
    "binary_hysteresis": {
        "key": "binary_hysteresis",
        "default_label": "Binary-Complex",
        "color": "#38b479",       # Verde esmeralda / Teal (idéntico al paper de referencia)
        "edge_color": "#175d3a",  # Borde contrastante
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Carga de datos experimentales desde archivos JSON
# ═══════════════════════════════════════════════════════════════════════════

def find_latest_run_dir(strategy_folder: str, inst_key: str, results_root: Path) -> Optional[Path]:
    """Localiza el directorio de resultados más reciente para una estrategia e instancia."""
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


def load_instance_activations(
    prob_name: str,
    idx: int,
    results_root: Path,
) -> Dict[str, Dict[str, List[int]]]:
    """
    Carga los vectores de 'fire_counts' (número de activaciones por corrida)
    para una instancia específica (ej. mknapcb1_0).

    Retorna:
        data[strat_key][mh] = List[int] (típicamente 31 valores de fire_counts)
    """
    inst_key = f"{prob_name}_{idx}"
    inst_data: Dict[str, Dict[str, List[int]]] = {
        strat_key: {} for strat_key in STRATEGY_CONFIG
    }

    for strat_key in STRATEGY_CONFIG:
        run_dir = find_latest_run_dir(strat_key, inst_key, results_root)
        if not run_dir:
            continue

        for mh in ALL_MHS:
            json_file = run_dir / f"{mh}_{inst_key}.json"
            if not json_file.is_file():
                continue

            try:
                content = json.loads(json_file.read_text(encoding="utf-8"))
                fire_counts = content.get("fire_counts", [])
                if fire_counts:
                    inst_data[strat_key][mh] = [int(x) for x in fire_counts]
            except Exception as exc:
                print(f"[WARN] Error leyendo {json_file}: {exc}")

    return inst_data


def load_all_activation_data(
    problems: List[str],
    indices: List[int],
    results_root: Path,
) -> Dict[str, Dict[int, Dict[str, Dict[str, List[int]]]]]:
    """
    Estructura jerárquica de datos:
        all_data[prob_name][idx][strat_key][mh] = List[int]
    """
    all_data: Dict[str, Dict[int, Dict[str, Dict[str, List[int]]]]] = {}

    for prob in problems:
        all_data[prob] = {}
        for idx in indices:
            inst_data = load_instance_activations(prob, idx, results_root)
            all_data[prob][idx] = inst_data

    return all_data


# ═══════════════════════════════════════════════════════════════════════════
# Cálculos Estadísticos
# ═══════════════════════════════════════════════════════════════════════════

def compute_stats(values: List[int]) -> Tuple[float, float, int]:
    """Retorna (mean, std_sample, n). Si n < 2, std es 0.0."""
    if not values:
        return 0.0, 0.0, 0
    arr = np.array(values, dtype=float)
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    return mean_val, std_val, len(arr)


def get_problem_pooled_stats(
    all_data: Dict[str, Dict[int, Dict[str, Dict[str, List[int]]]]],
    prob_name: str,
    strat_key: str,
    mh: str,
    indices: List[int],
) -> Tuple[float, float, int]:
    """Agrupa todas las corridas de las instancias seleccionadas de un problema."""
    pooled_runs: List[int] = []
    prob_dict = all_data.get(prob_name, {})
    for idx in indices:
        runs = prob_dict.get(idx, {}).get(strat_key, {}).get(mh, [])
        pooled_runs.extend(runs)
    return compute_stats(pooled_runs)


# ═══════════════════════════════════════════════════════════════════════════
# Funciones de Graficado
# ═══════════════════════════════════════════════════════════════════════════

def plot_dtw_activations_grid(
    all_data: Dict[str, Dict[int, Dict[str, Dict[str, List[int]]]]],
    problems: List[str],
    indices: List[int],
    output_dir: Path,
    title_suffix: str = "",
    file_prefix: str = "fig_dtw_activations_grid",
    simple_label: str = "Binary-Simple",
    complex_label: str = "Binary-Complex",
    dpi: int = 300,
    fixed_ylim: Optional[float] = None,
) -> Tuple[Path, Path]:
    """
    Genera el panel 2x2 (BPSO, GA, BGWO, BDE) idéntico a `results_old/fig_dtw_activations_grid.pdf`.
    Eje X: mknapcb1..mknapcb9.
    Barras: Binary-Simple (naranja) vs Binary-Complex (verde).
    Barras de error: Desviación estándar muestral (std).
    """
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(13.5, 7.8), sharex=True, sharey=False)
    axes_flat = [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]

    bar_width = 0.36
    x_indices = np.arange(len(problems))

    # Colores y etiquetas
    color_sim = STRATEGY_CONFIG["binary_simple"]["color"]
    edge_sim = STRATEGY_CONFIG["binary_simple"]["edge_color"]
    color_hys = STRATEGY_CONFIG["binary_hysteresis"]["color"]
    edge_hys = STRATEGY_CONFIG["binary_hysteresis"]["edge_color"]

    # Calcular límite Y máximo dinámico si no es fijo
    global_max_y = 0.0

    for mh_idx, mh in enumerate(ALL_MHS):
        ax = axes_flat[mh_idx]
        mh_label = MH_DISPLAY_NAMES.get(mh, mh)

        means_sim: List[float] = []
        stds_sim: List[float] = []
        means_hys: List[float] = []
        stds_hys: List[float] = []

        for prob in problems:
            m_sim, s_sim, _ = get_problem_pooled_stats(all_data, prob, "binary_simple", mh, indices)
            m_hys, s_hys, _ = get_problem_pooled_stats(all_data, prob, "binary_hysteresis", mh, indices)

            means_sim.append(m_sim)
            stds_sim.append(s_sim)
            means_hys.append(m_hys)
            stds_hys.append(s_hys)

            top_sim = m_sim + s_sim
            top_hys = m_hys + s_hys
            if top_sim > global_max_y:
                global_max_y = top_sim
            if top_hys > global_max_y:
                global_max_y = top_hys

        # Graficar barras de Binary-Simple
        ax.bar(
            x_indices - bar_width / 2,
            means_sim,
            width=bar_width,
            yerr=stds_sim,
            capsize=3.5,
            error_kw={"elinewidth": 1.1, "capthick": 1.1, "ecolor": "#222222"},
            color=color_sim,
            edgecolor=edge_sim,
            linewidth=1.0,
            alpha=0.88,
            label=simple_label,
            zorder=3,
        )

        # Graficar barras de Binary-Complex
        ax.bar(
            x_indices + bar_width / 2,
            means_hys,
            width=bar_width,
            yerr=stds_hys,
            capsize=3.5,
            error_kw={"elinewidth": 1.1, "capthick": 1.1, "ecolor": "#222222"},
            color=color_hys,
            edgecolor=edge_hys,
            linewidth=1.0,
            alpha=0.88,
            label=complex_label,
            zorder=3,
        )

        # Configuración estética del subplot
        ax.set_title(mh_label, fontsize=12.5, fontweight="bold", pad=8)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.7, alpha=0.55, color="#c8c8c8", zorder=0)
        ax.set_axisbelow(True)

        # Título de eje Y solo en la columna izquierda
        if mh_idx in (0, 2):
            ax.set_ylabel(r"Mean Activations ($s_t = 1$)", fontsize=11, fontweight="normal")

        # Ticks del eje X en todos los subplots (idéntico a la figura de referencia)
        ax.set_xticks(x_indices)
        ax.set_xticklabels(problems, rotation=35, ha="right", fontsize=9.5)
        ax.tick_params(axis="x", labelbottom=True)
        ax.tick_params(axis="y", labelsize=9.5)

    # Establecer límite uniforme del eje Y en todos los subplots
    y_top = fixed_ylim if fixed_ylim is not None else (13.0 if global_max_y <= 12.6 else np.ceil(global_max_y * 1.08))
    for ax in axes_flat:
        ax.set_ylim(bottom=0.0, top=y_top)

    # Leyenda unificada centrada en la parte superior
    legend_handles = [
        mpatches.Patch(facecolor=color_sim, edgecolor=edge_sim, label=simple_label, alpha=0.88),
        mpatches.Patch(facecolor=color_hys, edgecolor=edge_hys, label=complex_label, alpha=0.88),
    ]

    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.99),
        ncol=2,
        fontsize=11,
        frameon=True,
        facecolor="#fcfcfc",
        edgecolor="#d5d5d5",
        framealpha=0.95,
    )

    fig.tight_layout(rect=[0.02, 0.02, 0.98, 0.94])

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{file_prefix}.pdf"
    png_path = output_dir / f"{file_prefix}.png"

    fig.savefig(pdf_path, format="pdf", dpi=dpi, bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return pdf_path, png_path


def plot_dtw_activations_by_instance(
    all_data: Dict[str, Dict[int, Dict[str, Dict[str, List[int]]]]],
    problems: List[str],
    indices: List[int],
    output_dir: Path,
    file_prefix: str = "fig_dtw_activations_all_instances",
    simple_label: str = "Binary-Simple",
    complex_label: str = "Binary-Complex",
    dpi: int = 300,
) -> Tuple[Path, Path]:
    """
    Genera un panel 2x2 mostrando individualmente cada una de las 27 instancias
    (mknapcb1_0, mknapcb1_15, mknapcb1_29, ..., mknapcb9_29).
    Incluye líneas verticales tenues para separar visualmente cada problema.
    """
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(18.0, 9.0), sharex=True, sharey=False)
    axes_flat = [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]

    # Lista ordenada de claves de instancia
    inst_keys: List[Tuple[str, int, str]] = []
    for prob in problems:
        for idx in indices:
            label_short = f"{prob.replace('mknapcb', 'cb')}[{idx}]"
            inst_keys.append((prob, idx, label_short))

    n_items = len(inst_keys)
    x_positions = np.arange(n_items)
    bar_width = 0.38

    color_sim = STRATEGY_CONFIG["binary_simple"]["color"]
    edge_sim = STRATEGY_CONFIG["binary_simple"]["edge_color"]
    color_hys = STRATEGY_CONFIG["binary_hysteresis"]["color"]
    edge_hys = STRATEGY_CONFIG["binary_hysteresis"]["edge_color"]

    global_max_y = 0.0

    for mh_idx, mh in enumerate(ALL_MHS):
        ax = axes_flat[mh_idx]
        mh_label = MH_DISPLAY_NAMES.get(mh, mh)

        means_sim: List[float] = []
        stds_sim: List[float] = []
        means_hys: List[float] = []
        stds_hys: List[float] = []

        for prob, idx, _ in inst_keys:
            runs_sim = all_data.get(prob, {}).get(idx, {}).get("binary_simple", {}).get(mh, [])
            runs_hys = all_data.get(prob, {}).get(idx, {}).get("binary_hysteresis", {}).get(mh, [])

            m_sim, s_sim, _ = compute_stats(runs_sim)
            m_hys, s_hys, _ = compute_stats(runs_hys)

            means_sim.append(m_sim)
            stds_sim.append(s_sim)
            means_hys.append(m_hys)
            stds_hys.append(s_hys)

            top_val = max(m_sim + s_sim, m_hys + s_hys)
            if top_val > global_max_y:
                global_max_y = top_val

        ax.bar(
            x_positions - bar_width / 2,
            means_sim,
            width=bar_width,
            yerr=stds_sim,
            capsize=2.5,
            error_kw={"elinewidth": 0.9, "capthick": 0.9, "ecolor": "#222222"},
            color=color_sim,
            edgecolor=edge_sim,
            linewidth=0.8,
            alpha=0.88,
            zorder=3,
        )

        ax.bar(
            x_positions + bar_width / 2,
            means_hys,
            width=bar_width,
            yerr=stds_hys,
            capsize=2.5,
            error_kw={"elinewidth": 0.9, "capthick": 0.9, "ecolor": "#222222"},
            color=color_hys,
            edgecolor=edge_hys,
            linewidth=0.8,
            alpha=0.88,
            zorder=3,
        )

        # Divisores verticales para separar problemas
        for sep_i in range(len(indices), n_items, len(indices)):
            ax.axvline(sep_i - 0.5, color="#bbbbbb", linestyle=":", linewidth=1.0, zorder=1)

        ax.set_title(mh_label, fontsize=12, fontweight="bold", pad=8)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.7, alpha=0.5, color="#c8c8c8", zorder=0)
        ax.set_axisbelow(True)

        if mh_idx in (0, 2):
            ax.set_ylabel(r"Mean Activations ($s_t = 1$)", fontsize=10.5)

        ax.set_xticks(x_positions)
        ax.set_xticklabels([k[2] for k in inst_keys], rotation=60, ha="right", fontsize=8.0)
        ax.tick_params(axis="y", labelsize=8.5)

    y_top = max(13.0, np.ceil(global_max_y * 1.08))
    for ax in axes_flat:
        ax.set_ylim(bottom=0.0, top=y_top)

    legend_handles = [
        mpatches.Patch(facecolor=color_sim, edgecolor=edge_sim, label=simple_label, alpha=0.88),
        mpatches.Patch(facecolor=color_hys, edgecolor=edge_hys, label=complex_label, alpha=0.88),
    ]

    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=2,
        fontsize=11,
        frameon=True,
        facecolor="#fcfcfc",
        edgecolor="#d5d5d5",
    )

    fig.tight_layout(rect=[0.01, 0.02, 0.99, 0.94])

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{file_prefix}.pdf"
    png_path = output_dir / f"{file_prefix}.png"

    fig.savefig(pdf_path, format="pdf", dpi=dpi, bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return pdf_path, png_path


def plot_problem_breakdown(
    all_data: Dict[str, Dict[int, Dict[str, Dict[str, List[int]]]]],
    prob_name: str,
    indices: List[int],
    output_dir: Path,
    simple_label: str = "Binary-Simple",
    complex_label: str = "Binary-Complex",
    dpi: int = 300,
) -> Tuple[Path, Path]:
    """
    Genera una figura individual para un problema específico en formato 2x2
    (2 arriba: BPSO, GA; 2 abajo: BGWO, BDE), mostrando el comportamiento
    de las instancias (ej. 0, 15, 29).
    """
    prob_meta = PROBLEM_METADATA.get(prob_name, {"m": "?", "n": "?", "label": prob_name})
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(8.8, 6.8), sharex=True, sharey=True)
    axes_flat = [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]

    bar_width = 0.35
    x_positions = np.arange(len(indices))
    labels = [f"Inst. {idx}" for idx in indices]

    color_sim = STRATEGY_CONFIG["binary_simple"]["color"]
    edge_sim = STRATEGY_CONFIG["binary_simple"]["edge_color"]
    color_hys = STRATEGY_CONFIG["binary_hysteresis"]["color"]
    edge_hys = STRATEGY_CONFIG["binary_hysteresis"]["edge_color"]

    max_y = 0.0

    for mh_idx, mh in enumerate(ALL_MHS):
        ax = axes_flat[mh_idx]
        mh_label = MH_DISPLAY_NAMES.get(mh, mh)

        means_sim: List[float] = []
        stds_sim: List[float] = []
        means_hys: List[float] = []
        stds_hys: List[float] = []

        for idx in indices:
            runs_sim = all_data.get(prob_name, {}).get(idx, {}).get("binary_simple", {}).get(mh, [])
            runs_hys = all_data.get(prob_name, {}).get(idx, {}).get("binary_hysteresis", {}).get(mh, [])

            m_sim, s_sim, _ = compute_stats(runs_sim)
            m_hys, s_hys, _ = compute_stats(runs_hys)

            means_sim.append(m_sim)
            stds_sim.append(s_sim)
            means_hys.append(m_hys)
            stds_hys.append(s_hys)

            top_val = max(m_sim + s_sim, m_hys + s_hys)
            if top_val > max_y:
                max_y = top_val

        ax.bar(
            x_positions - bar_width / 2,
            means_sim,
            width=bar_width,
            yerr=stds_sim,
            capsize=3.0,
            error_kw={"elinewidth": 1.0, "capthick": 1.0, "ecolor": "#222222"},
            color=color_sim,
            edgecolor=edge_sim,
            linewidth=1.0,
            alpha=0.88,
            label=simple_label,
            zorder=3,
        )

        ax.bar(
            x_positions + bar_width / 2,
            means_hys,
            width=bar_width,
            yerr=stds_hys,
            capsize=3.0,
            error_kw={"elinewidth": 1.0, "capthick": 1.0, "ecolor": "#222222"},
            color=color_hys,
            edgecolor=edge_hys,
            linewidth=1.0,
            alpha=0.88,
            label=complex_label,
            zorder=3,
        )

        ax.set_title(mh_label, fontsize=11.5, fontweight="bold", pad=6)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.7, alpha=0.5, color="#c8c8c8", zorder=0)
        ax.set_axisbelow(True)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(labels, fontsize=9.5)
        ax.tick_params(axis="x", labelbottom=True)
        ax.tick_params(axis="y", labelsize=9.0)

        # Solo columna izquierda lleva etiqueta en el eje Y
        if mh_idx in (0, 2):
            ax.set_ylabel(r"Mean Activations ($s_t = 1$)", fontsize=10, fontweight="bold")

    y_top = max(10.0, np.ceil(max_y * 1.1))
    for ax in axes_flat:
        ax.set_ylim(bottom=0.0, top=y_top)

    dim_str = f"m = {prob_meta['m']}, n = {prob_meta['n']}"
    fig.suptitle(
        f"DTW Controller Activations across Instances — {prob_name} ({dim_str})\n"
        f"Comparison between {simple_label} and {complex_label} (31 runs per instance)",
        fontsize=11.5,
        fontweight="bold",
        y=0.985,
    )

    legend_patches = [
        mpatches.Patch(facecolor=color_sim, edgecolor=edge_sim, label=simple_label, alpha=0.88),
        mpatches.Patch(facecolor=color_hys, edgecolor=edge_hys, label=complex_label, alpha=0.88),
    ]
    fig.legend(
        handles=legend_patches,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.925),
        ncol=2,
        fontsize=9.5,
        frameon=True,
        facecolor="#fcfcfc",
        edgecolor="#d5d5d5",
    )

    fig.tight_layout(rect=[0.02, 0.02, 0.98, 0.89])

    indiv_dir = output_dir / "individuales"
    indiv_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = indiv_dir / f"{prob_name}_activations.pdf"
    png_path = indiv_dir / f"{prob_name}_activations.png"

    fig.savefig(pdf_path, format="pdf", dpi=dpi, bbox_inches="tight")
    fig.savefig(png_path, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    return pdf_path, png_path


# ═══════════════════════════════════════════════════════════════════════════
# Exportación de Tablas (LaTeX + CSV)
# ═══════════════════════════════════════════════════════════════════════════

def export_activations_tables(
    all_data: Dict[str, Dict[int, Dict[str, Dict[str, List[int]]]]],
    problems: List[str],
    indices: List[int],
    output_dir: Path,
) -> Tuple[Path, Path]:
    """Genera tablas cuantitativas detalladas de activaciones en CSV y LaTeX."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "tabla_activaciones_dtw.csv"
    tex_path = output_dir / "tabla_activaciones_dtw.tex"

    rows: List[Dict[str, Any]] = []

    for prob in problems:
        prob_meta = PROBLEM_METADATA.get(prob, {"m": "-", "n": "-"})
        dim_str = f"{prob_meta['m']}×{prob_meta['n']}"

        for idx in indices:
            for mh in ALL_MHS:
                runs_sim = all_data.get(prob, {}).get(idx, {}).get("binary_simple", {}).get(mh, [])
                runs_hys = all_data.get(prob, {}).get(idx, {}).get("binary_hysteresis", {}).get(mh, [])

                m_sim, s_sim, n_sim = compute_stats(runs_sim)
                m_hys, s_hys, n_hys = compute_stats(runs_hys)

                diff = m_hys - m_sim
                diff_pct = (diff / m_sim * 100.0) if m_sim > 0 else 0.0

                rows.append({
                    "problem": prob,
                    "dimension": dim_str,
                    "index": idx,
                    "mh": MH_DISPLAY_NAMES.get(mh, mh),
                    "mean_simple": m_sim,
                    "std_simple": s_sim,
                    "mean_complex": m_hys,
                    "std_complex": s_hys,
                    "diff": diff,
                    "diff_pct": diff_pct,
                })

    # Guardar CSV
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Problem", "Dim (m×n)", "Instance_Idx", "Algorithm",
            "Simple_Mean", "Simple_Std",
            "Complex_Mean", "Complex_Std",
            "Diff_Mean", "Diff_Pct"
        ])
        for r in rows:
            writer.writerow([
                r["problem"], r["dimension"], r["index"], r["mh"],
                f"{r['mean_simple']:.2f}", f"{r['std_simple']:.2f}",
                f"{r['mean_complex']:.2f}", f"{r['std_complex']:.2f}",
                f"{r['diff']:+.2f}", f"{r['diff_pct']:+.1f}%"
            ])

    # Guardar LaTeX
    lines: List[str] = [
        r"\begin{table*}[htbp]",
        r"\centering",
        r"\small",
        r"\caption{Comparison of DTW Exploration Activations ($s_t = 1$) between Binary-Simple and Binary-Complex across Problems and Instances (31 Independent Runs).}",
        r"\label{tab:dtw_activations}",
        r"\begin{tabular}{llrcccc}",
        r"\toprule",
        r"\textbf{Problem} & \textbf{Dim ($m \times n$)} & \textbf{Inst.} & \textbf{Algorithm} & \textbf{Binary-Simple} & \textbf{Binary-Complex} & \textbf{$\Delta$ (\%)} \\",
        r" & & & & (Mean $\pm$ Std) & (Mean $\pm$ Std) & \\",
        r"\midrule",
    ]

    current_prob = ""
    for r in rows:
        prob_str = r["problem"] if r["problem"] != current_prob else ""
        dim_str = r["dimension"] if r["problem"] != current_prob else ""
        current_prob = r["problem"]

        sim_str = f"{r['mean_simple']:.2f} $\\pm$ {r['std_simple']:.2f}"
        hys_str = f"{r['mean_complex']:.2f} $\\pm$ {r['std_complex']:.2f}"
        diff_str = f"{r['diff_pct']:+.1f}\\%"

        lines.append(
            f"{prob_str:<12} & {dim_str:<8} & {r['index']} & {r['mh']:<5} & {sim_str:<18} & {hys_str:<18} & {diff_str} \\\\"
        )

    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table*}",
    ])

    tex_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, tex_path


# ═══════════════════════════════════════════════════════════════════════════
# CLI y Orquestación Principal
# ═══════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generador de Figuras de Activaciones DTW para el Paper (MKP)"
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
        default=Path("results/figuras/activaciones"),
        help="Directorio destino para las figuras (default: results/figuras/activaciones)",
    )
    p.add_argument(
        "--problemas",
        nargs="+",
        default=None,
        help="Problemas a procesar (ej: mknapcb1 mknapcb2 ... default: mknapcb1..9)",
    )
    p.add_argument(
        "--desde",
        type=int,
        default=1,
        help="Número de problema inicial (default: 1)",
    )
    p.add_argument(
        "--hasta",
        type=int,
        default=9,
        help="Número de problema final (default: 9)",
    )
    p.add_argument(
        "--indices",
        nargs="+",
        type=int,
        default=DEFAULT_INDICES,
        help=f"Índices de instancias a incluir (default: {DEFAULT_INDICES})",
    )
    p.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolución DPI para exportación PNG (default: 300)",
    )
    p.add_argument(
        "--simple-label",
        type=str,
        default="Binary-Simple",
        help="Etiqueta para Binary-Simple (default: Binary-Simple)",
    )
    p.add_argument(
        "--complex-label",
        type=str,
        default="Binary-Complex",
        help="Etiqueta para Binary-Complex (default: Binary-Complex)",
    )
    p.add_argument(
        "--skip-individuales",
        action="store_true",
        help="Omitir la generación de paneles individuales por problema",
    )
    p.add_argument(
        "--skip-all-instances",
        action="store_true",
        help="Omitir la figura con el desglose de todas las instancias",
    )
    p.add_argument(
        "--skip-tables",
        action="store_true",
        help="Omitir exportación de tablas LaTeX y CSV",
    )
    return p.parse_args()


def resolve_problem_list(args: argparse.Namespace) -> List[str]:
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

    print("=" * 78)
    print("  GENERADOR DE FIGURAS DE ACTIVACIONES DTW — REPRODUCCIÓN & EXPANSIÓN (MKP)")
    print("=" * 78)
    print(f"  Directorio resultados: {results_root}")
    print(f"  Directorio salida:     {output_dir}")
    print(f"  Problemas a analizar:  {', '.join(problemas)} ({len(problemas)})")
    print(f"  Índices de instancias: {indices}")
    print(f"  Estrategias evaluadas: {args.simple_label} vs {args.complex_label}")
    print(f"  Metaheurísticas:       {list(MH_DISPLAY_NAMES.values())}")
    print(f"  Resolución:            {args.dpi} DPI (PDF vectorial + PNG)")
    print("=" * 78)
    print()

    # 1. Cargar datos
    print("-> Cargando datos de 'fire_counts' desde los resultados JSON...")
    all_data = load_all_activation_data(problemas, indices, results_root)

    total_series = 0
    for prob in problemas:
        for idx in indices:
            for strat in STRATEGY_CONFIG:
                for mh in ALL_MHS:
                    if all_data[prob][idx][strat].get(mh):
                        total_series += 1
    print(f"   [OK] Total de series experimentales cargadas: {total_series}")
    if total_series == 0:
        print(f"[ERROR] No se encontraron datos de activaciones en '{results_root}'. Verifique la ruta.")
        return 1

    # 2. Generar Figura Principal de Grid Consolidado (como en results_old/fig_dtw_activations_grid.pdf)
    print("\n-> Generando Panel Principal 2x2 (Problemas Agregados — réplica results_old)...")
    pdf_grid, png_grid = plot_dtw_activations_grid(
        all_data=all_data,
        problems=problemas,
        indices=indices,
        output_dir=output_dir,
        file_prefix="fig_dtw_activations_grid",
        simple_label=args.simple_label,
        complex_label=args.complex_label,
        dpi=args.dpi,
    )
    print(f"   [OK] Figura consolidada guardada en:")
    print(f"        PDF: {pdf_grid}")
    print(f"        PNG: {png_grid}")

    # 3. Generar Figuras de Grid para cada índice específico de instancia (0, 15, 29)
    if len(indices) > 1:
        print("\n-> Generando Paneles 2x2 específicos por índice de instancia...")
        for target_idx in indices:
            pdf_inst, _ = plot_dtw_activations_grid(
                all_data=all_data,
                problems=problemas,
                indices=[target_idx],
                output_dir=output_dir,
                file_prefix=f"fig_dtw_activations_inst{target_idx}",
                simple_label=args.simple_label,
                complex_label=args.complex_label,
                dpi=args.dpi,
            )
            print(f"   [OK] Panel para índice {target_idx}: {pdf_inst.name}")

    # 4. Generar Figura Completa con todas las 27 instancias
    if not args.skip_all_instances:
        print("\n-> Generando Panel 2x2 con desglose de todas las instancias individuales...")
        pdf_all, png_all = plot_dtw_activations_by_instance(
            all_data=all_data,
            problems=problemas,
            indices=indices,
            output_dir=output_dir,
            file_prefix="fig_dtw_activations_all_instances",
            simple_label=args.simple_label,
            complex_label=args.complex_label,
            dpi=args.dpi,
        )
        print(f"   [OK] Figura de todas las instancias: {pdf_all.name}")

    # 5. Generar Paneles Individuales por Problema (subfiguras por instancia)
    if not args.skip_individuales:
        print("\n-> Generando figuras individuales por problema (desglose instancias)...")
        indiv_count = 0
        for prob in problemas:
            pdf_prob, _ = plot_problem_breakdown(
                all_data=all_data,
                prob_name=prob,
                indices=indices,
                output_dir=output_dir,
                simple_label=args.simple_label,
                complex_label=args.complex_label,
                dpi=args.dpi,
            )
            indiv_count += 1
        print(f"   [OK] Generadas {indiv_count} figuras en: {output_dir / 'individuales'}/")

    # 6. Exportar Tablas (CSV + LaTeX)
    if not args.skip_tables:
        print("\n-> Exportando tablas cuantitativas...")
        csv_p, tex_p = export_activations_tables(all_data, problemas, indices, output_dir)
        print(f"   [OK] Tabla CSV:   {csv_p}")
        print(f"   [OK] Tabla LaTeX: {tex_p}")

    print("\n" + "=" * 78)
    print("  PROCESAMIENTO DE ACTIVACIONES DTW COMPLETADO EXITOSAMENTE")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
