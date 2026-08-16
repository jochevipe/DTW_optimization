"""
Binary-Hysteresis (A9) config — stateful explore/exploit switch based on delta.

All shared values come from mkp_common.config.
Change things there to affect ALL strategies at once.
"""

from mkp_common import BinaryDE, BinaryGWO, BinaryPSO, GeneticAlgorithm
from mkp_common.config import (
    RUTA_INSTANCIA,
    INDICE_INSTANCIA,
    NUM_PARTICULAS,
    NUM_ITERACIONES,
    EPOCHS,
    SEMILLA,
    VERBOSE,
    DTW_FIRE_D2,
)

# --- Default MH for single-run scripts ---
MH_CLASS = BinaryDE

# --- DTW config for this strategy ---
DTW_CFG = DTW_FIRE_D2


# --- A9 decision function (stateful) ---
class HysteresisController:
    """
    Control con histéresis puro sobre delta:
      - Entra a explore cuando delta >= theta_delta (estancamiento significativo)
      - Sale de explore cuando delta <= 0 (la curva muestra progreso)
    """

    def __init__(self):
        self.mode = "exploit"

    def __call__(self, out: dict) -> bool:
        if not out.get("ready"):
            return self.mode == "explore"

        if self.mode == "exploit" and out["delta"] >= out["theta_delta"]:
            self.mode = "explore"
        elif self.mode == "explore" and out["delta"] <= 0:
            self.mode = "exploit"

        return self.mode == "explore"


def make_fire_fn():
    """Factory: retorna una instancia fresca del controlador."""
    return HysteresisController()
