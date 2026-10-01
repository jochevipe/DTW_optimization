# Round 1: evidence-bounded final response draft

**NOT READY TO SUBMIT until the blockers listed in the final INTERNAL section are resolved. Not all reviewer requests are fully fulfilled.** This draft describes the current manuscript source and the available evidence, not a successfully rendered or fully reproducible submission.

We thank the reviewers for their constructive comments. Below we distinguish completed source revisions from requests that remain unresolved. The numbered reviewer requests are quoted faithfully from `b4f9ccc:contexto/Round-1/REVIEWER_1.md`, `REVIEWER_2.md`, and `REVIEWER_3.md` (5, 6, and 8 items respectively). Historical numerical statements in those comments refer to the original submission, not the expanded manuscript. Locations refer to `paper/MDPi__Search_Trajectory_Patterns_as_Feedback_for_Adaptive_Metaheuristic_Configuration_Control (1)/template.tex`; labels identify source locations, not validated PDF pages.

## Reviewer 1

### R1.1
**Reviewer request (verbatim):**
> Lack of statistical evidence for the main claim. The main result of the paper, that Binary-Complex is the superior method, is based on a globally non-significant Friedman test (χ² = 4.13, p = 0.2474). While the difference between the mean ranks (2.22 and 2.83 for the worst baseline method) is real, it is quite small, and the authors admit themselves that the ranking must be understood as a "favorable tendency," not proof of the superiority. This is the greatest weakness of the paper because it directly contradicts the selling point of the research.

**Response:** Thank you for identifying this central limitation. The expanded manuscript now reports 27 MKP instances, giving 108 metaheuristic-instance conditions, rather than the original nine-instance evaluation. Binary-Complex's mean rank is 2.13, followed by Binary-Simple (2.39), Vanilla-Exploration (2.56), and Vanilla-Exploitation (2.93). The manuscript reports Friedman χ²=21.64 and p=7.73×10⁻⁵. The audit reconciled the mean ranks and statistic arithmetic with the stored fitness data; this Friedman p-value is reported from the manuscript, not independently recalculated.

The source now separates global Bonferroni-Dunn comparisons from 324 unadjusted, exploratory Wilcoxon comparisons. The rank-based adjusted p-values reconcile arithmetically: 0.4200 against Binary-Simple, 0.0460 against Vanilla-Exploration, and 1.75×10⁻⁵ against Vanilla-Exploitation. The local counts and directions reconcile with stored results, but the Wilcoxon inferential p-values were not independently recomputed. These checks do not establish the validity of treating potentially correlated algorithm-instance blocks as independent, or justify choosing the best-observed strategy as post-hoc control. Those design questions remain unresolved. We therefore do not interpret the ranking as universal superiority or as an isolated effect of DDTW, and cannot regard this concern as fully closed.

**Manuscript location:** Abstract (unlabelled); Statistical Analysis (`subsec:statistical_analysis`), Tables `tab:wilcoxon_tests`, `tab:friedman_ranking`, `tab:bonferroni_posthoc_all`; Conclusions (`sec:conclusions`).

### R1.2
**Reviewer request (verbatim):**
> No comparison with existing adaptive control systems.

**Response:** We agree. The evaluated comparators remain two fixed profiles and the two proposed DDTW-based controllers. Published MKP results discussed in the manuscript provide context only, since budgets, metrics, and instance correspondence differ. They are not a matched evaluation of representative external adaptive controllers. This requested comparison remains unresolved, and the results do not establish an advantage over existing adaptive control systems.

**Manuscript location:** Metaheuristic Configurations (`sec:mh_config`); Results (`sec:results`) and Solution Quality (`subsec:solution_quality`), contextual MFSS and LBLP/QPSO discussion; Introduction (unlabelled), scope clarification before the contributions.

### R1.3
**Reviewer request (verbatim):**
> Narrow set of experiments. Everything takes place on the Multidimensional Knapsack Problem only; moreover, only the first problem of every of the nine Chu–Beasley group is selected.

**Response:** The evaluation has been expanded to three instances per benchmark group, using deterministic zero-based indices 0, 15, and 29 across all nine groups. The manuscript now covers 27 MKP instances, 432 conditions, and 13,392 runs. The audit confirmed 31 finite fitness values per condition and reconciled all 432 solution-quality rows with the stored arrays. This addresses the single-instance-per-group restriction, but not the restriction to one problem domain. The selection is neither random nor exhaustive, and we make no cross-domain generalization claim.

