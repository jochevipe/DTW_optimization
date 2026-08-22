"""
Statistical comparison of DTW versions vs V-Exploración baseline.
Uses Shapiro-Wilk normality checks on paired per-epoch differences and raw
paired Wilcoxon signed-rank tests.

Usage:
    python -m analisis.estadistico
    python -m analisis.estadistico --instancia instances/mknapcb1.txt
    python -m analisis.estadistico --instancia instances/mknapcb1.txt --indice 0
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from mkp_common.stats import (
    compare_versions,
    format_math_table,
    format_raw_table,
    format_table,
    format_time_table,
)


try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except Exception:  # pragma: no cover
    MATPLOTLIB_AVAILABLE = False


BASE = Path(__file__).resolve().parent.parent
MHS = ("PSO", "GA", "GWO", "DE")
RESULT_DIR_PREFIX = "comparacion_mhs_"
HYSTERESIS_RULE = "delta >= theta_delta -> explore; delta <= 0 -> exploit"


class ResultSelectionError(RuntimeError):
    """Raised when result directories cannot form a compatible campaign."""


class ResultMetadataError(ValueError):
    """Raised when one result directory lacks safe selection metadata."""


@dataclass(frozen=True)
class ResultCandidate:
    """Validated metadata for one complete strategy result directory."""

    directory: Path
    strategy: str
    campaign_id: str
    instance_path: str
    instance_name: str
    instance_index: int
    population: int
    iterations: int
    epochs: int
    decision_rule: Optional[str]
    dtw_window: Optional[int]
    legacy_campaign: bool


def _result_dirs(directory, subdir: Optional[str] = None):
    """Return result directories in newest-first order without reading data."""
    root = Path(directory)
    if subdir:
        target = root / subdir
        candidates = target.glob(f"{RESULT_DIR_PREFIX}*") if target.is_dir() else []
    else:
        candidates = list(root.glob(f"*/{RESULT_DIR_PREFIX}*"))
        if not candidates:
            candidates = root.glob(f"{RESULT_DIR_PREFIX}*")
    return sorted(
        (path for path in candidates if path.is_dir()),
        key=lambda path: path.name,
        reverse=True,
    )


def _legacy_campaign_id(directory: Path) -> Optional[str]:
    """Infer a campaign ID from the legacy directory name when possible."""
    if not directory.name.startswith(RESULT_DIR_PREFIX):
        return None
    campaign_id = directory.name[len(RESULT_DIR_PREFIX):]
    return campaign_id or None


def _normalise_instance_path(value: str) -> str:
    """Use a stable, case-insensitive path form for campaign comparisons."""
    return str(Path(value).expanduser().resolve(strict=False)).replace("\\", "/").casefold()


def _required_int(
    info: dict, key: str, directory: Path, minimum: int = 1
) -> int:
    value = info.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ResultMetadataError(
            f"{directory}: info[{key!r}] must be an integer >= {minimum}"
        )
    return value


def _strategy_rule(strategy: str, info: dict, directory: Path) -> Optional[str]:
    """Validate strategy-specific metadata without changing stored fields."""
    if strategy == "binary_simple":
        rule = info.get("decision_rule")
        if rule != "D2 <= theta_c":
            raise ResultMetadataError(
                f"{directory}: Binary-Simple decision_rule is {rule!r}, "
                "expected 'D2 <= theta_c'"
            )
        return rule

    if strategy == "binary_hysteresis":
        rule = info.get("decision_rule")
        if rule == HYSTERESIS_RULE or rule == "hysteresis on delta":
            return HYSTERESIS_RULE
        raise ResultMetadataError(
            f"{directory}: Binary-Hysteresis decision_rule is {rule!r}; "
            f"expected {HYSTERESIS_RULE!r}"
        )

    return None


def inspect_result_directory(
    directory,
    expected_strategy: Optional[str] = None,
    required_mhs: Tuple[str, ...] = MHS,
) -> ResultCandidate:
    """Validate all MH JSON files in a directory and return its metadata.

    Legacy JSON remains usable when it contains the original instance, budget,
    population, strategy, and epoch fields. Its campaign identity is inferred
    only from the standard ``comparacion_mhs_*`` folder name.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise ResultMetadataError(f"{directory}: result directory does not exist")

    records = []
    for mh in required_mhs:
        matches = sorted(directory.glob(f"{mh}_*.json"))
        if not matches:
            raise ResultMetadataError(f"{directory}: missing {mh} JSON result")
        if len(matches) != 1:
            raise ResultMetadataError(
                f"{directory}: expected one {mh} JSON result, found {len(matches)}"
            )
        path = matches[0]
        try:
            with path.open(encoding="utf-8") as stream:
                data = json.load(stream)
        except (OSError, json.JSONDecodeError) as exc:
            raise ResultMetadataError(f"{path}: cannot read JSON ({exc})") from exc

        info = data.get("info")
        if not isinstance(info, dict):
            raise ResultMetadataError(
                f"{path}: missing info metadata; refusing unsafe legacy pairing"
            )
        strategy = info.get("estrategia")
        if not isinstance(strategy, str) or not strategy:
            raise ResultMetadataError(f"{path}: missing info['estrategia']")
        if expected_strategy is not None and strategy != expected_strategy:
            raise ResultMetadataError(
                f"{path}: strategy {strategy!r} does not match "
                f"expected {expected_strategy!r}"
            )

        if data.get("mh") != mh:
            raise ResultMetadataError(
                f"{path}: JSON mh={data.get('mh')!r} does not match filename {mh!r}"
            )
        epochs = data.get("epochs")
        fitness = data.get("fitness")
        if (
            isinstance(epochs, bool)
            or not isinstance(epochs, int)
            or epochs <= 0
            or not isinstance(fitness, list)
            or len(fitness) != epochs
        ):
            raise ResultMetadataError(
                f"{path}: epochs and fitness length are missing or inconsistent"
            )

        instance = info.get("instancia")
        if not isinstance(instance, str) or not instance:
            raise ResultMetadataError(f"{path}: missing info['instancia']")
        idx = _required_int(info, "idx", directory, minimum=0)
        population = _required_int(info, "poblacion", directory)
        iterations = _required_int(info, "iteraciones", directory)
        decision_rule = _strategy_rule(strategy, info, directory)

        dtw_window = info.get("dtw_window")
        if strategy in {"binary_simple", "binary_hysteresis"}:
            if (
                isinstance(dtw_window, bool)
                or not isinstance(dtw_window, int)
                or dtw_window <= 0
            ):
                raise ResultMetadataError(
                    f"{path}: adaptive strategy requires a positive dtw_window"
                )
        elif dtw_window is not None:
            raise ResultMetadataError(
                f"{path}: vanilla strategy unexpectedly contains dtw_window"
            )

        explicit_campaign = info.get("campaign_id")
        if explicit_campaign is not None and (
            not isinstance(explicit_campaign, str) or not explicit_campaign
        ):
            raise ResultMetadataError(f"{path}: campaign_id must be a non-empty string")
        campaign_id = explicit_campaign or _legacy_campaign_id(directory)
        if campaign_id is None:
            raise ResultMetadataError(
                f"{directory}: missing campaign metadata and standard campaign folder name"
            )

        records.append(
            {
                "mh": mh,
                "strategy": strategy,
                "campaign_id": campaign_id,
                "instance_path": _normalise_instance_path(instance),
                "instance_name": Path(instance).stem,
                "instance_index": idx,
                "population": population,
                "iterations": iterations,
                "epochs": epochs,
                "decision_rule": decision_rule,
                "dtw_window": dtw_window,
                "legacy_campaign": explicit_campaign is None,
            }
        )

    reference = records[0]
    comparable_fields = (
        "strategy",
        "campaign_id",
        "instance_path",
        "instance_name",
        "instance_index",
        "population",
        "iterations",
        "epochs",
        "decision_rule",
        "dtw_window",
    )
    for record in records[1:]:
        differences = [
            field
            for field in comparable_fields
            if record[field] != reference[field]
        ]
        if differences:
            raise ResultMetadataError(
                f"{directory}: MH metadata disagree on {', '.join(differences)}"
            )

    return ResultCandidate(directory=directory, **{
        key: reference[key]
        for key in (
            "strategy",
            "campaign_id",
            "instance_path",
            "instance_name",
            "instance_index",
            "population",
            "iterations",
            "epochs",
            "decision_rule",
            "dtw_window",
            "legacy_campaign",
        )
    })


