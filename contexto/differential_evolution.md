# Differential Evolution (DE) — De cero a MKP

## 1. ¿Qué es DE y por qué es diferente?

**Differential Evolution** (Storn & Price, 1997) es un algoritmo evolutivo poblacional para optimización. A primera vista parece "otro GA", pero su mecanismo de búsqueda es **radicalmente distinto**: en vez de cruzar padres o seguir líderes, **genera candidatos sumando la diferencia entre vectores de la población**.

Pensalo así con una analogía:

| MH | Cómo busca nuevas soluciones |
|----|------------------------------|
| **GA** | "Tomo dos padres buenos, mezclo sus genes, y muto un poco" |
| **PSO** | "Me muevo hacia donde vi lo mejor (pbest) y hacia donde el grupo vio lo mejor (gbest)" |
| **GWO** | "Sigo al líder alpha, al beta, al delta, y promedio sus posiciones" |
| **DE** | "Tomo 3 individuos al azar, calculo la DIFERENCIA entre 2, y se la SUMO al tercero" |

La clave está en esa **diferencia entre vectores**. Cuando la población está dispersa (diversa), las diferencias son grandes → pasos grandes → exploración. Cuando la población converge (todos se parecen), las diferencias son chicas → pasos finos → explotación. Es un mecanismo **auto-escalante** por naturaleza.

---

## 2. Los 3 operadores de DE

DE tiene exactamente 3 operadores que se aplican a CADA individuo en cada iteración:

### 2.1 Mutación Diferencial

Este es el operador que hace único a DE. Para cada individuo `x_i` de la población:

1. Elegir 3 individuos distintos al azar: `x_r1`, `x_r2`, `x_r3` (todos ≠ `x_i`)
2. Calcular el **vector mutante**:

```
v_i = x_r1 + F * (x_r2 - x_r3)
```

Donde `F ∈ [0, 2]` es el **factor de escala** (típicamente entre 0.4 y 1.0).

**¿Qué está pasando acá?** Estás tomando un individuo base (`x_r1`) y le sumás una perturbación proporcional a la diferencia entre otros dos (`x_r2 - x_r3`). La magnitud de esa perturbación depende de:
- `F`: cuánto amplifico la diferencia (parámetro tunable)
- `|x_r2 - x_r3|`: la diversidad actual de la población (auto-escalante)

```
Población diversa (inicio):
  x_r2 = [0.8, 0.1, 0.9, 0.3]
  x_r3 = [0.1, 0.7, 0.2, 0.8]
  diferencia = [0.7, -0.6, 0.7, -0.5]  ← GRANDE → pasos grandes

Población convergida (final):
  x_r2 = [0.51, 0.49, 0.52, 0.48]
  x_r3 = [0.50, 0.50, 0.50, 0.50]
  diferencia = [0.01, -0.01, 0.02, -0.02]  ← CHICA → pasos finos
```

### 2.2 Crossover (Recombinación)

Después de generar el mutante `v_i`, se cruza con el individuo original `x_i` para crear un **candidato de prueba** `u_i`:

```
Para cada dimensión j:
    if rand() < CR  o  j == j_rand:
        u_i[j] = v_i[j]    ← toma del mutante
    else:
        u_i[j] = x_i[j]    ← mantiene del original
```

Donde:
- `CR ∈ [0, 1]` es la **tasa de crossover** (qué fracción viene del mutante)
- `j_rand` es una dimensión elegida al azar que SIEMPRE viene del mutante (garantiza que `u_i ≠ x_i`)

**¿Qué controla CR?**
- `CR alto (0.9)`: casi todo viene del mutante → cambios grandes → exploración
- `CR bajo (0.1)`: casi todo se mantiene del original → cambios mínimos → explotación

### 2.3 Selección (Greedy 1-a-1)

La selección de DE es **determinística y elitista**, comparando el candidato contra su "padre":

```
if fitness(u_i) >= fitness(x_i):
    x_i = u_i      ← el candidato reemplaza al original
else:
    x_i = x_i      ← el original sobrevive
```

