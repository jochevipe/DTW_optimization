# Guía directa de cambios al manuscrito: cortar, pegar o no tocar

Esta guía reemplaza el plan anterior más largo para que puedas trabajar directamente en `template.tex`. Cubre los 19 IDs de `paper/comentarios_respuestas.md`.

## Antes de editar

- Las líneas corresponden al `template.tex` actual y se moverán al editar.
- **NO CORTAR** significa que no encontré una frase incorrecta que convenga eliminar. En esos casos se agrega una aclaración, o no se cambia nada si el manuscrito ya atiende el punto.
- **PEGAR** significa que el bloque LaTeX está listo para insertar, según el contenido comprobado del manuscrito.
- **BLOQUEADO** significa que no pegues un texto factual hasta verificar datos, código, citas o una decisión de autor. No inventes los valores entre corchetes.
- **En esta revisión no se modificó `template.tex`.** Las respuestas de `paper/comentarios_respuestas.md` son borradores; no afirmes que estos cambios ya fueron realizados.

## Revisor 1

### R1.1 — La evidencia estadística no prueba superioridad global

**Ubicación:** abstract, líneas 136–137. La frase actual es:

```latex
while trajectory-driven adaptation provides significant improvements in
multiple experimental conditions.
```

**Qué hacer:** no la reemplaces todavía. Primero verificá las pruebas pareadas y si se corrigió la multiplicidad. El manuscrito ya informa que Friedman no demuestra superioridad global, en líneas 1401–1410.

**Estado:** **BLOQUEADO por verificación estadística.** Si esa frase no se sostiene después del análisis, reemplazala por un resultado estrictamente confirmado. No pegues una afirmación nueva de significancia sin recalcular.

### R1.2 — Falta comparar con controladores adaptativos externos

**Cortar:** nada.

**Pegar:** al final de Limitations (sección que empieza aproximadamente en la línea 1669):

```latex
This study does not compare the proposed controller with representative external adaptive parameter-control methods. The experiments therefore do not establish an advantage over such methods.
```

Esto deja clara la limitación; no reemplaza ejecutar la comparación pedida.

### R1.3 — Solo nueve instancias y un problema

**Cortar:** nada. Conservá la descripción del protocolo experimental.

**Pegar:** en Limitations, inmediatamente después de la oración que empieza `Third, the experimental study is restricted to the MKP...` (aprox. líneas 1675–1680):

```latex
The evaluation uses the first instance from each of nine Chu--Beasley benchmark groups; additional instances within those groups were not evaluated.
```

No afirmes generalización a otros problemas.

### R1.4 — Falta análisis de sensibilidad

**Cortar/pegar:** nada nuevo. Limitations ya dice que la sensibilidad a ventana, referencias, percentiles y persistencia queda por estudiar sistemáticamente (aprox. líneas 1685–1688).

**Qué hacer:** conservá esa oración. No agregues que los parámetros son robustos u óptimos. Los resultados OAT anotados en los borradores no se verificaron acá y no justifican por sí solos esas afirmaciones.

### R1.5 — Efectos diferentes según el algoritmo

**Cortar/pegar:** nada nuevo. El manuscrito ya presenta diferencias por algoritmo y advierte que no hay garantía de mejora universal (Results y Conclusions, aproximadamente líneas 1548–1581 y 1620–1665).

**Qué hacer:** conservá el análisis descriptivo. No agregues una explicación causal sobre población, reparación o sensibilidad: no está demostrada por los resultados descritos.

## Revisor 2

### R2.1 — Falta una hoja de ruta de secciones listo

**Cortar:** nada.

**Pegar:** al final de Introduction, **después** del `\end{itemize}` de contribuciones (línea 235) y **antes** de `\section{Related Work}` (línea 237):

```latex
The remainder of this paper is organized as follows. Section~\ref{sec:proposed_approach} presents the controller, and Section~\ref{sec:experimental_setup} describes the experimental design. Section~\ref{sec:results} reports and discusses the findings. Finally, Section~\ref{sec:conclusions} (Conclusions and Future Work) concludes the paper and outlines its limitations and future directions.
```

### R2.2 — Falta una ablación que retire DDTW

**Cortar:** nada. No describas Binary-Simple versus Binary-Complex como una ablación de DDTW.

**Pegar:** en Limitations, cerca de R1.2/R2.4 (sección alrededor de la línea 1669):

```latex
The present experiments do not include a DDTW-free ablation; the comparisons therefore do not isolate DDTW's contribution from the other controller components.
```

Para resolver experimentalmente el comentario hace falta implementar y evaluar un trigger sin DDTW. La frase reconoce que falta; no presenta una ablación como realizada.

### R2.3 — Justificar rampa y meseta

**Cortar:** nada. Conservá las definiciones actuales de las referencias (aprox. líneas 571–590).

**Pegar:** después del párrafo que define la referencia constante (aprox. líneas 586–590):

```latex
The linear-progress and constant-plateau references are simple design archetypes for sustained improvement and lack of progress, respectively; they are not an exhaustive model of the search dynamics of all four algorithms. The adequacy of alternative reference shapes has not been established.
```

El manuscrito fija una pendiente de 2.0; no afirmes que se probaron otras pendientes.

### R2.4 — Faltan baselines adaptativos representativos

**Cortar:** nada.

**Pegar:** en Limitations, la misma ubicación que R1.2. Pegá este bloque una sola vez para responder ambos comentarios; no lo dupliques si ya lo insertaste para R1.2:

```latex
This study does not compare the proposed controller with representative external adaptive parameter-control methods. The experiments therefore do not establish an advantage over such methods.
```

Conservá R1.2 y R2.4 como respuestas separadas en la carta.

