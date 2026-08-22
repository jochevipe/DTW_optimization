"""
DTW-Pulse config — stateful explore-base controller with bounded exploit pulses.

All shared values come from mkp_common.config.
Change things there to affect ALL strategies at once.

Design rationale:
  - Base regime EXPLORE prevents velocity collapse in BinaryPSO.
  - Short exploit pulses refine promising basins detected via fresh
    improvements or high activity (D2_vs_const > HIGH_ACTIVITY_MULT * theta_c).
  - A hard cap on pulse length avoids getting trapped in exploit, because
    no MH resets its population state on mode switch.

Limitation: no MH resets population state on a mode switch; the controller
mitigates this inertia with the bounded pulse length but cannot remove it.
"""

from mkp_common import BinaryPSO
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
MH_CLASS = BinaryPSO

# --- DTW config for this strategy ---
DTW_CFG = DTW_FIRE_D2

# --- Pulse strategy hyperparameters ---
# Exit guard: never stay longer than this many iterations inside one pulse.
MAX_PULSE_ITERATIONS = 10
# High-activity multiplier: enter pulse when D2_vs_const > this * theta_c.
HIGH_ACTIVITY_MULT = 2.0

# Exact decision-rule string saved into results metadata (and validated by
# analisis.estadistico). Keep in sync with the controller logic below.
DECISION_RULE = (
    "improve or D2 > 2*theta_c -> exploit; "
    "D2 <= theta_c without fresh improvement or max 10 iterations -> explore"
)


class DTWPulseController:
    """
    Control con base EXPLORE y pulsos cortos de EXPLOIT (target: BinaryPSO).

    Reglas:
      - Warm-up (monitor not ready): return True (explore base regime).
      - Enter exploit pulse when:
          * fresh improvement detected (no_improve_len == 0), OR
          * high activity: D2_vs_const > HIGH_ACTIVITY_MULT * theta_c.
      - Exit pulse back to explore when:
          * curve flattens (D2_vs_const <= theta_c) AND there is no fresh
            improvement, OR
          * the bounded max pulse length is reached (max_pulse_iterations).

    The max-pulse-length guard exists because no MH resets its population
    state on a mode switch; it bounds how long the swarm can be held in
    exploit before being forced back to exploration.
    """

    def __init__(
        self,
        max_pulse_iterations: int = MAX_PULSE_ITERATIONS,
        high_activity_mult: float = HIGH_ACTIVITY_MULT,
    ):
        self.max_pulse_iterations = int(max_pulse_iterations)
        self.high_activity_mult = float(high_activity_mult)
        self.mode = "explore"
        self._pulse_len = 0

    def __call__(self, out: dict) -> bool:
        # Warm-up placeholders (ready=False, D2=0.0): stay on the explore base.
        if not out.get("ready"):
            return self.mode == "explore"

        if self.mode == "explore":
            improved = out.get("no_improve_len") == 0
            high_activity = (
                out.get("D2_vs_const", 0.0)
                > self.high_activity_mult * out.get("theta_c", 0.0)
            )
            if improved or high_activity:
                self.mode = "exploit"
                self._pulse_len = 1
        else:
            self._pulse_len += 1
            flattened = out.get("D2_vs_const", 0.0) <= out.get("theta_c", 0.0)
            no_fresh_improvement = out.get("no_improve_len", 0) != 0
            maxed_out = self._pulse_len >= self.max_pulse_iterations
            if (flattened and no_fresh_improvement) or maxed_out:
                self.mode = "explore"
                self._pulse_len = 0

        return self.mode == "explore"


def make_fire_fn(
    max_pulse_iterations: int = MAX_PULSE_ITERATIONS,
    high_activity_mult: float = HIGH_ACTIVITY_MULT,
):
    """Factory: retorna una instancia fresca del controlador."""
    return DTWPulseController(
        max_pulse_iterations=max_pulse_iterations,
        high_activity_mult=high_activity_mult,
    )
