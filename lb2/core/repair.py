"""Funciones de reparación para soluciones MKP.

NOTA: Corrige el bug crítico del notebook original donde ambas
ramas del if/else en la fase de drop hacían lo mismo.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import numpy as np

if TYPE_CHECKING:
    from lb2.core.problem import MKPInstance


def compute_density_order(
    profits: np.ndarray,
    weights: np.ndarray,
    capacities: np.ndarray,
) -> np.ndarray:
    """Calcula el orden de densidad ascendente de los items.

    La densidad mínima por item se define como:
        density[j] = min_i( profits[j] / weights[i][j] )

    Para pesos de 0, se reemplaza el ratio infinito por
    10 × max(ratios finitos).

    Returns:
        Índices ordenados por densidad ascendente.
    """
    m = weights.shape[0]
    density_per_bag = np.array([profits / weights[i] for i in range(m)])

    # Reemplazar infinitos por un valor alto pero finito
    finite_mask = np.isfinite(density_per_bag)
    if finite_mask.any():
        finite_max = np.max(density_per_bag[finite_mask])
        density_per_bag[~finite_mask] = finite_max * 10
    else:
        density_per_bag[:] = 1.0

    density = np.min(density_per_bag, axis=0)
    return np.argsort(density)


def _is_feasible(solution: np.ndarray, weights: np.ndarray, capacities: np.ndarray) -> bool:
    """Verifica si una solución cumple todas las restricciones."""
    return bool(np.all(np.dot(solution, weights.T) <= capacities))


def repair_solution(
    solution: np.ndarray,
    problem: "MKPInstance",
) -> Tuple[np.ndarray, float]:
    """Repara una solución para hacerla factible.

    Fase 1 (DROP): Elimina items en orden de densidad ascendente
    (peores primero) hasta que la solución sea factible.

    Fase 2 (ADD): Agrega items en orden de densidad ascendente
    mientras la solución siga siendo factible.

    Args:
        solution: Vector binario (será copiado internamente).
        problem: Instancia MKP con profits, weights, capacities y density_order.

    Returns:
        Tupla (solución_reparada, valor_total).

    BUGFIX: En el notebook original, la fase DROP siempre asignaba
    `solucion = aux` independientemente de la factibilidad. Ahora
    solo asigna cuando la remoción NO logra factibilidad (continúa
    removiendo) o cuando SÍ la logra (y termina).
    """
    sol = np.asarray(solution, dtype=float).copy()
    p = problem.profits
    w = problem.weights
    b = problem.capacities
    order = problem.density_order

    # --- Fase 1: DROP (eliminar items, peor densidad primero) ---
    for i in range(len(sol)):
        idx = int(order[i])
        if sol[idx] == 0:
            continue
        aux = sol.copy()
        aux[idx] = 0
        if _is_feasible(aux, w, b):
            # Factible → aceptar y TERMINAR la fase de drop
            sol = aux
            break
        else:
            # Aún no factible → aceptar la remoción y CONTINUAR
            sol = aux

    # --- Fase 2: ADD (agregar items, mejor densidad primero) ---
    for i in range(len(sol)):
        idx = int(order[i])
        if sol[idx] == 1:
            continue
        aux = sol.copy()
        aux[idx] = 1
        if _is_feasible(aux, w, b):
            sol = aux
        else:
            break

    fitness = float(np.sum(sol * p))
    return sol, fitness
