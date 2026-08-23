# Índice de contexto del proyecto

> **Fuente de referencia del estudio**: adaptación de modos (explorar/explotar) de
> metaheurísticas binarias que resuelven el MKP, guiadas por un sensor DTW de estancamiento.
> Este índice refleja únicamente lo **implementado actualmente**; los documentos obsoletos
> fueron eliminados (recuperables vía historial de git).

## Estado actual del estudio

- **Estrategias activas (5)**: `vanilla_explotacion`, `vanilla_exploracion` (baseline),
  `binary_simple` (A3), `binary_hysteresis` (A9, reescrita sobre el disparo A4 sostenido),
  `binary_diversity_predictive` (A10, diversidad poblacional + detección predictiva).
- **Metaheurísticas (4)**: BinaryPSO, GeneticAlgorithm, BinaryGWO, BinaryDE.
- **Sensor DTW** (`mkp_common/monitor.py`, intacto): métricas D1, D2, delta=D1−D2;
  umbrales adaptativos θc/θr/θδ; ventana actual 50 con DDTW activado (ver `mkp_common/config.py`); warm-up con placeholders finitos.
- **Política experimental**: las versiones adaptativas inician en explore y evalúan la
  decisión desde la iteración 1 (`decision_on_early=True`); controladores stateful aíslan
  su estado por época vía `fire_fn_factory`.
- **Estadística** (`analisis/estadistico.py`, `mkp_common/stats.py`): Shapiro-Wilk +
  Wilcoxon pareado crudo contra el baseline; selección segura de campañas por metadatos e
  intersección de `campaign_id`; tabla descriptiva de tiempos (`tabla_tiempos.txt`).
- **Fuera del estudio** (carpetas presentes pero no registradas): `dtw_pulse/`,
  `dtw_phaselock/`.

## Documentos vigentes

### Oficiales — estrategias implementadas
| Archivo | Contenido |
|---|---|
| `oficial/01_binary_simple_fire_d2.md` | Estrategia A3: fire = D2 ≤ θc. Teoría y configuración |
| `oficial/02_binary_hysteresis_a4.md` | Estrategia A9 reescrita: histéresis sobre el disparo A4 sostenido; incluye la lección del controlador delta bloqueado |
| `oficial/03_binary_diversity_predictive.md` | Estrategia A10: autómata explore-base con compuerta de diversidad Hamming (P20/P50 adaptativos) y rama predictiva de tendencia de delta; evidencia de la sonda y desviaciones del diseño |

### Fundamentos
| Archivo | Contenido |
|---|---|
| `oficial/09_dtw_fundamentos.md` | Teoría DTW: recurrencia, banda Sakoe-Chiba, DDTW, interpretación de D1/D2/Δ, umbrales percentiles, warm-up |
| `info_dtw/explicacion_params_dtw.md` | Explicación pedagógica de cada parámetro del monitor (`StagnationConfig`) |

### Metaheurísticas
| Archivo | Contenido |
|---|---|
| `oficial/mhs/05_mh_pso.md` | BinaryPSO: velocidades → sigmoide; parámetros exploit/explore |
| `oficial/mhs/06_mh_ga.md` | GeneticAlgorithm: torneo, crossover uniforme, mutación, elitismo |
| `oficial/mhs/07_mh_gwo.md` | BinaryGWO: jerarquía α/β/δ, coeficiente a fijo por modo |
| `oficial/mhs/08_mh_de.md` | BinaryDE: DE/rand/1/bin, representación dual continua/binaria |

### Datos y metodología
| Archivo | Contenido |
|---|---|
| `params_instancias/instancias_mkp.md` | Instancias Chu & Beasley mknapcb1–9: tamaños, tightness, óptimos conocidos, formato OR-Library |
| `miscelaneo/OII464__calse_3 (1).md` | Apuntes de cátedra: diseño experimental, semillas, Shapiro-Wilk, Wilcoxon, tamaños de efecto — base metodológica del pipeline estadístico |

## Notas de mantenimiento

- Al modificar una regla de decisión, actualizar: el string `decision_rule` en el saver de
  resultados, el registro de `run_all_hpc.py` y la validación de `analisis/estadistico.py`
  (deben ser idénticos). Cada estrategia exporta su string como constante canónica:
  `DECISION_RULE` (`binary_simple` usa el literal `"D2 <= theta_c"`, `binary_hysteresis` y
  `binary_diversity_predictive` lo exportan desde su `config.py`; `estadistico.py` replica
  el literal de A10 en `DIVERSITY_PREDICTIVE_RULE`).
- Las métricas de diversidad poblacional viven solo en `mkp_common/diversity.py`
  (helper compartido por la sonda `analisis/diversidad_probe.py` y A10). Los controladores
  que necesiten leer la población usan el hook `bind(mh)` del runner genérico: se invoca
  exactamente una vez tras `mh.initialize()` si el `fire_fn` expone `bind`.
- Los resultados JSON no persisten `historial_modos`; el análisis de comportamiento de
  modos requiere correr sondas ad-hoc o extender la persistencia.
- Ninguna MH resetea población al cambiar de modo: los cambios de modo actúan solo sobre
  parámetros.
