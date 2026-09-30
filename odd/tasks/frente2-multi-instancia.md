# Feature: Frente 2 — Campaña multi-instancia (27 instancias)

Fecha de creación: 2026-09-18 · Rama: `dtw_discreto`
Origen: `contexto/Round-1/SINTESIS_REVIEWS.md` — Frente 2 (R1.3): el paper solo usó idx=0 de cada archivo Chu–Beasley; extender a 3 índices fijos por archivo (27 instancias).

## Diseño de selección de instancias

- Los 9 archivos `mknapcb{1..9}.txt` forman la grilla (m × n): m∈{5,10,30}, n∈{100,250,500}. Cada archivo tiene 30 instancias (idx 0..29).
- **Criterio**: idx=0 siempre incluido (comparabilidad directa con los resultados ya reportados del paper) + 2 índices adicionales muestreados sin reposición de [1,29] con `numpy.random.default_rng(1000 + i)` por archivo `i`. Determinista y documentado.
- `k=3` (configurable), `seed_base=1000` (configurable).

### Tabla oficial de índices (Criterio simétrico [0, 15, 29])

| Archivo | m × n | Índices |
|---|---|---|
| mknapcb1 | 5×100 | 0, 15, 29 |
| mknapcb2 | 5×250 | 0, 15, 29 |
| mknapcb3 | 5×500 | 0, 15, 29 |
| mknapcb4 | 10×100 | 0, 15, 29 |
| mknapcb5 | 10×250 | 0, 15, 29 |
| mknapcb6 | 10×500 | 0, 15, 29 |
| mknapcb7 | 30×100 | 0, 15, 29 |
| mknapcb8 | 30×250 | 0, 15, 29 |
| mknapcb9 | 30×500 | 0, 15, 29 |

Total: 27 instancias (9 archivos × 3 índices: primera, media y última).

## Tareas

1. [x] Extender `run_benchmark_hpc.py` con modo multi-índice: flags `--indices`, `--k`, `--sample-seed`, `--desde`, `--hasta`, `--dry-run`; guardado de `instance_selection.json` en `results/campaign_{id}/`.
2. [x] Documentar la campaña en `contexto/Round-1/INSTANCIAS_SELECCIONADAS.md` (tabla oficial `[0, 15, 29]`, criterio, protocolo de semillas pareadas, comando HPC).
3. [x] Ejecución completa de la campaña multi-instancia en HPC: 27 instancias ejecutadas en paralelo mediante 3 trabajos de 3 problemas cada uno con 40 CPUs y 31 épocas.
4. [x] Análisis estadístico individual por cada (archivo, índice) completado con tests de Wilcoxon y Holm-Bonferroni en `results/estadistico/`.

## No-goals

- No se toca `run_all_hpc.py` (ya soporta `--indice` arbitrario y guarda por `{inst}_{indice}`).
- Consolidación global de tablas multi-instancia (etapa posterior).

## Evidencia de ejecución

- Campaña ejecutada en HPC Océano: `campaign_20260929_141957` (27 instancias completadas sin errores). Manifiesto en `results/campaign_20260929_141957/instance_selection.json`.
- Estadísticas generadas en `results/estadistico/mknapcb{1..9}_{0,15,29}/`.
