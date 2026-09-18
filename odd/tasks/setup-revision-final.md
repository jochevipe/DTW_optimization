# Feature: Setup final de revisión — índices fijos, rename complex, limpieza

Fecha de creación: 2026-09-18 · Rama: `dtw_discreto`
Decisiones del usuario:
1. **Índices**: usar 0, 15, 29 fijos para los 9 archivos (muestreo sistemático: primera/media/última de cada archivo; las 30 instancias por archivo son i.i.d. del mismo par (m,n), ningún índice tiene valor particular).
2. **Rename**: `binary_hysteresis` → `binary_complex` para concordar con el paper (Binary-Complex, Eq. 26). Labels de vanilla unificados a los nombres del paper: Vanilla-Exploitation / Vanilla-Exploration.
3. **Limpieza**: borrar TODOS los resultados actuales (5 datasets de sensibilidad `results-*`, todo el contenido de `results/` incl. diversity_predictive y campañas viejas) para partir de cero con la campaña nueva; borrar `instances/mknapcb.zip` y `__pycache__/`. No tocar `contexto/` (latex, docs), `.engram/`, código.

## Tareas

1. [ ] Rename `binary_hysteresis/` → `binary_complex/` (git mv) + wiring (run_all.py, run_all_hpc.py, analisis/estadistico.py) + validator acepta `binary_complex` (canónica) y `binary_hysteresis` (legacy).
2. [ ] Unificar labels a nombres del paper: Vanilla-Exploitation / Vanilla-Exploration (run_all_hpc.py, run_all.py, analisis/estadistico.py, títulos de plotters vanilla si usan nombres viejos).
3. [ ] Actualizar selección oficial a `--indices 0 15 29` en `contexto/Round-1/INSTANCIAS_SELECCIONADAS.md` (mantener --k/--sample-seed como alternativa).
4. [ ] Limpieza: `git rm -r` datasets `results-*`, contenido de `results/`, `instances/mknapcb.zip`; borrar `__pycache__/` (untracked).
5. [ ] Verificación: imports/py_compile + smoke integrado (mknapcb1 idx 15, epochs=1, 5 estrategias) → luego limpiar artefactos del smoke.
6. [ ] Commits por unidad (rename+labels / índices / limpieza) y registrar evidencia.

## No-goals

- No tocar `mkp_common/config.py` (window/percentiles se alinean al final, antes de la corrida HPC).
- No borrar `contexto/`, `.engram/`, notebooks, apuntes.
- No implementar el baseline sin DTW en esta feature.

## Evidencia de commits

- `3f9a31f` — refactor: rename binary_hysteresis to binary_complex + labels del paper unificados (verificado: imports OK, smoke idx=15 con 5 estrategias y estadística con nombres nuevos).
- `(docs)` — actualización de INSTANCIAS_SELECCIONADAS.md a índices 0/15/29 + docs Round-1.
- `(chore)` — limpieza de datasets viejos, resultados y zip.
