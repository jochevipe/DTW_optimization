"""Estrategia Ruin & Recreate (V8 del notebook — más performante).

Destruye parcialmente la solución actual y la reconstruye con
un criterio greedy de densidad. Es la estrategia que dio los
mejores resultados (+1,112 pts) en el benchmark original.
"""

from __future__ import annotations

import random

import numpy as np

from lb2.core.problem import MKPInstance
from lb2.core.repair import repair_solution
from lb2.core.solution import Solution
from lb2.strategies.base import StagnationStrategy


class RuinRecreateStrategy(StagnationStrategy):
    """Ruin & Recreate.

    Attrs:
        ruin_rate: Fracción de items activos a "arruinar" (0-1).
    """

    def __init__(self, ruin_rate: float = 0.3) -> None:
        self.ruin_rate = ruin_rate

    @property
    def name(self) -> str:
        return "Ruin & Recreate"

    def apply(self, best: Solution, problem: MKPInstance) -> Solution:
        """Arruina y reconstruye la solución."""
        vec = best.vector.copy()
        n = problem.n

        # Fase RUIN: desactivar un % de los items activos
        active_indices = np.where(vec == 1)[0]
        num_ruin = max(1, int(self.ruin_rate * len(active_indices)))
        ruin_indices = random.sample(list(active_indices), min(num_ruin, len(active_indices)))
        for idx in ruin_indices:
            vec[idx] = 0

        # Fase RECREATE: reparar (que incluye la fase ADD greedy)
        repaired, fitness = repair_solution(vec, problem)

        if fitness > best.fitness:
            return Solution(vector=repaired, fitness=fitness, feasible=True)
        return best.copy()
