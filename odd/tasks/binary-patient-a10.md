# Feature: Estrategia Binary-Patient (A10) — D2 + patience

Fecha de creación: 2026-09-18 · Rama: `dtw_discreto`
Origen: Frente 1 de `contexto/Round-1/SINTESIS_REVIEWS.md` (comparación de variantes DTW); decisión del usuario: versión **D2 con patience** (descartadas D1-only y delta-only por evidencia empírica propia: A1/A2 disparan con progreso activo; delta nunca baja en MKP).

## Regla de decisión (stateful, asimétrica)

- **Entrada** (exploit → explore): `D2_vs_const <= theta_c` sostenido durante `patience` iteraciones consecutivas (contador interno de persistencia).
- **Salida** (explore → exploit): `no_improve_len == 0` (mejora fresca).
- Warm-up (`ready=False`): mantener modo actual.
- `patience` tomado de `DTW_FIRE_D2.patience` (config central).
- `DECISION_RULE = "D2 <= theta_c sustained for patience iterations -> explore; improvement -> exploit"`

## Tareas

1. [x] Implementar paquete `binary_patient/` + cableado (`run_all.py`, `run_all_hpc.py`, `analisis/estadistico.py`) — delegado a gentle-ai-worker, verificación enfocada verde.
2. [ ] Verificación técnica independiente (gentle-ai-verify).
3. [ ] Smoke integrado en `run_all_hpc.py` con las 5 estrategias (mknapcb1[0], epochs=2) + análisis estadístico con la versión nueva.
4. [ ] Documentar A10 en `contexto/Round-1/`.
5. [ ] Commit work-unit en `dtw_discreto` y registrar evidencia.

## Evidencia de commits

- `9a20c42` — feat: add Binary-Patient (A10) strategy with D2 patience (11 files, +903): paquete binary_patient/, cableado run_all.py + run_all_hpc.py + analisis/estadistico.py, doc ESTRATEGIA_A10_BINARY_PATIENT.md. Verificaciones: unit del controlador, gentle-ai-verify VERIFIED, smoke integrado 5 estrategias 40/40 tareas con columna Binary-Patient en la estadística.
