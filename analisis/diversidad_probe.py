"""
Sonda de medicion READ-ONLY: diversidad poblacional durante mesetas de best-so-far.

Hipotesis a validar (contexto/estrategias_dtw/diversidad_y_deteccion_predictiva.md):
  * GA converge prematuramente (la poblacion colapsa): sus mesetas de best-so-far
    coinciden con diversidad BAJA  -> "mesetas muertas" -> DTW lo rescata al explorar.
  * PSO con parametros de exploracion mantiene el enjambre disperso: sus mesetas
    coinciden con diversidad ALTA -> "mesetas vivas" -> conmutar a exploit en ese
    momento destruye el salto que venia, explicando la derrota de las variantes DTW.

Que hace esta sonda:
  * Corre cada MH (BinaryPSO, GeneticAlgorithm, BinaryGWO, BinaryDE) en modo fijo
    explore/exploit, sin monitor DTW ni runner: usa mh.initialize() + mh.step()
    (la logica real de paso de cada MH, sin reimplementar nada).
  * En cada iteracion registra: best-so-far, largo de racha sin mejora, y tres
    metricas de diversidad sobre la poblacion binaria evaluada:
      1) hamming_norm = distancia Hamming media por pares / n   (0..1)
      2) entropia     = entropia binaria media por gen          (0..1)
      3) fitness_std  = desviacion estandar del fitness poblacional
  * Detecta episodios de meseta (rachas consecutivas sin mejora de largo >= UMBRAL)
    y calcula diversidad al inicio, al final y promedio dentro de cada episodio.
  * Persiste los datos crudos en el directorio temporal pre-aprobado
    C:\\Users\\huaso\\AppData\\Local\\Temp\\opencode (nunca dentro del repo).

Uso:
  python -m analisis.diversidad_probe

No modifica archivos del repositorio ni escribe bajo results/.

Nota: las métricas de diversidad (hamming/entropía/fitness-std) y el mapeo de
atributos de población se importan de mkp_common/diversity.py (fuente única
compartida con la estrategia binary_diversity_predictive).
"""

import json
import statistics
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from mkp_common import diversity as mkp_common_diversity
from mkp_common.mh import BinaryDE, BinaryGWO, BinaryPSO, GeneticAlgorithm
from mkp_common.problem import cargar_instancia

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTANCES_DIR = REPO_ROOT / "instances"
TEMP_DIR = Path(r"C:\Users\huaso\AppData\Local\Temp\opencode")

SEED = 42
NUM_PARTICULAS = 20
NUM_ITERACIONES = 500
UMBRAL_EPISODIO = 10  # racha minima sin mejora para considerarla "meseta"

INSTANCIAS = [("mknapcb1", 0), ("mknapcb3", 0)]
MHS = [BinaryPSO, GeneticAlgorithm, BinaryGWO, BinaryDE]
MODOS = ["explore", "exploit"]

METRICAS = ["hamming_norm", "entropia", "fitness_std"]

# Atributo que expone la poblacion binaria evaluada en cada MH
# (verificado en mkp_common/mh/*.py). El mapeo y el cálculo de métricas viven
# en mkp_common/diversity.py (fuente única compartida con la estrategia A10);
# esta sonda solo los reutiliza — el comportamiento es idéntico al original.
POBLACION_ATTR = mkp_common_diversity.POBLACION_ATTR

# MHs que guardan el fitness de la poblacion actual en fitness_pop.
# PSO no lo guarda (solo pbest_fitness), asi que se calcula como p·x,
# valido porque la poblacion ya esta reparada (factible).
FITNESS_POP_MHS = mkp_common_diversity.FITNESS_POP_MHS


def _poblacion(mh) -> np.ndarray:
    """Poblacion binaria evaluada actual como ndarray (N, n)."""
    return mkp_common_diversity.population_of(mh)


def _fitness_poblacion(mh, pop: np.ndarray) -> np.ndarray:
    """Fitness de la poblacion actual (evaluado, sin re-evaluar reparaciones)."""
    return mkp_common_diversity.population_fitness_of(mh, pop)


def metricas_diversidad(pop: np.ndarray, fitness: np.ndarray) -> dict:
    """Las 3 metricas de diversidad sobre la poblacion binaria actual.

    La hamming_norm es la diversidad Hamming normalizada: la probabilidad de
    que dos individuos elegidos al azar difieran en un gen,
    2 * media_j(p_j*(1-p_j)), con p_j la frecuencia del bit 1 en el gen j —
    calculo vectorizado O(N*n), sin loop de pares. Es la distancia Hamming
    media por pares distintos multiplicada por (N-1)/N; la definicion se
    conserva identica a la de las campanas historicas.

    Delega en mkp_common.diversity.population_diversity (fuente unica de las
    metricas) y traduce sus claves a los nombres historicos de la sonda.
    """
    d = mkp_common_diversity.population_diversity(pop, fitness)
    return {
        "hamming_norm": d["hamming"],
        "entropia": d["entropy"],
        "fitness_std": d["fitness_std"],
    }