def find_latest(directory, subdir: str = None, expected_strategy: str = None):
    """Return the newest complete, metadata-valid result directory.

    This compatibility helper no longer treats a directory name alone as a
    valid result. Campaign-wide selection is performed by
    :func:`select_compatible_results` below.
    """
    for candidate in _result_dirs(directory, subdir=subdir):
        try:
            inspect_result_directory(candidate, expected_strategy=expected_strategy)
        except ResultMetadataError:
            continue
        return str(candidate)
    return None


def _validated_candidates(directory, strategy, subdir):
    valid = {}
    errors = []
    raw = _result_dirs(directory, subdir=subdir)
    for path in raw:
        try:
            candidate = inspect_result_directory(path, expected_strategy=strategy)
        except ResultMetadataError as exc:
            errors.append(str(exc))
            continue
        if candidate.campaign_id in valid:
            errors.append(
                f"{path}: duplicate campaign_id {candidate.campaign_id!r} "
                "for this strategy"
            )
            continue
        valid[candidate.campaign_id] = candidate
    return raw, valid, errors


def select_compatible_results(
    sources: Dict[str, Tuple[Path, str]],
    subdir: Optional[str] = None,
    requested_instance: Optional[str] = None,
    requested_campaign: Optional[str] = None,
) -> Dict[str, str]:
    """Select one common, metadata-compatible campaign for all available versions.

    ``sources`` maps the display label used by the statistical report to a
    ``(results_root, strategy_key)`` pair. Missing optional strategy roots are
    allowed for compatibility with skipped experiments; existing but invalid
    roots fail instead of being silently omitted.
    """
    baseline_label = "Exploration-only"
    if baseline_label not in sources:
        raise ResultSelectionError("Exploration-only is required as the baseline")

    candidate_sets = {}
    diagnostics = []
    for label, (directory, strategy) in sources.items():
        raw, valid, errors = _validated_candidates(directory, strategy, subdir)
        if not raw:
            if label == baseline_label:
                raise ResultSelectionError(
                    f"No result directories found for required baseline {directory}"
                )
            continue
        if not valid:
            diagnostics.append(
                f"{label}: no metadata-valid campaign under {directory}"
            )
            diagnostics.extend(f"  - {error}" for error in errors[-3:])
            continue
        if errors:
            diagnostics.append(
                f"{label}: rejected result candidates under {directory}"
            )
            diagnostics.extend(f"  - {error}" for error in errors[-3:])
        candidate_sets[label] = valid

    if baseline_label not in candidate_sets:
        detail = "\n".join(diagnostics)
        raise ResultSelectionError(
            "No metadata-valid Exploration-only baseline exists."
            + (f"\n{detail}" if detail else "")
        )
    if diagnostics:
        raise ResultSelectionError(
            "Existing result candidates could not be paired safely:\n"
            + "\n".join(diagnostics)
        )

    common_campaigns = set.intersection(
        *(set(candidates) for candidates in candidate_sets.values())
    )
    if not common_campaigns:
        available = "; ".join(
            f"{label}={sorted(candidates)}"
            for label, candidates in candidate_sets.items()
        )
        raise ResultSelectionError(
            "No compatible campaign is shared by the available strategies "
            f"(campaign IDs: {available})"
        )

    if requested_campaign is not None:
        if requested_campaign not in common_campaigns:
            raise ResultSelectionError(
                f"Requested campaign {requested_campaign!r} is not complete and "
                f"compatible across the available strategies "
                f"(available: {sorted(common_campaigns)})"
            )
        campaign_id = requested_campaign
    else:
        campaign_id = max(
            common_campaigns,
            key=lambda campaign: max(
                candidate_sets[label][campaign].directory.name
                for label in candidate_sets
            ),
        )
    selected = {
        label: candidates[campaign_id]
        for label, candidates in candidate_sets.items()
    }

    reference = selected[baseline_label]
    for label, candidate in selected.items():
        fields = (
            "instance_name",
            "instance_path",
            "instance_index",
            "population",
            "iterations",
            "epochs",
            "campaign_id",
        )
        mismatches = [
            field
            for field in fields
            if getattr(candidate, field) != getattr(reference, field)
        ]
        if mismatches:
            raise ResultSelectionError(
                f"Campaign {campaign_id!r} is incompatible for {label}: "
                f"{', '.join(mismatches)} differ"
            )

    dtw_windows = {
        candidate.dtw_window
        for candidate in selected.values()
        if candidate.dtw_window is not None
    }
    if len(dtw_windows) > 1:
        raise ResultSelectionError(
            f"Campaign {campaign_id!r} mixes adaptive dtw_window values: "
            f"{sorted(dtw_windows)}"
        )

    if subdir:
        expected_name, separator, expected_idx = subdir.rpartition("_")
        if separator and expected_idx.isdigit():
            if (
                reference.instance_name != expected_name
                or reference.instance_index != int(expected_idx)
            ):
                raise ResultSelectionError(
                    f"Selected metadata identifies "
                    f"{reference.instance_name}[{reference.instance_index}], "
                    f"not requested {subdir}"
                )

    if requested_instance is not None:
        requested_path = _normalise_instance_path(requested_instance)
        if reference.instance_path != requested_path:
            raise ResultSelectionError(
                f"Selected metadata points to {reference.instance_path!r}, "
                f"not requested instance {requested_path!r}"
            )

    return {
        label: str(candidate.directory)
        for label, candidate in selected.items()
    }


