# Análisis de Señales DTW y Diseño de 2 Versiones Discretas

> Fecha: 2026-08-16  
> Objetivo: Entender matemáticamente qué miden las señales del `StagnationMonitor` y proponer **2 versiones discretas** con fundamento para superar a `vanilla_exploracion` (explore-only).

---

## 1. Cómo funciona el monitor DTW

### 1.1 Ventana de observación

En cada iteración `t` el monitor guarda el mejor fitness histórico `best_so_far[t]`. Cuando `t >= W` (con `W=20`) toma la ventana:

```
X = [best_so_far[t-W+1], ..., best_so_far[t]]
```

Todas las métricas se computan sobre `X`.

### 1.2 Derivative DTW (DDTW)

Se aplica `first_diff` a `X`:

```
diff(X) = [0, x[1]-x[0], x[2]-x[1], ..., x[W-1]-x[W-2]]
```

El primer elemento es `0` por convención (Keogh & Pazzani, 2001). Esto hace que la métrica sea **invariante a escala**: una meseta siempre tiene derivada ≈ 0, sin importar si el fitness vale 10 o 10 000.

### 1.3 Patrones de referencia

- **Rampa ideal** `R`: `r_i = x_0 + s_min * i`, con `s_min = 2.0`.
  - Representa progreso lineal constante.
  - `diff(R) = [0, s_min, s_min, ..., s_min]`.
- **Constante ideal** `C`: `c_i = x_0`.
  - Representa estancamiento total.
  - `diff(C) = [0, 0, 0, ..., 0]`.

### 1.4 Métricas

```
D1 = DDTW(X, R)  # distancia a la rampa ideal
D2 = DDTW(X, C)  # distancia a la meseta ideal
delta = D1 - D2  # balance
```

| Señal | D1 | D2 | delta | Interpretación |
|---|---|---|---|---|
| Rampa perfecta con pendiente `s_min` | ≈ 0 | alto | < 0 | Puro progreso → explotar |
| Constante | alto | ≈ 0 | > 0 | Puro estancamiento → explorar |
| Ruido alrededor de constante | alto | bajo | > 0 | Parece estancamiento, pero puede ser ruido |
| Progreso irregular (saltos) | alto | alto | ≈ 0 | Ambiguo, depende del umbral |

### 1.5 Umbrales adaptativos

```
theta_c   = P_30(H_D2)     # ¿qué es un D2 anormalmente bajo?
theta_r   = P_70(H_D1)     # ¿qué es un D1 anormalmente alto?
theta_delta = P_70(H_delta) # ¿qué es un delta anormalmente alto?
```

`P_p` es el percentil `p` del historial acumulado. Esto auto-calibra cada MH e instancia.

---

## 2. Diagnóstico de las estrategias actuales

### 2.1 A3 — Fire D₂

```python
fire = D2 <= theta_c
```

**Interpretación**: "¿la curva es plana?"

**Fortalezas**:
- Simple, un solo parámetro implícito (`p_low=30`).
- En datos reales ya supera a explore-only en GA/DE para mknapcb2/3/5/6/8/9.

**Debilidades**:
- **Falsos positivos por progreso lento**: una curva puede ser "plana" (bajo D2) sin estar estancada, por ejemplo cuando la MH avanza lentamente pero monótonamente.
- Ignora la señal `delta`, que dice si la curva es más plana que rampa.

### 2.2 A4 — Fire Binario (monitor interno)

```python
cond_plateau   = no_improve_len >= 4
cond_constant  = D2 <= theta_c
cond_ramp      = (D1 >= theta_r) OR (delta >= theta_delta)
fire           = (cond_plateau AND cond_constant AND cond_ramp) durante patience=2
```

**Interpretación**: "¿hay meseta real sin mejora, la curva es plana Y está lejos de la rampa?"

**Fortalezas**:
- Muy robusto contra falsos positivos.

**Debilidades**:
- **Demasiado conservador**: requiere que TRES condiciones se cumplan simultáneamente. Puede perder oportunidades de exploración temprana.
- En mknapcb4 no supera significativamente a explore-only.

---

## 3. Estudio matemático de reglas discretas candidatas

Para cada regla definimos el conjunto de señales `X` donde dispara:

| Código | Regla | Conjunto de fire | Comentario |
|---|---|---|---|
| A1 | `delta > 0` | `{X : D1 > D2}` | Dispara siempre que la curva sea más plana que rampa. Muy sensible a ruido. |
| A2 | `delta >= theta_delta` | `{X : D1 - D2 >= P_70(H_delta)}` | Versión adaptativa de A1. |
| A3 | `D2 <= theta_c` | `{X : D2 <= P_30(H_D2)}` | Actual. Mide planitud absoluta. |
| A5 | `D1/D2 > 1` | `{X : D1 > D2}` | Equivalente a A1 (ratio). |
| A6 | `(delta > 0) AND (D2 <= theta_c)` | `{X : D1 > D2} ∩ {X : D2 <= θ_c}` | Combina planitud relativa + absoluta. |
| A7 | `(delta >= theta_delta) AND (D2 <= theta_c)` | `{X : D1-D2 >= θ_δ} ∩ {X : D2 <= θ_c}` | Versión adaptativa de A6. |
| A8 | `delta >= theta_delta` | Igual que A2 | - |
| A9 | Hysteresis: entrar `delta >= θ_δ`, salir `delta <= 0` | Estado con memoria | Evita oscilaciones. |
| A13 | `(no_improve_len >= pmax) AND (D2 <= θ_c)` | Requiere meseta real | Más conservador que A3. |
| A14 | `D1/D2 > θ_ratio` con `θ_ratio = P_70(H_ratio)` | Adaptativo sobre ratio | Puede ser inestable si D2 ≈ 0. |

