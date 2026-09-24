# Feature: Estrategia Binary-Patient (A10) — D2 + patience

Fecha de creación: 2026-09-18 · Rama: `dtw_discreto`
Origen: Frente 1 de `contexto/Round-1/SINTESIS_REVIEWS.md` (comparación de variantes DTW); decisión del usuario: versión **D2 con patience** (descartadas D1-only y delta-only por evidencia empírica propia: A1/A2 disparan con progreso activo; delta nunca baja en MKP).

**Estado:** A10 implementada y documentada; forma parte de las tres estrategias estudiadas en la campaña post-OAT. La verificación independiente y el smoke específico de este plan aún requieren evidencia registrada.

## Regla de decisión (stateful, asimétrica)

- **Entrada** (exploit → explore): `D2_vs_const <= theta_c` sostenido durante `patience` iteraciones consecutivas (contador interno de persistencia).
- **Salida** (explore → exploit): `no_improve_len == 0` (mejora fresca).
- Warm-up (`ready=False`): mantener modo actual.
- `patience` tomado de `DTW_FIRE_D2.patience` (config central).
- `DECISION_RULE = "D2 <= theta_c sustained for patience iterations -> explore; improvement -> exploit"`

## Tareas

1. [x] Implementar paquete `binary_patient/` + cableado (`run_all.py`, `run_all_hpc.py`, `analisis/estadistico.py`) — delegado a gentle-ai-worker; los checks enfocados del momento quedaron citados en el mensaje de `9a20c42`, pero sin comando/salida cruda archivada (verificable solo vía tareas 2–3).
2. [ ] Verificación técnica independiente (gentle-ai-verify). Para cerrar: registrar el resultado y comando de la verificación independiente.
3. [ ] Smoke integrado en `run_all_hpc.py` con las 5 estrategias (mknapcb1[0], epochs=2) + análisis estadístico con la versión nueva. Para cerrar: registrar el comando, la salida de las cinco estrategias y la columna Binary-Patient en la estadística; la mención de un smoke en el documento de estrategia no sustituye esa evidencia aquí.
4. [x] Documentar A10 en `contexto/Round-1/ESTRATEGIA_A10_BINARY_PATIENT.md` (`9a20c42`; actualización de estado en `40920b8`).
5. [x] Commit work-unit en `dtw_discreto` y registrar evidencia (`9a20c42`).

## Evidencia de commits

- `9a20c42` — `feat: add Binary-Patient (A10) strategy with D2 patience`: paquete, cableado y documento de estrategia.
- `40920b8` — `docs(round-1): refresh review record for the post-OAT state`: actualiza el estado del documento de estrategia.
