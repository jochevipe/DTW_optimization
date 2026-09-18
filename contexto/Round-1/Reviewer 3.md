||Yes|Can be improved|Must be improved|Not applicable|
|---|---|---|---|---|
|Does the introduction provide sufficient background and include all relevant references?|( )|(x)|( )|( )|
|Is the research design appropriate?|( )|(x)|( )|( )|
|Are the methods adequately described?|( )|(x)|( )|( )|
|Are the results clearly presented?|( )|(x)|( )|( )|
|Are the conclusions supported by the results?|( )|(x)|( )|( )|
|Are all figures and tables clear and well-presented?|( )|(x)|( )|( )|

Comments and Suggestions for Authors

The manuscript proposes a trajectory-based adaptive mechanism that uses DDTW to identify progress and stagnation patterns and switch between exploration- and exploitation-oriented parameter configurations. The topic is relevant, and the proposed framework is potentially useful. However, the current manuscript requires further methodological clarification and stronger experimental validation.

My comments:

1. Define the research gap and explain how the proposed method differs from existing adaptive parameter-control and hyper-heuristic approaches.
2. Strengthen the literature review, particularly regarding adaptive parameter control, reinforcement learning, fuzzy control, and trajectory-based search analysis.
3. Provide a complete mathematical definition of DDTW, including derivative calculation, distance normalization, and boundary handling.
4. Include representative plots showing fitness trajectories, DDTW distances, thresholds, and controller states.
5. Clarify how the exploration and exploitation parameter values were selected and whether they were tuned specifically for the tested instances.
6. Provide a complete pseudocode algorithm.
7. The results indicate that the adaptive controller is more beneficial for some algorithms, especially BDE and GA, while the improvements for BPSO and BGWO are less consistent. The authors should analyze why the controller interacts differently with each algorithm. Differences in population dynamics, parameter sensitivity, repair effects, and exploration mechanisms may explain this behavior.
8. The manuscript would be significantly clearer if it included plots showing:
- the best-so-far fitness trajectory;
- the progress and plateau reference trajectories;
- DR(t), DC(t), and Delta ti;
- the controller state over time;
- the corresponding parameter switches.