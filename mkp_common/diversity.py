"""
Diversidad poblacional binaria — helper compartido.

Fuente única de las métricas de diversidad usadas por la sonda
``analisis/diversidad_probe.py`` y por la estrategia A10
``binary_diversity_predictive``. La sonda importa estas funciones para que las
métricas queden definidas en un solo lugar (su salida no cambió).

Métricas sobre una población binaria P (N individuos x n genes):
  1) hamming    = diversidad Hamming normalizada (0..1): probabilidad de que
                  dos individuos elegidos al azar difieran en un gen,
                  2 * media_j(p_j * (1 - p_j)) con p_j la frecuencia del bit 1
                  en el gen j — cálculo vectorizado O(N*n), sin loop de pares.
                  Equivale a la distancia Hamming media por pares DISTINTOS
                  multiplicada por (N-1)/N; se mantiene esta definición para
                  conservar sin cambios la salida histórica de la sonda y la
                  escala de los umbrales calibrados con ella.
  2) entropy    = entropía binaria media por gen (0..1):
                  media_j( -p_j*log2(p_j) - (1-p_j)*log2(1-p_j) ).
  3) fitness_std= desviación estándar del fitness poblacional (solo si se
                  provee el fitness; 0.0 en caso contrario).

Atributos de población verificados en mkp_common/mh/*.py:
  BinaryPSO.poblacion        : ndarray (N, n) — posiciones reparadas
  GeneticAlgorithm.poblacion : list[ndarray] (+ fitness_pop)
  BinaryGWO.poblacion        : list[ndarray] (+ fitness_pop)
  BinaryDE.poblacion_bin     : ndarray (N, n) (+ fitness_pop)

Las MHs con fitness_pop lo exponen evaluado; BinaryPSO no lo guarda, así que
se calcula como p · x (válido porque la población ya está reparada).
"""

import numpy as np

# Atributo que expone la población binaria evaluada en cada MH.
POBLACION_ATTR = {
    "BinaryPSO": "poblacion",
    "GeneticAlgorithm": "poblacion",
    "BinaryGWO": "poblacion",
    "BinaryDE": "poblacion_bin",
}

# MHs que guardan el fitness de la población actual en fitness_pop.
FITNESS_POP_MHS = {"GeneticAlgorithm", "BinaryGWO", "BinaryDE"}


def population_of(mh) -> np.ndarray:
    """Población binaria evaluada actual de una MH como ndarray (N, n).

    Lee el atributo correcto según la clase de la MH; lanza TypeError para
    clases no registradas en ``POBLACION_ATTR`` (agregar ahí las nuevas MHs).
    """
    nombre = type(mh).__name__
    if nombre not in POBLACION_ATTR:
        raise TypeError(
            f"{nombre}: MH no registrada en mkp_common.diversity.POBLACION_ATTR"
        )
    return np.asarray(getattr(mh, POBLACION_ATTR[nombre]), dtype=float)


def population_fitness_of(mh, pop: np.ndarray) -> np.ndarray:
    """Fitness de la población actual (evaluado, sin re-evaluar reparaciones).

    Usa ``fitness_pop`` cuando la MH lo expone; para BinaryPSO calcula p · x
    sobre la población ya reparada.
    """
    if type(mh).__name__ in FITNESS_POP_MHS:
        return np.asarray(mh.fitness_pop, dtype=float)
    return np.asarray(mh.inst["p"], dtype=float) @ np.asarray(pop, dtype=float).T


def population_diversity(pop, fitness=None) -> dict:
    """Las 3 métricas de diversidad sobre una población binaria.

    Args:
        pop:     ndarray (N, n) o lista de vectores binarios.
        fitness: fitness por individuo (opcional). Si es None, ``fitness_std``
                 es 0.0; si se provee un solo valor, también 0.0 (std exige
                 más de un dato). Robustez ante ausencia de fitness.

    Returns:
        {"hamming": float, "entropy": float, "fitness_std": float}
    """
    pop = np.asarray(pop, dtype=float)
    if pop.ndim != 2 or pop.shape[0] == 0 or pop.shape[1] == 0:
        raise ValueError(
            f"population_diversity espera un arreglo 2D no vacío (N, n); "
            f"recibió shape={pop.shape}"
        )

    p = pop.mean(axis=0)  # frecuencia del bit 1 por gen
    hamming = float(2.0 * np.mean(p * (1.0 - p)))

    ent = np.zeros_like(p)
    mask = (p > 0) & (p < 1)
    ent[mask] = -p[mask] * np.log2(p[mask]) - (1.0 - p[mask]) * np.log2(1.0 - p[mask])
    entropy = float(np.mean(ent))

    fitness_std = 0.0
    if fitness is not None:
        farr = np.asarray(fitness, dtype=float)
        if farr.size > 1:
            fitness_std = float(np.std(farr))

    return {"hamming": hamming, "entropy": entropy, "fitness_std": fitness_std}
