"""
Statistical comparison of DTW versions vs Vanilla baseline.
Uses Wilcoxon signed-rank test (paired by seed) with Bonferroni correction.

Usage:
    python -m analisis.estadistico
"""

from pathlib import Path

from mkp_common.stats import compare_versions, format_table, format_math_table


try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:  # pragma: no cover
    MATPLOTLIB_AVAILABLE = False


BASE = Path(__file__).resolve().parent.parent


def find_latest(directory):
    """Return the most recent ``comparacion_mhs_*`` directory under *directory*."""
    dirs = sorted(Path(directory).glob("comparacion_mhs_*"))
    return str(dirs[-1]) if dirs else None


def _ensure_scipy() -> bool:
    """Verify scipy is installed; print a friendly message otherwise."""
    try:
        import scipy  # noqa: F401
        return True
    except ImportError:
        print("scipy is not installed. Please run: pip install scipy")
        return False


def _plot_box(results: dict, output_path: Path) -> None:
    """Optional boxplot comparing all versions (requires matplotlib)."""
    if not MATPLOTLIB_AVAILABLE:
        return

    mhs = results.get("mhs", {})
    if not mhs:
        return

    version_names = []
    for mh_entry in mhs.values():
        version_names.extend(mh_entry.get("versions", {}).keys())
    version_names = list(dict.fromkeys(version_names))

    n_mhs = len(mhs)
    n_versions = len(version_names) + 1  # +1 for vanilla
    fig_width = max(8, 2.5 * n_versions)
    fig, axes = plt.subplots(1, n_mhs, figsize=(fig_width, 5), sharey=False)
    if n_mhs == 1:
        axes = [axes]

    for ax, (mh, mh_entry) in zip(axes, mhs.items()):
        data = [mh_entry.get("baseline_fitness", [])]
        labels = ["Vanilla"]

        # Fitness arrays are stored by compare_versions for plotting.
        for v_name in version_names:
            v = mh_entry.get("versions", {}).get(v_name)
            if v is None:
                data.append([])
            else:
                data.append(v.get("version_fitness", []))
            labels.append(v_name)

        ax.boxplot([d for d in data if d], tick_labels=[labels[i] for i, d in enumerate(data) if d])
        ax.set_title(mh)
        ax.set_ylabel("Fitness")
        ax.tick_params(axis="x", rotation=30)

    fig.suptitle("DTW Adaptations vs Vanilla — Fitness Distribution")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Boxplot saved to: {output_path}")


def main():
    if not _ensure_scipy():
        return 1

    baseline = find_latest(BASE / "results" / "vanilla" / "todos")
    versions = {
        "Fire D2 (A3)": find_latest(BASE / "results" / "fire_d2" / "todos"),
        "Fire Binario (A4)": find_latest(BASE / "results" / "fire_binario" / "todos"),
        "B1 Sigmoide": find_latest(BASE / "results" / "sigmoid_delta" / "todos"),
    }

    # Drop versions whose directories are missing.
    versions = {k: v for k, v in versions.items() if v is not None}
    if not versions:
        print("No DTW result directories found. Run the experiments first.")
        return 1

    if baseline is None:
        print("Baseline vanilla results not found. Run the vanilla experiment first.")
        return 1

    mhs = ["PSO", "GA", "GWO", "DE"]

    results = compare_versions(baseline, versions, mhs, alpha=0.05, alternative="two-sided")

    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = BASE / "results" / "estadistico"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Formatted table (console + file)
    table = format_table(results, title="DTW Adaptation vs Vanilla — Wilcoxon Signed-Rank (two-sided)")
    print(table)

    # Math table (console + file)
    print()
    math_table = format_math_table(results, title="Numerical Results — Vanilla vs DTW Versions")
    print(math_table)

    # Save both to files
    table_path = output_dir / f"tabla_estadistica_{stamp}.txt"
    math_path = output_dir / f"tabla_matematica_{stamp}.txt"
    table_path.write_text(table + "\n", encoding="utf-8")
    math_path.write_text(math_table + "\n", encoding="utf-8")
    print(f"\nSaved: {table_path}")
    print(f"Saved: {math_path}")

    if MATPLOTLIB_AVAILABLE:
        plot_path = output_dir / f"comparacion_{stamp}.png"
        _plot_box(results, plot_path)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
