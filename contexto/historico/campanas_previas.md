# Campañas previas retiradas

El 2026-09-23 se retiraron deliberadamente seis árboles `results*` en `fe12f2f` para empezar de cero los experimentos post-OAT. Este catálogo resume el inventario de archivos de `08c2f29` (`fe12f2f^`), no conserva salidas generadas ni representa las campañas OAT, cuyos artefactos primarios permanecen en la rama OAT.

| Campaña | Archivos | Rango de ejecuciones (identificadores de fecha/hora) | Cobertura | Parámetros inferidos del nombre | Estrategias presentes |
|---|---:|---|---|---|---|
| `results_base_50/` | 261 | `20260818_221742`–`20260819_014225` | 9 archivos, índice 0 | Significado de `base_50` desconocido | `binary_simple`, `binary_hysteresis`, `vanilla_exploracion`, `vanilla_explotacion`, `estadistico` |
| `results/` | 35 | `20260822_233823` (una ejecución) | Solo `mknapcb1_0` | Sin sufijo | `binary_simple`, `binary_hysteresis`, `binary_diversity_predictive`, `vanilla_exploracion`, `vanilla_explotacion`, `estadistico` |
| `results-200-40-60/` | 377 | `20260823_214835`–`20260824_020318` | 9 archivos, índice 0 | W=200; p bajo=40, alto=60 | `binary_simple`, `binary_hysteresis`, `vanilla_exploracion`, `vanilla_explotacion`, `estadistico` |
| `results-200-20-80/` | 261 | `20260824_114136`–`20260824_151546` | 9 archivos, índice 0 | W=200; p bajo=20, alto=80 | `binary_simple`, `binary_hysteresis`, `vanilla_exploracion`, `vanilla_explotacion`, `estadistico` |
| `results-100-50-60/` | 261 | `20260825_083307`–`20260825_120721` | 9 archivos, índice 0 | W=100; p bajo=50, alto=60 | `binary_simple`, `binary_hysteresis`, `vanilla_exploracion`, `vanilla_explotacion`, `estadistico` |
| `results-100-20-80/` | 261 | `20260825_152125`–`20260825_184921` | 9 archivos, índice 0 | W=100; p bajo=20, alto=80 | `binary_simple`, `binary_hysteresis`, `vanilla_exploracion`, `vanilla_explotacion`, `estadistico` |

La interpretación del sufijo `results-<W>-<p_low>-<p_high>` como ventana y percentiles es **inferida de los nombres**, no verificada en la configuración de cada ejecución. `binary_hysteresis` es la etiqueta histórica de la estrategia luego llamada `binary_complex`; `binary_diversity_predictive` fue una variante experimental cuyo módulo ya no está en esta rama.

Desde la raíz del repositorio, para listar los archivos históricos:

```sh
git ls-tree -r 08c2f29 --name-only | grep ^results
```

Para recuperar **solo una** campaña en el árbol de trabajo (acción que modifica archivos; no ejecutarla salvo decisión explícita):

```sh
git restore --source=08c2f29 -- results-100-20-80/
```

El cuaderno archivado [`advance_LB2_MKP.ipynb`](advance_LB2_MKP.ipynb) está en este mismo directorio.
