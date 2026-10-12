# Minimal MDPI formatting follow-up

## Scope and completed tasks
User requires actual simple editorial formatting or explicit acceptance, concise English %J.V.: replies and truthful realizado labels. Preserve59 original MDPI comments/author notes, scientific data, labels and unrelated edits. No broad reinstatement of reverted changes.
- [x] T1 delegated worker: ID4 keyword lowercase; ID9 three independent paragraph boundaries/revised reply; ID11 two prose italic wrappers removed; ID12 monospace-retention reply. Only Markdown responses4/9/11/12/21/31/32/41 changed. Multi-file/preparation trigger.
- [x] T2 independent verifier: Exact backup diff whitelist/invariants, external clean builds and affected-page visual checks passed.
- [x] T3 parent: Candidate hash/comments/replies/tags spot check passed; report actual formatting, accepts and pending.

## Backup and source evidence
Exact pre-write copies+manifest at C:/Users/joche/AppData/Local/Temp/mdpi-simple-format-backup-s0lf2yf0/.
TeX before e9146b5226891aea5ee85ac549d8bf9c2bb877c88ddcfa4b980b85f7a5c596cb; after cd6ad78f266be70d97c7bb22d38a2f826d587cbe94165a3a85d0733995c8fd56.
Markdown before eb67e48a5521b5607550f1ff69c9e69cc74952dbf4e866042ac8552ed16b0c76; after35582aa686276df7bebb5b3d9a45ea5a48cbe9efd3f8c0d8cf2d4796c2dd8f9f.
Diff: TeX+10/-4, Markdown+8/-8. Exact reversible patch;59 complete MDPI comments/order, numeric tokens, labels/refs/citations/noindent preserved.32 standalone replies and32 realizado tags. IDs21/31/32/41 remain pending, not falsely completed.

## Functional verification
No meaningful RED/GREEN for editorial formatting; exact diff/structural/build checks used. MiKTeX latexmk -pdf -interaction=nonstopmode -halt-on-error -no-shell-escape with MIKTEX_ENABLE_INSTALLER=0 and unique external jobnames: baseline exit0/43pages, clean current exit0/44pages. Source patch causes one-page reflow. Default jobname read stale cwd aux and showed of43; clean current uses only external aux and correctly shows of44. No source/class pagination repairs performed.
PDF C:/Users/joche/AppData/Local/Temp/mdpi-independent-verify-mf_xx9zh/clean-current/verified-current.pdf.
Visual pages1/5/7/8/9/11: lowercase keyword,3 normal indents,upright shape+PUCV,monospace identifiers,nearby tables/figure intact. Targeted only, not full audit.
Baseline/current warning families/counts same: duplicate labels,18 PDF-string tokens,27 duplicate destinations,7 underfull boxes,1 PDF page-group warning; headheight warnings43→44 track page count; no overfull boxes. Shell-escape-disabled warning present.2401 existing non-Git files unchanged during verification. Parent repeated hash/comment/tag check PASS.

## Delivery and next step
Native assess unassessable/inspect blocked by unrelated nested repo, no authority mutation; functional verification not native approval. No new commit/push authorized/performed; forecast<100 changed lines,ask-on-risk.32 of59 replied/applied or accepted,27 remain. User reviews this minimal patch and remaining requests before further changes.
