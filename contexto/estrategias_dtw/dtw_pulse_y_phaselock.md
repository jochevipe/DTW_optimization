# Estrategias específicas por MH: DTW-Pulse y DTW-PhaseLock

> **Documento de referencia de implementación**
> Basado en `contexto/oficial/06_estrategias_complementarias.md`, corregido contra el código real
> y la evidencia estadística de las campañas previas (ver sección 5 para las desviaciones).
> Código: carpetas `dtw_pulse/` y `dtw_phaselock/`.

---

## 1. Base común: el sensor DTW

Ambas estrategias comparten el mismo sensor, que permanece **intacto** (`mkp_common/monitor.py`):

- Ventana deslizante `W = 50` sobre `best_so_far(t)`.
- Métricas por iteración:
  - `D1_vs_ramp`: distancia DTW a una rampa (progreso).
  - `D2_vs_const`: distancia DTW a una constante (meseta).
  - `delta = D1 - D2`.
- Umbrales adaptativos calculados sobre el historial:
  - `theta_c` = P30 del historial de `D2`.
  - `theta_r` = P70 del historial de `D1`.
  - `theta_delta` = P70 del historial de `delta`.
- `no_improve_len`: iteraciones consecutivas sin mejora del mejor fitness.
  **`no_improve_len == 0` significa que en esta iteración hubo mejora** — es la señal
  de "mejora detectada" usada por ambos controladores.

### Warm-up

Mientras la ventana no esté llena (< 50 iteraciones), el monitor emite `ready=False`
con valores placeholder finitos (`D1=D2=delta=0`). Con `decision_on_early=True`, el
runner invoca igualmente al controlador desde la iteración 1, y este responde con su
régimen base hasta tener datos reales.

### Contrato con el runner

| Elemento | Valor |
|---|---|
| Firma | `fire_fn(out: dict) -> bool` |
| Retorno | `True` = explorar, `False` = explotar |
| Estado | Los controladores son **stateful**; se crea una instancia fresca por época vía `fire_fn_factory` (evita filtrar estado entre épocas) |
| Modo inicial | `initial_mode` debe coincidir con lo que el controlador devuelve durante el warm-up |

---

## 2. DTW-Pulse — `dtw_pulse/`

**Metaheurística objetivo: BinaryPSO** (también válido para enjambres).

**Filosofía:** en PSO, el modo exploit colapsa las velocidades y la población se vuelve
idéntica. La estrategia mantiene **exploración permanente como régimen base** e inyecta
**pulsos cortos de explotación** solo cuando hay progreso refinable, volviendo inmediatamente
a explorar cuando la curva se aplana.

### Reglas de transición

```text
                ┌─────────────────────────────────────────────────┐
                ▼                                                 │ D2 <= theta_c
        ┌──────────────┐    mejora (no_improve_len==0)     ┌────────┴────────┐
        │   EXPLORE    │    Ó  D2 > 2.0 * theta_c          │     EXPLOIT     │
        │ (régimen base)├──────────────────────────────────►│  (pulso corto)  │
        └──────────────┘                                    └─────────────────┘
                                ◄── también sale al cumplir MAX_PULSE_ITERATIONS ──
```

| Estado actual | Condición | Nuevo estado |
|---|---|---|
| Warm-up (`ready=False`) | — | Permanece en `explore` (devuelve `True`) |
| `explore` → `exploit` | `no_improve_len == 0` **O** `D2_vs_const > HIGH_ACTIVITY_MULT * theta_c` | Inicia pulso |
| `exploit` → `explore` | (`D2_vs_const <= theta_c` **Y** `no_improve_len != 0`) **O** pulso alcanzó `MAX_PULSE_ITERATIONS` | Fin del pulso |

**Nota sobre el tope de pulso:** ninguna MH resetea su población al cambiar de modo
(`adapt()` solo cambia parámetros). Sin tope, un pulso podría quedar atrapado en exploit;
el límite duro de iteraciones garantiza el retorno a la base exploratoria.

### Parámetros (`dtw_pulse/config.py`)

| Parámetro | Default | Significado |
|---|---|---|
| `MAX_PULSE_ITERATIONS` | `10` | Longitud máxima de un pulso de explotación antes de volver forzosamente a explore |
| `HIGH_ACTIVITY_MULT` | `2.0` | Umbral de alta actividad: entra a pulso si `D2 > 2.0 × theta_c` |
| Modo inicial | `"explore"` | Régimen base y valor devuelto durante warm-up |

