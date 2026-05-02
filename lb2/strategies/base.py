"""Interfaz base para estrategias de respuesta al estancamiento."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lb2.core.problem import MKPInstance
    from lb2.core.solution import Solution


class StagnationStrategy(ABC):
    """Interfaz para estrategias que responden al estancamiento.

    Cada estrategia recibe la mejor solución actual y la instancia
    del problema, y retorna una solución (posiblemente mejorada).
    """

    @property
    def name(self) -> str:
        """Nombre legible de la estrategia."""
        return self.__class__.__name__

    @abstractmethod
    def apply(self, best: "Solution", problem: "MKPInstance") -> "Solution":
        """Aplica la estrategia para intentar escapar del estancamiento.

        Args:
            best: Mejor solución actual.
            problem: Instancia MKP.

        Returns:
            Solución (posiblemente mejorada).
        """
