# Round 1 — Preguntas y respuestas a revisores

Documento de trabajo para preparar la respuesta a la revisión mayor. Fuente de este esquema: [`SINTESIS_REVIEWS.md`](SINTESIS_REVIEWS.md), sección 2. Las cartas literales están disponibles en `Reviewer 1.md`, `Reviewer 2.md` y `Reviewer 3.md` de esta carpeta: **cotejar cada respuesta con esos textos antes de enviarla**. Los 19 puntos se ordenan por revisor e identificador; las preguntas son reformulaciones de la síntesis, no citas textuales. Hay comentarios que originalmente son solicitudes o críticas, no preguntas literales. Conservar cada ID por separado aunque varios puntos se solapen.

## Preguntas y solicitudes

### Revisor 1

1. Lack of statistical evidence for the main claim. The main result of the paper, that Binary-Complex is the superior method, is based on a globally non-significant Friedman test (χ² = 4.13, p = 0.2474). While the difference between the mean ranks (2.22 and 2.83 for the worst baseline method) is real, it is quite small, and the authors admit themselves that the ranking must be understood as a "favorable tendency," not proof of the superiority. This is the greatest weakness of the paper because it directly contradicts the selling point of the research.
2. No comparison with existing adaptive control systems.
3. Narrow set of experiments. Everything takes place on the Multidimensional Knapsack Problem only; moreover, only the first problem of every of the nine Chu–Beasley group is selected.
4. Absence of a study of sensitivity to hyperparameters. The important design decisions such as the length of the window (W=200), width of the Sakoe-Chiba band, thresholds of percentiles (40th/60th), persistence factor (τ_pat=3) and improvement threshold (π_max=5) are all fixed beforehand without any examination of the influence of their change.

5. Inconsistency of effects across algorithms.

### Revisor 2

1. The organization of this paper needs to be given at the end of section 1. Each section should be briefly described.
2. The central methodological component of the paper is DDTW. However, there is no sufficiently convincing ablation study demonstrating that DDTW itself is responsible for the observed improvements.
3. The proposed method uses a linear reference trajectory for sustained progress and a constant trajectory for stagnation. The reference slope is fixed. However, the manuscript does not sufficiently explain why these two patterns are adequate to characterize the highly diverse search dynamics of BPSO, GA, BGWO, and BDE.
4. The experimental comparison with existing state-of-the-art methods is insufficient. The authors should include representative state-of-the-art adaptive methods as additional baselines. Otherwise, it is difficult to determine whether the proposed DDTW controller provides a meaningful improvement over existing adaptive parameter-control techniques or merely over two manually selected fixed configurations.
5. The manuscript provides the main algorithmic procedure and experimental settings, which is positive. However, for a trajectory-based adaptive method, reproducibility requires more detailed implementation information. If possible, the authors had better provide a public code to improve the reproducibility and verifiability.
6. Abstract needs to be corrected from the first sentence.

### Revisor 3

1. Define the research gap and explain how the proposed method differs from existing adaptive parameter-control and hyper-heuristic approaches.
2. Strengthen the literature review, particularly regarding adaptive parameter control, reinforcement learning, fuzzy control, and trajectory-based search analysis.
3. Provide a complete mathematical definition of DDTW, including derivative calculation, distance normalization, and boundary handling.
4. Include representative plots showing fitness trajectories, DDTW distances, thresholds, and controller states.
5. Clarify how the exploration and exploitation parameter values were selected and whether they were tuned specifically for the tested instances.
6. Provide a complete pseudocode algorithm.
7. The results indicate that the adaptive controller is more beneficial for some algorithms, especially BDE and GA, while the improvements for BPSO and BGWO are less consistent. The authors should analyze why the controller interacts differently with each algorithm. Differences in population dynamics, parameter sensitivity, repair effects, and exploration mechanisms may explain this behavior.
8. The manuscript would be significantly clearer if it included plots showing:
the best-so-far fitness trajectory;
the progress and plateau reference trajectories;
DR(t), DC(t), and Delta ti​;
the controller state over time;
the corresponding parameter switches.

## Respuestas

Completar cada entrada con la respuesta al revisor, el cambio verificable en el manuscrito (sección/figura/tabla) y la evidencia experimental correspondiente. No presentar propuestas de `SINTESIS_REVIEWS.md` como resultados ya obtenidos; verificar configuraciones y resultados actuales antes de afirmarlos.

### Revisor 1

- **R1.1:** Pendiente.
- **R1.2:** Pendiente.
- **R1.3:** Pendiente.
- **R1.4:** Pendiente.
- **R1.5:** Pendiente.

### Revisor 2

- **R2.1:** Pendiente.
- **R2.2:** Pendiente.
- **R2.3:** Pendiente.
- **R2.4:** Pendiente.
- **R2.5:** Pendiente.
- **R2.6:** Pendiente.

### Revisor 3

- **R3.1:** Pendiente.
- **R3.2:** Pendiente.
- **R3.3:** Pendiente.
- **R3.4:** Pendiente.
- **R3.5:** Pendiente.
- **R3.6:** Pendiente.
- **R3.7:** Pendiente.
- **R3.8:** Pendiente.