def _fila(iteracion: int, best: float, no_improve: int, improved: bool,
          modo: str, pop: np.ndarray, fitness: np.ndarray) -> dict:
    fila = {
        "iteracion": iteracion,
        "best": best,
        "no_improve_len": no_improve,
        "improved": improved,
        "modo": modo,
    }
    fila.update(metricas_diversidad(pop, fitness))
    return fila


def correr(mh_cls, inst: dict, modo: str, nombre_inst: str) -> dict:
    """Una corrida en modo fijo, usando la logica real de la MH (sin DTW)."""
    rng = np.random.default_rng(SEED)
    mh = mh_cls(inst, rng, num_particulas=NUM_PARTICULAS)
    mh.initialize()
    # Modo fijo para toda la corrida: misma via que initial_mode del runner.
    mh.adapt(modo == "explore")

    rows = []
    pop = _poblacion(mh)
    fitness = _fitness_poblacion(mh, pop)
    best = float(mh.get_best()[1])
    rows.append(_fila(0, best, 0, False, mh.mode, pop, fitness))

    for it in range(1, NUM_ITERACIONES + 1):
        best_nuevo = float(mh.step())
        improved = best_nuevo > best
        best = best_nuevo  # gbest es monotono por construccion
        no_improve = 0 if improved else rows[-1]["no_improve_len"] + 1
        pop = _poblacion(mh)
        fitness = _fitness_poblacion(mh, pop)
        rows.append(_fila(it, best, no_improve, improved, mh.mode, pop, fitness))

    return {
        "mh": type(mh).__name__,
        "modo": modo,
        "instancia": nombre_inst,
        "n": inst["n"],
        "m": inst["m"],
        "optimo": inst["optimo"],
        "best_final": best,
        "rows": rows,
    }


def detectar_episodios(run: dict, umbral: int = UMBRAL_EPISODIO) -> list:
    """Rachas maximales de iteraciones sin mejora (largo >= umbral).

    Se evalúan desde la iteración 1: la iteración 0 no tiene previo y no
    puede ser "sin mejora".
    """
    rows = run["rows"]
    n_rows = len(rows)
    episodios = []
    t = 1
    while t < n_rows:
        if not rows[t]["improved"]:
            inicio = t
            while t < n_rows and not rows[t]["improved"]:
                t += 1
            fin = t - 1
            largo = fin - inicio + 1
            if largo >= umbral:
                episodios.append({
                    "mh": run["mh"],
                    "modo": run["modo"],
                    "instancia": run["instancia"],
                    "inicio": inicio,
                    "fin": fin,
                    "largo": largo,
                    "div_inicio": {k: rows[inicio][k] for k in METRICAS},
                    "div_fin": {k: rows[fin][k] for k in METRICAS},
                    "div_media": {
                        k: statistics.mean(rows[i][k] for i in range(inicio, fin + 1))
                        for k in METRICAS
                    },
                })
        else:
            t += 1
    return episodios


def resumen_episodios(episodios: list) -> dict:
    if not episodios:
        return {
            "n_episodios": 0,
            "longitudes": [],
            "largo_media": None,
            "largo_max": None,
        }
    out = {
        "n_episodios": len(episodios),
        "longitudes": [e["largo"] for e in episodios],
        "largo_media": statistics.mean(e["largo"] for e in episodios),
        "largo_max": max(e["largo"] for e in episodios),
    }
    for k in METRICAS:
        valores = [e["div_media"][k] for e in episodios]
        out[f"{k}_media_ep"] = statistics.mean(valores)
        out[f"{k}_min_ep"] = min(valores)
        out[f"{k}_inicio_media"] = statistics.mean(e["div_inicio"][k] for e in episodios)
        out[f"{k}_fin_media"] = statistics.mean(e["div_fin"][k] for e in episodios)
    return out


def _div_global(run: dict, k: str) -> float:
    """Diversidad media de toda la corrida (iteraciones 1..500)."""
    return statistics.mean(run["rows"][i][k] for i in range(1, len(run["rows"])))


