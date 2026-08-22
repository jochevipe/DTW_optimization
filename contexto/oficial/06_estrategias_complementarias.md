# Estrategias DTW Complementarias por Taxonomía de Metaheurísticas

> **Documento de diseño para agentes e investigación**  
> **Objetivo**: Fundamentar y formalizar la creación de **dos versiones complementarias de adaptación en tiempo de ejecución** basadas en el sensor DTW para superar consistentemente al baseline (`vanilla_exploracion`) en el *Multidimensional Knapsack Problem* (MKP).  
> **Principio de Invariancia**: El monitor DTW base (`StagnationMonitor`) y sus métricas ($D_1, D_2, \Delta, \theta_c, \theta_r, \theta_\delta$) permanecen **estrictamente idénticos**; la innovación radica exclusivamente en la lógica de decisión y control de parámetros.

---

## 1. Declaración de Principios y Arquitectura

```text
┌────────────────────────────────────────────────────────────────────────┐
│               SENSOR DTW BASE (StagnationMonitor)                      │
│   • Ventana W sobre best_so_far(t)                                     │
│   • DDTW (primeras diferencias) + Banda Sakoe-Chiba (w=2)              │
│   • Rampa R (progreso) vs Constante C (estancamiento)                  │
│   • Métricas: D1, D2, delta = D1 - D2                                  │
│   • Umbrales adaptativos: theta_c (P_low), theta_r / theta_delta (P_high)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Emite métricas numéricas
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
   ┌─────────────────────────────┐     ┌─────────────────────────────┐
   │  VERSIÓN 1: DTW-Pulse       │     │  VERSIÓN 2: DTW-PhaseLock   │
   │  (Control Reactivo Asimétrico)│    │  (Histéresis Multi-Umbral)  │
   ├─────────────────────────────┤     ├─────────────────────────────┤
   │ • Especialidad: Enjambres   │     │ • Especialidad: Evolutivos  │
   │   (BinaryPSO, BinaryDE)     │     │   (GeneticAlgorithm, BGWO)  │
   │ • Régimen base: EXPLORE     │     │ • Régimen base: EXPLOIT     │
   │ • Pulso temporal: EXPLOIT   │     │ • Fase sostenida: EXPLORE   │
   └─────────────────────────────┘     └─────────────────────────────┘
```

El monitor actúa como un **sensor de forma agnóstico** que no toma decisiones por sí mismo. Las *estrategias* son funciones o autómatas de decisión que interpretan el flujo de métricas para conmutar o modular los parámetros de la metaheurística en cada iteración $t$.

---

## 2. Diagnóstico: Por qué un único controlador falla y por qué `vanilla_exploracion` es tan fuerte

### 2.1 El Operador de Reparación Greedy como Explotador Implícito
En MKP, el operador `reparar(sol, inst)` descarta variables excedentes según su ratio beneficio/peso y luego añade greedymente ítems factibles de alto rendimiento.
* **Consecuencia**: `reparar()` es un proyector extremadamente agresivo hacia la frontera de factibilidad.
* **El peligro de la Explotación pura**: Si los individuos de la población se concentran en una región pequeña del espacio continuo/binario, `reparar()` recibe vectores casi idénticos y produce **exactamente la misma solución binaria**. La población colapsa a diversidad cero en menos de 20 iteraciones.
* **La fuerza de `vanilla_exploracion`**: Al forzar parámetros de alta exploración durante el 100% del tiempo, genera vectores de entrada dispersos. `reparar()` proyecta cada vector disperso en una esquina distinta del poliedro factible, logrando un baseline muy difícil de superar.

### 2.2 La Dinámica de Curva en Escalera (*Staircase*) en MKP
El avance del mejor fitness en optimización combinatoria restringida no es una curva suave; es una función en escalera:
$$\frac{d}{dt} \text{best\_fitness}(t) = 0 \quad \text{en la gran mayoría de iteraciones}$$
* En una ventana $W$, la distancia a la meseta $D_2$ es casi siempre pequeña y la distancia a la rampa $D_1$ es grande ($\Delta = D_1 - D_2 > 0$).
* **Falla de reglas ingenuas**: Condiciones de salida estáticas como $\Delta \le 0$ casi nunca se cumplen tras las primeras 50 iteraciones, bloqueando a controladores con histéresis simple en un solo modo durante toda la corrida.

### 2.3 Taxonomía y Modos de Falla de las 4 Metaheurísticas

