"""
Runner para Binary-Patient (estrategia A10).
Wrapper sobre el runner genérico con fire_fn = PatientD2Controller.
"""

from mkp_common.runner import run_experiment as _run_experiment
from mkp_common.runner import run_epochs as _run_epochs

from .config import make_fire_fn


def _make_exploring_fire_fn():
    """Create the stateful controller used by one adaptive epoch."""
    return make_fire_fn(initial_mode="explore")


def run_experiment(**kwargs):
    """run_experiment con estrategia A10 (D2 sostenido / mejora)."""
    kwargs.setdefault("fire_fn", _make_exploring_fire_fn())
    kwargs.setdefault("initial_mode", "explore")
    kwargs.setdefault("decision_on_early", True)
    return _run_experiment(**kwargs)


def run_epochs(**kwargs):
    """run_epochs con estrategia A10 (D2 sostenido / mejora)."""
    if "fire_fn" not in kwargs and "fire_fn_factory" not in kwargs:
        kwargs["fire_fn_factory"] = _make_exploring_fire_fn
    kwargs.setdefault("initial_mode", "explore")
    kwargs.setdefault("decision_on_early", True)
    return _run_epochs(**kwargs)
