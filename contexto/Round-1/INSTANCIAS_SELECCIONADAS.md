# Selección de instancias y Metodología Experimental — Campaña de revisión (Round 1)

Responde a **R1.3** (cobertura limitada de instancias) y **R1.4** (reconciliación de hiperparámetros).
La campaña de re-experimentos extiende la evaluación a **3 instancias representativas por archivo**:
**27 instancias en total** (9 archivos Chu & Beasley × 3 índices: `0`, `15` y `29`).

## 1. Criterio de selección de instancias

1. **Cobertura simétrica y determinista (`0`, `15`, `29`)**:
   - Cada archivo `mknapcb1.txt` a `mknapcb9.txt` contiene 30 instancias (índices `0` a `29`).
   - Se seleccionaron la **primera (`0`)**, la **intermedia (`15`)** y la **última (`29`)** instancia para todos los problemas sin excepción.
   - **Conservación histórica**: El índice `0` está presente en todos los casos, garantizando la comparabilidad directa con las tablas del manuscrito original.
   - **Representatividad**: Los índices `15` y `29` evalúan el comportamiento del controlador en el centro y extremo de la distribución de coeficientes de cada grupo benchmark.
2. **Balance de dimensiones**:
   - La grilla $(m \times n)$ queda perfectamente balanceada: 3 instancias para cada una de las 9 combinaciones ($m \in \{5, 10, 30\}$, $n \in \{100, 250, 500\}$).

## 2. Tabla oficial de instancias

| Archivo | Dimensión ($m \times n$) | Índices evaluados | Instancias por problema |
|---|---|---|---|
| `mknapcb1.txt` | $5 \times 100$  | `0`, `15`, `29` | 3 |
| `mknapcb2.txt` | $5 \times 250$  | `0`, `15`, `29` | 3 |
| `mknapcb3.txt` | $5 \times 500$  | `0`, `15`, `29` | 3 |
| `mknapcb4.txt` | $10 \times 100$ | `0`, `15`, `29` | 3 |
| `mknapcb5.txt` | $10 \times 250$ | `0`, `15`, `29` | 3 |
| `mknapcb6.txt` | $10 \times 500$ | `0`, `15`, `29` | 3 |
| `mknapcb7.txt` | $30 \times 100$ | `0`, `15`, `29` | 3 |
| `mknapcb8.txt` | $30 \times 250$ | `0`, `15`, `29` | 3 |
| `mknapcb9.txt` | $30 \times 500$ | `0`, `15`, `29` | 3 |

**Total:** 27 unidades de trabajo $\times$ 4 estrategias $\times$ 4 metaheurísticas $\times$ 31 épocas = **13.392 ejecuciones**.

## 3. Protocolo de semillas y diseño experimental pareado

1. **Repeticiones estocásticas independientes (31 épocas)**:
   - Cada metaheurística corre durante 31 épocas independientes (`epochs = 31`).
   - Las semillas por época son deterministas y consecutivas: época $k \in \{1, \dots, 31\}$ corre con semilla inicial `seed = k` (`seed = epoch + 1`), inicializando en `SEMILLA = 1`.
2. **Evaluación pareada (Paired Seeds)**:
   - Para una época fija $k$, **todas las estrategias comparadas** (`Vanilla-Explotación`, `Vanilla-Exploración`, `Binary-Simple`, `Binary-Hysteresis`) parten **exactamente de la misma población inicial y condiciones pseudoaleatorias**.
   - **Justificación inferencial**: El análisis estadístico no paramétrico de Wilcoxon (*Wilcoxon signed-rank test*) requiere muestras pareadas:
     $$\Delta_k = \text{Fitness}_{\text{DTW}}^{(k)} - \text{Fitness}_{\text{Baseline}}^{(k)}$$
     El emparejamiento por semilla elimina el ruido de inicialización y asegura que cualquier diferencia significativa sea atribuible de forma aislada al mecanismo adaptativo.

## 4. Hiperparámetros del controlador DTW reconciliados

De acuerdo a la solicitud R1.4, se reconciliaron los valores en `mkp_common/config.py`:
- **Longitud de ventana**: $W = 200$ iteraciones.
- **Percentiles adaptativos**: $p_{\text{low}} = 40.0$ (umbral $\theta_c$ de estancamiento/meseta) y $p_{\text{high}} = 60.0$ (umbral $\theta_r$ y $\theta_\Delta$ de progreso/rampa).
- **Ancho de banda Sakoe-Chiba**: $r = 2$.
- **Tolerancia de meseta**: $\pi_{\max} = 5$.
- **Paciencia de estancamiento**: $\tau_{\text{pat}} = 3$.
- **Presupuesto por corrida**: Población $N = 20$, iteraciones $T = 2000$.

## 5. Distribución de cómputo en HPC Océano (PUCV)

Para optimizar los tiempos de ejecución, la carga de 27 instancias se dividió en **3 trabajos simultáneos** de 3 problemas cada uno (9 instancias por trabajo), ejecutados en paralelo sobre nodos con 40 CPUs:

- **Trabajo 1** (`run_dtw1.sh`): Problemas `mknapcb1..3` ($m=5$).
  ```bash
  python run_benchmark_hpc.py --desde 1 --hasta 3 --indices 0 15 29 --cpus 40 --epochs 31
  ```
- **Trabajo 2** (`run_dtw2.sh`): Problemas `mknapcb4..6` ($m=10$).
  ```bash
  python run_benchmark_hpc.py --desde 4 --hasta 6 --indices 0 15 29 --cpus 40 --epochs 31
  ```
- **Trabajo 3** (`run_dtw3.sh`): Problemas `mknapcb7..9` ($m=30$).
  ```bash
  python run_benchmark_hpc.py --desde 7 --hasta 9 --indices 0 15 29 --cpus 40 --epochs 31
  ```

Lanzamiento automatizado de los 3 trabajos: `bash submit_jobs.sh` (o mediante SLURM Array en `run_dtw.sh`).

## 6. Trazabilidad y artefactos

- **Manifiesto de selección**: Registrado en `results/campaign_20260929_141957/instance_selection.json`.
- **Resultados primarios**: Serializados por estrategia e instancia en `results/<estrategia>/todos/mknapcb{i}_{idx}/comparacion_mhs_<run_id>/`.
- **Análisis estadístico**: Generado automáticamente en `results/estadistico/mknapcb{i}_{idx}/` conteniendo:
  - `tabla_estadistica.txt` (Wilcoxon signed-rank test y valores $p$ corregidos).
  - `tabla_matematica.txt` (estadísticas descriptivas: media, std, mejor, peor, gap).
  - `tabla_tiempos.txt` (tiempos de ejecución por MH).
  - `comparacion.png` y `comparacion.pdf` (boxplots comparativos con óptimo teórico).
