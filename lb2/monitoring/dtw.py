"""Detección de estancamiento basada en DTW (Dynamic Time Warping).

Extraído directamente del notebook original (dtw_stagnation.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np


def dtw_distance(
    s: np.ndarray, t: np.ndarray, window: Optional[int] = None
) -> float:
    """Calcula la distancia DTW entre dos series temporales."""
    s = np.asarray(s, dtype=float)
    t = np.asarray(t, dtype=float)
    n, m = len(s), len(t)
    if window is None:
        window = max(n, m)
    window = max(window, abs(n - m))
    INF = float("inf")
    D = np.full((n + 1, m + 1), INF)
    D[0, 0] = 0.0
    for i in range(1, n + 1):
        j_start = max(1, i - window)
        j_end = min(m, i + window)
        si = s[i - 1]
        for j in range(j_start, j_end + 1):
            cost = abs(si - t[j - 1])
            D[i, j] = cost + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    return float(D[n, m])


def first_diff(x: np.ndarray) -> np.ndarray:
    """Primera diferencia de una serie temporal."""
    x = np.asarray(x, dtype=float)
    return np.diff(x, prepend=x[0])


def ddtw_distance(
    s: np.ndarray, t: np.ndarray, window: Optional[int] = None
) -> float:
    """Distancia DDTW (Derivative DTW)."""
    return dtw_distance(first_diff(s), first_diff(t), window=window)


def ramp_baseline(start_value: float, s_min: float, length: int) -> np.ndarray:
    """Genera una rampa lineal como baseline de progreso ideal."""
    i = np.arange(length, dtype=float)
    return start_value + s_min * i


def constant_baseline(start_value: float, length: int) -> np.ndarray:
    """Genera una constante como baseline de estancamiento total."""
    return np.full(length, float(start_value))


def moving_percentile(buffer: List[float], p: float) -> float:
    """Percentil móvil sobre un buffer."""
    arr = np.asarray(buffer, dtype=float)
    return float(np.percentile(arr, p)) if arr.size > 0 else float("nan")


@dataclass
class StagnationConfig:
    """Configuración del monitor de estancamiento.

    Attributes:
        window: Tamaño de la ventana de observación.
        band: Ancho de banda Sakoe-Chiba para DTW. Si 0, usa 10% de window.
        min_slope: Pendiente mínima esperada para la rampa.
        plateau_max: Iteraciones sin mejora para considerar meseta.
        patience: Confirmaciones consecutivas antes de disparar.
        use_ddtw: Si True, usa DDTW (analiza pendientes).
        adapt_thresholds: Si True, adapta umbrales dinámicamente.
        p_low: Percentil bajo para umbral constante.
        p_high: Percentil alto para umbral rampa.
    """

    window: int = 30
    band: int = 0
    min_slope: float = 0.0
    plateau_max: int = 15
    patience: int = 3
    use_ddtw: bool = False
    adapt_thresholds: bool = True
    p_low: float = 30.0
    p_high: float = 70.0

    def __post_init__(self) -> None:
        if self.band <= 0:
            self.band = max(1, int(0.1 * self.window))


@dataclass
class StagnationMonitor:
    """Monitor de estancamiento usando DTW.

    Compara la curva de convergencia actual contra dos baselines:
    - Rampa (progreso ideal)
    - Constante (estancamiento total)

    Cuando la curva se parece más a la constante que a la rampa
    durante `patience` confirmaciones, dispara `fire=True`.
    """

    cfg: StagnationConfig
    best_so_far: List[float] = field(default_factory=list)
    no_improve_len: int = 0
    trigger_streak: int = 0
    d1_hist: List[float] = field(default_factory=list)
    d2_hist: List[float] = field(default_factory=list)
    delta_hist: List[float] = field(default_factory=list)

    def reset(self) -> None:
        """Resetea el monitor para un nuevo epoch."""
        self.best_so_far.clear()
        self.no_improve_len = 0
        self.trigger_streak = 0
        self.d1_hist.clear()
        self.d2_hist.clear()
        self.delta_hist.clear()

    def update(self, new_best: float) -> Dict:
        """Actualiza el monitor con un nuevo valor de best fitness.

        Args:
            new_best: Mejor fitness actual de la iteración.

        Returns:
            Dict con claves:
                - ready: bool, True si hay suficientes datos para analizar.
                - fire: bool, True si se detectó estancamiento.
                - D1_vs_ramp, D2_vs_const, delta: métricas DTW.
                - theta_c, theta_r, theta_delta: umbrales.
                - no_improve_len: iteraciones sin mejora.
                - trigger_streak: confirmaciones consecutivas.
                - n: cantidad de observaciones.
        """
        # Sanitize input
        if isinstance(new_best, (list, tuple, np.ndarray)):
            arr = np.asarray(new_best, dtype=float)
            new_best = float(np.max(arr))
        else:
            new_best = float(new_best)

        # Sanitize historial
        if self.best_so_far and isinstance(
            self.best_so_far[-1], (list, tuple, np.ndarray)
        ):
            self.best_so_far = [
                float(np.max(np.asarray(v, dtype=float))) for v in self.best_so_far
            ]

        if self.best_so_far and new_best <= self.best_so_far[-1]:
            self.no_improve_len += 1
            new_best = self.best_so_far[-1]
        else:
            self.no_improve_len = 0
        self.best_so_far.append(float(new_best))

        n = len(self.best_so_far)
        W = self.cfg.window
        if n < W:
            return {
                "ready": False,
                "fire": False,
                "no_improve_len": self.no_improve_len,
                "n": n,
            }

        X = np.array(self.best_so_far[-W:], dtype=float)
        start = X[0]

        s_min = self.cfg.min_slope
        if s_min == 0.0:
            rng = max(1.0, abs(X[-1] - X[0]))
            s_min = 0.01 * rng / W

        r = ramp_baseline(start, s_min, W)
        c = constant_baseline(start, W)

        if self.cfg.use_ddtw:
            D1 = ddtw_distance(X, r, window=self.cfg.band)
            D2 = ddtw_distance(X, c, window=self.cfg.band)
        else:
            D1 = dtw_distance(X, r, window=self.cfg.band)
            D2 = dtw_distance(X, c, window=self.cfg.band)

        delta = D1 - D2
        self.d1_hist.append(D1)
        self.d2_hist.append(D2)
        self.delta_hist.append(delta)

        if self.cfg.adapt_thresholds and len(self.d1_hist) >= 10:
            theta_c = moving_percentile(self.d2_hist, self.cfg.p_low)
            theta_r = moving_percentile(self.d1_hist, self.cfg.p_high)
            theta_delta = moving_percentile(self.delta_hist, self.cfg.p_high)
        else:
            theta_c = 0.1 * W
            theta_r = 0.5 * W
            theta_delta = 0.3 * W

        cond_plateau = self.no_improve_len >= self.cfg.plateau_max
        cond_constant = D2 <= theta_c
        cond_ramp = (D1 >= theta_r) or (delta >= theta_delta)

        if cond_plateau and cond_constant and cond_ramp:
            self.trigger_streak += 1
        else:
            self.trigger_streak = 0

        fire = self.trigger_streak >= self.cfg.patience
        return {
            "ready": True,
            "fire": bool(fire),
            "D1_vs_ramp": float(D1),
            "D2_vs_const": float(D2),
            "delta": float(delta),
            "theta_c": float(theta_c),
            "theta_r": float(theta_r),
            "theta_delta": float(theta_delta),
            "no_improve_len": int(self.no_improve_len),
            "trigger_streak": int(self.trigger_streak),
            "n": int(n),
        }
