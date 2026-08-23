"""
Binary-Diversity-Predictive (A10) config — controlador explore/exploit con
conciencia de diversidad y detección predictiva.

Evidencia que motiva las reglas (sonda analisis/diversidad_probe.py, medida)
---------------------------------------------------------------------------
La sonda midió la diversidad Hamming durante mesetas de best-so-far en modo
fijo:

  * GA-exploit: mesetas MUERTAS — Hamming 0.008-0.014 (la población colapsó;
    ahí sí conviene explorar).
  * PSO-explore y PSO-exploit: mesetas VIVAS — Hamming 0.17-0.21 (el enjambre
    sigue disperso trabajando; conmutar a exploit en ese momento destruye el
    salto que venía).

Dos consecuencias de diseño:

  1. El controlador NUNCA entra a exploit mientras la diversidad esté alta
     (compuerta sobre la transición explore -> exploit).
  2. La salida de exploración se decide por mejora observable
     (no_improve_len == 0), jamás por delta <= 0: en la curva escalera del
     MKP delta = D1 - D2 permanece estrictamente positivo, y la condición
     delta <= 0 es inalcanzable (lección del Binary-Hysteresis original,
     que quedaba bloqueado en explore y resultaba bit-idéntico a
     vanilla_exploracion).

Reglas de transición (base EXPLORE; warm-up devuelve True)
----------------------------------------------------------
  * EXPLORE -> EXPLOIT: mejora detectada (no_improve_len == 0) Y
    diversidad <= theta_div_high (P50 de la historia de diversidad).
    Nunca se explota una población viva/diversa.
  * EXPLOIT -> EXPLORE, dos ramas (EITHER):
      (a) colapso de meseta muerta: out["fire"] es True Y
          diversidad <= theta_div_low (P20 de la historia) — estancamiento
          A4 sostenido CON colapso de diversidad confirmado;
      (b) early-warning predictivo: tendencia creciente de delta (pendiente
          de los últimos 5 deltas listos > 0) Y delta >= theta_delta —
          "nos acercamos a una meseta" antes de que se forme.

Umbrales adaptativos de diversidad (por corrida, iteraciones listas):
  theta_div_low  = P20 de la historia rodante de diversidad.
  theta_div_high = P50 de la historia rodante de diversidad.
  Sin historia todavía: fallbacks documentados abajo.

Hipótesis operativa: la compuerta de diversidad protege al PSO (mesetas
vivas) de conmutaciones destructivas, mientras que la rama (a) rescata al GA
(mesetas muertas) y la rama (b) anticipa mesetas en todas las MHs.

All shared values come from mkp_common.config.
Change things there to affect ALL strategies at once.
"""

from collections import deque

import numpy as np

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
from mkp_common.diversity import population_diversity, population_of

# --- Stable exported decision-rule string (used by results, HPC registry,
# --- and the statistical validator; do not change casually) ---
DECISION_RULE = (
    "exploit if improvement AND div<=P50; "
    "explore if (fire AND div<=P20) OR (rising delta slope>0 AND delta>=theta_delta)"
)

# --- Default MH for single-run scripts ---
MH_CLASS = BinaryDE

# --- DTW config for this strategy ---
DTW_CFG = DTW_FIRE_D2

# --- Hyperparámetros del canal de diversidad / detección predictiva ---
_P_DIV_LOW = 20.0      # percentil de la historia de diversidad -> theta_div_low
_P_DIV_HIGH = 50.0     # percentil de la historia de diversidad -> theta_div_high
_TREND_WINDOW = 5      # últimas N muestras de delta para la pendiente predictiva
_HISTORY_MAX = 100     # tope rodante de las historias (diversidad y delta)

# Fallbacks cuando aún no hay iteraciones listas en la historia:
#   theta_div_high = 0.5  -> máximo teórico de la Hamming normalizada por pares
#                            para poblaciones binarias aleatorias; compuerta
#                            permisiva sin evidencia (equivale a histéresis A9).
#   theta_div_low  = 0.15 -> un orden de magnitud por encima de las mesetas
#                            muertas medidas en GA-exploit (0.008-0.014);
#                            conservador para confirmar "colapso".
_FALLBACK_THETA_DIV_LOW = 0.15
_FALLBACK_THETA_DIV_HIGH = 0.5


