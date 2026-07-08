"""
Configuración centralizada del enfoque B3 — D2 Direct Intensity.
Estrategia de adaptación continua: intensity = 1 - clip(D2 / (theta_c * scale), 0, 1).

Cuanto más plana la curva de fitness (D2 bajo), más explora (intensity alto).
Usa exactamente la misma señal que A3 (fire_d2) pero con transición gradual.
"""

import os

from mkp_common import BinaryPSO
from mkp_common.monitor import StagnationConfig

# --- Instancia (sobrescribible via env: MKP_INSTANCIA, MKP_INDICE) ---
RUTA_INSTANCIA = os.environ.get("MKP_INSTANCIA", "instances/mknapcb4.txt")
INDICE_INSTANCIA = int(os.environ.get("MKP_INDICE", "0"))

# --- Población y presupuesto ---
NUM_PARTICULAS = 20
NUM_ITERACIONES = 100
EPOCHS = 10
VERBOSE = False
SEMILLA = 3  # None para aleatoriedad real

# --- MH por defecto ---
MH_CLASS = BinaryPSO

# --- DTW ---
DTW_CFG = StagnationConfig(
    window=10,
    band=2,
    min_slope=2.0,
    use_ddtw=True,
    adapt_thresholds=True,  # Necesario para theta_c adaptativo
    p_low=30.0,
    p_high=70.0,
)

# --- B3 D2 Direct hypers ---
SCALE = 2.0
# intensity = 1 - clip(D2 / (theta_c * SCALE + eps), 0, 1)
# scale > 1: more tolerant (needs stronger stagnation to trigger explore)
# scale < 1: more sensitive (triggers explore with weaker stagnation)
# scale = 1: D2 = theta_c → intensity = 0 (pure exploit)
