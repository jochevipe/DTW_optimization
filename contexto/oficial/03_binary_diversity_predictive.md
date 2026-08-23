# Binary-Diversity-Predictive — DTW con conciencia de diversidad y detección predictiva

> **Documento oficial de implementación** (estrategia A10)
> Código: carpeta `binary_diversity_predictive/` (`config.py`, `runner.py`, `resultados.py`),
> helper compartido `mkp_common/diversity.py`, hook de observación en `mkp_common/runner.py`.
> Implementa el diseño propuesto en `estrategias_dtw/diversidad_y_deteccion_predictiva.md`,
> con desviaciones documentadas en §6.

---

## 1. Idea central

A10 extiende la señal del monitor DTW con un **segundo canal físico**: la diversidad
Hamming de la población binaria. La hipótesis validada por la sonda
(`analisis/diversidad_probe.py`) es que existen dos tipos de meseta de best-so-far que el
monitor no distingue:

- **Meseta muerta**: la población colapsó (diversidad ≈ 0). Ahí conviene explorar.
- **Meseta viva**: la población sigue dispersa trabajando (diversidad alta). Conmutar a
  explotación ahí destruye el salto que viene en camino.

El controlador es un **autómata de dos estados con base EXPLORE** cuyas transiciones están
compuertadas por diversidad y anticipadas por la tendencia de delta:

- **Nunca explota una población viva**: entrar a exploit exige mejora reciente Y diversidad
  colapsada respecto de la propia historia de la corrida.
- **Sale de exploración por evidencia observable**: colapso confirmado de meseta (disparo A4
  sostenido + diversidad mínima) o advertencia temprana predictiva (delta subiendo hacia su
  umbral antes de que la meseta se forme).
- La salida **jamás** usa `delta <= 0`: lección del Binary-Hysteresis original (condición
  geométricamente inalcanzable en la curva escalera del MKP).

## 2. Reglas de transición

```text
              ┌────────────────────────────────────────────────────────────┐
              │   rama predictiva: pendiente(últimos 5 deltas listos) > 0  │
              ▼   AND delta >= θδ                                          │
      ┌──────────────┐                                            ┌────────┴────────┐
      │    EXPLOIT   │   rama colapso: out["fire"] == True (A4    │     EXPLORE     │
      │              │   sostenido) AND div <= θ_div_low (P20)    │   (base)        │
      └──────────────┘───────────────────────────────────────────►│                 │
              ◄───────────────────────────────────────────────────└─────────────────┘
        mejora (no_improve_len == 0) AND div <= θ_div_high (P50)
```

| Estado actual | Condición | Nuevo estado |
|---|---|---|
| Warm-up (`ready=False`) | — | Permanece en su modo (`explore`; devuelve True) |
| `exploit` → `explore` | `out["fire"] == True` AND `div <= θ_div_low` (colapso de meseta muerta) **O** pendiente de los últimos 5 deltas listos `> 0` AND `delta >= θδ` (advertencia predictiva) | Exploración |
| `explore` → `exploit` | `no_improve_len == 0` (mejora) AND `div <= θ_div_high` | Explotación |

Detalles:

- Cada iteración lista el controlador mide la diversidad Hamming de la población actual vía
  `mkp_common.diversity.population_diversity` (fuente única compartida con la sonda) y
  mantiene historias rodantes propias de diversidad y delta (solo iteraciones listas,
  tope 100 muestras).
- Los umbrales de diversidad son **adaptativos por corrida**: `θ_div_low = P20` y
  `θ_div_high = P50` de la historia rodante. Comparar contra la propia historia evita fijar
  constantes globales frágiles entre instancias y metaheurísticas.
- El canal predictivo usa regresión lineal (pendiente por mínimos cuadrados) sobre los
  últimos 5 deltas listos; con menos de 5 muestras la rama está deshabilitada (exige
  evidencia antes de anticipar).
- Durante el warm-up el runner igualmente invoca al controlador (`decision_on_early=True`);
  responde con su modo actual sin tocar historias ni umbrales.
- Cada época recibe una instancia fresca del controlador vía `fire_fn_factory` (es stateful).
- El controlador necesita acceso a la población: el runner genérico invoca
  `fire_fn.bind(mh)` exactamente una vez tras `mh.initialize()` si el fire_fn expone `bind`.
  Sin bind, `__call__` falla con un error explícito. Las estrategias previas no exponen
  `bind` y no se ven afectadas.

## 3. Parámetros