**Manuscript location:** Benchmark Instances (`sec:instances`), Table `tab:instances`; Experimental Protocol (`sec:protocol`); Table `tab:gap_all_instances`; supplementary tables (`sec:appendix_tables`); Limitations (`subsec:limitations`).

### R1.4
**Reviewer request (verbatim):**
> Absence of a study of sensitivity to hyperparameters. The important design decisions such as the length of the window (W=200), width of the Sakoe-Chiba band, thresholds of percentiles (40th/60th), persistence factor (τ_pat=3) and improvement threshold (π_max=5) are all fixed beforehand without any examination of the influence of their change.

**Response:** The source now includes a bounded OAT sensitivity section covering the window, band, lower and upper percentiles, plateau limit, and persistence, with three alternatives per factor and one common base. It describes separate Binary-Simple and Binary-Complex campaigns on mknapcb1[0,15,29], with four algorithms and 31 runs per condition. The historical summary records 19 configurations and 228 files per strategy, with 7,068 finite fitness values per campaign. Its reported ranges and counts agree with the manuscript, but these are secondary records: the primary OAT JSON files were unavailable to the current audit, so we cannot independently certify those campaign claims.

The reported signed mean-fitness ranges are descriptive, not uncertainty intervals or evidence of robust or optimal settings. The source explicitly excludes slope variation, parameter interactions, and the other eight MKP groups, and explains that several settings do not enter Binary-Simple's rule. The fixed reference slope remains 2.0. A sensitivity section has therefore been added, but primary-data verification and inferential uncertainty remain unresolved.

**Manuscript location:** Controller parameters (`sec:dtw_config`), Table `tab:dtw_params`; OAT Sensitivity Analysis (`subsec:oat_sensitivity`), Table `tab:oat_sensitivity`; plateau-score identity (`eq:plateau_score_identity`); Limitations (`subsec:limitations`).

### R1.5
**Reviewer request (verbatim):**
> Inconsistency of effects across algorithms.

**Response:** We agree that this variation must be explicit rather than obscured by global ranks. The expanded source reports equal-instance average gaps separately by algorithm. For BDE, Binary-Simple and Binary-Complex yield 0.75% and 0.77%, versus 0.94% for fixed exploration and 1.51% for fixed exploitation. For GA, fixed exploitation remains stronger on average (0.41%) than Binary-Complex (0.52%). BPSO favors fixed exploration (1.64%, versus 1.72% for Binary-Complex), while BGWO's gaps remain close (2.73% to 2.79%). Controller-activity and runtime summaries are also algorithm-specific. These observations support heterogeneous effects, not a guarantee of improvement or a demonstrated causal explanation.

**Manuscript location:** Solution Quality (`subsec:solution_quality`), Table `tab:gap_all_instances`; Statistical Analysis (`subsec:statistical_analysis`); Computational Overhead (`subsec:computational_time`); Adaptive Controller Behavior (`subsec:controller_behavior`); Conclusions (`sec:conclusions`).

## Reviewer 2

### R2.1
**Reviewer request (verbatim):**
> The organization of this paper needs to be given at the end of section 1. Each section should be briefly described.

**Response:** A roadmap paragraph is now present at the end of the Introduction, describing Proposed Approach, Experimental Setup, Results, and Conclusions and Future Work. Thank you for this navigation suggestion. The revision is only partial: the paragraph does not briefly describe Related Work or Background, so it does not yet meet the request to cover each section.

**Manuscript location:** Introduction (unlabelled), final paragraph before Related Work; roadmap references `sec:proposed_approach`, `sec:experimental_setup`, `sec:results`, and `sec:conclusions`.

### R2.2
**Reviewer request (verbatim):**
> The central methodological component of the paper is DDTW. However, there is no sufficiently convincing ablation study demonstrating that DDTW itself is responsible for the observed improvements.

**Response:** We agree. Both Binary-Simple and Binary-Complex use DDTW, so their comparison tests differences in controller logic, not removal of DDTW. The fixed baselines also do not isolate DDTW from switching and temporal confirmation. The new plateau-score identity clarifies that Binary-Simple's constant-reference score reduces to cumulative window progress for a nondecreasing best-so-far trajectory. This clarification is not an experimental ablation. A matched DDTW-free controller comparison is absent, and this request remains unresolved.

