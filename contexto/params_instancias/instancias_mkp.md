# Instancias MKP: OR-Library (Chu-Beasley)

## Descripción

Las instancias de Chu-Beasley son un benchmark del Multidimensional Knapsack Problem (MKP), descrito por P. C. Chu y J. E. Beasley (1998) y disponible en OR-Library.

## Instancias disponibles

La cantidad y las dimensiones se comprobaron en las cabeceras de `instances/mknapcb*.txt` (primera y segunda línea de cada archivo):

| Archivo | n (ítems) | m (restricciones) | Instancias |
|---------|-----------|-------------------|------------|
| `mknapcb1` | 100 | 5 | 30 |
| `mknapcb2` | 250 | 5 | 30 |
| `mknapcb3` | 500 | 5 | 30 |
| `mknapcb4` | 100 | 10 | 30 |
| `mknapcb5` | 250 | 10 | 30 |
| `mknapcb6` | 500 | 10 | 30 |
| `mknapcb7` | 100 | 30 | 30 |
| `mknapcb8` | 250 | 30 | 30 |
| `mknapcb9` | 500 | 30 | 30 |

**Total: 270 instancias** (9 archivos × 30). La campaña post-OAT selecciona tres índices por archivo (27 en total): ver [selección oficial](../Round-1/INSTANCIAS_SELECCIONADAS.md).

## Tightness (α) y valores de referencia

Según Chu y Beasley (1998), el *tightness* relaciona las capacidades con la suma de pesos de cada restricción:

```
capacity[i] = α × sum(weights[i])
```

La literatura describe niveles α = 0,25; 0,50; 0,75. Una menor capacidad restringe más el conjunto factible, pero la dificultad efectiva no se infiere solo de α. **No se verificó en los datos en esta revisión** qué nivel corresponde a cada instancia ni los valores de referencia (*best-known*/óptimos) publicados; por eso no se atribuye un α o una dificultad a cada archivo. El tercer número de la cabecera se presenta como valor de referencia en el formato descrito por Chu y Beasley (1998), sin certificar aquí su optimalidad ni cotejar todas las instancias.

## Formato del archivo

Cada archivo contiene 30 instancias; el esquema ilustrativo es:

```
30                          ← número de instancias en el archivo

100 5 24381                 ← n ítems, m restricciones, valor de referencia (ejemplo)
 92  81  98  54 ... 42      ← profits (pueden abarcar varias líneas)
 67  23  ...                ← weights restricción 1
 45  12  ...                ← weights restricción 2
 ...                        ← weights restricción m
 2137  1546  ...            ← capacities (m valores)

100 5 24274                 ← siguiente instancia (ejemplo)
...
```

Los números ilustran el orden del formato, no verifican los valores de referencia de esas instancias.

## Descarga

Fuente: [OR-Library](http://people.brunel.ac.uk/~mastjjb/jeb/orlib/mknapinfo.html).

## Referencia

Chu, P. C., & Beasley, J. E. (1998). “A Genetic Algorithm for the Multidimensional Knapsack Problem.” *Journal of Heuristics*, 4(1), 63–86.

## Métricas de evaluación

Para comparar una solución con el valor de referencia:

```
RPD = 100 × (valor de referencia - best_fitness) / valor de referencia
```

- **RPD = 0 %** → Alcanzó el valor de referencia.
- **RPD < 1 %** → Diferencia inferior al 1 % respecto de la referencia.

El promedio y el número de corridas deben indicarse para la campaña evaluada; no extrapolar resultados de los tres índices seleccionados a las 30 instancias del archivo.
