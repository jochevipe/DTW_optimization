"""ParameterController — autoconfiguración de parámetros basada en DTW.

Interpreta las señales del StagnationMonitor y decide si la
metaheurística debe explorar, explotar, o activar una estrategia
de respuesta al estancamiento.

Absorbe la funcionalidad de las versiones V2-V4 del notebook original.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict


class ControlAction(Enum):
    """Acción que el controller decide para la metaheurística."""

    HOLD = "hold"           # Progreso normal, no tocar nada
    EXPLORE = "explore"     # Señales tempranas de estancamiento → explorar más
    EXPLOIT = "exploit"     # Mejora reciente → explotar la región
    INTERVENE = "intervene" # Estancamiento confirmado → activar strategy


class ParameterController:
    """Controla los parámetros de la metaheurística basándose en la señal DTW.

    Threshold para intervención: fire=True O no_improve_len >= no_improve_threshold.
    """

    def __init__(
        self,
        no_improve_threshold: int = 15,
        explore_params: Dict | None = None,
        exploit_params: Dict | None = None,
    ) -> None:
        """
        Args:
            no_improve_threshold: Iteraciones sin mejora para activar INTERVENE.
            explore_params: Parámetros para modo exploración.
            exploit_params: Parámetros para modo explotación.
        """
        self.no_improve_threshold = no_improve_threshold
        self._explore_params = explore_params or {
            "inertia": 0.95,
            "cognitive": 2.5,
            "social": 1.0,
        }
        self._exploit_params = exploit_params or {
            "inertia": 0.35,
            "cognitive": 1.2,
            "social": 2.8,
        }

    def decide(self, dtw_output: Dict) -> ControlAction:
        """Analiza la salida del monitor DTW y decide la acción.

        Args:
            dtw_output: Dict retornado por StagnationMonitor.update().

        Returns:
            ControlAction indicando qué debe hacer la metaheurística.
        """
        if not dtw_output.get("ready", False):
            return ControlAction.HOLD

        fire = dtw_output.get("fire", False)
        no_improve = dtw_output.get("no_improve_len", 0)

        # Estancamiento confirmado → INTERVENIR con strategy
        if fire or no_improve >= self.no_improve_threshold:
            return ControlAction.INTERVENE

        # Mejora reciente → explotar
        if no_improve == 0:
            return ControlAction.EXPLOIT

        # Sin mejora pero no estancado aún → nada
        return ControlAction.HOLD

    def get_explore_params(self) -> Dict:
        """Retorna parámetros para modo exploración."""
        return self._explore_params.copy()

    def get_exploit_params(self) -> Dict:
        """Retorna parámetros para modo explotación."""
        return self._exploit_params.copy()