**Manuscript location:** Trajectory analysis (`sec:trajectory_analysis`), Equation `eq:plateau_score_identity`; controller strategies (`sec:adaptation_strategies`); Statistical Analysis (`subsec:statistical_analysis`), final scope qualification.

### R2.3
**Reviewer request (verbatim):**
> The proposed method uses a linear reference trajectory for sustained progress and a constant trajectory for stagnation. The reference slope is fixed. However, the manuscript does not sufficiently explain why these two patterns are adequate to characterize the highly diverse search dynamics of BPSO, GA, BGWO, and BDE.

**Response:** The source now characterizes the ramp and plateau as operational endpoints for sustained and low progress, not an exhaustive model of population dynamics. It specifies that slope 2.0 means two objective-function units per iteration, is not fitted from the current window, and is common across algorithms and instances. First differences remove additive offsets, but not multiplicative rescaling. The explanation also notes that distance histories adapt within a run, not across objective scales. This makes the design rationale and limitations explicit; it does not empirically validate reference adequacy across the four algorithms. Alternative shapes and slope sensitivity have not been established, and the OAT section does not vary the slope.

**Manuscript location:** Reference Trajectory Patterns within `sec:trajectory_analysis`, Equations `eq:ramp_pattern`, `eq:constant_pattern`; OAT Sensitivity Analysis (`subsec:oat_sensitivity`).

### R2.4
**Reviewer request (verbatim):**
> The experimental comparison with existing state-of-the-art methods is insufficient. The authors should include representative state-of-the-art adaptive methods as additional baselines. Otherwise, it is difficult to determine whether the proposed DDTW controller provides a meaningful improvement over existing adaptive parameter-control techniques or merely over two manually selected fixed configurations.

**Response:** We agree with this distinction. No representative external adaptive state-of-the-art method has been evaluated under the same protocol. The MFSS and LBLP/QPSO discussions explicitly acknowledge incompatible evaluation settings and are contextual rather than comparative evidence. Neither those published values nor the Binary-Simple comparison fulfills the requested adaptive baseline evaluation. The evidence is limited to the tested fixed profiles and proposed controllers; this request remains unresolved.

**Manuscript location:** Metaheuristic Configurations (`sec:mh_config`); contextual comparisons in Results (`sec:results`) and Solution Quality (`subsec:solution_quality`); Introduction (unlabelled), contribution-scope clarification.

### R2.5
**Reviewer request (verbatim):**
> The manuscript provides the main algorithmic procedure and experimental settings, which is positive. However, for a trajectory-based adaptive method, reproducibility requires more detailed implementation information. If possible, the authors had better provide a public code to improve the reproducibility and verifiability.

**Response:** The source now specifies first differences, local absolute cost, raw accumulated distances, band handling, warm-up, percentile history, state timing, and switching rules. Its reproduction section describes seeds 1 through 31 and serialization by run index, and distinguishes in-memory histories from saved aggregate results. The audited main-campaign metadata agree with N=20, T=2000, W=200, band=2, slope=2.0, percentiles 40/60, plateau limit=5, and patience=3. Seed correspondence is described in the protocol, not independently certified by explicit seed arrays in the saved files.

The data-availability statement names a development repository but does not identify a permanently archived release of the full code and data. Public accessibility and release completeness have not been confirmed. The saved files omit full temporal histories, explicit seeds, and a source commit hash. Moreover, the source reference to executable reproduction commands points to `sec:appendix_reproduction`, which is explicitly missing from the current worktree. We therefore report expanded implementation documentation, not a validated executable appendix or complete public reproducibility package. This request remains partially addressed.

**Manuscript location:** Background, DTW/DDTW subsection (unlabelled), Equations `eq:dtw_local_cost`, `eq:first_difference`; `sec:trajectory_analysis`; Algorithms `alg:run`, `alg:monitor`; Implementation and Reproduction Details (`subsec:reproduction`); `sec:appendix_reproduction` (explicitly missing); data-availability statement (unlabelled).

### R2.6
**Reviewer request (verbatim):**
> Abstract needs to be corrected from the first sentence.

**Response:** Thank you. The abstract now opens with the complete sentence, “Adaptive decisions are often based on algorithm-specific feedback or simple indicators that provide limited information about the evolving search dynamics.” It also reflects the expanded 27-instance evaluation and algorithm-dependent effects rather than the earlier nine-instance result. Its inferential statements remain subject to the statistical-design qualifications described in R1.1.

