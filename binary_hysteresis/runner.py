"""
Runner para Binary-Hysteresis (estrategia A9).
Wrapper sobre el runner genérico con fire_fn = HysteresisController.
"""

from mkp_common.runner import run_experiment as _run_experiment
from mkp_common.runner import run_epochs as _run_epochs

from .config import make_fire_fn


def run_experiment(**kwargs):
    """run_experiment con estrategia A9 (histéresis sobre delta)."""
    kwargs.setdefault("fire_fn", make_fire_fn())
    return _run_experiment(**kwargs)


def run_epochs(**kwargs):
    """run_epochs con estrategia A9 (histéresis sobre delta)."""
    kwargs.setdefault("fire_fn", make_fire_fn())
    return _run_epochs(**kwargs)
