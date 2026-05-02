"""Interfaz base para metaheurísticas.

Cualquier metaheurística poblacional que quiera integrarse al
framework debe implementar esta ABC.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from lb2.core.problem import MKPInstance
    from lb2.core.solution import Solution


class Metaheuristic(ABC):
    """Interfaz base para cualquier metaheurística."""

    @abstractmethod
    def initialize(self, problem: "MKPInstance", seed: int | None = None) -> None:
        """Inicializa la población/soluciones para un nuevo epoch.

        Args:
            problem: Instancia MKP a resolver.
            seed: Semilla para reproducibilidad (opcional).
        """

    @abstractmethod
    def step(self, iteration: int, total_iterations: int) -> float:
        """Ejecuta UNA iteración de la metaheurística.

        Args:
            iteration: Índice de la iteración actual (0-based).
            total_iterations: Total de iteraciones planeadas.

        Returns:
            Mejor fitness actual.
        """

    @abstractmethod
    def get_best(self) -> "Solution":
        """Retorna la mejor solución encontrada hasta ahora."""

    @abstractmethod
    def get_params(self) -> Dict:
        """Retorna los parámetros actuales (para logging/autoconfig)."""

    @abstractmethod
    def set_params(self, params: Dict) -> None:
        """Modifica parámetros en runtime.

        Usado por el ParameterController para autoconfigurar
        exploración vs explotación.
        """

    @abstractmethod
    def inject_solution(self, solution: "Solution", fraction: float = 0.4) -> None:
        """Inyecta una solución en una fracción de la población.

        Usado por las StagnationStrategy cuando encuentran algo mejor
        mediante búsqueda local.

        Args:
            solution: Solución a inyectar.
            fraction: Fracción de la población a reemplazar (0 a 1).
        """
