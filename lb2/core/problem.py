"""Definición del problema MKP (Multidimensional Knapsack Problem)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class MKPInstance:
    """Una instancia del Multidimensional Knapsack Problem.

    Attributes:
        n: Número de items.
        m: Número de restricciones (mochilas).
        profits: Valores de cada item (n,).
        weights: Pesos por restricción (m, n).
        capacities: Capacidades de cada mochila (m,).
        optimal_value: Valor óptimo conocido (0.0 si no se conoce).
        name: Identificador de la instancia.
        density_order: Índices ordenados por densidad ascendente
                       (precomputados para reparación).
    """

    n: int
    m: int
    profits: np.ndarray
    weights: np.ndarray
    capacities: np.ndarray
    optimal_value: float = 0.0
    name: str = ""
    density_order: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))

    def __post_init__(self) -> None:
        """Precomputa el orden de densidad si no fue provisto."""
        if self.density_order.size == 0:
            from lb2.core.repair import compute_density_order

            self.density_order = compute_density_order(
                self.profits, self.weights, self.capacities
            )
