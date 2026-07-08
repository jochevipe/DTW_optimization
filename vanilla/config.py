"""
Configuración centralizada de las corridas Vanilla (sin DTW).
"""

import os

from mkp_common import BinaryDE, BinaryGWO, GeneticAlgorithm, BinaryPSO

# --- Instancia (sobrescribible via env: MKP_INSTANCIA, MKP_INDICE) ---
RUTA_INSTANCIA = os.environ.get("MKP_INSTANCIA", "instances/mknapcb4.txt")
INDICE_INSTANCIA = int(os.environ.get("MKP_INDICE", "0"))

# --- Población y presupuesto ---
NUM_PARTICULAS = 20
NUM_ITERACIONES = 100
EPOCHS = 10
SEMILLA = 3  # None para aleatoriedad real

# --- MH por defecto (para scripts individuales) ---
MH_CLASS = BinaryPSO
