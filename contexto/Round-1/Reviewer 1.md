||Yes|Can be improved|Must be improved|Not applicable|
|---|---|---|---|---|
|Does the introduction provide sufficient background and include all relevant references?|(x)|( )|( )|( )|
|Is the research design appropriate?|(x)|( )|( )|( )|
|Are the methods adequately described?|(x)|( )|( )|( )|
|Are the results clearly presented?|( )|(x)|( )|( )|
|Are the conclusions supported by the results?|( )|(x)|( )|( )|
|Are all figures and tables clear and well-presented?|(x)|( )|( )|( )|


Comments and Suggestions for Authors

1. Lack of statistical evidence for the main claim. The main result of the paper, that Binary-Complex is the superior method, is based on a globally non-significant Friedman test (χ² = 4.13, p = 0.2474). While the difference between the mean ranks (2.22 and 2.83 for the worst baseline method) is real, it is quite small, and the authors admit themselves that the ranking must be understood as a "favorable tendency," not proof of the superiority. This is the greatest weakness of the paper because it directly contradicts the selling point of the research.
2. No comparison with existing adaptive control systems.
3. Narrow set of experiments. Everything takes place on the Multidimensional Knapsack Problem only; moreover, only the first problem of every of the nine Chu–Beasley group is selected.
4. Absence of a study of sensitivity to hyperparameters. The important design decisions such as the length of the window (W=200), width of the Sakoe-Chiba band, thresholds of percentiles (40th/60th), persistence factor (τ_pat=3) and improvement threshold (π_max=5) are all fixed beforehand without any examination of the influence of their change.
5. Inconsistency of effects across algorithms.