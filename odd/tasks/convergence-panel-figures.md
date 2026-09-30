# Convergence panel figures

## Objective and scope
Six preview figures: mknapcb1, mknapcb5 and mknapcb9, separately for Binary-Simple and Binary-Complex. Each figure has one column of three panels, instance indices 0, 15, 29 from top to bottom. The user rejected the original horizontal 2-by-3 design. Remove seed titles; rename visible Hysteresis to Complex. Preserve curves and originals. Do not edit the manuscript or algorithm implementations.

## Constraints and routing
- Existing worktree edits remain untouched; no commits authorized or made.
- Delegated worker plus independent read-only verifier; parent visual readback and pdftotext spot check.
- TDD disabled for T2 by explicit user choice in the parent session (verification questionnaire). Figure composition only; use artifact checks and visual inspection, not algorithm tests.
- Forecast under 200 authored lines, generated files excluded; strategy ask-on-risk.

## Tasks
- [x] T1: Compose and verify initial 2-by-3 grids (technically verified, design rejected by user).
- [x] T2: Generate and verify six separate 3-by-1 vertical figures, preserving source curves and corrected crop boundaries.

## Outputs
- analisis/componer_figuras_convergencia.py
- paper/figures/convergence/mknapcb{1,5,9}.{pdf,png}
- paper/figures/convergence/source_manifest.md
- Reproducible vector-panel/TeX build intermediates remain; exploratory probe files removed by parent.

## Verification evidence
- Worker: python3 analisis/componer_figuras_convergencia.py passed; all 18 original source hashes unchanged and match manifest.
- Three nonempty single-page PDF/PNG pairs; six panels each.
- Parent pdftotext spot check confirms groups, indices and row labels; no seed or Hysteresis extracted. Curves use outlined vectors so visual checks required too.
- Independent verifier found clipped boundary tick labels; worker expanded crop to y=12..234.5 and selectively removed title glyphs. Independent final visual recheck passed for all three figures including 54000/60000 boundaries, axes and legends; no original titles or control-diagnostic axes leaked.
- Native risk assessment unavailable because ambient untracked scope undeclared: unassessable, independent verifier used. Native review outcome unknown; no approved review claimed.
- Source best-of-31 selection caveat recorded; not mean or typical-run convergence. Original convergence legends and line styles preserved.

## Next step
Six vertical PDF/PNG pairs generated: paper/figures/convergence/mknapcb{1,5,9}_binary_{simple,complex}.{pdf,png}. Writer generation/artifact checks passed, all 18 source hashes matched; earlier horizontal output hashes unchanged. Independent verifier inspected all six PNGs and source hashes: PASS correct 0/15/29 order, titles, unclipped axes, no seed titles/control axes. Parent pdfinfo/pdftotext spot check passed all six single-page PDFs (532.8 x 662.4 pt). Native assessment unassessable due ambient untracked scope, separate verification performed, no native approval claimed. User can review new previews; manuscript incorporation is not authorized.
