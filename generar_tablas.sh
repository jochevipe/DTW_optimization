#!/bin/bash
# ==============================================================================
# generar_tablas.sh — Generación Automatizada de Tablas LaTeX para el Paper
# ==============================================================================
# Genera las tablas científicas requeridas para la revisión del paper (MKP):
#   1. Tablas de calidad de solución (results/tables/solucion/)
#   2. Tablas no paramétricas de Wilcoxon (results/tables/wilcoxon/)
#   3. Tablas de ranking global de Friedman y Bonferroni-Dunn (results/tables/bonferroni/)
# ==============================================================================

source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate DTW_optimization

echo "=========================================================="
echo "Iniciando generación de tablas LaTeX y CSV para el Paper..."
echo "=========================================================="

echo ""
echo ">>> [1/4] Generando tablas de Calidad de Solución..."
python -m analisis.generar_tablas_solucion "$@"

echo ""
echo ">>> [2/4] Generando tablas de Wilcoxon Signed-Rank Tests..."
python -m analisis.generar_tablas_wilcoxon "$@"

echo ""
echo ">>> [3/4] Generando tablas de Friedman Ranking y Bonferroni-Dunn..."
python -m analisis.generar_tablas_bonferroni "$@"

echo ""
echo ">>> [4/4] Generando tablas de Tiempo Computacional..."
python -m analisis.generar_tablas_tiempo "$@"

echo ""
echo "=========================================================="
echo "Tablas generadas exitosamente en results/tables/:"
echo "  - Solución:    results/tables/solucion/mknapcb{1..9}_{0,15,29}.tex"
echo "  - Wilcoxon:    results/tables/wilcoxon/wilcoxon_{0,15,29,all}.tex"
echo "  - Bonferroni:  results/tables/bonferroni/bonferroni_{0,15,29,all}.tex"
echo "  - Tiempo:      results/tables/tiempo/costo_computacional_{0,15,29,all}.tex"
echo "=========================================================="