Esto es fundamentalmente distinto de GA (torneo entre toda la población) o PSO (no hay selección explícita, las partículas se mueven). Cada individuo compite **solo contra sí mismo**. No hay presión de selección global — solo mejoras locales.

---

## 3. Variantes de DE (Notación DE/x/y/z)

DE tiene una notación estándar para describir sus variantes:

```
DE / base / num_diferencias / crossover_type
```

| Componente | Opciones |
|-----------|----------|
| `base` | `rand` (aleatorio), `best` (mejor global), `current-to-best` |
| `num_diferencias` | `1` (una diferencia), `2` (dos diferencias sumadas) |
| `crossover_type` | `bin` (binomial), `exp` (exponencial) |

### Las más usadas:

**DE/rand/1/bin** (la clásica):
```
v_i = x_r1 + F * (x_r2 - x_r3)
```
- Base aleatoria, 1 diferencia, crossover binomial
- Muy exploratoria, buena diversidad

**DE/best/1/bin** (orientada al mejor):
```
v_i = x_best + F * (x_r1 - x_r2)
```
- Base = mejor global, 1 diferencia
- Más explotación (converge más rápido, pero puede quedar atrapada)

**DE/current-to-best/1/bin** (la equilibrada):
```
v_i = x_i + F * (x_best - x_i) + F * (x_r1 - x_r2)
```
- El individuo actual se mueve HACIA el mejor + perturbación aleatoria
- Buen balance exploración/explotación
- **Esta es la que recomiendo para nuestro caso con DTW**

### ¿Por qué DE/current-to-best/1/bin para MKP+DTW?

Porque tiene DOS componentes que el DTW puede modular:
1. `F * (x_best - x_i)`: atracción hacia el mejor (explotación)
2. `F * (x_r1 - x_r2)`: perturbación diferencial (exploración)

En lugar de un solo F, podemos usar dos:
- `F1` controla la atracción al mejor
- `F2` controla la perturbación aleatoria

Cuando DTW detecta estancamiento: subir F2, bajar F1 (más perturbación, menos atracción).
Cuando hay progreso: subir F1, bajar F2 (más convergencia, menos ruido).

---

## 4. DE Binario para MKP

DE fue diseñado para espacios continuos, pero se binariza para MKP. Hay varias estrategias:

### 4.1 Transfer Function (como PSO y GWO)

El enfoque más directo: usar el vector mutante continuo como entrada de una función sigmoid para decidir si cada bit es 0 o 1.

```
# Paso 1: Mutación diferencial en espacio continuo
v_i = x_r1 + F * (x_r2 - x_r3)   # v_i es un vector continuo

# Paso 2: Crossover con el original (en continuo)
u_i[j] = v_i[j] if rand() < CR else x_i_continuo[j]

# Paso 3: Binarizar con sigmoid
prob = sigmoid(u_i)  = 1 / (1 + exp(-u_i))
solucion_binaria[j] = 1 if rand() < prob[j] else 0
```

**Nota**: Necesitamos mantener una representación continua paralela para que la mutación diferencial funcione. Cada individuo tiene:
- `x_continuo`: vector real en R^n (para la aritmética de DE)
- `x_binario`: solución binaria en {0,1}^n (para evaluar fitness en MKP)

### 4.2 Angle Modulation (Pampara et al., 2005)

En vez de optimizar n bits directamente, DE optimiza 4 parámetros de una función trigonométrica que genera los bits. Reduce la dimensionalidad drásticamente pero pierde granularidad.

### 4.3 Operadores binarios nativos

Reemplazar la resta/suma vectorial por operadores XOR y lógica binaria:
```
diferencia = x_r2 XOR x_r3
mutante = x_r1 XOR (F_mask AND diferencia)
```
Donde `F_mask` es una máscara de bits generada con probabilidad F.

**Para nuestro proyecto: usaremos el enfoque 4.1 (Transfer Function)** porque:
- Es consistente con cómo binarizamos PSO y GWO
- Permite comparación justa entre MHs
- La mecánica diferencial se preserva fielmente

