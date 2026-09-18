# Feature: Frente 2 — Campaña multi-instancia (27 instancias)

Fecha de creación: 2026-09-18 · Rama: `dtw_discreto`
Origen: `contexto/Round-1/SINTESIS_REVIEWS.md` — Frente 2 (R1.3): el paper solo usó idx=0 de cada archivo Chu–Beasley; extender a 3 índices fijos por archivo (27 instancias).

## Diseño de selección de instancias

- Los 9 archivos `mknapcb{1..9}.txt` forman la grilla (m × n): m∈{5,10,30}, n∈{100,250,500}. Cada archivo tiene 30 instancias (idx 0..29).
- **Criterio**: idx=0 siempre incluido (comparabilidad directa con los resultados ya reportados del paper) + 2 índices adicionales muestreados sin reposición de [1,29] con `numpy.random.default_rng(1000 + i)` por archivo `i`. Determinista y documentado.
- `k=3` (configurable), `seed_base=1000` (configurable).

### Tabla oficial de índices

| Archivo | m × n | Índices |
|---|---|---|
| mknapcb1 | 5×100 | 0, 18, 26 |
| mknapcb2 | 5×250 | 0, 12, 17 |
| mknapcb3 | 5×500 | 0, 6, 9 |
| mknapcb4 | 10×100 | 0, 1, 21 |
| mknapcb5 | 10×250 | 0, 3, 13 |
| mknapcb6 | 10×500 | 0, 10, 15 |
| mknapcb7 | 30×100 | 0, 2, 3 |
| mknapcb8 | 30×250 | 0, 5, 10 |
| mknapcb9 | 30×500 | 0, 2, 21 |

Total: 27 instancias (9 archivos × 3 índices).

## Tareas

1. [ ] Extender `run_benchmark_hpc.py` con modo multi-índice: flags `--k`, `--sample-seed`, `--include-zero`; generación determinista por archivo; guardado de `instance_selection.json` en la carpeta de campaña (`results/campaign_{id}/`); pasar cada par (archivo, índice) a `run_all_hpc.py` con `--indice`.
2. [ ] Documentar la campaña en `contexto/Round-1/INSTANCIAS_SELECCIONADAS.md` (tabla oficial, criterio, comando HPC).
3. [ ] Smoke test local reducido (1 archivo, idx=0, `--epochs 2`, estrategias acotadas) → verificar resultados + análisis estadístico por índice.
4. [ ] Commit work-unit en `dtw_discreto` (Conventional Commit) y registrar identidad acá.

## No-goals

- No se toca `run_all_hpc.py` (ya soporta `--indice` arbitrario y guarda por `{inst}_{indice}`).
- No se implementa análisis agregado multi-instancia en esta feature (etapa posterior).
- No se alinean `window`/percentiles del config (Frente 3 / precondición aparte).

## Evidencia de commits

- `792c099` — feat: multi-index HPC campaign for Chu-Beasley revision (27 instances): run_benchmark_hpc.py + INSTANCIAS_SELECCIONADAS.md + este doc. Smoke test end-to-end previo: mknapcb1[0], 2 epochs, 32/32 tareas OK, análisis estadístico OK, manifiesto generado.