Un baseline externo requiere experimentos nuevos; la aclaración no sustituye esa comparación.

### R2.5 — Reproducibilidad y disponibilidad de código

**Cortar:** nada. La declaración actual `\dataavailability` (aprox. línea 1812) dice que los datasets son públicos; no dice que el código esté publicado.

**Pegar:** **nada por ahora. BLOQUEADO** hasta confirmar semillas por corrida, artefactos disponibles y decisión de autores sobre publicación del código. No pegues una URL o disponibilidad que no esté confirmada ni cambies la declaración de datasets para que parezca una declaración de código.

### R2.6 — El abstract empieza con un fragmento listo

**Cortar exactamente:** al comienzo de `\abstract{...}` (línea 121), reemplazá el bloque actual:

```latex
as optimization progresses. However, adaptive decisions are often based on algorithm-specific feedback or simple indicators that provide limited
information about the evolving search dynamics.
```

**Pegar en el mismo lugar:**

```latex
Adaptive decisions in metaheuristics are often based on algorithm-specific feedback or simple indicators that provide limited information about the evolving search dynamics.
```

La nueva oración repara el fragmento y conserva la idea de la oración original sin duplicar `However, ...`.

## Revisor 3

### R3.1 — Definir el research gap y distinguir hyper-heuristics listo

**Cortar:** nada.

**Pegar:** al final del texto introductorio, **antes** de `The main contributions of this work are summarized as follows:` (aprox. línea 223):

```latex
This study focuses on using search-trajectory pattern comparisons as feedback for switching between predefined configurations. This describes the scope of the proposed controller and does not establish an advantage over adaptive parameter-control or hyper-heuristic methods.
```

Para afirmar diferencias específicas frente a trabajos concretos, primero agregá citas verificadas.

### R3.2 — Ampliar Related Work

**Cortar:** nada. No elimines citas actuales sin una razón bibliográfica concreta.

**Pegar:** **BLOQUEADO; no hay un bloque completo listo para pegar.** Primero agregá y verificá referencias sobre control fuzzy y análisis de trayectorias, y compará esas fuentes con el método. No dejes frases genéricas que parezcan cubrir literatura que todavía no se citó.

### R3.3 — Completar la definición matemática de DDTW

**Cortar:** nada todavía. Conservá la recurrencia y los bordes de DTW ya definidos (aprox. líneas 418–435).

**Pegar:** nada todavía. **BLOQUEADO** hasta confirmar qué implementación generó los resultados: el manuscrito y el código actualmente inspeccionado difieren en el costo local, y hay que confirmar derivada inicial, normalización por longitud de camino y límites de banda. No pegues una fórmula con esas decisiones inventadas.

### R3.4 — Agregar gráfico de diagnóstico

**Cortar:** nada. Conservá la figura agregada existente de conteos de transiciones (aprox. líneas 1531–1546); muestra otra cosa.

**Pegar:** **BLOQUEADO; no hay bloque listo para pegar.** Primero generá y validá una traza real con trayectoria, referencias, distancias, umbrales y estado del controlador sincronizados. No reemplaces los conteos actuales por datos que no existen.

### R3.5 — Explicar cómo se eligieron los parámetros

**Cortar:** nada. Conservá la tabla `tab:mh_params`.

**Pegar:** **BLOQUEADO; no hay texto factual listo para pegar.** Primero confirmá con los autores la procedencia de los valores y si se ajustaron por instancia. El lugar correcto, una vez confirmado, es después del párrafo que termina `These configurations are kept unchanged across all benchmark instances.` (aprox. línea 943), fuera de la tabla. No afirmes “not tuned” sin confirmación.

### R3.6 — Completar Algorithm 1

**Cortar/reemplazar:** **no borres todavía**. Dentro del bloque de *warm-up* (aprox. línea 1030) está el paso genérico:

```latex
\State Compute the DDTW-based trajectory information
```

**Pegar:** **BLOQUEADO; no hay pasos listos para pegar.** Primero verificá la implementación que generó los resultados y determiná el cálculo de derivada, actualización de umbrales y condiciones de switch. Después reemplazá solo esa línea genérica con los pasos reales; conservá los pasos siguientes que ya toman la decisión, actualizan configuración y guardan diagnósticos.

### R3.7 — Explicar las diferencias entre algoritmos

**Cortar/pegar:** nada nuevo. Results ya describe variación entre algoritmos y Conclusions aclara que el efecto depende de la dinámica del algoritmo. No agregues como hechos causas que no se hayan medido; la reparación, dinámica poblacional y sensibilidad son hipótesis.

### R3.8 — Mostrar todas las señales en el gráfico

**Cortar:** nada. Conservá la figura de transiciones agregadas.

**Pegar:** **BLOQUEADO; no hay caption listo para pegar.** Primero generá y validá la figura. Debe mostrar, para la misma corrida, best-so-far, ambas referencias, $D_R(t)$, $D_C(t)$, $\Delta_t$, umbrales, estado, switches y parámetros activos. Puede ser la misma figura nueva de R3.4, pero verificá todos los elementos antes de responder al revisor.

## Resumen rápido de cortes

1. **Corte seguro:** solo el bloque del abstract de R2.6 indicado arriba.
2. **Corte condicional:** la frase del abstract de R1.1 (`while trajectory-driven adaptation...`) solo después de verificar estadísticas/multiplicidad y decidir su reemplazo.
3. **Resto de puntos:** no cortes texto existente; seguí las instrucciones de pegar, no cambiar, o esperar evidencia de cada ID.
4. **No se hicieron cambios en el manuscrito.** Las respuestas a revisores deben describir cambios como completados únicamente después de aplicarlos y verificar el resultado.
