# Binary-Hysteresis — Histéresis Asimétrica sobre el Disparo A4 Sostenido

> **Documento oficial de implementación y marco teórico** (estrategia A9)  
> Código: carpeta `binary_hysteresis/` (`config.py`, `runner.py`, `run.py`, `resultados.py`)  
> Reemplaza al diseño original basado en delta puro, que resultaba bloqueado (ver §5).

---

## 1. Idea Central y Filosofía de Control

Binary-Hysteresis es un **controlador con memoria (*stateful*) y conmutación asimétrica** que regula los modos de *Exploración* y *Explotación* de las metaheurísticas:

- **Entrar a Exploración exige evidencia acumulada**: Requiere la confirmación del disparo A4 completo del monitor (meseta prolongada + planitud $D_2$ + ausencia de rampa), sostenido durante $patience$ iteraciones consecutivas.
- **Salir de Exploración requiere un evento real de progreso**: Se mantiene explorando de manera **sostenida y protegida** hasta que la metaheurística efectivamente descubre una mejora en su mejor fitness histórico (`no_improve_len == 0`). En ese instante exacto, regresa a explotación para intensificar y refinar la nueva cuenca encontrada.

Esta asimetría crea un **pestillo (*latch*) temporal** que elimina por completo el *flickering* (cambios bruscos iteración a iteración) y protege la diversidad de la población.

---

## 2. Reglas de Transición de Estados

```text
                  ┌────────────────────────────────────────────────────────┐
                  │                                                        │
                  ▼                                                        │ SE DETECTA UNA MEJORA
         ┌─────────────────┐        ESTANCAMIENTO CONFIRMADO      ┌────────┴────────┐
         │     EXPLORE     │◄─────────────────────────────────────┤     EXPLOIT     │
         │ (Fase Sostenida)│       (out["fire"] == True de A4:    │ (Intensificación)│
         └─────────────────┘       plateau ∧ D2≤θc ∧ (D1≥θr ∨     └─────────────────┘
                                   δ≥θδ) durante patience iters)
```

| Estado Actual | Evento Evaluado | Nuevo Estado | Explicación Operativa |
|---|---|---|---|
| **Warm-up** (`ready=False`) | — | `explore` | Permanece en el modo inicial configurado hasta llenar la ventana $W$. |
| **`exploit` $\to$ `explore`** | `out["fire"] == True` | `explore` | Disparo A4 sostenido: estancamiento severo confirmado por el monitor. |
| **`explore` $\to$ `exploit`** | `no_improve_len == 0` | `exploit` | Salto de fitness: la exploración descubrió una solución mejor; se conmuta a refinarla. |
| **Cualquier otro caso** | No hay disparo ni mejora | Mantiene estado | Preserva el régimen activo sin oscilaciones espurias. |

---

## 3. Comparación Crítica: Binary-Hysteresis Actual vs Fire Binario Original (Notebook / A4)

Una duda conceptual frecuente es en qué se diferencia esta estrategia del **Fire Binario original del notebook**. La distinción es profunda:

| Dimensión | Fire Binario Original (Notebook / A4) | Binary-Hysteresis Actual (A9) |
|---|---|---|
| **Naturaleza del Controlador** | **Sin memoria (*stateless*)**: Evalúa `fire` instantáneo en cada iteración. | **Con memoria (*stateful*)**: Mantiene un estado persistente (`self.mode`). |
| **Entrada a Explore** | `out["fire"] == True` (3 condiciones $\land$ paciencia). | `out["fire"] == True` (exactamente la misma condición A4). |
| **Salida de Explore** | **Inmediata cuando `fire == False`**: Basta con que una sola de las 3 condiciones oscile para perder el modo. | **Solo ante progreso real**: Requiere `no_improve_len == 0` ($\text{fitness}(t) > \text{fitness}(t-1)$). |
| **Tiempo de permanencia en Explore** | **Efímero y frágil** (1 o 2 iteraciones aisladas). | **Sostenido y protegido** (todo el tiempo necesario hasta encontrar una mejor solución). |
| **Riesgo de *Flickering*** | **Extremo**: Oscila constantemente en el borde del umbral. | **Nulo**: La histéresis bloquea el estado hasta que haya un resultado. |
| **Impacto en MKP** | Fallaba porque la MH colapsa si pasa 95% del tiempo en exploit. | Da a la MH la diversidad necesaria para escapar de óptimos locales. |

---

## 4. Ejemplo Práctico Iteración a Iteración

Supongamos que la metaheurística cae en una meseta en la iteración 50:

| Iteración | Señal del Monitor DTW | Fire Binario Original (Notebook) | Binary-Hysteresis Actual |
|---|---|---|---|
| **50–52** | Meseta detectada, `fire=True` | Cambia a `explore` | Cambia a `explore` |
| **53** | La exploración generó dispersión; $D_1$ bajó levemente $\to$ `fire=False` (pero **no hubo mejora** de fitness). | ❌ **Vuelve a `exploit` prematuramente** (colapsando la población otra vez). | ✅ **Permanece en `explore`** (sigue buscando activamente). |
| **54–58** | `fire=False`, la población sigue buscando. | ❌ Sigue atrapada en `exploit`. | ✅ Sigue buscando en `explore`. |
| **59** | La MH encuentra un nuevo mejor fitness ($\text{fitness} \uparrow$). | Está en `exploit` por azar. | ✅ **Detecta la mejora y conmuta a `exploit`** para intensificar sobre el nuevo pico. |

---

## 5. Lección Aprendida: Por qué se descartó la versión previa con $\Delta \le 0$

El primer diseño de histéresis intentó usar:
- Entrada: $\Delta \ge \theta_\delta$
- Salida: $\Delta \le 0$

**El fallo matemático**: En MKP, la curva de mejor fitness es una **función escalera monótona** (derivada 0 casi en todo punto). Tras las primeras 50 iteraciones, $D_2 \to 0$ y $D_1$ es alto, por lo que $\Delta = D_1 - D_2 > 0$ se mantiene estrictamente positivo casi el 100% del tiempo.

La condición $\Delta \le 0$ era **geométricamente inalcanzable**, haciendo que el controlador quedara atrapado en `explore` para siempre (produciendo resultados bit-idénticos a `vanilla_exploracion`, comprobado en la campaña del 2026-08-22 con 20/20 comparaciones idénticas).

**La solución actual** resolvió esto reemplazando la condición de salida abstracta por la señal empírica directa de éxito: **la aparición de una mejora real de fitness (`no_improve_len == 0`)**.

---

## 6. Configuración e Integración en el Código

- **Configuración DTW**: Comparte la configuración global en `mkp_common/config.py` (`DTW_FIRE_D2`):
  `window=200` (o `50`), `band=2`, `min_slope=2.0`, `use_ddtw=True`, `adapt_thresholds=True`, `p_low=30`.
- **Parámetros A4**: `plateau_max=4`, `patience=2`.
- **Fábrica de Controladores**: Cada época recibe una instancia fresca e independiente vía `make_fire_fn(initial_mode="explore")` (`fire_fn_factory`).
- **Registro**: Integrada en `run_all_hpc.py` y `run_all.py` bajo la clave `"binary_hysteresis"`.
