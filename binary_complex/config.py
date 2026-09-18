"""
Binary-Complex (A9) config — stateful explore/exploit switch built on the
monitor's sustained A4 trigger with true asymmetric hysteresis.

Why the previous delta-only hysteresis was dead
-----------------------------------------------
The original controller entered explore when ``delta >= theta_delta`` and left
explore only when ``delta <= 0``. On MKP instances the best-so-far fitness
curve is a monotone staircase: once the window fills with flat steps,
D2_vs_const collapses toward zero while D1_vs_ramp stays high, so ``delta``
(D1 - D2) stays strictly positive forever. ``delta <= 0`` therefore became an
unreachable exit condition: any run that ever entered explore stayed locked in
explore, making the strategy bit-identical to vanilla_exploracion in every
comparison of the 2026-08-22 campaign.

The fix
-------
Replace the delta thresholds with the monitor's own sustained A4 trigger:

- Entry (exploit -> explore): ``bool(out["fire"])`` — plateau AND D2-constant
  AND ramp/delta conditions held for ``patience`` iterations
  (trigger_streak), i.e. confirmed stagnation.
- Exit (explore -> exploit): improvement detected, i.e.
  ``int(out["no_improve_len"]) == 0``.

Both transitions require ``out["ready"]``, giving true asymmetric hysteresis:
entry needs sustained multi-condition evidence, exit needs a single fresh
improvement.

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

# --- Stable exported decision-rule string (used by results, HPC registry,
# --- and the statistical validator; do not change casually) ---
DECISION_RULE = "A4 fire sustained (plateau+constant+ramp) -> explore; improvement -> exploit"

# --- Default MH for single-run scripts ---
MH_CLASS = BinaryDE

# --- DTW config for this strategy ---
DTW_CFG = DTW_FIRE_D2


# --- A9 decision function (stateful) ---
def is_entry_trigger(out: dict, mode: str) -> bool:
    """Return whether the Hysteresis entry condition is active (exploit -> explore).

    True when the monitor reports its sustained A4 trigger (fire): plateau,
    D2-constant and ramp/delta conditions held for patience iterations.
    """
    return (
        mode == "exploit"
        and bool(out.get("ready"))
        and bool(out.get("fire"))
    )


def is_exit_trigger(out: dict, mode: str) -> bool:
    """Return whether the Hysteresis exit condition is active (explore -> exploit).

    True when improvement is detected (no_improve_len reset to 0).
    """
    return (
        mode == "explore"
        and bool(out.get("ready"))
        and int(out.get("no_improve_len", 1)) == 0
    )


class HysteresisController:
    """
    Control con histéresis asimétrica sobre la señal A4 del monitor:
      - Entra a explore cuando fire=True (A4 sostenido: meseta + constante +
        rampa/delta durante patience iteraciones seguidas).
      - Sale de explore apenas hay mejora (no_improve_len == 0).
    """

    def __init__(self, initial_mode: str = "explore"):
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


def make_fire_fn(initial_mode: str = "explore"):
    """Factory: retorna una instancia fresca del controlador."""
    return HysteresisController(initial_mode=initial_mode)
