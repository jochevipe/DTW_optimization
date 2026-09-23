# Binary-Simple — Estrategia de Adaptación por Umbral D₂

> **Clasificación**: Estrategia binaria A3 — Fire D2 puro  
> **Filosofía**: "La pregunta más directa posible: ¿está plana la curva?"

---

## 1. Posición en el Espacio de Diseño

Dentro de la familia de estrategias de adaptación basadas en DTW, Binary-Simple ocupa el extremo de **máxima simplicidad con señal informada**. Es más simple que Binary-Complex (A9), que usa el disparo A4 completo del monitor, pero más sofisticada que una decisión puramente basada en conteo de iteraciones sin mejora. Las baselines registradas son Vanilla-Exploration y Vanilla-Exploitation, no Binary-Complex.

En el espectro de las estrategias booleanas definidas en el marco teórico del proyecto:

| Estrategia | Señal usada | Complejidad |
|---|---|---|
| A1 — Delta puro | `δ > 0` | Mínima |
| A2 — Delta + theta | `δ ≥ θ_δ` | Baja |
| **A3 — D2 puro** | **`D₂ ≤ θ_c`** | **Baja** |
| A4 — disparo del monitor usado por Binary-Complex (A9) | D₂, D₁, δ, plateau, patience | Alta |
| A5 — Ratio normalizado + patience | `δ/θ_δ > 1` con patience | Media |

Binary-Simple implementa la estrategia **A3**, que se distingue por hacer exactamente una pregunta: **¿la curva de fitness se parece a una meseta?**

---

## 2. Fundamento Teórico

### 2.1 La señal D₂ como detector directo de estancamiento

El monitor DTW computa dos distancias fundamentales en cada iteración:

- **D₁**: distancia DTW entre la ventana de fitness y una **rampa ideal** (progreso constante). Un D₁ alto significa que la curva NO se parece a progreso.
- **D₂**: distancia DTW entre la ventana de fitness y una **meseta** (línea plana). Un D₂ bajo significa que la curva SÍ se parece a estancamiento.

Mientras que el disparo A4 del monitor exige evidencia simultánea de meseta prolongada, curva plana y ausencia de rampa, A3 se enfoca en una sola señal: **D₂ bajo**.

La intuición es directa: si la curva de convergencia es indistinguible de una línea plana según la métrica DTW, la metaheurística está estancada, independientemente de cuánto tiempo lleve así o de qué tan lejos esté de una rampa ideal.

### 2.2 ¿Por qué D₂ y no delta?

La métrica `δ = D₁ − D₂` combina dos señales en una sola. Aunque es informativa, introduce ambigüedad: un delta positivo puede deberse a D₁ alto (lejos de la rampa) o a D₂ bajo (cerca de la meseta), o a una combinación de ambos. Esto requiere umbrales cuidadosamente calibrados para distinguir las causas.

D₂, en cambio, responde una sola pregunta sin ambigüedad: **¿cuán plana es la curva?**. Es una señal más pura, más directa, y requiere menos calibración.

### 2.3 El rol del DDTW (Derivative DTW)

Binary-Simple opera con **DDTW activado** (`use_ddtw=True`). Esto es crucial porque:

- El DTW estándar compara valores absolutos del fitness. Si el fitness salta de 10,000 a 50,000 entre ejecuciones (diferentes instancias MKP), las distancias absolutas no son comparables.
- El DDTW aplica DTW sobre la **primera derivada** de las secuencias. Compara pendientes, no magnitudes. Una meseta tiene derivada ≈ 0 en cualquier escala.
- Esto hace que D₂ sea **invariante a la escala del fitness**, permitiendo que la misma configuración funcione en instancias MKP de distintos tamaños (n = 100 a n = 500) sin recalibración.

---

## 3. Mecanismo de Decisión

### 3.1 Regla de disparo

La regla es mínima:

```
fire = D₂ ≤ θ_c
```

Donde:
- **D₂** es la distancia DTW (derivative) entre la ventana de fitness actual y una meseta ideal
- **θ_c** es el umbral de D₂; pasa a ser adaptativo cuando hay suficiente historial de mediciones

