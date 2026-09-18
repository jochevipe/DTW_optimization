# Estrategia A10 — Binary-Patient (D2 + patience)

Nueva variante DTW agregada para la revisión (Frente 1, comparación de variantes).
Paquete: `binary_patient/` · Label: **Binary-Patient** · Código de estrategia: **A10**.

## Motivación

- **Binary-Simple (A3)** decide con `D2 <= theta_c` **sin memoria**: cada iteración es
  independiente, lo que puede producir flickering (entrar/salir de explore por ruido
  de la señal D2).
- **Binary-Complex (A9)** entra solo con el trigger A4 sostenido del monitor
  (meseta ∧ D2≤θc ∧ (D1≥θr ∨ δ≥θδ)) y sale con mejora — entrada muy estricta.
- **A10** ocupa el punto intermedio: misma señal que A3 (D2 puro) pero con la
  **memoria de persistencia** de A9. Responde directamente a la crítica de
  sensibilidad/robustez del umbral (R1.4/R2.3) mostrando el efecto de agregar
  paciencia a la regla más simple.

## Regla formal (stateful, asimétrica)

Sea τ = `patience` (config central `DTW_FIRE_D2.patience`) y `streak` el número de
iteraciones listas consecutivas con `D2_vs_const <= theta_c`:

- **Entrada** (exploit → explore): `streak >= τ`
- **Salida** (explore → exploit): `no_improve_len == 0` (mejora fresca)
- **Warm-up** (`ready == False`): se mantiene el modo y el streak actual.

```text
DECISION_RULE = "D2 <= theta_c sustained for patience iterations -> explore; improvement -> exploit"
```

| | A3 Binary-Simple | A10 Binary-Patient | A9 Binary-Complex |
|---|---|---|---|
| Señal de entrada | D2 ≤ θc | D2 ≤ θc sostenido τ iters | A4 sostenido (meseta ∧ D2 ∧ rampa/delta) τ iters |
| Memoria | No | Streak propio | Streak del monitor |
| Salida | D2 > θc | Mejora | Mejora |

## Estado

- [x] Implementada y cableada (`run_all.py`, `run_all_hpc.py`, `analisis/estadistico.py`).
- [x] Verificada (unit del controlador, smoke integrado 5 estrategias, estadística incluye la columna Binary-Patient).
- [ ] Pendiente: corrida HPC completa (27 instancias × 31 epochs) junto con las otras 4 versiones.