**Manuscript location:** Abstract (unlabelled, `\abstract{...}`).

## Reviewer 3

### R3.1
**Reviewer request (verbatim):**
> Define the research gap and explain how the proposed method differs from existing adaptive parameter-control and hyper-heuristic approaches.

**Response:** The Introduction now explicitly frames the study as trajectory-pattern feedback for switching between prescribed configurations, rather than independent updates of individual parameters. It also states that this scope does not establish an advantage over adaptive parameter-control or hyper-heuristic methods. Related Work discusses successful-parameter histories, population-state signals, and learning-based adaptation. However, the direct, reference-supported contrast with hyper-heuristics remains incomplete. The added scope clarification partially addresses the request, but is not a completed comparative research-gap argument or proof of novelty.

**Manuscript location:** Introduction (unlabelled), paragraph immediately before the contributions; Related Work (unlabelled); framework (`sec:framework_arch`).

### R3.2
**Reviewer request (verbatim):**
> Strengthen the literature review, particularly regarding adaptive parameter control, reinforcement learning, fuzzy control, and trajectory-based search analysis.

**Response:** We agree that a critical comparison across these lines is needed. The current Related Work discusses JADE, SHADE, evolutionary-state estimation, reinforcement-learning-based PSO adaptation, population signals, and stagnation indicators; Background introduces DTW/DDTW. These existing discussions do not constitute a complete treatment of fuzzy control or hyper-heuristics, or a sufficiently developed contrast with trajectory-based search analysis. We cannot claim that the requested literature extension has been completed or that additional references have been added where none are observed. This request remains partially addressed.

**Manuscript location:** Related Work (unlabelled); Background, DTW/DDTW subsection (unlabelled); trajectory-analysis formulation (`sec:trajectory_analysis`).

### R3.3
**Reviewer request (verbatim):**
> Provide a complete mathematical definition of DDTW, including derivative calculation, distance normalization, and boundary handling.

**Response:** The source now defines the evaluated first-difference representation, with zero at the first sample and backward difference at the final sample, preserving sequence length. It distinguishes this estimator from the original smoothed DDTW derivative. The DTW recurrence retains zero at the origin and infinite first-row/first-column boundaries; the local cost is now explicitly absolute difference. The returned value is the raw accumulated endpoint cost, with no square root, path-length division, or amplitude normalization. Band handling uses max(w,|n−m|) to retain endpoint reachability. The source also distinguishes band-limited recurrence evaluations from full-matrix allocation and initialization. These are observed mathematical source clarifications, not a new numerical rerun or rendered validation.

**Manuscript location:** Background, DTW/DDTW subsection (unlabelled), Equations `eq:dtw_local_cost`, `eq:first_difference`; trajectory signals (`eq:ddtw_distances`, `eq:trajectory_delta`); monitor pseudocode (`alg:monitor`).

### R3.4
**Reviewer request (verbatim):**
> Include representative plots showing fitness trajectories, DDTW distances, thresholds, and controller states.

**Response:** Convergence figure blocks and captions are now present for Binary-Simple and Binary-Complex on three benchmark groups, with indices 0, 15, and 29. For each algorithm, variant, and instance, the selected trajectory is the best-final-fitness run among 31, not an average or typical run. The selection is limited to three groups for space and readability; tables and statistical summaries cover all 27 instances. Additional fitness convergence plots can be prepared upon request, which would extend the illustrations, not establish new controller diagnostics.

These fitness illustrations and aggregate transition counts do not show synchronized DDTW distances, thresholds, and states. The source figure additions have not been rendered successfully in this audit, and their referenced paths require repair before submission. Full temporal diagnostic histories are absent from the saved aggregate campaign files. This request is therefore only partially addressed, with no claim that the requested diagnostic plots are complete.

**Manuscript location:** Solution Quality (`subsec:solution_quality`), Figures `fig:convergence_mknapcb1_binary_simple`, `fig:convergence_mknapcb1_binary_complex`; convergence appendix (`subsec:appendix_convergence_trajectories`); controller counts (`subsec:controller_behavior`, `fig:dtw_activations`); persistence limits (`subsec:reproduction`).

### R3.5
**Reviewer request (verbatim):**
> Clarify how the exploration and exploitation parameter values were selected and whether they were tuned specifically for the tested instances.

