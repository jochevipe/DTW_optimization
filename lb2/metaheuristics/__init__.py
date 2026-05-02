"""Metaheurísticas: interfaz base + implementaciones."""

from lb2.metaheuristics.base import Metaheuristic
from lb2.metaheuristics.pso import BinaryPSO

__all__ = ["Metaheuristic", "BinaryPSO"]