---

## 3. DTW-PhaseLock — `dtw_phaselock/`

**Metaheurística objetivo: GeneticAlgorithm** (se corre además en BinaryDE y BinaryGWO).

**Filosofía:** en GA, alternar modos iteración a iteración (*flickering*) destruye la
presión selectiva y rompe los building blocks. Se requiere operar en **explotación sostenida
como régimen base**, escapando a exploración únicamente ante estancamiento profundo
confirmado, y retornando apenas aparezca una mejora.

### Reglas de transición

```text
                ┌─────────────────────────────────────────────────┐
                ▼                                                 │ mejora (no_improve_len==0)
        ┌──────────────┐    D2 <= theta_c                  ┌────────┴────────┐
        │   EXPLOIT    │    Y  no_improve_len >= 5         │     EXPLORE     │
        │ (régimen base)├──────────────────────────────────►│ (fase sostenida)│
        └──────────────┘                                    └─────────────────┘
                          ◄── también retorna si D2 > 2.5 * theta_c ──
```

| Estado actual | Condición | Nuevo estado |
|---|---|---|
| Warm-up (`ready=False`) | — | Permanece en `exploit` (devuelve `False`) |
| `exploit` → `explore` | `D2_vs_const <= theta_c` **Y** `no_improve_len >= PLATEAU_MIN` | Fase de exploración |
| `explore` → `exploit` | `no_improve_len == 0` **O** `D2_vs_const > RECOVERY_MULT * theta_c` | Retorno a explotación |

La doble condición de entrada (señal baja + meseta prolongada) funciona como banda muerta:
evita entrar a explorar por ruido transitorio de la señal.

### Parámetros (`dtw_phaselock/config.py`)

| Parámetro | Default | Significado |
|---|---|---|
| `PLATEAU_MIN` | `5` | Iteraciones mínimas sin mejora para confirmar estancamiento profundo antes de explorar |
| `RECOVERY_MULT` | `2.5` | Retorno a exploit si la actividad sube: `D2 > 2.5 × theta_c` |
| Modo inicial | `"exploit"` | Régimen base y valor devuelto durante warm-up |

---

## 4. Integración con el experimento

- Ambas estrategias están registradas en `run_all_hpc.py` (`STRATEGIES`, labels
  `DTW-Pulse` / `DTW-PhaseLock`) y como etapas en `run_all.py`.
- Cada `resultados.py` guarda metadatos compatibles con la selección segura de campañas
  (`estrategia`, `decision_rule`, instancia, idx, población, iteraciones), y heredan
  `campaign_id` vía `MKP_CAMPAIGN_ID`.
- `analisis/estadistico.py` valida el string exacto de `decision_rule` de cada estrategia;
  los tres puntos (saver ↔ registro ↔ validador) deben mantenerse sincronizados.
- Comparación estadística contra `vanilla_exploracion` (baseline) con Wilcoxon pareado
  por época; tabla de tiempos descriptiva incluida.

---

## 5. Desviaciones respecto al doc 06

| Doc 06 proponía | Implementación real | Motivo |
|---|---|---|
| Controladores con acceso a `current_fitness` | Mejora detectada vía `no_improve_len == 0` | El runner pasa solo `out`; no hay fitness en la señal |
| Banda muerta P20/P80 del historial de D2 | Multiplicadores de `theta_c` (entrada ≤ 1×, recuperación > 2.5×) + `PLATEAU_MIN` | El monitor no expone P80 y debía permanecer intacto |
| Pulso sin límite de duración | Tope duro `MAX_PULSE_ITERATIONS = 10` | Ninguna MH resetea población al cambiar de modo; evita atrapamiento |

## 6. Limitaciones conocidas

- **Inercia de población**: `adapt()` cambia parámetros pero no resetea velocidades,
  jerarquías ni poblaciones. Un cambio de modo no diversifica/concentra instantáneamente.
  Los topes y confirmaciones de meseta mitigan, no eliminan, este efecto.
- **Hiperparámetros sin ajuste empírico**: los valores default (`10`, `2.0`, `5`, `2.5`)
  provienen del diseño; conviene revisarlos tras la primera campaña completa.
- La asignación de DE y GWO a PhaseLock es hipótesis/control: la evidencia previa muestra
  a GWO casi insensible al modo y a DE sin preferencia estable de régimen.