def _ensure_scipy() -> bool:
    """Verify scipy is installed; print a friendly message otherwise."""
    try:
        import scipy  # noqa: F401
        return True
    except ImportError:
        print("scipy is not installed. Please run: pip install scipy")
        return False


def _plot_box(results: dict, output_path: Path, instance_label: str = "",
              optimo: Optional[float] = None) -> None:
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
    n_versions = len(version_names) + 1  # +1 for V-Exploración (baseline)
    fig_width = max(8, 2.5 * n_versions)
    fig, axes = plt.subplots(1, n_mhs, figsize=(fig_width, 5), sharey=False)
    if n_mhs == 1:
        axes = [axes]

    for ax, (mh, mh_entry) in zip(axes, mhs.items()):
        data = [mh_entry.get("baseline_fitness", [])]
        labels = ["Exploration-only"]

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
        for label in ax.get_xticklabels():
            label.set_ha("right")

        if optimo and optimo > 0:
            ax.axhline(
                optimo,
                color="#2ecc71",
                linestyle="--",
                linewidth=2,
            )

    if optimo and optimo > 0:
        opt_part = f" (opt={optimo:.0f})"
    else:
        opt_part = ""
    suptitle = f"Fitness distribution across MH variants — {instance_label}{opt_part}"
    fig.suptitle(suptitle)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Boxplot saved to: {output_path}")
    # also save PNG for quick preview
    png_path = output_path.with_suffix(".png")
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    print(f"Boxplot saved to: {png_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Statistical comparison of DTW versions vs V-Exploración baseline"
    )
    parser.add_argument(
        "--instancia",
        default=None,
        help="Filtrar por instancia (ej: instances/mknapcb1.txt). "
             "Si no se especifica, usa los resultados más recientes de cualquier instancia.",
    )
    parser.add_argument(
        "--indice",
        type=int,
        default=0,
        help="Índice de la instancia (default: 0). Solo se usa con --instancia.",
    )
    parser.add_argument(
        "--one-sided",
        action="store_true",
        default=False,
        help="Usar test one-sided (version > baseline) en vez de two-sided (default).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not _ensure_scipy():
        return 1

    # Build instance subdirectory filter
    subdir = None
    instance_label = "?"
    instance_dir = "unknown"

    if args.instancia:
        inst_name = Path(args.instancia).stem
        subdir = f"{inst_name}_{args.indice}"
        instance_label = f"{inst_name}[{args.indice}]"
        instance_dir = subdir
        print(f"  Instancia seleccionada: {instance_label}")
        print(f"  Buscando en: results/*/todos/{subdir}/")
        print()

    sources = {
        "Exploration-only": (
            BASE / "results" / "vanilla_exploracion" / "todos",
            "vanilla_exploracion",
        ),
        "Exploitation-only": (
            BASE / "results" / "vanilla_explotacion" / "todos",
            "vanilla_explotacion",
        ),
        "Binary-Simple": (
            BASE / "results" / "binary_simple" / "todos",
            "binary_simple",
        ),
        "Binary-Hysteresis": (
            BASE / "results" / "binary_hysteresis" / "todos",
            "binary_hysteresis",
        ),
    }
    try:
        selected = select_compatible_results(
            sources,
            subdir=subdir,
            requested_instance=args.instancia,
            requested_campaign=os.environ.get("MKP_CAMPAIGN_ID"),
        )
    except ResultSelectionError as exc:
        print(f"ERROR: result selection refused: {exc}")
        return 1

    baseline = selected["Exploration-only"]
    versions = {
        label: directory
        for label, directory in selected.items()
        if label != "Exploration-only"
    }
    if not versions:
        print("No compatible comparison versions found. Run the experiments first.")
        return 1

    mhs = list(MHS)

    alternative = "greater" if args.one_sided else "two-sided"
    results = compare_versions(baseline, versions, mhs, alpha=0.05, alternative=alternative)

    # Extract the already-validated instance metadata if not explicitly set.
    if instance_label == "?":
        baseline_metadata = inspect_result_directory(
            baseline, expected_strategy="vanilla_exploracion"
        )
        instance_label = (
            f"{baseline_metadata.instance_name}"
            f"[{baseline_metadata.instance_index}]"
        )
        instance_dir = (
            f"{baseline_metadata.instance_name}_"
            f"{baseline_metadata.instance_index}"
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = BASE / "results" / "estadistico" / instance_dir / f"comparacion_{stamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    alt_label = "(one-tailed >)" if args.one_sided else "(two-sided)"

    # Formatted table (console + file)
    title1 = f"DTW Adaptation vs Exploration-only — {instance_label} — Wilcoxon Signed-Rank {alt_label}"
    table = format_table(results, title=title1)
    print(table)

    # Math table (console + file)
    print()
    title2 = f"Numerical Results — {instance_label} — Exploration-only vs Variants"
    math_table = format_math_table(results, title=title2)
    print(math_table)

    # Descriptive runtime table (console + file)
    print()
    title4 = f"Execution Times — {instance_label} — Exploration-only vs Variants"
    time_table = format_time_table(results, title=title4)
    print(time_table)



    # Save all tables to files
    table_path = output_dir / "tabla_estadistica.txt"
    math_path = output_dir / "tabla_matematica.txt"
    time_path = output_dir / "tabla_tiempos.txt"
    table_path.write_text(table + "\n", encoding="utf-8")
    math_path.write_text(math_table + "\n", encoding="utf-8")
    time_path.write_text(time_table + "\n", encoding="utf-8")
    print(f"\nSaved: {table_path}")
    print(f"Saved: {math_path}")
    print(f"Saved: {time_path}")

    if MATPLOTLIB_AVAILABLE:
        plot_path = output_dir / "comparacion.pdf"
        optimo = results.get("summary", {}).get("optimo_conocido")
        _plot_box(results, plot_path, instance_label=instance_label, optimo=optimo)

    return 0


if __name__ == "__main__":
    sys.exit(main())
