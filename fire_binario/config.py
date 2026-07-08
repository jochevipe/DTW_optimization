"""
Configuración centralizada del enfoque Fire Binario.
Todos los scripts de esta estrategia importan de acá.
"""

import os

from mkp_common import BinaryDE, BinaryGWO, GeneticAlgorithm, BinaryPSO 
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

# --- MH por defecto (para scripts individuales) ---
MH_CLASS = BinaryPSO

# --- DTW (idéntico al notebook "original") ---
DTW_CFG = StagnationConfig(
    window=10,
    band=2,
    plateau_max=2,
    patience=2,
    min_slope=2.0,
    use_ddtw=True,
    adapt_thresholds=True,
)
