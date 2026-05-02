"""PSO Binario con framework de binarización LB2.

Extraído y refactorizado del notebook original.
"""

from __future__ import annotations

import random
from typing import Dict, List

import numpy as np

from lb2.core.problem import MKPInstance
from lb2.core.repair import repair_solution
from lb2.core.solution import Solution
from lb2.metaheuristics.base import Metaheuristic


class BinaryPSO(Metaheuristic):
    """PSO binario usando el framework de binarización LB2.

    LB2 usa dos funciones de transferencia complementarias (L1 y L2)
    que generan dos candidatos por iteración. Los parámetros G1, G2, G3
    evolucionan linealmente durante la ejecución.
    """

    def __init__(
        self,
        num_particles: int = 20,
        inertia: float = 0.65,
        cognitive: float = 2.0,
        social: float = 2.0,
        v_max: float = 8.0,
        g1_range: tuple = (0.5, 1.0),
        g2_range: tuple = (0.5, 7.2),
        g3_range: tuple = (0.5, 0.0),
    ) -> None:
        self.num_particles = num_particles
        self.inertia = inertia
        self.cognitive = cognitive
        self.social = social
        self.v_max = v_max
        self.g1_range = g1_range
        self.g2_range = g2_range
        self.g3_range = g3_range

        # Estado interno (se inicializa en initialize())
        self._problem: MKPInstance | None = None
        self._particles: List[Dict] = []
        self._best_global: Solution = Solution(vector=np.array([]))

    def initialize(self, problem: MKPInstance, seed: int | None = None) -> None:
        """Inicializa el enjambre para un nuevo epoch."""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self._problem = problem
        self._particles = []
        self._best_global = Solution(vector=np.zeros(problem.n), fitness=float("-inf"))

        for _ in range(self.num_particles):
            vec = [random.randint(0, 1) for _ in range(problem.n)]
            repaired, fitness = repair_solution(np.array(vec, dtype=float), problem)
            particle = {
                "solucion": list(repaired),
                "valor": fitness,
                "mejor_valor_personal": fitness,
                "mejor_solucion_personal": list(repaired),
            }
            self._particles.append(particle)
            if fitness > self._best_global.fitness:
                self._best_global = Solution(
                    vector=repaired.copy(), fitness=fitness, feasible=True
                )

    def step(self, iteration: int, total_iterations: int) -> float:
        """Ejecuta una iteración del PSO binario con LB2."""
        assert self._problem is not None, "Llamar initialize() primero"

        problem = self._problem
        n = problem.n

        # Calcular G1, G2, G3 linealmente
        G1_i, G1_f = self.g1_range
        G2_i, G2_f = self.g2_range
        G3_i, G3_f = self.g3_range
        denom = 1 - total_iterations
        G1 = G1_f + (G1_i - G1_f) / denom * (iteration - total_iterations)
        G2 = G2_f + (G2_i - G2_f) / denom * (iteration - total_iterations)
        G3 = G3_f + (G3_i - G3_f) / denom * (iteration - total_iterations)

        best_sol = list(self._best_global.vector)

        for particle in self._particles:
            # Velocidad PSO
            vel = (
                np.array(particle["solucion"]) * self.inertia
                + np.array(particle["mejor_solucion_personal"])
                * self.cognitive
                * random.random()
                + np.array(best_sol) * self.social * random.random()
            )

            # LB2: dos funciones de transferencia
            L1 = np.clip(-G1 * vel / (self.v_max - G2) + G3, 0, 1)
            L2 = np.clip(G1 * vel / (self.v_max - G2) + G3, 0, 1)

            x1 = particle["solucion"].copy()
            x2 = particle["solucion"].copy()

            for i in range(n):
                if np.random.rand() < L1[i]:
                    x1[i] = 1 - x1[i]
            for i in range(n):
                if np.random.rand() < L2[i]:
                    x2[i] = 1 - x2[i]

            x1, x1_fit = repair_solution(np.array(x1, dtype=float), problem)
            x2, x2_fit = repair_solution(np.array(x2, dtype=float), problem)

            # Seleccionar el mejor candidato
            if x1_fit > x2_fit:
                x2, x2_fit = x1, x1_fit

            # Actualizar partícula
            if x2_fit > particle["valor"]:
                particle["solucion"] = list(x2)
                particle["valor"] = x2_fit

            # Actualizar mejor personal
            if particle["valor"] > particle["mejor_valor_personal"]:
                particle["mejor_valor_personal"] = particle["valor"]
                particle["mejor_solucion_personal"] = particle["solucion"][:]

            # Actualizar mejor global
            if particle["valor"] > self._best_global.fitness:
                self._best_global = Solution(
                    vector=np.array(particle["solucion"], dtype=float),
                    fitness=particle["valor"],
                    feasible=True,
                )

        return self._best_global.fitness

    def get_best(self) -> Solution:
        """Retorna la mejor solución global."""
        return self._best_global.copy()

    def get_params(self) -> Dict:
        """Retorna los parámetros actuales del PSO."""
        return {
            "inertia": self.inertia,
            "cognitive": self.cognitive,
            "social": self.social,
            "v_max": self.v_max,
            "num_particles": self.num_particles,
        }

    def set_params(self, params: Dict) -> None:
        """Modifica parámetros del PSO en runtime."""
        if "inertia" in params:
            self.inertia = params["inertia"]
        if "cognitive" in params:
            self.cognitive = params["cognitive"]
        if "social" in params:
            self.social = params["social"]
        if "v_max" in params:
            self.v_max = params["v_max"]

    def inject_solution(self, solution: Solution, fraction: float = 0.4) -> None:
        """Inyecta una solución en una fracción del enjambre."""
        num_inject = max(1, int(fraction * self.num_particles))
        indices = random.sample(range(self.num_particles), min(num_inject, self.num_particles))

        for idx in indices:
            self._particles[idx]["solucion"] = list(solution.vector)
            self._particles[idx]["valor"] = solution.fitness
            self._particles[idx]["mejor_solucion_personal"] = list(solution.vector)
            self._particles[idx]["mejor_valor_personal"] = solution.fitness

        # Actualizar global si es mejor
        if solution.fitness > self._best_global.fitness:
            self._best_global = solution.copy()