def veredicto(resumenes: dict) -> str:
    """Comparacion focal de la hipotesis, con numeros para verificacion humana."""
    lineas = []
    for inst in [i for i, _ in INSTANCIAS]:
        llave_ga = (inst, "GeneticAlgorithm", "exploit")
        llave_pso_explore = (inst, "BinaryPSO", "explore")
        ga = resumenes.get(llave_ga)
        pso = resumenes.get(llave_pso_explore)
        if ga is None or pso is None:
            lineas.append(f"{inst}: falta corrida GA-exploit o PSO-explore")
            continue
        if ga["n_episodios"] == 0 or pso["n_episodios"] == 0:
            lineas.append(f"{inst}: sin episodios en GA-exploit o PSO-explore; "
                          "no se puede comparar")
            continue
        h_ga = ga["hamming_norm_media_ep"]
        h_pso = pso["hamming_norm_media_ep"]
        ratio = h_pso / h_ga if h_ga > 0 else float("inf")
        lineas.append(
            f"{inst}: GA-exploit mesetas {ga['n_episodios']} (hamming media "
            f"{h_ga:.4f}) vs PSO-explore mesetas {pso['n_episodios']} (hamming "
            f"media {h_pso:.4f}) -> ratio {ratio:.1f}x"
        )
    return "\n".join(lineas)


def main() -> None:
    t_total = time.perf_counter()
    corridas, episodios_todos = [], []

    for nombre_inst, idx in INSTANCIAS:
        ruta = INSTANCES_DIR / f"{nombre_inst}.txt"
        inst = cargar_instancia(str(ruta), idx)
        print(f"[probe] instancia {nombre_inst} idx={idx}: n={inst['n']} "
              f"m={inst['m']} optimo={inst['optimo']:.0f}")
        for mh_cls in MHS:
            for modo in MODOS:
                t_run = time.perf_counter()
                run = correr(mh_cls, inst, modo, nombre_inst)
                dt = time.perf_counter() - t_run
                episodios = detectar_episodios(run)
                corridas.append(run)
                episodios_todos.extend(episodios)
                print(f"  {run['mh']:<16} {modo:<7} {nombre_inst:<8} "
                      f"{dt:6.1f}s best_final={run['best_final']:.0f} "
                      f"#ep={len(episodios)}")

    resumenes = {}
    for run in corridas:
        llave = (run["instancia"], run["mh"], run["modo"])
        res = resumen_episodios([e for e in episodios_todos
                                 if e["mh"] == run["mh"]
                                 and e["modo"] == run["modo"]
                                 and e["instancia"] == run["instancia"]])
        res["div_global_hamming"] = _div_global(run, "hamming_norm")
        res["div_global_entropia"] = _div_global(run, "entropia")
        resumenes[llave] = res

    # ---- Persistir datos crudos (fuera del repo) ----
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = TEMP_DIR / f"diversidad_probe_{timestamp}.json"
    payload = {
        "meta": {
            "generado": datetime.now().isoformat(timespec="seconds"),
            "seed": SEED,
            "num_particulas": NUM_PARTICULAS,
            "num_iteraciones": NUM_ITERACIONES,
            "umbral_episodio": UMBRAL_EPISODIO,
            "instancias": [list(i) for i in INSTANCIAS],
            "mhs": [m.__name__ for m in MHS],
            "modos": MODOS,
            "metricas": METRICAS,
            "nota": "sonda read-only; no usa monitor DTW ni runner; "
                    "mh.adapt(modo) fijo por corrida",
        },
        "corridas": corridas,
        "episodios": episodios_todos,
        "resumenes": {
            f"{k[0]}|{k[1]}|{k[2]}": v for k, v in resumenes.items()
        },
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # ---- Reporte compacto ----
    print()
    print("=" * 100)
    print("REPORTE: diversidad durante episodios de meseta (rachas sin mejora >= "
          f"{UMBRAL_EPISODIO})")
    print("=" * 100)
    enc = (f"{'MH':<17}{'modo':<8}{'inst':<9}{'#ep':>3}{'largo(media|max)':>18}"
           f"{'hamm(media|min)':>16}{'ent(media|min)':>15}{'fstd(media)':>13}"
           f"{'hamm_global':>12}")
    print(enc)
    print("-" * 100)
    for (inst_name, mh_name, modo), res in sorted(resumenes.items()):
        largo = "-"
        hamm = "-"
        ent = "-"
        fstd = "-"
        if res["n_episodios"] > 0:
            largo = f"{res['largo_media']:.1f}|{res['largo_max']}"
            hamm = f"{res['hamming_norm_media_ep']:.4f}|{res['hamming_norm_min_ep']:.4f}"
            ent = f"{res['entropia_media_ep']:.4f}|{res['entropia_min_ep']:.4f}"
            fstd = f"{res['fitness_std_media_ep']:.1f}"
        print(f"{mh_name:<17}{modo:<8}{inst_name:<9}{res['n_episodios']:>3}"
              f"{largo:>18}{hamm:>16}{ent:>15}{fstd:>13}"
              f"{res['div_global_hamming']:>12.4f}")
    print()
    print("VEREDICTO DE LA HIPOTESIS (meseta viva vs muerta):")
    print(veredicto(resumenes))
    print()
    print(f"[probe] datos crudos -> {out_path}")
    print(f"[probe] tiempo total: {time.perf_counter() - t_total:.1f}s "
          f"({len(corridas)} corridas)")


if __name__ == "__main__":
    main()
