"""
LB2 MKP Framework
==================
Framework extensible de metaheurísticas para resolver el
Multidimensional Knapsack Problem (MKP) con detección de
estancamiento basada en DTW y autoconfiguración de parámetros.
"""

__version__ = "0.1.0"



from lb2.instances import load_mkp_instances
from lb2.metaheuristics import BinaryPSO
from lb2.strategies import RuinRecreateStrategy
from lb2.engine import OptimizationEngine, RunConfig

# 1. Cargar un problema
instances = load_mkp_instances("mknapcb1")
problem = instances[9]

# 2. Armar el engine
engine = OptimizationEngine(
    metaheuristic=BinaryPSO(num_particles=20),
    strategies=[RuinRecreateStrategy(ruin_rate=0.3)],
)

# 3. Ejecutar
result = engine.run(problem, RunConfig(epochs=3, iterations_per_epoch=50, seed=42))