| Metaheurística | Mecanismo Central | Modo de Falla Crítico | Régimen Óptimo de Búsqueda |
|---|---|---|---|
| **BinaryPSO** | Velocidades continuas $\to$ sigmoide | **Colapso de velocidad**: En exploit ($w=0.729$), las velocidades caen a 0 y todas las partículas se vuelven idénticas. | **Exploración de base** ($w=0.9, c_1=2.5$). Intensificación (exploit) solo en ráfagas cortas. |
| **BinaryDE** | Mutación diferencial continua $\to$ sigmoide | **Pérdida de varianza vectorial**: En exploit ($F=0.5$), las diferencias entre vectores se anulan. | **Exploración de base** ($F=0.9, CR=0.3$). Intensificación solo ante nuevas cuencas. |
| **GeneticAlgorithm** | Torneo, Crossover uniforme, Mutación | **Disrupción de esquemas (*building blocks*)**: En explore ($mut=0.15$), la alta mutación destruye soluciones buenas ya reparadas. | **Explotación de base** ($cx=0.9, mut=0.01$). Exploración sostenida solo ante estancamiento severo. |
| **BinaryGWO** | Jerarquía Alpha/Beta/Delta $\to$ sigmoide | **Oscilación por exceso de radio**: En explore ($a=2.0$), los lobos orbitan sin converger a la presa. | **Explotación/Convergencia de base** ($a=0.5$). Exploración controlada cuando el trío líder se estanca. |

---

## 3. Versión 1: DTW-Pulse (Control Reactivo Asimétrico)

### 3.1 Filosofía de Diseño
Diseñada prioritariamente para **metaheurísticas de enjambre y de espacio continuo-binario (BinaryPSO, BinaryDE)**.
* **Hipótesis**: Mantener a la población en modo de exploración permanente previene el colapso de diversidad. Cuando el sensor DTW detecta que se ha encontrado una nueva cuenca prometedora (salto de fitness o $D_2$ alto transitorio), se inyecta un **pulso breve de explotación** para refinar y exprimir localmente la solución. En cuanto la curva se aplana ($D_2 \le \theta_c$), se retorna inmediatamente a exploración.

### 3.2 Lógica de Transición de Estados

```text
               ┌────────────────────────────────────────────────────────┐
               │                                                        │
               ▼                                                        │ D2 <= theta_c
      ┌─────────────────┐                                      ┌────────┴────────┐
      │   EXPLORACIÓN   ├─────────────────────────────────────►│   EXPLOTACIÓN   │
      │ (Régimen Base)  │   fitness(t) > fitness(t-1)          │  (Pulso Corto)  │
      └─────────────────┘   O  D2 > theta_c_high               └─────────────────┘
```

### 3.3 Regla Algorítmica Formal

```python
class DTWPulseController:
    """
    Controlador Reactivo Asimétrico (Exploration-default).
    Régimen base: EXPLORE.
    Intensificación (EXPLOIT): Disparada por detección de progreso.
    Retorno a base: Disparado por planitud (D2 <= theta_c).
    """

    def __init__(self, p_low: float = 30.0, p_high: float = 80.0):
        self.mode = "explore"
        self.p_low = p_low
        self.p_high = p_high
        self.last_fitness = -float("inf")

    def __call__(self, out: dict, current_fitness: float) -> bool:
        """
        Retorna True para EXPLORE, False para EXPLOIT.
        """
        if not out.get("ready"):
            self.last_fitness = current_fitness
            return True  # Warm-up en modo explore

        theta_c_low = out.get("theta_c", 0.0)  # P_30 de D2
        d2 = out.get("D2_vs_const", 0.0)
        found_improvement = current_fitness > self.last_fitness
        self.last_fitness = current_fitness

        if self.mode == "explore":
            # Si hay un salto de mejora o la curva muestra alta actividad (lejos de meseta)
            if found_improvement or d2 > (theta_c_low * 2.0):
                self.mode = "exploit"  # Iniciar pulso de intensificación
        elif self.mode == "exploit":
            # Si la curva vuelve a aplanarse, finalizar el pulso y volver a explorar
            if d2 <= theta_c_low and not found_improvement:
                self.mode = "explore"

        return self.mode == "explore"
```

---

## 4. Versión 2: DTW-PhaseLock (Histéresis Multi-Umbral)

### 4.1 Filosofía de Diseño
Diseñada prioritariamente para **metaheurísticas evolutivas y jerárquicas (GeneticAlgorithm, BinaryGWO)**.
* **Hipótesis**: En algoritmos basados en crossover y jerarquías, el cambio de modo iteración a iteración (*flickering*) destruye la presión selectiva. Se requiere un régimen de **fases sostenidas**: operar en explotación para permitir la convergencia de esquemas, y conmutar a exploración sostenida únicamente cuando el estancamiento es estadísticamente profundo. La salida de exploración ocurre solo cuando se confirma una mejora real.

### 4.2 Banda de Histéresis sobre $D_2$ y Fitness
Para evitar la trampa de $\Delta \le 0$, la histéresis se define mediante dos umbrales adaptativos sobre $D_2$ combinados con la señal de mejora discreta:
* **Umbral de Estancamiento Profundo**: $\theta_{c,\text{low}} = P_{20}(H_{D_2})$
* **Umbral de Actividad / Progreso**: $\theta_{c,\text{high}} = P_{80}(H_{D_2})$
* **Banda Muerta**: El intervalo $[\theta_{c,\text{low}}, \theta_{c,\text{high}}]$ garantiza estabilidad y persistencia temporal.