**Response:** The configuration discussion now explains the intended directions of parameter changes for each algorithm and identifies the numerical profiles as prescribed constants, unchanged across the evaluated instances. It says that the cited literature motivates parameter roles and change directions, not optimal numerical values for MKP; no systematic profile search or separate training/validation phase is reported. This clarifies the documented experimental design. It does not establish the historical provenance of profile selection or rule out earlier instance-informed tuning without author confirmation. That part of the request remains unresolved, and the OAT monitor study is not a tuning study of these algorithm profiles.

**Manuscript location:** Metaheuristic Configurations (`sec:mh_config`), Table `tab:mh_params` and following profile-selection discussion; OAT Sensitivity Analysis (`subsec:oat_sensitivity`).

### R3.6
**Reviewer request (verbatim):**
> Provide a complete pseudocode algorithm.

**Response:** The source now contains two explicit algorithms: a single-run procedure and a monitor update. They specify initialization, applied-mode recording, observation-then-decision timing, warm-up, reference construction, first differences, DTW recurrence, history updates, linear percentiles, initial thresholds, no-improvement counting, persistence, and next-iteration profile selection. The single-run procedure distinguishes transitions into exploration from other mode changes and separates in-memory histories from serialized outputs. This is a substantial source-level expansion of the earlier high-level pseudocode. It does not imply that the missing executable reproduction appendix exists or that the document has passed rendered validation.

**Manuscript location:** Experimental Protocol (`sec:protocol`), Algorithms `alg:run`, `alg:monitor`; switching rules (`eq:binary_simple`, `eq:binary_complex`); Implementation and Reproduction Details (`subsec:reproduction`).

### R3.7
**Reviewer request (verbatim):**
> The results indicate that the adaptive controller is more beneficial for some algorithms, especially BDE and GA, while the improvements for BPSO and BGWO are less consistent. The authors should analyze why the controller interacts differently with each algorithm. Differences in population dynamics, parameter sensitivity, repair effects, and exploration mechanisms may explain this behavior.

**Response:** The expanded analysis distinguishes improvement over a weak profile from improvement over the strongest fixed profile. BDE benefits relative to both fixed profiles on average, while GA's Binary-Complex average gap remains above fixed exploitation. BPSO favors fixed exploration, and BGWO shows small differences. The source also reports different transition activity under the same monitor settings: Binary-Simple/Complex mean counts are 3.65/4.80 for BPSO, 1.43/1.21 for GA, 2.12/1.51 for BGWO, and 3.71/7.19 for BDE. More switches are not inherently better, as BDE's slightly lower average gap occurs with Binary-Simple.

These descriptive associations sharpen the algorithm-specific account, but do not identify why the interactions occur. Population dynamics, parameter sensitivity, repair, and exploration mechanisms remain plausible explanations rather than measured causal effects. Without synchronized traces or targeted controls, the requested mechanistic analysis is not fully fulfilled.

**Manuscript location:** Solution Quality (`subsec:solution_quality`), Table `tab:gap_all_instances`; Adaptive Controller Behavior (`subsec:controller_behavior`); Conclusions (`sec:conclusions`); Limitations (`subsec:limitations`).

### R3.8
**Reviewer request (verbatim):**
> The manuscript would be significantly clearer if it included plots showing:
> - the best-so-far fitness trajectory;
> - the progress and plateau reference trajectories;
> - DR(t), DC(t), and Delta ti;
> - the controller state over time;
> - the corresponding parameter switches.

**Response:** We agree that these signals need to be shown together for the same run to make the decision process inspectable. The source adds selected best-so-far fitness illustrations and defines the progress/plateau references, D_R(t), D_C(t), Δ_t, thresholds, and switching rules mathematically. It does not provide a synchronized plot containing the reference trajectories, distances, controller state, and corresponding parameter switches. Aggregate transition bars cannot substitute for that temporal view, and best-of-31 fitness curves are not representative controller-state diagnostics. The missing persisted histories and unresolved figure paths also prevent a claim of complete visual validation. This request remains partially addressed; the additional fitness plots offered upon request would not by themselves fulfill it.

**Manuscript location:** Selected-run figures `fig:convergence_mknapcb1_binary_simple`, `fig:convergence_mknapcb1_binary_complex`; appendix `subsec:appendix_convergence_trajectories`; references and signals (`eq:ramp_pattern`, `eq:constant_pattern`, `eq:ddtw_distances`, `eq:trajectory_delta`); controller rules (`sec:adaptation_strategies`); saved-history limitations (`subsec:reproduction`).

---

