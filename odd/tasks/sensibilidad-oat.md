# Feature: Sistema de sensibilidad OAT (Frente 3 — ablation de hiperparámetros)

Fecha de creación: 2026-09-18 · Rama: `dtw_discreto`
Origen: `contexto/Round-1/SINTESIS_REVIEWS.md` Frente 3 (R1.4, R2.3, R3.5). Decisión del usuario: OAT con vectores de valores preestablecidos (la alternativa — tuning automático irace/SMAC — no responde lo que piden los revisores).

## Diseño

- **Estrategia**: solo Binary-Complex (la del paper, Eq. 26).
- **Instancias**: mknapcb1[0, 15, 29] (1 archivo × 3 índices, n=100).
- **Grid (7 vectores × 4 valores, centrados en el paper)**:
  W {50,100,200,400}, banda {1,2,4,8}, s_min {1,2,3,4}, p_low {20,30,40,50}, p_high {50,60,70,80}, π_max {3,5,8,12}, τ_pat {1,2,3,5}.
- **Configuraciones OAT**: 1 base (valores del paper) + 3 variantes off-base por parámetro = **22 configs**.
- Overrides por env vars (`MKP_WINDOW`, `MKP_BAND`, ...) leídas en `mkp_common/config.py`; cada run lleva sus valores explícitos → el OAT no depende del estado del config local (que se alinea al final).
- Runner `sensibilidad/run_sensitivity.py` lanza `run_all_hpc.py` por (config, índice) con `--no-stats` y `MKP_CAMPAIGN_ID` propio por config; manifiesto en `results/sensibilidad/campaign_<id>/configs.json`.
- Análisis `sensibilidad/analizar.py`: tabla OAT por parámetro (mean best fitness por MH vs base) en markdown.
- Doc: `contexto/Round-1/SENSIBILIDAD_OAT.md`.

## Tareas

1. [ ] Env overrides del monitor en `mkp_common/config.py` (7 vars, defaults locales intactos).
2. [ ] `run_all_hpc.py`: flag `--no-stats` + respetar `MKP_CAMPAIGN_ID` del env si existe.
3. [ ] Módulo `sensibilidad/` (grid.py, run_sensitivity.py, analizar.py) con manifiesto y tabla OAT.
4. [ ] Doc `contexto/Round-1/SENSIBILIDAD_OAT.md`.
5. [ ] Verificación (worker + independiente) y smoke de overrides (epochs=1).
6. [ ] Commit work-unit y registrar evidencia.

## Evidencia de commits

- (commit abajo) — feat: sistema OAT (env overrides + sensibilidad/ + --no-stats + resume). Verificaciones: happy-path checks puros (grid 22 configs, overrides MKP_*, _environment, resume con manifest reutilizado, --no-stats), py_compile, revisión independiente (NEEDS FIX → corregido: resume real con --campaign). Sin experimentos locales: la campaña se corre en HPC.
