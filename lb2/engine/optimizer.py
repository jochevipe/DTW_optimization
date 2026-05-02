"""OptimizationEngine — Orquestador del framework.

Coordina el flujo:
  Metaheurística → StagnationMonitor → ParameterController → Strategy
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from lb2.core.problem import MKPInstance
from lb2.core.solution import Solution
from lb2.metaheuristics.base import Metaheuristic
from lb2.monitoring.controller import ControlAction, ParameterController
from lb2.monitoring.dtw import StagnationConfig, StagnationMonitor
from lb2.strategies.base import StagnationStrategy

logger = logging.getLogger(__name__)


@dataclass
class RunConfig:
    """Configuración para una ejecución del engine.

    Attributes:
        epochs: Número de epochs (reinicios completos).
        iterations_per_epoch: Iteraciones por epoch.
        seed: Semilla base (se incrementa por epoch para reproducibilidad).
        stagnation_config: Configuración del monitor DTW.
        inject_fraction: Fracción del enjambre a inyectar cuando se interviene.
        verbose: Si True, imprime info de progreso.
    """

    epochs: int = 10
    iterations_per_epoch: int = 100
    seed: int | None = None
    stagnation_config: StagnationConfig = field(default_factory=StagnationConfig)
    inject_fraction: float = 0.4
    verbose: bool = True


@dataclass
class EpochResult:
    """Resultado de un epoch individual."""

    epoch: int
    best_fitness: float
    best_solution: Solution
    convergence_history: List[float] = field(default_factory=list)
    interventions: int = 0


@dataclass
class RunResult:
    """Resultado completo de una ejecución."""

    best_fitness: float = float("-inf")
    best_solution: Optional[Solution] = None
    epoch_results: List[EpochResult] = field(default_factory=list)
    total_interventions: int = 0
    metadata: Dict = field(default_factory=dict)


class OptimizationEngine:
    """Orquestador principal del framework.

    Coordina la metaheurística, el monitor de estancamiento,
    el controller de parámetros, y las estrategias de respuesta.

    Usage:
        ```python
        from lb2.metaheuristics import BinaryPSO
        from lb2.strategies import RuinRecreateStrategy
        from lb2.engine import OptimizationEngine, RunConfig

        engine = OptimizationEngine(
            metaheuristic=BinaryPSO(num_particles=20),
            strategies=[RuinRecreateStrategy(ruin_rate=0.3)],
        )
        result = engine.run(problem, RunConfig(epochs=10, iterations_per_epoch=100))
        print(f"Best: {result.best_fitness}")
        ```
    """

    def __init__(
        self,
        metaheuristic: Metaheuristic,
        strategies: List[StagnationStrategy] | None = None,
        controller: ParameterController | None = None,
    ) -> None:
        """
        Args:
            metaheuristic: Implementación de la metaheurística (PSO, GWO, etc).
            strategies: Lista de estrategias de respuesta al estancamiento.
                       Se aplican en orden secuencial. Si alguna mejora, se inyecta.
            controller: Controller de parámetros. Si None, se usa el default.
        """
        self.metaheuristic = metaheuristic
        self.strategies = strategies or []
        self.controller = controller or ParameterController()

    def run(self, problem: MKPInstance, config: RunConfig) -> RunResult:
        """Ejecuta la optimización completa.

        Args:
            problem: Instancia MKP a resolver.
            config: Configuración de la ejecución.

        Returns:
            RunResult con la mejor solución y metadata.
        """
        result = RunResult()

        for epoch in range(config.epochs):
            seed = None
            if config.seed is not None:
                seed = config.seed + epoch

            epoch_result = self._run_epoch(
                problem=problem,
                epoch_num=epoch,
                iterations=config.iterations_per_epoch,
                seed=seed,
                stagnation_cfg=config.stagnation_config,
                inject_fraction=config.inject_fraction,
                verbose=config.verbose,
            )

            result.epoch_results.append(epoch_result)
            result.total_interventions += epoch_result.interventions

            if epoch_result.best_fitness > result.best_fitness:
                result.best_fitness = epoch_result.best_fitness
                result.best_solution = epoch_result.best_solution.copy()

            if config.verbose:
                print(
                    f"  Epoch {epoch + 1}/{config.epochs} — "
                    f"Best: {epoch_result.best_fitness:.1f} "
                    f"(interventions: {epoch_result.interventions})"
                )

        if config.verbose:
            print(
                f"\n{'='*50}\n"
                f"Resultado final: {result.best_fitness:.1f}\n"
                f"Óptimo conocido: {problem.optimal_value}\n"
                f"Intervenciones totales: {result.total_interventions}\n"
                f"{'='*50}"
            )

        return result

    def _run_epoch(
        self,
        problem: MKPInstance,
        epoch_num: int,
        iterations: int,
        seed: int | None,
        stagnation_cfg: StagnationConfig,
        inject_fraction: float,
        verbose: bool,
    ) -> EpochResult:
        """Ejecuta un epoch completo."""
        # Inicializar metaheurística y monitor
        self.metaheuristic.initialize(problem, seed=seed)
        monitor = StagnationMonitor(cfg=stagnation_cfg)

        convergence = []
        interventions = 0

        for it in range(iterations):
            # 1. Paso de la metaheurística
            best_fitness = self.metaheuristic.step(it, iterations)
            convergence.append(best_fitness)

            # 2. Actualizar monitor DTW
            dtw_out = monitor.update(best_fitness)

            # 3. Controller decide acción
            action = self.controller.decide(dtw_out)

            if action == ControlAction.INTERVENE:
                # 4. Aplicar estrategias
                current_best = self.metaheuristic.get_best()
                improved = False

                for strategy in self.strategies:
                    new_sol = strategy.apply(current_best, problem)
                    if new_sol.fitness > current_best.fitness:
                        current_best = new_sol
                        improved = True
                        logger.info(
                            "Epoch %d, iter %d: %s mejoró a %.1f",
                            epoch_num,
                            it,
                            strategy.name,
                            new_sol.fitness,
                        )

                if improved:
                    self.metaheuristic.inject_solution(current_best, inject_fraction)

                interventions += 1

                # Reset trigger para no disparar de nuevo inmediatamente
                monitor.trigger_streak = 0
                monitor.no_improve_len = 0

            elif action == ControlAction.EXPLORE:
                self.metaheuristic.set_params(self.controller.get_explore_params())

            elif action == ControlAction.EXPLOIT:
                self.metaheuristic.set_params(self.controller.get_exploit_params())

        best = self.metaheuristic.get_best()
        return EpochResult(
            epoch=epoch_num,
            best_fitness=best.fitness,
            best_solution=best,
            convergence_history=convergence,
            interventions=interventions,
        )