## INTERNAL: preparación y límites de evidencia (no enviar)

### Bloqueadores de envío
- **Estructura y renderizado:** 7 de las 8 rutas gráficas activas no existen donde las referencia el manuscrito. Los seis PDF compuestos de convergencia existen en `results/figuras/convergencia_vertical`, pero eso no valida las rutas `figures/` ni un PDF renderizado. La etiqueta `sec:appendix_reproduction` está explícitamente ausente porque el apéndice fue retirado del worktree. La auditoría previa informó que `lastpage.sty` no está disponible. No se ejecutaron compilaciones en esta tarea ni se corrigió el manuscrito.
- **Inferencia:** la aritmética de rangos, estadístico Friedman y post-hoc no demuestra validez del diseño. Falta justificar dependencia entre bloques y elección de Binary-Complex como control por ser el mejor observado. El p de Friedman se cita como reportado; los p de Wilcoxon no se recalcularon independientemente. Resolver estas limitaciones antes de sostener inferencias definitivas en la carta y el abstract.
- **OAT:** no están disponibles los JSON primarios en el árbol actual ni entre los archivos rastreados de OAT. `git show OAT:contexto/Round-1/HALLAZGOS_OAT.md` y `SENSIBILIDAD_OAT.md` son fuentes secundarias. Sus rangos/conteos coinciden con el texto, pero no autorizan la frase de auditoría independiente de las campañas que aún aparece en el manuscrito. No convertir rangos agregados en dispersión ni afirmar robustez.
- **Pedidos no cerrados:** faltan comparador adaptativo externo/SOTA (R1.2, R2.4), ablación sin DDTW (R2.2), diagnósticos temporales completos (R3.4, R3.8), contraste bibliográfico suficiente de fuzzy/hyper-heuristics y trayectorias (R3.1, R3.2), y validación de pendiente/referencias (R2.3). Las aclaraciones no sustituyen esos resultados.
- **Autoría y reproducción:** confirmar selección histórica/tuning de perfiles (R3.5), accesibilidad pública y contenido del release (R2.5). La URL observada no prueba acceso público ni archivo permanente. La persistencia de semillas, commit y trazas sigue incompleta. La hoja de ruta omite Related Work y Background (R2.1).

### Evidencia numérica recibida y alcance
- La auditoría previa del padre verificó 432 JSON, 13.392 fitness finitos, 31 tiempos y conteos por registro, y consistencia de índices, MH, estrategia, N=20 y T=2000. Para adaptativos: W=200, banda=2, pendiente=2, percentiles=40/60, π=5 y paciencia=3. Este writer usa esa evidencia recibida; no repitió experimentos.
- Las 432 filas de calidad reconciliaron best, media, desviación estándar muestral y gap de la media. Los tiempos reconciliaron medias, desviaciones muestrales y ratios por instancia. No confundir gap medio con gap del mejor fitness serializado.
- Rangos reconciliados: Complex=2.1296296, Simple=2.3888889, Explore=2.5555556, Exploit=2.9259259; estadístico Friedman=21.644444. Post-hoc rank-z Bonferroni: Complex vs Simple=0.42004951, vs Explore=0.045999486, vs Exploit=0.00001747879. Esto verifica aritmética, no supuestos inferenciales.
- Las direcciones y conteos de 324 comparaciones Wilcoxon almacenadas reconciliaron. NumPy no estaba disponible para recalcular sus p ni el p de Friedman en la auditoría previa. El p publicado 7.73×10⁻⁵ se mantiene expresamente como reportado, no como recálculo independiente.
- Alcance experimental: 27 instancias de MKP, no múltiples dominios ni 108 problemas independientes. OAT histórico: solo mknapcb1[0,15,29], con pendiente fija. Convergencia: mejor corrida final entre 31 por MH/variante/instancia, tres grupos por legibilidad, sin distancias, umbrales, estados ni parámetros sincronizados.

### Decisión de uso
Esta carta es un borrador final acotado por evidencia, no una certificación de cumplimiento total. El manuscrito actual prevalece sobre los estados viejos de los planes; los tres documentos previos quedan intactos. Antes de enviar, los autores deben resolver o aceptar explícitamente las brechas y reconciliar los claims restantes del manuscrito. No hay autorización implícita para nuevos experimentos, publicación, cambios al paper o promesas de ejecución. Preparar más gráficos FITNESS ante una solicitud no equivale a comprometer una nueva campaña experimental.
