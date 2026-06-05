"""
Configuración centralizada del enfoque Fire D2 (estrategia A3).
Todos los scripts de esta estrategia importan de acá.

La única diferencia con fire_binario es la función fire_fn:
    fire = D2 <= theta_c  (¿la curva es plana?)

NOTA: plateau_max y patience siguen en la config del DTW porque el
StagnationMonitor los necesita para calcular sus métricas internas,
pero NO se usan en la decisión de fire de esta estrategia.
"""

from mkp_common import BinaryDE, BinaryGWO, BinaryPSO, GeneticAlgorithm
from mkp_common.monitor import StagnationConfig

# --- Instancia ---
RUTA_INSTANCIA = "instances/mknapcb4.txt"
INDICE_INSTANCIA = 0

# --- Población y presupuesto ---
NUM_PARTICULAS = 20
NUM_ITERACIONES = 100
EPOCHS = 10
VERBOSE = False
SEMILLA = 3  # None para aleatoriedad real

# --- MH por defecto (para scripts individuales) ---
MH_CLASS = BinaryDE

# --- DTW (misma config base que fire_binario para comparación justa) ---
DTW_CFG = StagnationConfig(
    window=10,
    band=2,
    plateau_max=10,   # no se usa en la decisión A3, pero el monitor lo necesita
    patience=2,       # no se usa en la decisión A3, pero el monitor lo necesita
    min_slope=2.0,
    use_ddtw=True,
    adapt_thresholds=True,
)


# --- Función de decisión A3: D2 puro ---
def fire_d2(out: dict) -> bool:
    """
    Estrategia A3: fire si D2 <= theta_c.
    "¿La curva de fitness se parece a una meseta?"

    - D2 bajo → la ventana es plana → estancamiento → fire=True
    - theta_c se auto-adapta al historial (percentil p_low de D2)
    """
    return out["D2_vs_const"] <= out["theta_c"]
