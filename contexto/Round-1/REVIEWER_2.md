||Yes|Can be improved|Must be improved|Not applicable|
|---|---|---|---|---|
|Does the introduction provide sufficient background and include all relevant references?|( )|(x)|( )|( )|
|Is the research design appropriate?|( )|(x)|( )|( )|
|Are the methods adequately described?|( )|(x)|( )|( )|
|Are the results clearly presented?|( )|(x)|( )|( )|
|Are the conclusions supported by the results?|( )|(x)|( )|( )|
|Are all figures and tables clear and well-presented?|(x)|( )|( )|( )|

Comments and Suggestions for Authors

The manuscript proposes a trajectory-driven adaptive configuration-control framework in which Derivative Dynamic Time Warping (DDTW) is used to analyze recent best-so-far fitness trajectories and guide the switching between predefined exploration- and exploitation-oriented configurations. The framework is evaluated using BPSO, GA, BGWO, and BDE on nine Multidimensional Knapsack Problem (MKP) instances. The experimental results indicate that the proposed Binary-Complex strategy can provide improvements in several experimental conditions. The proposed framework is potentially interesting, but several issues need to be addressed. My comments are given as follows:

1. The organization of this paper needs to be given at the end of section 1. Each section should be briefly described.
2. The central methodological component of the paper is DDTW. However, there is no sufficiently convincing ablation study demonstrating that DDTW itself is responsible for the observed improvements.
3. The proposed method uses a linear reference trajectory for sustained progress and a constant trajectory for stagnation. The reference slope is fixed. However, the manuscript does not sufficiently explain why these two patterns are adequate to characterize the highly diverse search dynamics of BPSO, GA, BGWO, and BDE.
4. The experimental comparison with existing state-of-the-art methods is insufficient. The authors should include representative state-of-the-art adaptive methods as additional baselines. Otherwise, it is difficult to determine whether the proposed DDTW controller provides a meaningful improvement over existing adaptive parameter-control techniques or merely over two manually selected fixed configurations.
5. The manuscript provides the main algorithmic procedure and experimental settings, which is positive. However, for a trajectory-based adaptive method, reproducibility requires more detailed implementation information. If possible, the authors had better provide a public code to improve the reproducibility and verifiability.
6. Abstract needs to be corrected from the first sentence.