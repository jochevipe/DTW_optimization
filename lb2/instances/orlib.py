"""Carga y parseo de instancias MKP desde OR-Library.

Soporta archivos tipo mknapcb (Chu & Beasley).
"""

from __future__ import annotations

from typing import List

import numpy as np
import requests

from lb2.core.problem import MKPInstance


# URLs estándar de la OR-Library (Beasley)
ORLIB_URLS = {
    "mknapcb1": "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/mknapcb1.txt",
    "mknapcb2": "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/mknapcb2.txt",
    "mknapcb3": "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/mknapcb3.txt",
    "mknapcb4": "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/mknapcb4.txt",
    "mknapcb5": "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/mknapcb5.txt",
    "mknapcb6": "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/mknapcb6.txt",
    "mknapcb7": "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/mknapcb7.txt",
    "mknapcb8": "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/mknapcb8.txt",
    "mknapcb9": "http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/mknapcb9.txt",
}


def parse_mkp_text(text: str, source_name: str = "") -> List[MKPInstance]:
    """Parsea el contenido de un archivo MKP tipo Chu & Beasley.

    El formato esperado es:
      - Primera línea: número de instancias
      - Para cada instancia:
          - n, m, valor_optimo
          - Coeficientes de profit (posiblemente en múltiples líneas)
          - m filas de restricciones (pesos)
          - Capacidades de las mochilas

    Args:
        text: Contenido del archivo como string.
        source_name: Nombre identificador del archivo fuente.

    Returns:
        Lista de MKPInstance.
    """
    instances: List[MKPInstance] = []
    lines = text.strip().split("\n")
    numbers = [list(map(float, line.split())) for line in lines]

    line_idx = 0
    n_instances = int(numbers[line_idx][0])

    for inst_num in range(n_instances):
        line_idx += 1
        if not numbers[line_idx]:
            line_idx += 1

        n_items, m_constraints, opt_value = numbers[line_idx]
        n_items, m_constraints = int(n_items), int(m_constraints)
        line_idx += 1

        # Leer profits
        profits: List[float] = []
        while len(profits) < n_items:
            profits += numbers[line_idx]
            line_idx += 1

        # Leer restricciones (pesos)
        weights: List[List[float]] = []
        capacities: List[float] = []

        for _ in range(m_constraints):
            row: List[float] = []
            while len(row) < n_items:
                row += numbers[line_idx]
                line_idx += 1
            weights.append(row)

        # Leer capacidades
        while len(capacities) < m_constraints:
            capacities += numbers[line_idx]
            line_idx += 1
        line_idx -= 1  # Ajuste del notebook original

        name = f"{source_name}_{inst_num}" if source_name else f"inst_{inst_num}"

        instances.append(
            MKPInstance(
                n=n_items,
                m=m_constraints,
                profits=np.array(profits),
                weights=np.array(weights),
                capacities=np.array(capacities),
                optimal_value=opt_value,
                name=name,
            )
        )

    return instances


def load_mkp_instances(name: str, url: str | None = None) -> List[MKPInstance]:
    """Descarga y parsea instancias MKP de la OR-Library.

    Args:
        name: Nombre del conjunto (ej. "mknapcb1").
        url: URL opcional. Si no se provee, se busca en ORLIB_URLS.

    Returns:
        Lista de MKPInstance.

    Raises:
        ValueError: Si el nombre no se encuentra y no se provee URL.
        requests.HTTPError: Si falla la descarga.
    """
    if url is None:
        url = ORLIB_URLS.get(name)
        if url is None:
            raise ValueError(
                f"Nombre '{name}' no encontrado en ORLIB_URLS. "
                f"Disponibles: {list(ORLIB_URLS.keys())}"
            )

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return parse_mkp_text(response.text, source_name=name)
