"""Estrategia LP Relaxation (V6 del notebook).

Resuelve la relajación lineal del MKP para obtener un upper bound
y una solución fraccional que guía la búsqueda.

Si scipy está disponible, usa linprog. De lo contrario,
usa un greedy basado en densidad como fallback.
"""

from __future__ import annotations

import numpy as np

from lb2.core.problem import MKPInstance
from lb2.core.repair import repair_solution
from lb2.core.solution import Solution
from lb2.strategies.base import StagnationStrategy


class LPRelaxationStrategy(StagnationStrategy):
    """LP Relaxation para guiar la búsqueda.

    Resuelve la relajación lineal (variables en [0,1]) y luego
    redondea + repara para obtener una solución factible.
    """

    @property
    def name(self) -> str:
        return "LP Relaxation"

    def apply(self, best: Solution, problem: MKPInstance) -> Solution:
        """Resuelve LP relaxation y redondea la solución."""
        try:
            from scipy.optimize import linprog

            result = self._solve_lp(problem)
            if result is not None:
                vec = np.array([1.0 if x >= 0.5 else 0.0 for x in result], dtype=float)
                repaired, fitness = repair_solution(vec, problem)
                if fitness > best.fitness:
                    return Solution(vector=repaired, fitness=fitness, feasible=True)
        except ImportError:
            return self._greedy_fallback(best, problem)

        return best.copy()

    def _solve_lp(self, problem: MKPInstance):
        """Resuelve la relajación lineal del MKP."""
        from scipy.optimize import linprog

        # Maximizar profits → minimizar -profits
        c = -problem.profits

        # Restricciones: A @ x <= b
        A_ub = problem.weights
        b_ub = problem.capacities

        # Bounds: 0 <= x_i <= 1
        bounds = [(0, 1) for _ in range(problem.n)]

        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
        if result.success:
            return result.x
        return None

    def _greedy_fallback(self, best: Solution, problem: MKPInstance) -> Solution:
        """Fallback greedy si scipy no está disponible."""
        # Construir solución greedy por densidad descendente
        order = problem.density_order[::-1]
        vec = np.zeros(problem.n, dtype=float)
        remaining = problem.capacities.copy()

        for idx in order:
            col = problem.weights[:, int(idx)]
            if np.all(remaining - col >= 0):
                vec[int(idx)] = 1.0
                remaining -= col

        fitness = float(np.sum(vec * problem.profits))
        if fitness > best.fitness:
            return Solution(vector=vec, fitness=fitness, feasible=True)
        return best.copy()
