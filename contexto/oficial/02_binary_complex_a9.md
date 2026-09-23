# Binary-Complex (A9) — Histéresis sobre el disparo DDTW completo

> **Controlador estudiado**: `binary_complex/` (`config.py`, `runner.py`, `run.py`, `resultados.py`).
> **Regla**: entrada con el disparo A4 sostenido del monitor; salida al detectar una mejora.

## 1. Decisión y estados

Binary-Complex conserva el modo entre iteraciones. El monitor DDTW compara la ventana de mejor fitness con una meseta (`D₂`) y una rampa (`D₁`), y calcula `δ = D₁ − D₂`. Su disparo A4 exige simultáneamente:

```text
no_improve_len ≥ plateau_max
∧ D₂ ≤ θ_c
∧ (D₁ ≥ θ_r ∨ δ ≥ θ_δ)
```

El monitor cuenta las iteraciones consecutivas en que se cumplen las tres condiciones. Solo entrega `fire=True` cuando `trigger_streak ≥ patience`. Con umbrales adaptativos, θ_c usa el percentil bajo del historial de D₂; θ_r y θ_δ usan el percentil alto de D₁ y δ respectivamente. Para el cálculo inicial se usan umbrales provisionales hasta acumular 10 mediciones válidas.

El controlador A9 aplica una **histéresis asimétrica** a ese disparo:

| Modo actual | Condición (`ready=True`) | Modo siguiente |
|---|---|---|
| `exploit` | `fire=True` (A4 sostenido) | `explore` |
| `explore` | `no_improve_len == 0` (nuevo mejor fitness) | `exploit` |
| Cualquiera | Ninguna transición anterior | Conserva el modo |

Cada corrida comienza en `explore`. Antes de completar la ventana, el monitor no tiene métricas DDTW válidas (`ready=False`) y el controlador conserva ese modo inicial; no presupone explotación durante el arranque. El runner crea un controlador nuevo por época para no compartir estado entre semillas. Al entrar en exploración, las MH cambian sus parámetros discretamente; al salir, vuelven a los parámetros de explotación. A diferencia de [Binary-Simple (A3)](01_binary_simple_fire_d2.md), A9 no sigue cada fluctuación de D₂: requiere evidencia sostenida para entrar y una mejora para salir. [Binary-Patient (A10)](../Round-1/ESTRATEGIA_A10_BINARY_PATIENT.md) utiliza D₂ con paciencia en vez del disparo A4 completo.

## 2. Configuración

### Valores vigentes verificados

Fuente: [`mkp_common/config.py`](../../mkp_common/config.py) y [`binary_complex/config.py`](../../binary_complex/config.py). Son valores **actuales del código**, no resultados de una campaña nueva.

| Parámetro | Valor vigente | Alcance |
|---|---:|---|
| Iteraciones (`T`) | 2000 | Presupuesto por corrida |
| Épocas (`R`, semillas 1..31) | 31 | Corridas independientes |
| Población | 20 | Individuos por MH |
| Ventana (`W`) | 100 | Valores de fitness para calcular DDTW |
| Banda (`band`) | 2 | Banda Sakoe–Chiba |
| Pendiente (`min_slope`) | 2.0 | Rampa ideal |
| DDTW (`use_ddtw`) | Activado | Comparación de pendientes |
| Umbrales adaptativos (`adapt_thresholds`) | Activados | Percentiles tras 10 mediciones válidas |
| Percentil bajo (`p_low`) | 20 | θ_c para D₂ |
| Percentil alto (`p_high`) | 80 | θ_r para D₁ y θ_δ para δ |
| Meseta (`plateau_max`) | 5 | Iteraciones consecutivas sin mejora |
| Paciencia (`patience`) | 3 | Confirmaciones consecutivas del disparo A4 |

En ejecución individual, la MH predeterminada de Binary-Complex es DE. La [tabla del README](../../README.md#parámetros-y-precondición-experimental) resume la configuración compartida; los [hallazgos OAT](../Round-1/HALLAZGOS_OAT.md) documentan sensibilidad observada en la ronda anterior, no resultados de la campaña post-OAT.

### Valores históricos / del paper (no vigentes)

| Fuente | Valor histórico | Diferencia con el código actual |
|---|---|---|
| Artículo, según [tabla del README](../../README.md#parámetros-y-precondición-experimental) | `W=200`, `p_low=40`, `p_high=60`; `T=2000`, `R=31`, población=20, `band=2`, `min_slope=2.0`, DDTW/umbrales adaptativos activados, `plateau_max=5`, `patience=3` | Solo `W`, `p_low` y `p_high` difieren de la configuración vigente. |
| Documento A4/A9 anterior | `W=200` o `W=50`, `p_low=30`, `plateau_max=4`, `patience=2` en sus ejemplos de configuración | Borrador previo, **no** configuración vigente. |

## 3. Historia

Este documento reemplaza `02_binary_hysteresis_a4.md`. El módulo anterior `binary_hysteresis/` fue eliminado en el commit `fe12f2f`; **la implementación vigente es `binary_complex/` y su identidad es A9**. El disparo A4 sigue siendo la regla del monitor que A9 usa para entrar en exploración, no el nombre de una estrategia registrada aparte. Las dos baselines registradas son `vanilla_exploracion` y `vanilla_explotacion`.
