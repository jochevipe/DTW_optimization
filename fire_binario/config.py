"""
Configuración centralizada del enfoque Fire Binario.
Todos los scripts de esta estrategia importan de acá.
"""

from mkp_common import BinaryDE, BinaryGWO, GeneticAlgorithm, BinaryPSO 
from mkp_common.monitor import StagnationConfig

# --- Instancia ---
RUTA_INSTANCIA = "instances/mknapcb1.txt"
INDICE_INSTANCIA = 0

# --- Población y presupuesto ---
NUM_PARTICULAS = 20
NUM_ITERACIONES = 100
EPOCHS = 10
VERBOSE = True

# --- MH por defecto (para scripts individuales) ---
MH_CLASS = GeneticAlgorithm

# --- DTW (idéntico al notebook "original") ---
DTW_CFG = StagnationConfig(
    window=15,
    band=2,
    plateau_max=10,
    patience=2,
    min_slope=2.0,
    use_ddtw=True,
    adapt_thresholds=True,
)
