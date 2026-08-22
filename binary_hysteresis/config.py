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
def is_entry_trigger(out: dict, mode: str) -> bool:
    """Return whether the Hysteresis entry condition is active."""
    return (
        mode == "exploit"
        and bool(out.get("ready"))
        and out["delta"] >= out["theta_delta"]
    )


def is_exit_trigger(out: dict, mode: str) -> bool:
    """Return whether the Hysteresis exit condition is active."""
    return (
        mode == "explore"
        and bool(out.get("ready"))
        and out["delta"] <= 0
    )


class HysteresisController:
    """
    Control con histéresis puro sobre delta:
      - Entra a explore cuando delta >= theta_delta (estancamiento significativo)
      - Sale de explore cuando delta <= 0 (la curva muestra progreso)
    """

    def __init__(self, initial_mode: str = "exploit"):
        if initial_mode not in {"exploit", "explore"}:
            raise ValueError("initial_mode must be 'exploit' or 'explore'")
        self.mode = initial_mode

    def __call__(self, out: dict) -> bool:
        if not out.get("ready"):
            return self.mode == "explore"

        if is_entry_trigger(out, self.mode):
            self.mode = "explore"
        elif is_exit_trigger(out, self.mode):
            self.mode = "exploit"

        return self.mode == "explore"


def make_fire_fn(initial_mode: str = "exploit"):
    """Factory: retorna una instancia fresca del controlador."""
    return HysteresisController(initial_mode=initial_mode)
