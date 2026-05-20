# Parámetros Estándar de Referencia

## Parámetros Compartidos

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| `pop_size` | 50 | Balance entre diversidad y costo computacional |
| `max_iter` | 500 | Suficiente para convergencia en n=100-250 |
| `runs` | 30 | Significancia estadística (30 repeticiones) |

---

## Binary PSO (Kennedy & Eberhart 1997, Clerc & Kennedy 2002)

| Parámetro | Valor | Referencia |
|-----------|-------|------------|
| `w` (inercia) | 0.729 | Clerc & Kennedy 2002 — constriction factor |
| `c1` (cognitivo) | 1.49445 | Clerc & Kennedy 2002 — constriction factor |
| `c2` (social) | 1.49445 | Clerc & Kennedy 2002 — constriction factor |
| `v_max` | 6.0 | Kennedy & Eberhart 1997 — limita velocidad |

### Ecuaciones
```
v[i] = w * v[i] + c1 * r1 * (pbest[i] - x[i]) + c2 * r2 * (gbest - x[i])
v[i] = clip(v[i], -v_max, v_max)
prob  = sigmoid(v[i]) = 1 / (1 + exp(-v[i]))
x[i]  = 1 si rand() < prob, sino 0
```

### Referencias
- Kennedy, J., & Eberhart, R. C. (1997). "A discrete binary version of the particle swarm algorithm." *IEEE SMC*.
- Clerc, M., & Kennedy, J. (2002). "The particle swarm - explosion, stability, and convergence." *IEEE TEC*, 6(1), 58-73.

---

## Genetic Algorithm (GA)

| Parámetro | Valor | Referencia |
|-----------|-------|------------|
| `crossover_rate` | 0.8 | Goldberg 1989 |
| `crossover_type` | Uniforme | Syswerda 1989 |
| `mutation_rate` | 1/n | Bäck 1993 — proporcional al tamaño del cromosoma |
| `tournament_size` | 3 | Miller & Goldberg 1995 |
| `elitism` | 1 | De Jong 1975 — preservar el mejor individuo |

### Operadores
```
1. Selección: torneo de tamaño 3
2. Crossover: uniforme con probabilidad 0.8 por par
3. Mutación: bit-flip con probabilidad 1/n por bit
4. Reemplazo: generacional con elitismo (preservar top-1)
```

### Referencias
- Goldberg, D. E. (1989). *Genetic Algorithms in Search, Optimization and Machine Learning*. Addison-Wesley.
- Syswerda, G. (1989). "Uniform Crossover in Genetic Algorithms." *ICGA*.
- Bäck, T. (1993). "Optimal Mutation Rates in Genetic Search." *ICGA*.

---

## Binary GWO (Mirjalili et al. 2014, Emary et al. 2016)

| Parámetro | Valor | Referencia |
|-----------|-------|------------|
| `a` | 2 → 0 (lineal) | Mirjalili et al. 2014 — decay lineal |
| (sin otros parámetros libres) | — | Diseño del algoritmo |

### Ecuaciones
```
a = 2 - 2 * (t / max_iter)
A = 2 * a * r - a          (r ∈ [0,1])
C = 2 * r                   (r ∈ [0,1])

X1 = X_alpha - A1 * |C1 * X_alpha - X[i]|
X2 = X_beta  - A2 * |C2 * X_beta  - X[i]|
X3 = X_delta - A3 * |C3 * X_delta - X[i]|
X_new = (X1 + X2 + X3) / 3

prob  = sigmoid(X_new) = 1 / (1 + exp(-X_new))
x[i]  = 1 si rand() < prob, sino 0
```

### Referencias
- Mirjalili, S., Mirjalili, S. M., & Lewis, A. (2014). "Grey Wolf Optimizer." *Advances in Engineering Software*, 69, 46-61.
- Emary, E., Zawbaa, H. M., & Hassanien, A. E. (2016). "Binary grey wolf optimization approaches for feature selection." *Neurocomputing*, 172, 371-381.

---

## DTW Monitor

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| `window` | 20 | Balance entre agilidad y estabilidad |
| `band` | 2 | Banda Sakoe-Chiba — reduce costo O(n²) a O(n·band) |
| `min_slope` | 0.0 | Se auto-calcula como 1% del rango / window |
| `use_ddtw` | True | DDTW usa derivadas — más sensible a cambios de tendencia |
