"""Representación de una solución candidata."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Solution:
    """Solución candidata para un problema binario.

    Attributes:
        vector: Vector binario (0/1) de tamaño n.
        fitness: Valor objetivo (suma de profits de items seleccionados).
        feasible: True si cumple todas las restricciones de capacidad.
    """

    vector: np.ndarray
    fitness: float = 0.0
    feasible: bool = True

    def copy(self) -> "Solution":
        """Retorna una copia profunda de la solución."""
        return Solution(
            vector=self.vector.copy(),
            fitness=self.fitness,
            feasible=self.feasible,
        )
