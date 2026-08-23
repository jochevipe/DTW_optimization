# Binary-Hysteresis — Histéresis sobre el disparo A4 sostenido

> **Documento oficial de implementación** (estrategia A9)
> Código: carpeta `binary_hysteresis/` (`config.py`, `runner.py`, `run.py`, `resultados.py`)
> Reemplaza al diseño original basado en delta puro, que resultó no funcional (ver §4).

---

## 1. Idea central

Binary-Hysteresis es un **autómata de dos estados con histéresis asimétrica** sobre las
señales del monitor:

- **Entrar a exploración exige evidencia fuerte**: el disparo A4 completo del monitor,
  sostenido durante varias iteraciones.
- **Salir de exploración solo requiere una mejora**: en cuanto aparece progreso nuevo,
  vuelve a explotar.

Esta asimetría evita el *flickering* (alternancia iteración a iteración) sin caer en
condiciones de salida inalcanzables.

## 2. Reglas de transición

```text
                ┌──────────────────────────────────────────────────┐
                ▼                                                  │ mejora
        ┌──────────────┐   fire del monitor (A4 sostenido)  ┌────────┴────────┐
        │    EXPLOIT   │   = plateau ∧ D2≤θc ∧ (D1≥θr ∨     │     EXPLORE     │
        │              │     δ≥θδ), held ≥ patience iters    │                 │
        └──────────────┘────────────────────────────────────►│                 │
                ◄──────────────────────────────────────────── └─────────────────┘
                                no_improve_len == 0 (mejora detectada)
```

| Estado actual | Condición | Nuevo estado |
|---|---|---|
| Warm-up (`ready=False`) | — | Permanece en su modo inicial (`explore`) |
| `exploit` → `explore` | `out["fire"] == True` (disparo A4 sostenido del monitor) | Exploración |
| `explore` → `exploit` | `no_improve_len == 0` (mejora del mejor fitness) | Explotación |

Detalles:

- `out["fire"]` es calculado por `StagnationMonitor` y ya incorpora la paciencia:
  `trigger_streak >= patience` con las tres condiciones booleanas activas.
- El controlador arranca en `explore` (`initial_mode="explore"`), consistente con la
  política experimental de comparar contra `vanilla_exploracion`.
- Durante el warm-up el runner invoca igualmente al controlador (`decision_on_early=True`),
  que responde con su modo actual hasta tener datos reales.
- Cada época recibe una instancia fresca vía `fire_fn_factory` (el controlador es stateful).

## 3. Cobertura de métricas

Con esta estrategia, el estudio cubre todo el espacio de señales del sensor:

| Estrategia | Señal usada | Rol en el estudio |
|---|---|---|
| Binary-Simple (A3) | Solo `D2 ≤ θc` | Ablation de métrica única |
| Binary-Hysteresis (A9) | `D1`, `D2`, `delta` + meseta + paciencia (regla A4 completa) | Estrategia de señal completa |

## 4. Por qué se reescribió (lección aprendida)

El diseño original usaba histéresis pura sobre delta: entrar a explore cuando
`delta ≥ θδ`, salir cuando `delta ≤ 0`. En la curva escalera del MKP, `delta = D1 − D2`
es **estrictamente positivo casi siempre** (la ventana se parece más a una constante que
a una rampa), por lo que la condición de salida era inalcanzable: el controlador quedaba
bloqueado en explore y producía resultados **bit-idénticos a `vanilla_exploracion`**
(confirmado empíricamente en la campaña de 2026-08-22: 20/20 comparaciones con diff ±0.0
y p=1.0).

La regla A4 del monitor resuelve esto porque sus tres condiciones booleanas sí se activan
en estancamiento real, y la salida depende de progreso observable (mejora), no de un
evento geométricamente raro.

## 5. Configuración del sensor

Comparte la configuración DTW global de `mkp_common/config.py` (`DTW_FIRE_D2`):
`window=50`, `band=2`, `min_slope=2.0`, `use_ddtw=True`, `adapt_thresholds=True`,
`p_low=30`. Los parámetros de la regla A4 (`plateau_max=4`, `patience=2`) viven en la
configuración del monitor (`mkp_common/config.py`).

## 6. Integración

- Registrada como `binary_hysteresis` en `run_all_hpc.py` (`STRATEGIES`) y como etapa en `run_all.py`.
- Metadatos guardados con `decision_rule` canónico exportado como constante desde
  `binary_hysteresis/config.py`; ese mismo string valida `analisis/estadistico.py`.
- Los strings legacy de campañas antiguas siguen aceptándose, pero la intersección estricta
  de `campaign_id` impide mezclar campañas viejas (controlador muerto) con nuevas.