| Parámetro | Valor | Rol |
|---|---|---|
| `_P_DIV_LOW` / `_P_DIV_HIGH` | 20 / 50 (percentiles) | Umbrales adaptativos de diversidad |
| `_FALLBACK_THETA_DIV_LOW` | 0.15 | Sin historia aún: orden de magnitud sobre las mesetas muertas medidas (conservador para confirmar colapso) |
| `_FALLBACK_THETA_DIV_HIGH` | 0.5 | Sin historia aún: máximo teórico de la Hamming normalizada (compuerta permisiva, equivale a no gatear) |
| `_TREND_WINDOW` | 5 | Muestras de delta para la pendiente predictiva |
| `_HISTORY_MAX` | 100 | Tope rodante de las historias (diversidad y delta) |
| Sensor DTW | `DTW_FIRE_D2` compartida | Misma configuración global de `mkp_common/config.py` |

Configuración experimental: `initial_mode="explore"`, `decision_on_early=True`,
`fire_fn_factory` por época — misma política del resto de versiones adaptativas.

## 4. Evidencia de la sonda que motiva las reglas

Sonda read-only `analisis/diversidad_probe.py` (16 corridas en modo fijo: 4 MHs × 2 modos ×
mknapcb1/mknapcb3 idx 0, seed 42, pop 20, 500 iteraciones), midiendo diversidad durante
rachas sin mejora de largo ≥ 10:

- **GA-exploit: mesetas MUERTAS** — Hamming media ≈ 0.008–0.014. La población colapsó;
  explorar ahí es el rescate correcto → motiva la rama (a) del retorno a explore.
- **PSO-explore/exploit: mesetas VIVAS** — Hamming media ≈ 0.17–0.21. El enjambre sigue
  disperso; conmutar a exploit destruye el salto en curso → motiva la compuerta de entrada
  a exploit (nunca explotar diversidad alta).

La sonda importa sus métricas de `mkp_common/diversity.py`, de modo que las cifras de la
evidencia y las decisiones del controlador usan exactamente la misma definición de
diversidad.

## 5. Integración

- Registrada como `binary_diversity_predictive` en `run_all_hpc.py` (`STRATEGIES`, runner
  dedicado, `dtw_window` en metadatos, plotter propio) y como etapa en `run_all.py`.
- Metadatos guardados con `decision_rule` canónico exportado como constante `DECISION_RULE`
  desde `binary_diversity_predictive/config.py`; ese mismo string valida
  `analisis/estadistico.py` (`DIVERSITY_PREDICTIVE_RULE`) y la estrategia figura en sus
  `sources` con exigencia de `dtw_window > 0`.
- Diagnóstico por iteración en `out["_diversity_state"]` (misma dict que `historial_dtw`)
  alimenta la consola y el panel 2 de los gráficos (delta + tendencia, diversidad vs
  umbrales P20/P50).

## 6. Desviaciones respecto del documento de diseño

Respecto de `estrategias_dtw/diversidad_y_deteccion_predictiva.md`:

1. **Salida de exploración**: el diseño proponía `Δ <= 0` (§5.4). No se implementó: es la
   condición muerta que bloqueó al Binary-Hysteresis original (en la curva escalera del MKP
   `delta = D1 − D2` permanece estrictamente positivo casi siempre). Se reemplazó por salida
   por mejora observable (`no_improve_len == 0`), además compuertada por diversidad.
2. **Trigger de exploración**: el diseño proponía `tendencia(Δ) creciente AND (Δ >= θδ OR
   diversidad <= θ_div)` como disparo único. La implementación lo separa en dos ramas OR del
   estado EXPLOIT — colapso confirmado (`fire` A4 sostenido AND `div <= P20`) y advertencia
   predictiva (pendiente creciente AND `delta >= θδ`) — porque el disparo A4 ya incorpora
   meseta + paciencia y es la señal validada por A9.
3. **Base del autómata**: el diseño describía un monitor reactivo con disparos de
   exploración; A10 adopta base EXPLORE (política experimental del estudio: comparar contra
   `vanilla_exploracion`).
4. **Patrón de referencia cóncavo** (§4 del diseño): fuera de alcance; el monitor queda
   intacto.
5. **Canal de entropía**: el helper calcula entropía y fitness-std, pero el controlador
   compuertera solo con Hamming (métrica con evidencia medida en la sonda).
6. **Validación**: el diseño sugería validar primero solo en PSO; la implementación corre
   las 4 MHs uniformemente por el pipeline genérico (la compuerta protege al PSO y las ramas
   (a)/(b) benefician a GA/DE/GWO según su dinámica de convergencia).