class DiversityPredictiveController:
    """
    Controlador stateful A10 (base explore) con tres canales:

      * fire del monitor (A4 sostenido) para confirmar estancamiento;
      * diversidad Hamming de la población (umbrales adaptativos P20/P50);
      * tendencia de delta (pendiente de las últimas 5 muestras listas) como
        early-warning predictivo.

    Requiere el hook de observación del runner: ``bind(mh)`` se invoca
    exactamente una vez después de ``mh.initialize()`` (ver
    mkp_common/runner.run_experiment). Sin bind, ``__call__`` falla con un
    error explícito: medir diversidad exige acceso a la población.

    Cada iteración lista, el controlador registra en ``out["_diversity_state"]``
    su diagnóstico interno (diversidad, umbrales, pendiente, modo) para los
    gráficos de ``resultados.py`` — mismo objeto dict que el runner guarda en
    ``historial_dtw``.
    """

    def __init__(self, initial_mode: str = "explore"):
        if initial_mode not in {"exploit", "explore"}:
            raise ValueError("initial_mode must be 'exploit' or 'explore'")
        self.mode = initial_mode
        self._mh = None
        # Historias rodantes (solo iteraciones listas: out["ready"] True).
        self._div_hist = deque(maxlen=_HISTORY_MAX)
        self._delta_hist = deque(maxlen=_HISTORY_MAX)

    # ------------------------------------------------------------------ #
    # Hook de observación del runner
    # ------------------------------------------------------------------ #
    def bind(self, mh) -> None:
        """Capturar la MH una sola vez (tras initialize) para leer su población."""
        self._mh = mh

    # ------------------------------------------------------------------ #
    # Métricas internas
    # ------------------------------------------------------------------ #
    def _current_hamming(self) -> float:
        """Diversidad Hamming normalizada de la población actual de la MH."""
        if self._mh is None:
            raise RuntimeError(
                "DiversityPredictiveController.__call__ requires bind(mh) first "
                "(the generic runner binds the MH right after initialize)"
            )
        pop = population_of(self._mh)
        return float(population_diversity(pop)["hamming"])

    def _thresholds(self) -> tuple:
        """(theta_div_low, theta_div_high) = (P20, P50) de la historia de diversidad."""
        if len(self._div_hist) == 0:
            return (_FALLBACK_THETA_DIV_LOW, _FALLBACK_THETA_DIV_HIGH)
        arr = np.asarray(self._div_hist, dtype=float)
        return (
            float(np.percentile(arr, _P_DIV_LOW)),
            float(np.percentile(arr, _P_DIV_HIGH)),
        )

    def _delta_trend(self):
        """Pendiente de regresión de los últimos _TREND_WINDOW deltas listos.

        None si aún no hay suficientes muestras: la rama predictiva exige
        evidencia antes de anticipar una meseta.
        """
        if len(self._delta_hist) < _TREND_WINDOW:
            return None
        deltas = np.asarray(self._delta_hist, dtype=float)[-_TREND_WINDOW:]
        x = np.arange(_TREND_WINDOW, dtype=float)
        return float(np.polyfit(x, deltas, 1)[0])

    # ------------------------------------------------------------------ #
    # Decisión
    # ------------------------------------------------------------------ #
    def __call__(self, out: dict) -> bool:
        """Decide el modo para esta iteración; retorna True = explore.

        Warm-up (out["ready"] False): devuelve el modo actual (base explore)
        sin tocar historias ni umbrales.
        """
        if not out.get("ready"):
            return self.mode == "explore"

        # 1) Observar: diversidad actual + señal delta (solo iteraciones listas).
        div = self._current_hamming()
        self._div_hist.append(div)
        self._delta_hist.append(float(out.get("delta", 0.0)))

        # 2) Umbrales adaptativos e indicadores.
        theta_div_low, theta_div_high = self._thresholds()
        trend = self._delta_trend()

        fire = bool(out.get("fire"))
        improved = int(out.get("no_improve_len", 1)) == 0
        delta_over = float(out.get("delta", 0.0)) >= float(out.get("theta_delta", 0.0))

        # 3) Transiciones.
        if self.mode == "explore":
            # EXPLORE -> EXPLOIT solo con mejora Y diversidad colapsada:
            # nunca explotar una población viva (evidencia PSO: 0.17-0.21).
            if improved and div <= theta_div_high:
                self.mode = "exploit"
        else:
            # EXPLOIT -> EXPLORE:
            #   (a) meseta muerta: A4 sostenido + colapso de diversidad (P20).
            collapse = fire and div <= theta_div_low
            #   (b) early-warning predictivo: delta subiendo (pendiente > 0)
            #       y ya por encima de su umbral — anticipa la meseta.
            predictive = (trend is not None and trend > 0.0) and delta_over
            if collapse or predictive:
                self.mode = "explore"

        # 4) Diagnóstico para los gráficos (mismo dict que historial_dtw).
        out["_diversity_state"] = {
            "mode": self.mode,
            "hamming": div,
            "theta_div_low": theta_div_low,
            "theta_div_high": theta_div_high,
            "trend_slope": trend,
            "delta": float(out.get("delta", 0.0)),
            "theta_delta": float(out.get("theta_delta", 0.0)),
            "n_div_samples": len(self._div_hist),
        }
        return self.mode == "explore"


def make_fire_fn(initial_mode: str = "explore"):
    """Factory: retorna una instancia fresca del controlador (stateful)."""
    return DiversityPredictiveController(initial_mode=initial_mode)
