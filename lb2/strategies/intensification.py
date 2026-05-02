"""Estrategia de Intensificación (V1 del notebook).

Exploración local de vecindario: flip de 1 o 2 bits para
buscar mejoras incrementales alrededor de la mejor solución.
"""

from __future__ import annotations

import numpy as np

from lb2.core.problem import MKPInstance
from lb2.core.repair import repair_solution
from lb2.core.solution import Solution
from lb2.strategies.base import StagnationStrategy


class IntensificationStrategy(StagnationStrategy):
    """Búsqueda local por flip de bits (intensificación).

    Recorre todos los bits y prueba flips de 1 y 2 bits,
    aceptando la primera mejora (first improvement).
    """

    @property
    def name(self) -> str:
        return "Intensification"

    def apply(self, best: Solution, problem: MKPInstance) -> Solution:
        """Aplica búsqueda local de vecindario 1-flip y 2-flip."""
        current = best.copy()
        n = problem.n

        # 1-flip
        for i in range(n):
            neighbor = current.vector.copy()
            neighbor[i] = 1 - neighbor[i]
            repaired, fitness = repair_solution(neighbor, problem)
            if fitness > current.fitness:
                current = Solution(vector=repaired, fitness=fitness, feasible=True)

        # 2-flip
        for i in range(n):
            for j in range(i + 1, min(i + 10, n)):
                neighbor = current.vector.copy()
                neighbor[i] = 1 - neighbor[i]
                neighbor[j] = 1 - neighbor[j]
                repaired, fitness = repair_solution(neighbor, problem)
                if fitness > current.fitness:
                    current = Solution(vector=repaired, fitness=fitness, feasible=True)

        return current
