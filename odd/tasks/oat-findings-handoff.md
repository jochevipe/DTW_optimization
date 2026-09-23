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
- [ ] T2: Transfer the exact selected documentation and project Engram chunks into an isolated `dtw_discreto` worktree, preserving its reviewer letters and other work. Check: no code, raw results or deletions in target diff. Route: delegated multi-file writer.
- [ ] T3: Verify target diff and branch freshness, commit reviewable work unit(s), and push only `dtw_discreto` to `origin`. Check: remote points at produced commit; report any skipped checks and blocker. Route: parent Git coordination and delegated read-only verification where needed.

## Progress and evidence
- Baseline: `OAT` at a291028 with local modifications; `dtw_discreto` at d8d0c2c; branches diverge. Original reviewer letters are present on `dtw_discreto`, absent from `OAT`.
- OAT audit: two campaigns each contain 19 configs, 228/228 expected MH JSON, 31 finite fitness values per JSON (7068/7068). No Slurm execution performed.
- T1: readback of 19 configs, 228 JSON/7068 finite fitness values per campaign and all six Δ ranges against existing `tabla_oat.md` completed; `git diff --cached --check` passed; commit `af127d5`. No experiment jobs or test suite run (documentation only).
- T2: blocked. Isolated `dtw_discreto` worktree was created clean at `d8d0c2c`; delegated writer observed a transient modified/untracked state followed by clean status and wrote nothing. The target reflog records `reset: moving to HEAD` shortly after worktree creation. The actor and scope are unknown. Source OAT documents and memory chunks remain present. No safe transfer or target commit can be claimed.
- T3: pending; do not push while T2 is blocked.

## Next step
Stop target writes and publication until the unexpected worktree reset and transient changes are understood; request a fresh human decision on whether to resume after the destination is stable or cancel the transfer.