Cuando `fire = True`, la metaheurística recibe la señal de cambiar sus parámetros al modo **explore**. Cuando `fire = False`, retorna al modo **exploit**.

### 3.2 El umbral adaptativo θ_c

θ_c no es un valor fijo. Se calcula como el **percentil móvil** del historial de D₂:

```
θ_c = percentile(D₂_hist, p_low)
```

Con el `p_low = 20` vigente, θ_c corresponde al percentil 20 del historial de D₂ una vez acumuladas 10 mediciones válidas. Antes se usa el umbral provisional `0.1 × W`. Así, durante la fase adaptativa **el sistema aprende qué significa "plano" en el contexto de esta ejecución específica**.

Esta adaptación es fundamental por tres razones:

1. **Invarianza a la escala del problema**: instancias con n=100 y n=500 producen rangos de fitness diferentes, y por tanto valores de D₂ en diferentes escalas. El percentil se adapta automáticamente.

2. **Invarianza a la metaheurística**: PSO, GA, GWO y DE tienen dinámicas de convergencia distintas. Lo que es "plano" para PSO puede no serlo para DE. El percentil captura el comportamiento específico de cada MH.

3. **Invarianza a la fase de búsqueda**: al inicio, cuando la MH explora, D₂ tiende a ser alto (la curva no es plana). En fases tardías, cuando converge, D₂ tiende a ser bajo. El percentil se ajusta dinámicamente a esta evolución.

### 3.3 Período de arranque

El monitor necesita `W = 100` valores de fitness para calcular DDTW (`ready=True` desde el valor número 100). El runner de Binary-Simple **inicializa en exploración** y llama a la regla A3 incluso antes de `ready`, con valores provisionales de D₂ y θ_c. Por eso no corresponde afirmar que el arranque transcurre en explotación ni que no hay decisiones hasta llenar la ventana. Las mediciones DDTW reales y los percentiles adaptativos llegan después: el percentil requiere 10 mediciones válidas.

---

## 4. Comportamiento Esperado

### 4.1 Comparación conceptual con Binary-Complex (A9)

| Aspecto | Binary-Simple (A3) | Binary-Complex (A9, disparo A4) |
|---|---|---|
| Señales requeridas | 1 (D₂) | 3 + patience |
| Hiperparámetros de decisión | 0 (θ_c es auto-adaptativo) | 2 (plateau_max, patience) |
| Latencia de detección | Baja (reacciona en cuanto D₂ cruza θ_c) | Alta (necesita acumular plateau + confirmaciones) |
| Riesgo de falsos positivos (hipótesis) | Mayor: una fluctuación de D₂ puede disparar | Menor: exige más condiciones |
| Riesgo de falsos negativos (hipótesis) | Menor ante mesetas detectadas por D₂ | Mayor si no se cumplen las condiciones adicionales |

La hipótesis a contrastar es si **la simplicidad de A3 conserva rendimiento** frente a A9. El monitor A4 incorpora meseta, rampa y confirmación temporal; su aporte frente a D₂ sola debe evaluarse experimentalmente.

### 4.2 Limitaciones conocidas

1. **Ignora el progreso**: A diferencia del disparo A4, A3 no consulta D₁ (distancia a la rampa). Esto significa que no distingue entre una meseta por convergencia al óptimo y una meseta por trampa local. En teoría, podría disparar exploración innecesaria cuando la MH ya encontró el óptimo global.

2. **Sin filtro temporal**: A3 no usa `plateau_max` ni `patience` en su decisión, aunque el monitor los configure para su disparo A4. Si D₂ fluctúa alrededor de θ_c, la MH podría oscilar entre modos exploit/explore.

3. **Sensibilidad al ruido**: en problemas donde el fitness tiene varianza alta entre iteraciones, D₂ puede ser ruidoso. El DDTW mitiga parcialmente esto al operar sobre derivadas, pero no elimina el problema por completo.

---

## 5. Relación con las Metaheurísticas

Binary-Simple es agnóstico a la MH subyacente. La misma señal D₂ ≤ θ_c se aplica a PSO, GA, GWO y DE sin modificaciones. Lo que cambia es **cómo responde cada MH** a la señal:

