"""
binary_diversity_predictive — Estrategia A10: DTW con conciencia de diversidad
poblacional y detección predictiva de mesetas.
================================================================================
Controlador binario explore/exploit que combina la señal A4 del monitor DTW con
un canal de diversidad Hamming de la población (medida en cada iteración lista
via mkp_common.diversity) y con la tendencia de delta como early-warning.
"""

from .config import DECISION_RULE, DiversityPredictiveController, make_fire_fn

__all__ = ["DECISION_RULE", "DiversityPredictiveController", "make_fire_fn"]
