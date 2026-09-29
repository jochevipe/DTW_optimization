# Recreate historical Wilcoxon tables

## Objective
Reproduce the existing untracked `results/tabla_wilcoxon/tabla_wilcoxon1.csv` schema for each of the five historical campaigns, without overwriting that original or ranking incompatible protocols together.

## Scope and constraints
- Sources: `results_base_50`, `results-200-40-60`, `results-200-20-80`, `results-100-50-60`, `results-100-20-80` JSON, nine instance groups index 0 and four MH per group.
- Focal strategy: `binary_hysteresis`; direct comparisons against `vanilla_explotacion`, `vanilla_exploracion`, and `binary_simple` separately per campaign. Preserve the CSV column order, MH display labels, signs, raw p-values, and signed mean differences.
- The existing table matches 108/108 recomputed comparisons with paired, two-sided SciPy Wilcoxon `zero_method='wilcox'`, alpha .05. This differs from the current general stats helper's `zsplit` default; explicitly match the historical table without altering the helper.
- `base_50` uses W=50, 1000 iterations and a legacy rule; other campaigns use 2000 iterations/A4. Do not combine across campaigns or infer equivalence of legacy and A4 variants.
- In `results-200-40-60`, old mknapcb6 JSON under W=200 directory actually declares W=100: exclude it. Duplicates for 7–9 have identical fitness arrays; select a complete metadata-matching campaign deterministically. Validate campaign identity shared across all strategies/MH and fitness epoch counts before output.
- Preserve all existing untracked files; output five new per-campaign CSVs under `results/tabla_wilcoxon/by_campaign/`. No jobs, experiment reruns, stash changes, publishing, or commits without explicit user instruction.
- TDD: no configured project TDD mode found; ordinary focused correctness checks using the installed `DTW_optimization` Conda Python. Expected authored implementation under ~400 lines; generated CSV rows excluded. Delivery: ask-on-risk; no PR planned.

## Tasks
- [x] T1 (delegated bounded writer): implement a reproducible generator for the five campaign tables, with metadata validation, stable selection and preservation of the existing CSV. Check: generated base_50 matches existing table cell-for-cell (including p-values/signs/diffs); 36 rows and correct schema for each output; reject a mislabeled/ambiguous source.
- [x] T2 (read-only verification): independently check generated tables against source JSON, source provenance and selected duplicates; report any failed/skipped checks. Do not claim statistical superiority from raw p-values.
- [ ] T3 (delivery): native review was offered but declined for this candidate by the interactive host; commit the work unit only after explicit user authorization. Check: preserve the original untracked CSV and report review outcome.

## Progress and evidence
- Initial tree: clean except untracked `results/tabla_wilcoxon/tabla_wilcoxon1.csv`; no tracked outputs overwritten.
- Baseline parity checked before implementation: 108/108 p-values, mean differences and signs match under SciPy `wilcox`, `two-sided`.
- T1 route: delegated writer; `analisis/generar_tablas_wilcoxon.py`, `analisis/test_generar_tablas_wilcoxon.py`, five generated CSVs in `results/tabla_wilcoxon/by_campaign/`. Conda Python `-B -m unittest analisis.test_generar_tablas_wilcoxon`: 4 tests passed. Generator command `-B -m analisis.generar_tablas_wilcoxon`: passed. No experiments were run. No commit requested.
- T2 route: independent `gentle-ai-verify` ran the exact test command (4 passed), inspected the five 36-row, 12-column tables and source selection. Parent spot-check recomputed all five saved CSVs cell-for-cell from source JSON and confirmed original SHA-256 `1493d6afbb4a9a44c6596f1a9627d97dca3846ae711086b469f4fc18cdd94ac5`. The older mknapcb6 run in the W200 folder has W100 and is excluded; 7–9 duplicate fitness arrays match. Pairing is positional; aggregated JSON omits explicit seeds, so seed identity across runs is not proven independently. Raw unadjusted p-values and `≈` (non-rejection) do not prove equivalence or overall superiority.
- Native review assess returned `unassessable` because untracked intent required declaration; independent verifier was run. Native inspect selected only eight new paths and excluded the original reference CSV. START returned `consent-declined-this-candidate` from the interactive host (`lineage_created=false`, `mutation_performed=false`); no native review verdict or receipt. Work-unit commit pending explicit user instruction.

## Next step
Report the five verified tables and decline outcome; do not commit or publish unless explicitly instructed.
