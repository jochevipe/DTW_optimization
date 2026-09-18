"""
Binary-Patient (A10) config — stateful D2 patience controller.

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
DECISION_RULE = (
    "D2 <= theta_c sustained for patience iterations -> explore; "
    "improvement -> exploit"
)

# --- Default MH for single-run scripts ---
MH_CLASS = BinaryDE

# --- DTW config for this strategy ---
DTW_CFG = DTW_FIRE_D2


class PatientD2Controller:
    """Stateful D2 threshold controller with asymmetric patience."""

    def __init__(self, patience: int, initial_mode: str = "explore"):
        if initial_mode not in {"exploit", "explore"}:
            raise ValueError("initial_mode must be 'exploit' or 'explore'")
        if isinstance(patience, bool) or not isinstance(patience, int) or patience <= 0:
            raise ValueError("patience must be a positive integer")
        self.patience = patience
        self.mode = initial_mode
        self.streak = 0

    def __call__(self, out: dict) -> bool:
        """Apply sustained D2 entry and one-step improvement exit rules."""
        if not out.get("ready"):
            out["streak"] = self.streak
            return self.mode == "explore"

        if out["D2_vs_const"] <= out["theta_c"]:
            self.streak += 1
        else:
            self.streak = 0
        out["streak"] = self.streak

        if self.mode == "exploit" and self.streak >= self.patience:
            self.mode = "explore"
        elif self.mode == "explore" and int(out.get("no_improve_len", 1)) == 0:
            self.mode = "exploit"

        return self.mode == "explore"


def make_fire_fn(initial_mode: str = "explore"):
    """Factory: return a fresh patient D2 controller."""
    return PatientD2Controller(DTW_CFG.patience, initial_mode)
