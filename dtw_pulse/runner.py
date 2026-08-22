"""
Runner para DTW-Pulse (base explore con pulsos acotados de exploit).
Wrapper sobre el runner genérico con fire_fn = DTWPulseController.

The factory pattern guarantees a fresh stateful controller per epoch so
controller state never leaks across epochs.
"""

from mkp_common.runner import run_experiment as _run_experiment
from mkp_common.runner import run_epochs as _run_epochs

from .config import make_fire_fn


def _make_pulsing_fire_fn():
    """Create the stateful controller used by one adaptive epoch."""
    return make_fire_fn()


def run_experiment(**kwargs):
    """run_experiment con estrategia DTW-Pulse."""
    kwargs.setdefault("fire_fn", _make_pulsing_fire_fn())
    kwargs.setdefault("initial_mode", "explore")
    kwargs.setdefault("decision_on_early", True)
    return _run_experiment(**kwargs)


def run_epochs(**kwargs):
    """run_epochs con estrategia DTW-Pulse (fresh controller per epoch)."""
    if "fire_fn" not in kwargs and "fire_fn_factory" not in kwargs:
        kwargs["fire_fn_factory"] = _make_pulsing_fire_fn
    kwargs.setdefault("initial_mode", "explore")
    kwargs.setdefault("decision_on_early", True)
    return _run_epochs(**kwargs)