| MH | Efecto de fire=True (→ explore) |
|---|---|
| **PSO** | w↑ (0.729→0.9), c₁↑ (1.49445→2.5), c₂↓ (1.49445→0.5), con \|v\|≤6. Las partículas confían más en su historia personal y menos en el enjambre. |
| **GA** | crossover↓ (0.9→0.6), mutación↑ (0.01→0.15). Se reduce la herencia de los padres y se aumenta la perturbación aleatoria. |
| **GWO** | a↑ (0.5→2.0). Los lobos se alejan de los líderes alfa/beta/delta, explorando regiones más lejanas. |
| **DE** | F↑ (0.5→0.9), CR↓ (0.9→0.3). Mayor perturbación diferencial y menor herencia del padre. |

La transición es **discreta y global**: todos los individuos de la población cambian sus parámetros simultáneamente. No hay interpolación ni estados intermedios.

---

## 6. Rol en el Paper

Binary-Simple cumple tres funciones en la narrativa científica del estudio:

1. **Evaluación de la señal D₂**: permite comprobar si una sola métrica (D₂) puede guiar la adaptación sin las condiciones adicionales del disparo A4.

2. **Puente conceptual**: ocupa el punto medio entre la simplicidad ingenua (A1: `fire = δ > 0`) y la complejidad completa (A4). Si A3 funciona comparablemente a A4, se fortalece el argumento de que D₂ es la señal dominante.

3. **Ablación de señal única**: al comparar A3 con Binary-Complex (A9), que usa el disparo A4 completo del monitor, se puede medir si D₂ sola basta o si D₁, Δ y la persistencia aportan valor adicional.

---

## 7. Configuración

### Valores vigentes verificados

Fuente: [`mkp_common/config.py`](../../mkp_common/config.py) y [`binary_simple/config.py`](../../binary_simple/config.py). Son los valores **actuales del código**, no resultados de una campaña nueva.

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
| Percentil alto (`p_high`) | 80 | θ_r y θ_Δ del monitor; no intervienen en la regla A3 |
| Meseta (`plateau_max`) | 5 | Configurada en el monitor; no interviene en la regla A3 |
| Paciencia (`patience`) | 3 | Configurada en el monitor; no interviene en la regla A3 |

En ejecución individual, la MH predeterminada de Binary-Simple es DE. La configuración vigente compartida por las estrategias también figura en la [tabla del README](../../README.md#parámetros-y-precondición-experimental). Para sensibilidad de parámetros observada en la ronda OAT, ver [hallazgos OAT](../Round-1/HALLAZGOS_OAT.md); esos datos no sustituyen una evaluación post-OAT.

### Valores históricos / del paper (no vigentes)

| Fuente | Valor histórico | Diferencia con el código actual |
|---|---|---|
| Artículo, según [tabla del README](../../README.md#parámetros-y-precondición-experimental) | `W=200`, `p_low=40`, `p_high=60`; `T=2000`, `R=31`, población=20, `band=2`, `min_slope=2.0`, DDTW/umbrales adaptativos activados, `plateau_max=5`, `patience=3` | Solo `W`, `p_low` y `p_high` difieren de la configuración vigente. |
| Borradores anteriores de este documento | `W=20` en el texto de arranque y `W=50` en la antigua tabla; `p_low=30`, `plateau_max=4`, `patience=2` | Valores contradictorios o anteriores, **no** configuración de la campaña nueva. |

---

## 8. Preguntas Abiertas para el Análisis Experimental

- ¿Es A3 más reactivo que A9? ¿Se traduce esto en más entradas a exploración pero de menor duración?
- ¿En qué MHs funciona mejor? Una hipótesis es que MHs con convergencia más ruidosa se benefician del filtro A4 usado por A9.
- ¿El umbral adaptativo θ_c converge a un valor estable o fluctúa durante toda la ejecución?
- ¿Hay diferencia en el gap al óptimo entre A3 y A9 que justifique la complejidad adicional?

Documentos de las estrategias hermanas: [Binary-Complex (A9)](02_binary_complex_a9.md) y [Binary-Patient (A10)](../Round-1/ESTRATEGIA_A10_BINARY_PATIENT.md).