---

## 5. Los parámetros y qué controlan

DE tiene solo 3 parámetros fundamentales (mucho menos que GA o PSO):

| Parámetro | Rango típico | Efecto |
|-----------|-------------|--------|
| **NP** (tamaño población) | 5n a 10n (nosotros: 20) | Más NP = más diversidad base |
| **F** (factor de escala) | [0.4, 1.0] | Amplitud de la perturbación diferencial |
| **CR** (tasa de crossover) | [0.1, 0.9] | Fracción de dimensiones que cambian |

### F (Factor de Escala) — El acelerador

```
F bajo (0.4-0.5):
  → Diferencias pequeñas entre vectores se amplifican poco
  → Pasos cortos, búsqueda local, EXPLOTACIÓN
  → Converge más rápido pero puede estancarse

F alto (0.8-1.0):
  → Diferencias se amplifican mucho
  → Pasos largos, saltos grandes, EXPLORACIÓN
  → Más diversidad pero puede perder buenas soluciones
```

### CR (Tasa de Crossover) — El mezclador

```
CR bajo (0.1-0.3):
  → Pocas dimensiones cambian por iteración
  → Cambios quirúrgicos y localizados → EXPLOTACIÓN
  → Bueno para problemas separables (dimensiones independientes)

CR alto (0.7-0.9):
  → Muchas dimensiones cambian a la vez
  → Cambios masivos y globales → EXPLORACIÓN
  → Bueno para problemas no-separables (dimensiones correlacionadas)
```

### Interacción F × CR

| | CR bajo | CR alto |
|---|---------|---------|
| **F bajo** | Explotación máxima (búsqueda local fina) | Mezcla agresiva pero pasos cortos |
| **F alto** | Saltos grandes en pocas dims | Exploración máxima (diversificación total) |

---

## 6. Pseudocódigo completo (DE/rand/1/bin)

```
ENTRADA: función objetivo f, dimensión n, NP, F, CR, max_iter
SALIDA: mejor solución encontrada

1.  Inicializar población X = {x_1, ..., x_NP} aleatoriamente
2.  Evaluar fitness de cada x_i
3.  Registrar x_best = argmax(fitness)

4.  PARA iter = 1 hasta max_iter:
5.      PARA CADA individuo x_i (i = 1..NP):
6.
7.          // --- MUTACIÓN ---
8.          Elegir r1, r2, r3 ∈ {1..NP}, todos distintos y ≠ i
9.          v_i = x_r1 + F * (x_r2 - x_r3)
10.
11.         // --- CROSSOVER ---
12.         j_rand = randint(0, n-1)
13.         PARA j = 0 hasta n-1:
14.             if rand() < CR  o  j == j_rand:
15.                 u_i[j] = v_i[j]
16.             else:
17.                 u_i[j] = x_i[j]
18.
19.         // --- BINARIZACIÓN (para MKP) ---
20.         prob = sigmoid(u_i)
21.         sol_binaria = (rand(n) < prob).astype(int)
22.         sol_binaria = reparar(sol_binaria, inst)  // factibilidad MKP
23.
24.         // --- SELECCIÓN ---
25.         fit_candidato = evaluar(sol_binaria)
26.         if fit_candidato >= fitness(x_i):
27.             x_i = u_i           // reemplazar (en continuo)
28.             x_binario_i = sol_binaria
29.             fitness_i = fit_candidato
30.             if fit_candidato > fitness(x_best):
31.                 x_best = sol_binaria
32.
33.     RETORNAR x_best, fitness(x_best)
```

---

## 7. Mapeo a la interfaz BaseMH

