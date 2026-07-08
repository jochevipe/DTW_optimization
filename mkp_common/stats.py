"""
mkp_common.stats — Statistical helpers for comparing metaheuristic variants.

Provides Wilcoxon signed-rank tests (paired by seed/epoch) and Bonferroni
correction for comparing DTW adaptations against a vanilla baseline.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np


def _check_scipy():
    """Return scipy.stats if available, otherwise None."""
    try:
        from scipy import stats
        return stats
    except Exception:  # pragma: no cover
        return None


def wilcoxon_test(
    baseline_fits: Sequence[float],
    version_fits: Sequence[float],
    alpha: float = 0.05,
    alternative: str = "greater",
) -> Dict:
    """
    Paired Wilcoxon signed-rank test comparing a version against a baseline.

    H1 with alternative='greater' is: version > baseline.

    Parameters
    ----------
    baseline_fits, version_fits : sequence of float
        Paired fitness values (same length, same seed/epoch order).
    alpha : float, optional
        Significance level for the raw test (default 0.05).
    alternative : str, optional
        SciPy alternative hypothesis for ``version - baseline``.

    Returns
    -------
    dict
        {"p_value": float, "significant": bool, "statistic": float,
         "median_diff": float, "effect_size": float}
    """
    stats = _check_scipy()
    if stats is None:
        raise RuntimeError("scipy is required for statistical tests. Run: pip install scipy")

    baseline = np.asarray(baseline_fits, dtype=float)
    version = np.asarray(version_fits, dtype=float)

    if baseline.shape != version.shape:
        raise ValueError("baseline_fits and version_fits must have the same length")

    median_diff = float(np.median(version - baseline))
    n_pairs = len(baseline)

    try:
        result = stats.wilcoxon(
            version,
            baseline,
            alternative=alternative,
            zero_method="zsplit",
            mode="auto",
        )
        statistic = float(result.statistic)
        p_value = float(result.pvalue)
    except ValueError:
        # All differences are zero (or otherwise degenerate).
        statistic = 0.0
        p_value = 1.0

    # Rank-biserial correlation as a simple effect-size estimate.
    effect_size = statistic / n_pairs if n_pairs > 0 else 0.0

    return {
        "p_value": p_value,
        "significant": p_value < alpha,
        "statistic": statistic,
        "median_diff": median_diff,
        "effect_size": effect_size,
    }


def _load_mh_json(directory: Optional[str], mh: str) -> Optional[dict]:
    """Load the first JSON file matching ``{mh}_*.json`` in *directory*."""
    if not directory:
        return None
    path = Path(directory)
    if not path.is_dir():
        return None

    candidates = sorted(path.glob(f"{mh}_*.json"))
    if not candidates:
        return None

    try:
        with open(candidates[0], encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def compare_versions(
    baseline_dir: str,
    version_dirs: Dict[str, str],
    mh_names: List[str],
    alpha: float = 0.05,
    alternative: str = "greater",
) -> Dict:
    """
    Compare every version in *version_dirs* against the vanilla baseline.

    Bonferroni correction is applied across the number of versions tested.

    Parameters
    ----------
    baseline_dir : str
        Path to the vanilla JSON directory.
    version_dirs : dict[str, str]
        Mapping ``version_label -> directory_path``.
    mh_names : list[str]
        Metaheuristics to compare (e.g., ["PSO", "GA", "GWO", "DE"]).
    alpha : float, optional
        Family-wise error rate.
    alternative : str, optional
        SciPy alternative hypothesis (default "greater", use "two-sided" for
        detecting both improvement and degradation).

    Returns
    -------
    dict
        Structured results with summary, per-MH statistics and per-version
        Wilcoxon outcomes.
    """
    stats = _check_scipy()
    if stats is None:
        raise RuntimeError("scipy is required for statistical tests. Run: pip install scipy")

    n_versions = len(version_dirs)
    alpha_corrected = alpha / n_versions if n_versions > 0 else alpha

    per_mh: Dict[str, Dict] = {}
    for mh in mh_names:
        baseline_data = _load_mh_json(baseline_dir, mh)
        if baseline_data is None:
            continue

        baseline_fits = baseline_data.get("fitness", [])
        mh_entry = {
            "baseline_mean": float(np.mean(baseline_fits)) if baseline_fits else np.nan,
            "baseline_std": float(np.std(baseline_fits)) if baseline_fits else np.nan,
            "versions": {},
        }

        for version_name, version_dir in version_dirs.items():
            version_data = _load_mh_json(version_dir, mh)
            if version_data is None:
                continue

            version_fits = version_data.get("fitness", [])
            if len(version_fits) != len(baseline_fits):
                continue

            test_result = wilcoxon_test(
                baseline_fits,
                version_fits,
                alpha=alpha_corrected,
                alternative=alternative,
            )

            mh_entry["versions"][version_name] = {
                "mean": float(np.mean(version_fits)) if version_fits else np.nan,
                "std": float(np.std(version_fits)) if version_fits else np.nan,
                "version_fitness": version_fits,
                **test_result,
            }

        mh_entry["baseline_fitness"] = baseline_fits

        per_mh[mh] = mh_entry

    return {
        "summary": {
            "alpha": alpha,
            "n_versions": n_versions,
            "alpha_corrected": alpha_corrected,
            "test": "Wilcoxon signed-rank (paired)",
            "correction": "Bonferroni",
            "alternative": alternative,
        },
        "mhs": per_mh,
    }


def _marker(p_value: float, alpha: float, alpha_corrected: float, ascii_only: bool = False) -> str:
    """Return significance marker for a p-value."""
    if p_value < alpha_corrected:
        if p_value < 0.001:
            return "***"
        if p_value < 0.01:
            return "**"
        return "*"
    if p_value < alpha:
        return "^" if ascii_only else "¹"
    return ""


def _can_encode_unicode() -> bool:
    """Return True if stdout can encode common box-drawing characters."""
    import sys

    try:
        enc = sys.stdout.encoding
    except AttributeError:
        return False

    if enc is None:
        return False

    sample = "╔╗╚╝║═╤╧╪│╠╣╟╢"
    try:
        sample.encode(enc)
        return True
    except UnicodeEncodeError:
        return False


def format_table(
    results: Dict,
    title: str = "Statistical Comparison vs Vanilla",
    ascii_only: Optional[bool] = None,
) -> str:
    """
    Format comparison results as a paper-ready table.

    Parameters
    ----------
    results : dict
        Output from :func:`compare_versions`.
    title : str, optional
        Table title.
    ascii_only : bool, optional
        If True, use plain ASCII characters. If None, auto-detect stdout
        encoding capability.

    Returns
    -------
    str
        Multi-line formatted table.
    """
    if ascii_only is None:
        ascii_only = not _can_encode_unicode()

    if ascii_only:
        title = title.replace("—", "--").replace("–", "-")

    summary = results.get("summary", {})
    mhs = results.get("mhs", {})
    alpha = summary.get("alpha", 0.05)
    alpha_corrected = summary.get("alpha_corrected", alpha)
    n_versions = summary.get("n_versions", 0)

    version_names = []
    for mh_entry in mhs.values():
        version_names.extend(mh_entry.get("versions", {}).keys())
    version_names = list(dict.fromkeys(version_names))

    # Build rows: each MH has a primary row (mean ± std) and a secondary row
    # with delta/p-value for each version.
    rows = []
    for mh, mh_entry in mhs.items():
        baseline_mean = mh_entry.get("baseline_mean", np.nan)
        baseline_std = mh_entry.get("baseline_std", np.nan)

        pm_symbol = "+/-" if ascii_only else "±"
        primary_cells = [f"{baseline_mean:.1f} {pm_symbol} {baseline_std:.1f}"]
        secondary_cells = [""]

        for version_name in version_names:
            v = mh_entry.get("versions", {}).get(version_name)
            if v is None:
                primary_cells.append("-" if ascii_only else "—")
                secondary_cells.append("-" if ascii_only else "—")
                continue

            mean = v.get("mean", np.nan)
            std = v.get("std", np.nan)
            median_diff = v.get("median_diff", np.nan)
            p_value = v.get("p_value", np.nan)
            marker = _marker(p_value, alpha, alpha_corrected, ascii_only=ascii_only)

            primary_cells.append(f"{mean:.1f} {pm_symbol} {std:.1f}")
            sign = "+" if median_diff >= 0 else ""
            delta_symbol = "Delta" if ascii_only else "Δ"
            secondary_cells.append(
                f"{delta_symbol}={sign}{median_diff:.1f}, p={p_value:.3f}{marker}"
            )

        rows.append((mh, primary_cells))
        rows.append(("", secondary_cells))

    # Column headers.
    pm_symbol = "+/-" if ascii_only else "±"
    headers = ["MH", f"Vanilla (mean {pm_symbol} std)"] + version_names

    # Column widths based on content.
    col_widths = [len(h) for h in headers]
    for _, cells in rows:
        for i, cell in enumerate(cells):
            col_widths[i] = max(col_widths[i], len(cell))

    # Choose box-drawing charset.
    if ascii_only:
        HL = "="
        VL = "|"
        TL = TR = BL = BR = "+"
        LC = RC = "+"
        TS = BS = CROSS = "+"
        CS = "|"
        LEFT_T = RIGHT_T = "+"
        HBAR = "-"
    else:
        HL = "═"
        VL = "║"
        TL = "╔"
        TR = "╗"
        BL = "╚"
        BR = "╝"
        LC = "╠"
        RC = "╣"
        TS = "╤"
        BS = "╧"
        CS = "│"
        CROSS = "╪"
        LEFT_T = "╟"
        RIGHT_T = "╢"
        HBAR = "─"
        em_dash = "—"

    def sep(left: str, right: str, cross: str = TS, line: str = HL) -> str:
        parts = [line * (col_widths[0] + 2)]
        for w in col_widths[1:]:
            parts.extend([cross, line * (w + 2)])
        return left + "".join(parts) + right

    def row_line(label: str, cells: List[str]) -> str:
        parts = [f" {label:<{col_widths[0]}} "]
        for i, cell in enumerate(cells):
            width = col_widths[i + 1]
            parts.append(f" {cell:>{width}} ")
        line = CS.join(parts)
        return VL + line + VL

    title_text = f" {title} "
    bonferroni_text = (
        f" Bonferroni alpha = {alpha_corrected:.4f} ({n_versions} comparison"
        f"{'s' if n_versions != 1 else ''}) "
    )

    title_width = sum(col_widths) + 3 * len(col_widths) + 1
    title_line = title_text.center(title_width)
    bonferroni_line = bonferroni_text.center(title_width)

    lines = [
        TL + HL * (title_width - 2) + TR,
        VL + title_line + VL,
        VL + bonferroni_line + VL,
        sep(LC, RC),
        row_line(headers[0], headers[1:]),
        sep(LC, RC, cross=CROSS),
    ]

    for i, (label, cells) in enumerate(rows):
        lines.append(row_line(label, cells))
        if i < len(rows) - 1 and label == "":
            # Separator between MH blocks.
            lines.append(sep(LEFT_T, RIGHT_T, cross=CROSS, line=HBAR))

    lines.append(sep(BL, BR, cross=BS))

    # Legend.
    lines.append("")
    lines.append("Significance markers:")
    lines.append("  *   p < 0.05 (significant after Bonferroni)")
    lines.append("  **  p < 0.01")
    lines.append("  *** p < 0.001")
    marker_legend = "^" if ascii_only else "¹"
    lines.append(
        f"  {marker_legend}   p < {alpha:.3f} but not significant after "
        f"Bonferroni (alpha_corr = {alpha_corrected:.4f})"
    )

    return "\n".join(lines)


def format_math_table(
    results: Dict,
    title: str = "Numerical Results",
) -> str:
    """
    Format comparison results as a clean mathematical table with raw numbers.

    Shows mean, std, median delta, p-value, and significance per MH per version.
    Designed for direct inspection before paper formatting.
    """
    summary = results.get("summary", {})
    mhs = results.get("mhs", {})
    alpha = summary.get("alpha", 0.05)
    alpha_corrected = summary.get("alpha_corrected", alpha)
    alternative = summary.get("alternative", "greater")
    alt_text = "(two-sided)" if alternative == "two-sided" else "(one-tailed >)"

    version_names = []
    for mh_entry in mhs.values():
        version_names.extend(mh_entry.get("versions", {}).keys())
    version_names = list(dict.fromkeys(version_names))

    lines = []
    lines.append(f"{'=' * 80}")
    lines.append(f"  {title}")
    lines.append(f"  Wilcoxon signed-rank {alt_text} | Bonferroni alpha = {alpha_corrected:.4f}")
    lines.append(f"{'=' * 80}")
    lines.append("")

    for mh, mh_entry in mhs.items():
        b_mean = mh_entry["baseline_mean"]
        b_std = mh_entry["baseline_std"]

        lines.append(f"  [{mh}]")
        lines.append(f"    Vanilla:            {b_mean:.1f}  +/- {b_std:.1f}")
        lines.append(f"    {'Version':<20s} {'Mean':>10s} {'Std':>10s} {'Delta':>10s} {'p-value':>10s}  Sig")
        lines.append(f"    {'-'*20} {'-'*10} {'-'*10} {'-'*10} {'-'*10}  ---")

        for vn in version_names:
            v = mh_entry.get("versions", {}).get(vn)
            if v is None:
                continue
            mean = v["mean"]
            std = v["std"]
            delta = v["median_diff"]
            p = v["p_value"]
            sig = "YES" if v["significant"] else "no"
            sign = "+" if delta >= 0 else ""
            lines.append(
                f"    {vn:<20s} {mean:10.1f} {std:10.1f} {sign}{delta:9.1f} {p:10.4f}  {sig}"
            )

        # Best version for this MH
        best_v = None
        best_delta = float("-inf")
        for vn in version_names:
            v = mh_entry.get("versions", {}).get(vn)
            if v and v["median_diff"] > best_delta:
                best_delta = v["median_diff"]
                best_v = vn
        if best_v:
            lines.append(f"    -> Best: {best_v}  (delta = +{best_delta:.1f})")
        lines.append("")

    return "\n".join(lines)