### 3.1 Relación de inclusiones

```
A7 ⊆ A6 ⊆ A3
A2 ⊆ A1
A9 (entrada) ⊆ A2
```

A7 es el más restrictivo de los basados en `delta`; A3 es el más permisivo. A6 está en el medio: exige que la curva sea plana (A3) **y** que sea más plana que rampa (A1).

### 3.2 Análisis empírico preliminar (GA, mknapcb4[0], 150 iter, 3 seeds)

| Regla | mean | diff vs base | Observación |
|---|---|---|---|
| A3 | 22 720.33 | +40.67 | Mejor que baseline |
| A6 | 22 720.33 | +40.67 | Igual que A3 en esta muestra |
| A7 | 22 720.33 | +40.67 | Igual que A3 en esta muestra |
| vanilla_exploracion | 22 679.67 | 0.00 | Baseline |
| A1 | 22 629.33 | -50.33 | Peor: dispara demasiado |
| A5 | 22 629.33 | -50.33 | Equivalente a A1 |

Esto confirma la hipótesis: **usar solo `delta > 0` es demasiado agresivo**. Combinar `delta` con `D2` (A6/A7) mantiene la robustez de A3.

---

## 4. Propuesta de 2 versiones discretas

### 4.1 Versión 1 — A6-Combined: `fire = (delta > 0) AND (D2 <= theta_c)`

**Nombre sugerido**: `binary_delta_d2` o `binary_combined`

**Lógica**:
- `D2 <= theta_c`: la curva es realmente plana (no es solo ruido o progreso irregular).
- `delta > 0`: la curva se parece más a una constante que a una rampa (estancamiento confirmado).

**Justificación matemática**:
- A3 usa un semiespacio en el espacio de formas: `{X : D2(X,C) <= θ_c}`.
- A6 intersecta con `{X : D1(X,R) > D2(X,C)}`, que es el semiespacio donde la forma es "más constante que rampa".
- Esto reduce falsos positivos cuando la curva es plana pero aún progresa lentamente.

**Implementación**:
```python
def fire_combined(out: dict) -> bool:
    return (out["delta"] > 0) and (out["D2_vs_const"] <= out["theta_c"])
```

### 4.2 Versión 2 — A9-Hysteresis: `explore` con delta, `exploit` con delta <= 0

**Nombre sugerido**: `binary_hysteresis` o `binary_delta_lock`

**Lógica**:
- Entrar a **explore**: `delta >= theta_delta` (estancamiento estadísticamente significativo).
- Salir de **explore** y volver a **exploit**: `delta <= 0` (la curva muestra progreso real).

**Justificación matemática**:
- `delta` es la señal más limpia de "forma de la curva".
- Sin histéresis, una oscilación rápida de `delta` alrededor de 0 provoca cambios de modo constantes (`flickering`), desperdiciando iteraciones.
- La histéresis crea una banda muerta: `[0, θ_δ]`. Solo entramos en explore cuando delta es alto; solo salimos cuando es claramente negativo.

**Implementación**:
```python
class HysteresisController:
    def __init__(self):
        self.mode = "exploit"

    def __call__(self, out: dict) -> bool:
        if not out.get("ready"):
            return self.mode == "explore"
        if self.mode == "exploit" and out["delta"] >= out["theta_delta"]:
            self.mode = "explore"
        elif self.mode == "explore" and out["delta"] <= 0:
            self.mode = "exploit"
        return self.mode == "explore"
```

**Nota**: la función de decisión debe mantener estado entre llamadas (no es pura). El runner genérico acepta cualquier `Callable[[Dict], bool]`, así que esto es compatible.

---

## 5. Por qué estas 2 versiones pueden vencer a vanilla_exploracion

### Sobre PSO

`vanilla_exploracion` es extremadamente fuerte en PSO para mknapcb1/4/7. La razón: PSO con parámetros de exploración (`w=0.9, c1=2.5, c2=0.5`) ya equilibra bien exploración/explotación, y forzar explotación (`w=0.729`) empeora los resultados.

**Implicación**: cualquier versión discreta que dispare "exploit" demasiado perderá contra el baseline en PSO. A6 y A9 son conservadoras, lo que minimiza el daño.

### Sobre GA/DE

`vanilla_exploracion` gana en instancias como mknapcb2/6, pero la explotación pura también es competitiva. La oportunidad de DTW es:
- Detectar cuándo la exploración está estancada.
- Cambiar a explotación **solo** durante esos periodos.
- Volver a exploración antes de que la diversidad se pierda.

A6 reduce falsos positivos respecto a A3; A9 evita el flickering. Ambas mantienen la MH en explore la mayor parte del tiempo (como el baseline), pero intervienen selectivamente cuando hay evidencia fuerte de estancamiento.

---

## 6. Plan de validación recomendado

1. **Implementar A6** en `binary_delta_d2/` (copiar estructura de `binary_simple/`).
2. **Implementar A9** en `binary_hysteresis/`.
3. **Mantener A3** en `binary_simple/` como referencia interna.
4. Ejecutar `run_all.py` (que ahora incluye el análisis estadístico automático) sobre las 9 instancias.
5. Comparar contra `vanilla_exploracion` con Wilcoxon + Holm-Bonferroni.
6. Si una versión no gana, ajustar:
   - `p_low` (30 → 40/50) para hacer theta_c más/menos restrictivo.
   - `plateau_max` y `patience` para A9.
   - Umbrales de salida de la histéresis (`0` → `theta_c/2`).

---

## 7. Referencias

- Sakoe & Chiba (1978): DTW original.
- Keogh & Pazzani (2001): Derivative DTW.
- `mkp_common/monitor.py`: implementación del monitor.
- `binary_simple/config.py`: implementación actual de A3.