```python
class BinaryDE(BaseMH):
    # --- Parámetros por modo ---
    F_EXPLOIT,  CR_EXPLOIT  = 0.5, 0.9
    F_EXPLORE,  CR_EXPLORE  = 0.9, 0.3

    def __init__(self, inst, rng, **kwargs):
        super().__init__(inst, rng)
        self.num_particulas = kwargs.get("num_particulas", 20)
        self.v_max = 6.0
        self.F = self.F_EXPLOIT
        self.CR = self.CR_EXPLOIT

        # Estado dual: continuo (para aritmética DE) + binario (para fitness MKP)
        self.poblacion_cont = None    # R^n — donde opera la mutación diferencial
        self.poblacion_bin = None     # {0,1}^n — para evaluar fitness
        self.fitness_pop = None
        self.gbest = None
        self.gbest_fitness = -inf

    def initialize(self):
        # Generar población continua aleatoria + binarizar + reparar
        ...

    def step(self) -> float:
        # Para cada individuo:
        #   1. Mutación diferencial (en espacio continuo)
        #   2. Crossover binomial (en espacio continuo)
        #   3. Binarizar con sigmoid
        #   4. Reparar factibilidad MKP
        #   5. Selección greedy 1-a-1
        ...
        return self.gbest_fitness

    def adapt(self, fire: bool):
        if fire and self.mode != "explore":
            self.mode = "explore"
            self.F = self.F_EXPLORE    # más perturbación
            self.CR = self.CR_EXPLORE  # menos crossover (cambios quirúrgicos)
        elif not fire and self.mode == "explore":
            self.mode = "exploit"
            self.F = self.F_EXPLOIT
            self.CR = self.CR_EXPLOIT

    def get_best(self):
        return self.gbest.copy(), self.gbest_fitness
```

---

## 8. ¿Por qué DE complementa bien a GA, PSO y GWO?

| Aspecto | GA | PSO | GWO | DE |
|---------|-----|-----|-----|-----|
| Mecanismo de búsqueda | Recombinación genética | Velocidad + atracción | Jerarquía de líderes | Diferencia de vectores |
| Selección | Torneo (competitiva) | No hay (implícita) | No hay (implícita) | Greedy 1-a-1 (local) |
| Usa info del mejor global | No directamente | Sí (gbest) | Sí (alpha) | No (DE/rand) o Sí (DE/best) |
| Auto-escalado | No | No | Parcial (a decrece) | Sí (diferencias ∝ diversidad) |
| Nro. de parámetros | 3+ (cx, mut, torneo, elitism) | 3 (w, c1, c2) | 1 (a) | 2 (F, CR) |
| Exploit/Explore | mut_rate y cx_rate | w, c1/c2 balance | a (2→0) | F y CR |

### Lo que DE aporta al paper que los otros NO tienen:

1. **Auto-escalado natural**: La perturbación disminuye automáticamente cuando la población converge (las diferencias se achican). Esto es una propiedad teórica única de DE.

2. **Selección local (greedy 1-a-1)**: No hay presión de selección global. Cada individuo solo compite contra su propia versión anterior. Esto preserva diversidad mejor que GA.

3. **Menos parámetros**: Solo F y CR. Más fácil de analizar cómo el DTW los modula.

4. **Operador de mutación basado en la población misma**: No usa distribuciones externas (como la gaussiana en ES) ni parámetros de velocidad (como PSO). La información de búsqueda EMERGE de la estructura de la población.

---

## 9. Referencias clave

- **Original**: Storn, R., & Price, K. (1997). "Differential Evolution – A Simple and Efficient Heuristic for Global Optimization over Continuous Spaces." *Journal of Global Optimization*, 11(4), 341-359.
- **Tutorial definitivo**: Das, S., & Suganthan, P.N. (2011). "Differential Evolution: A Survey of the State-of-the-Art." *IEEE Trans. Evolutionary Computation*, 15(1), 4-31.
- **DE binario para knapsack**: Pampara, G., Engelbrecht, A.P., & Franken, N. (2006). "Binary Differential Evolution." *IEEE CEC*.
- **DE/current-to-best**: Zhang, J., & Sanderson, A.C. (2009). "JADE: Adaptive Differential Evolution." *IEEE Trans. Evolutionary Computation*.
