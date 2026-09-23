# OAT findings handoff to dtw_discreto

## Objective
Record the completed OAT evidence and carry only review-facing documentation and project Engram snapshots to `dtw_discreto`, so the next full-experiment campaign can start there without merging OAT code or generated results.

## Constraints and scope
- The user alone submits Slurm jobs. Do not submit or run experiments.
- Preserve dirty `OAT`, existing `dtw_discreto` commits and its literal reviewer letters.
- Do not merge the OAT history, delete datasets, or add the ~50 MB untracked `results/` tree.
- Include a self-contained analysis with exact campaign IDs and limitations; target docs: the new analysis, current reviewer synthesis, question/response working sheet, and selected-instance plan. The OAT runner/design documentation stays in OAT because target lacks `sensibilidad/`.
- Carry `.engram/manifest.json` and new project chunks without deleting pre-existing chunks; review changes before publishing.
- TDD: off for this documentation/transfer task (no project TDD setting established); verification: structural readback, exact Git diff/status and remote branch safety check. No test runner required for docs-only transfer.
- Delivery strategy: single documentation handoff; expected authored text under ~400 changed lines, excluding compressed memory chunks. If larger, reassess before commit.

## Tasks
- [x] T1: Record verified OAT findings in `contexto/Round-1/HALLAZGOS_OAT.md` on OAT. Check: source-linked metrics, completeness, limits and next experiment decision, with no false generalization. Route: inline single-file documentation, readback. Work-unit commit: `af127d5` (`docs(oat): record audited sensitivity findings`).
- [x] T2: Transfer the exact selected documentation and project Engram chunks into an isolated `dtw_discreto` worktree, preserving its reviewer letters and other work. Check: no code, raw results or deletions in target diff. Route: delegated multi-file writer. Work-unit commit: `74359f6` (`docs(round-1): carry OAT findings and project context`).
- [x] T3: Verify target diff and branch freshness, commit reviewable work unit(s), and push only `dtw_discreto` to `origin`. Check: remote points at produced commit; report any skipped checks and blocker. Route: parent Git coordination and read-only verification. Work-unit commits: `74359f6`, `0209110`.

## Progress and evidence
- Baseline: `OAT` at a291028 with local modifications; `dtw_discreto` at d8d0c2c; branches diverge. Original reviewer letters are present on `dtw_discreto`, absent from `OAT`.
- OAT audit: two campaigns each contain 19 configs, 228/228 expected MH JSON, 31 finite fitness values per JSON (7068/7068). No Slurm execution performed.
- T1: readback of 19 configs, 228 JSON/7068 finite fitness values per campaign and all six Δ ranges against existing `tabla_oat.md` completed; `git diff --cached --check` passed; commit `af127d5`. No experiment jobs or test suite run (documentation only).
- T2: initial attempt blocked by unexpected transient target changes and a `reset: moving to HEAD` reflog entry (actor unknown). Following user confirmation that the destination was stable, fresh delegated readback found clean `d8d0c2c`; 13 authorized paths copied, source/target bytes matched before target-only corrections, old reviewer letters preserved. `git diff --cached --check` passed; 238 additions/43 deletions plus seven compressed chunks, no code or raw results; commit `74359f6`. Target-only synthesis corrects stale configuration and notes OAT module is absent; response sheet points to literal letters. No jobs or tests run (docs-only transfer).
- T3: `git diff --cached --check` passed; exact changed paths from `d8d0c2c` contained docs, the ODD ledger and Engram only. Fresh `git fetch origin dtw_discreto` confirmed remote ancestor before push. Non-force push advanced `origin/dtw_discreto` from `d8d0c2c` to `0209110`; `ls-remote` returned full `0209110e56d494491d98e39060b3969ea7bbc418`, and target worktree was clean. Full test suite and Slurm jobs skipped (documentation/memory-only handoff; user owns jobs). The original unknown reset actor remains unexplained; the retried transfer was explicitly approved and verified clean beforehand.

## Next step
Next: in `dtw_discreto`, the user reviews `HALLAZGOS_OAT.md`, aligns effective run configuration with paper settings and chooses the next full-experiment campaign. Source OAT code, raw results and dirty changes remain untouched.
