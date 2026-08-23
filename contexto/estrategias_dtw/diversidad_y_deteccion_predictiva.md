# Monitor DTW con Conciencia de Diversidad y Detección Predictiva

> Fecha: 2026-08-19
> Objetivo: Analizar críticamente la naturaleza de la convergencia de las metaheurísticas y proponer mejoras al `StagnationMonitor` para superar a `vanilla_exploracion` donde las versiones actuales fallan.

---

## 1. El error conceptual del monitor actual

El monitor observa **best-so-far**, que es **monótono por construcción**: solo sube, nunca baja. Por lo tanto, una "meseta" en best-so-far significa simplemente "hace N iteraciones que no aparece un nuevo máximo", y el monitor lo interpreta como estancamiento.

Existen dos tipos de meseta que el monitor actual no distingue:

1. **Meseta muerta**: la población colapsó en un óptimo local. Diversidad ≈ 0; toda la población converge al mismo punto. Aquí SÍ conviene explorar (o reiniciar parcialmente).
2. **Meseta viva**: best-so-far está quieto, pero la población sigue dispersa explorando regiones prometedoras. Es el preludio de un salto. Si se conmuta a explotación en este momento, se destruye el salto que venía.

El monitor actual no distingue entre ambas porque **no observa la diversidad poblacional**.

### 1.1 Explicación de los resultados observados

- **GA gana con DTW**: el GA sufre convergencia prematura real (población colapsa, meseta muerta). El DTW detecta la meseta y explora → rescata al GA. Ganancias fuertes y significativas en instancias grandes (mknapcb2/3/5/6/8/9, p ≈ 0.0000).
- **PSO pierde**: con `w=0.9, c1=2.5, c2=0.5` el enjambre ya está equilibrado. Sus mesetas de best-so-far son casi siempre **mesetas vivas** (el enjambre sigue viajando). El monitor lee "estancamiento" donde hay trabajo en curso, conmuta a explotación, reduce diversidad y arruina el salto. Por eso `vanilla_exploracion` es imbatible en PSO (26/27 comparaciones WORSE).
- **GWO neutro**: efectos pequeños, casi ningún resultado significativo.
- **DE dependiente de la instancia**: pierde en instancias chicas, gana en las grandes (mknapcb8/9).

---

## 2. Palanca crítica: diversidad como segundo canal

La señal que falta es **diversidad poblacional**. Con ella se construye el trigger correcto:

```
estancamiento real = meseta en best-so-far  AND  diversidad colapsada
```

Reglas de decisión:

- Meseta + diversidad alta → no intervenir (el swarm está trabajando).
- Meseta + diversidad baja → explorar (o reiniciar parcialmente).
- Progreso real (Δ negativo, D1 < D2) → explotar con confianza.

Para MKP binario, la diversidad es barata de medir:

- Distancia Hamming promedio entre soluciones de la población.
- Entropía por gen.
- Desviación estándar de los fitness de la población.

Costo: O(n²) por iteración con poblaciones de 20 — despreciable frente al costo del DTW.

Esta mejora ataca directamente el caso difícil: en PSO, el trigger nuevo casi nunca dispararía sobre mesetas vivas, por lo que no destruiría la exploración natural. Sería la versión "DTW consciente de diversidad".

---

## 3. Detección predictiva, no reactiva

El monitor actual reacciona **después** de que la meseta ya se formó. Pero las señales disponibles tienen dinámica propia: Δ = D1 − D2 sube *mientras* la curva se aplana.

La **tendencia de Δ** (pendiente de Δ entre ventanas consecutivas) funciona como early-warning: indica "nos acercamos a una meseta" antes de llegar.

```
if tendencia(Δ) creciente y acelerando → preparar exploración
if Δ cruza θ_δ → disparar exploración (confirmación)
```

Es el equivalente a detectar el codo de la curva de convergencia con anticipación. Un trigger así puede mejorar la **velocidad de convergencia**, no solo el fitness final — métrica que hoy no se explota en el paper.

---

## 4. El patrón de referencia está mal modelado

La "rampa ideal" es lineal con pendiente 2.0. Pero la convergencia real de una MH **no es lineal**: es logarítmica (rendimientos decrecientes).

Al final de la corrida, incluso una búsqueda sana se ve "plana" contra una rampa lineal, y el monitor dispara falsos positivos en la fase tardía.

Propuesta: patrón de referencia **cóncavo** (tipo power-law con tasa decreciente estimada online). Esto reduciría los falsos positivos tardíos.

---

## 5. Propuesta de experimento: versión A10

**Nombre sugerido**: `binary_diversity_predictive` (A10 — Diversity-Aware Predictive DTW)

Componentes:

1. Monitor DTW actual (D1, D2, Δ, umbrales adaptativos).
2. Canal nuevo: diversidad Hamming/entropía de la población, con umbral adaptativo propio θ_div.
3. Trigger de exploración:

```
tendencia(Δ) creciente AND (Δ ≥ θ_δ OR diversidad ≤ θ_div)
```

4. Salida de exploración: `Δ ≤ 0` (progreso real) — igual que la histéresis actual.
5. Patrón de referencia cóncavo opcional (sección 4).

**Validación**: probar primero en **PSO** (el caso donde todas las versiones actuales fallan). Si A10 gana ahí, la contribución es fuerte: "el DTW consciente de diversidad supera exploration-only donde las versiones naive fallan".

---

## 6. Próximos pasos

- [ ] Visualizar la diversidad poblacional de las corridas actuales para confirmar el diagnóstico de mesetas vivas/muertas.
- [ ] Implementar el canal de diversidad en el monitor.
- [ ] Implementar la versión A10 (`binary_diversity_predictive/`).
- [ ] Validar en PSO sobre las 9 instancias.
- [ ] Comparar contra `vanilla_exploracion` con Wilcoxon + Shapiro-Wilk (raw, sin corrección múltiple).
