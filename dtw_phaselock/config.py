"""
DTW-PhaseLock config — exploit-base controller with confirmed-stagnation explore.

All shared values come from mkp_common.config.
Change things there to affect ALL strategies at once.

Design (target: GeneticAlgorithm; also run for DE and GWO as assignment/control):
  - Base regime EXPLOIT: the GA keeps its exploitation dynamics by default.
  - Sustained explore is entered ONLY on confirmed deep stagnation:
    D2_vs_const <= theta_c AND no_improve_len >= plateau_min.
  - Return to exploit on fresh improvement (no_improve_len == 0) or high
    activity (D2_vs_const > RECOVERY_MULT * theta_c).

Deviation from doc 06: the monitor exposes no P80 dead-band key. The band
is implemented as multipliers of theta_c instead (plateau_min iterations of
flat curve to enter explore, recovery at D2 > RECOVERY_MULT * theta_c).

Limitation: no MH resets population state on a mode switch; the controller
inherits this inertia and cannot undo partial convergence caused by an
explore episode.
"""

from mkp_common import GeneticAlgorithm
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
MH_CLASS = GeneticAlgorithm

# --- DTW config for this strategy ---
DTW_CFG = DTW_FIRE_D2

# --- PhaseLock strategy hyperparameters ---
# Minimum consecutive non-improving iterations before sustained explore.
PLATEAU_MIN = 5
# Recovery multiplier: leave explore when D2_vs_const > this * theta_c.
RECOVERY_MULT = 2.5

# Exact decision-rule string saved into results metadata (and validated by
# analisis.estadistico). Keep in sync with the controller logic below.
DECISION_RULE = (
    "D2 <= theta_c and no_improve_len >= 5 -> explore; "
    "improve or D2 > 2.5*theta_c -> exploit"
)


class DTWPhaseLockController:
    """
    Control con base EXPLOIT y explore solo ante estancamiento profundo
    confirmado (target: GeneticAlgorithm).

    Reglas:
      - Warm-up (monitor not ready): return False (exploit base regime).
      - Enter sustained explore only when BOTH hold:
          * curve flattened: D2_vs_const <= theta_c, AND
          * deep stagnation: no_improve_len >= plateau_min.
      - Return to exploit when:
          * improvement detected (no_improve_len == 0), OR
          * high activity: D2_vs_const > recovery_mult * theta_c.

    Deviation from doc 06: the P80 dead-band does not exist in the monitor;
    the band is implemented via the plateau_min gate and the recovery_mult
    multiplier of theta_c instead.

    Limitation: no MH resets population state on mode switch, so switching
    back to exploit inherits whatever exploration changed in the population.
    """

    def __init__(
        self,
        initial_mode: str = "exploit",
        plateau_min: int = PLATEAU_MIN,
        recovery_mult: float = RECOVERY_MULT,
    ):
        if initial_mode not in {"exploit", "explore"}:
            raise ValueError("initial_mode must be 'exploit' or 'explore'")
        self.mode = initial_mode
        self.plateau_min = int(plateau_min)
        self.recovery_mult = float(recovery_mult)

    def __call__(self, out: dict) -> bool:
        # Warm-up placeholders (ready=False): stay on the exploit base regime.
        if not out.get("ready"):
            return self.mode == "explore"

        if self.mode == "exploit":
            flat = out.get("D2_vs_const", 0.0) <= out.get("theta_c", 0.0)
            deep_stagnation = out.get("no_improve_len", 0) >= self.plateau_min
            if flat and deep_stagnation:
                self.mode = "explore"
        else:
            improved = out.get("no_improve_len") == 0
            high_activity = (
                out.get("D2_vs_const", 0.0)
                > self.recovery_mult * out.get("theta_c", 0.0)
            )
            if improved or high_activity:
                self.mode = "exploit"

        return self.mode == "explore"


def make_fire_fn(
    initial_mode: str = "exploit",
    plateau_min: int = PLATEAU_MIN,
    recovery_mult: float = RECOVERY_MULT,
):
    """Factory: retorna una instancia fresca del controlador."""
    return DTWPhaseLockController(
        initial_mode=initial_mode,
        plateau_min=plateau_min,
        recovery_mult=recovery_mult,
    )
