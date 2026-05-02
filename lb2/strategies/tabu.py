"""Estrategia Tabu Search (V7 del notebook).

Mantiene una lista de movimientos prohibidos (tabú) para
forzar la exploración de regiones no visitadas.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Set

import numpy as np

from lb2.core.problem import MKPInstance
from lb2.core.repair import repair_solution
from lb2.core.solution import Solution
from lb2.strategies.base import StagnationStrategy


class TabuSearchStrategy(StagnationStrategy):
    """Búsqueda Tabú simplificada.

    Attrs:
        max_iters: Iteraciones de la búsqueda tabú.
        tabu_tenure: Duración del tabú (en iteraciones).
    """

    def __init__(self, max_iters: int = 50, tabu_tenure: int = 7) -> None:
        self.max_iters = max_iters
        self.tabu_tenure = tabu_tenure

    @property
    def name(self) -> str:
        return "Tabu Search"

    def apply(self, best: Solution, problem: MKPInstance) -> Solution:
        """Ejecuta la búsqueda tabú desde la solución actual."""
        current = best.copy()
        best_found = best.copy()
        n = problem.n
        tabu_list: Deque[int] = deque(maxlen=self.tabu_tenure)
        tabu_set: Set[int] = set()

        for _ in range(self.max_iters):
            best_neighbor = None
            best_neighbor_fit = float("-inf")
            best_move = -1

            for i in range(n):
                if i in tabu_set:
                    continue
                neighbor = current.vector.copy()
                neighbor[i] = 1 - neighbor[i]
                repaired, fitness = repair_solution(neighbor, problem)
                if fitness > best_neighbor_fit:
                    best_neighbor_fit = fitness
                    best_neighbor = repaired
                    best_move = i

            if best_neighbor is None:
                break

            current = Solution(
                vector=best_neighbor, fitness=best_neighbor_fit, feasible=True
            )

            # Actualizar tabú
            if len(tabu_list) == self.tabu_tenure:
                removed = tabu_list[0]
                tabu_set.discard(removed)
            tabu_list.append(best_move)
            tabu_set.add(best_move)

            # Actualizar mejor
            if current.fitness > best_found.fitness:
                best_found = current.copy()

        return best_found
