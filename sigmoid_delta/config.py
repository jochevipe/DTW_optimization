"""
Configuración centralizada del enfoque Sigmoid Delta (B1).
Estrategia de adaptación continua con sigmoid sobre delta/theta_delta.
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
    adapt_thresholds=True,  # Necesario para theta_delta adaptativo
    p_low=30.0,
    p_high=70.0,
)

# --- B1 Sigmoid hypers ---
K = 5.0         # steepness (higher = sharper transition)
CENTER = 0.5    # inflection point on r_balance scale
# r_balance = delta / (theta_delta + eps)
# intensity = 1 / (1 + exp(-K * (r_balance - CENTER)))