```text
               ┌────────────────────────────────────────────────────────┐
               │                                                        │
               ▼                                                        │ fitness(t) > fitness(t-1)
      ┌─────────────────┐                                      ┌────────┴────────┐
      │   EXPLOTACIÓN   ├─────────────────────────────────────►│   EXPLORACIÓN   │
      │ (Régimen Base)  │   D2 <= theta_c_low                  │ (Fase Sostenida)│
      └─────────────────┘   AND no_improve >= plateau_min      └─────────────────┘
```

### 4.3 Regla Algorítmica Formal

```python
class DTWPhaseLockController:
    """
    Controlador de Fases Sostenidas con Histéresis Multi-Umbral (Exploitation-default).
    Régimen base: EXPLOIT.
    Escape (EXPLORE): Disparado por estancamiento profundo confirmado.
    Retorno a base: Disparado por descubrimiento de mejora o alta actividad D2.
    """

    def __init__(self, plateau_min: int = 5):
        self.mode = "exploit"
        self.plateau_min = plateau_min
        self.last_fitness = -float("inf")

    def __call__(self, out: dict, current_fitness: float) -> bool:
        """
        Retorna True para EXPLORE, False para EXPLOIT.
        """
        if not out.get("ready"):
            self.last_fitness = current_fitness
            return False  # Warm-up en modo exploit

        theta_c_low = out.get("theta_c", 0.0)  # P_low de D2
        d2 = out.get("D2_vs_const", 0.0)
        no_imp = out.get("no_improve_len", 0)
        found_improvement = current_fitness > self.last_fitness
        self.last_fitness = current_fitness

        if self.mode == "exploit":
            # Entrar a explore solo ante evidencia contundente de meseta
            if d2 <= theta_c_low and no_imp >= self.plateau_min:
                self.mode = "explore"
        elif self.mode == "explore":
            # Retornar a exploit cuando se encuentra una solución mejor o la curva acelera
            if found_improvement or d2 > (theta_c_low * 2.5):
                self.mode = "exploit"

        return self.mode == "explore"
```

---

## 5. Matriz de Complementariedad y Validación Científica

### 5.1 Cobertura de Fortalezas y Debilidades

| Escenario Experimental | Comportamiento DTW-Pulse (V1) | Comportamiento DTW-PhaseLock (V2) | Ganador Esperado |
|---|---|---|---|
| **BinaryPSO en instancias grandes (n=250, 500)** | Mantiene enjambre disperso; intensifica ante saltos. **Evita colapso a 0**. | Puede colapsar en fases de exploit prolongadas. | **DTW-Pulse (V1)** |
| **BinaryDE en instancias difíciles** | Preserva variabilidad en vectores continuos $F \cdot (x_2 - x_3)$. | Puede estancar diferencias vectoriales. | **DTW-Pulse (V1)** |
| **GA en instancias con alta interacción (m=30)** | La alta exploración base puede generar ruido en mutación. | **Protege los bloques constructivos**; explora solo cuando la meseta es total. | **DTW-PhaseLock (V2)** |
| **BinaryGWO en paisajes multimodales** | Mantiene lobos activos alrededor del espacio. | Permite que Alpha/Beta/Delta converjan de forma ordenada. | **DTW-PhaseLock (V2)** |

### 5.2 Argumentación para el Paper Académico
1. **Teoría del No Free Lunch en Control Adaptativo**:
   * No existe una única política monomodal de conmutación de parámetros que sea óptima para todas las clases de metaheurísticas.
   * La interacción entre el operador de reparación greedy y el mecanismo de representación (vectorial continua vs cromosómica discreta) impone requisitos de control asimétricos.
2. **El Sensor DTW como Plataforma Unificada**:
   * Ambas estrategias operan sobre las mismas señales del `StagnationMonitor` ($D_2$ derivativo y percentiles móviles).
   * El sensor DTW proporciona una descripción morfológica rica de la curva de convergencia que soporta tanto **control de alta frecuencia reactivo (pulsos)** como **control de baja frecuencia estructural (fases)**.

---

## 6. Instrucciones de Integración para el Agente

1. **Mantener `mkp_common/monitor.py` intacto**: El cálculo de $D_1, D_2, \Delta$ y percentiles no requiere modificaciones.
2. **Implementar las dos carpetas de estrategia**:
   * `dtw_pulse/`: Contiene `config.py`, `runner.py`, `resultados.py` (usando `DTWPulseController`).
   * `dtw_phaselock/`: Contiene `config.py`, `runner.py`, `resultados.py` (usando `DTWPhaseLockController`).
3. **Actualizar el Runner HPC (`run_all_hpc.py`)**:
   * Registrar ambas estrategias en el diccionario `STRATEGIES`.
   * Ejecutar la batería de pruebas sobre las instancias `mknapcb1..9`.
4. **Validación Estadística**:
   * Ejecutar `python -m analisis.estadistico` para verificar significancia estadística ($p < 0.05$ con corrección de Holm-Bonferroni) contra `vanilla_exploracion`.
