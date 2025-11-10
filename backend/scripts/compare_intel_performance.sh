#!/bin/bash
# Script para comparar rendimiento con y sin Intel Extension
# Ejecuta benchmarks en ambos modos y compara resultados

echo "================================================================================"
echo "🚀 COMPARACIÓN DE RENDIMIENTO: PyTorch Estándar vs Intel Extension"
echo "================================================================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para ejecutar benchmark
run_benchmark() {
    local mode=$1
    echo "📊 Ejecutando benchmark en modo: $mode"
    echo "------------------------------------------------------------------------------"
    
    python backend/scripts/benchmark_intel_performance.py 2>&1 | tee "benchmark_${mode}.log"
    
    # Extraer tiempos del log
    local lstm_training=$(grep "Entrenamiento LSTM completado" "benchmark_${mode}.log" | grep -oP '\d+\.\d+ segundos' | grep -oP '\d+\.\d+' || echo "N/A")
    local lstm_inference=$(grep "Inferencia LSTM completada" "benchmark_${mode}.log" | grep -oP 'Tiempo promedio: \d+\.\d+ ms' | grep -oP '\d+\.\d+' || echo "N/A")
    local matrix_ops=$(grep "Operaciones de matriz completadas" "benchmark_${mode}.log" | grep -oP '\d+\.\d+ ms' | grep -oP '\d+\.\d+' || echo "N/A")
    
    echo "$lstm_training|$lstm_inference|$matrix_ops"
}

# Ejecutar benchmark con Intel Extension (si está disponible)
echo "🔧 Verificando Intel Extension..."
python -c "import intel_extension_for_pytorch as ipex; print('Intel Extension disponible')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Intel Extension está disponible${NC}"
    echo ""
    
    echo "📊 Ejecutando benchmark con Intel Extension..."
    intel_results=$(run_benchmark "intel")
    echo ""
else
    echo -e "${YELLOW}⚠️  Intel Extension no está disponible${NC}"
    echo "   Ejecutando benchmark con PyTorch estándar solamente..."
    echo ""
fi

# Ejecutar benchmark con PyTorch estándar
echo "📊 Ejecutando benchmark con PyTorch estándar..."
standard_results=$(run_benchmark "standard")
echo ""

# Comparar resultados
echo "================================================================================"
echo "📊 COMPARACIÓN DE RESULTADOS"
echo "================================================================================"
echo ""

if [ -n "$intel_results" ] && [ -n "$standard_results" ]; then
    echo "Comparando resultados..."
    # Aquí podrías agregar lógica para comparar los resultados
    echo "Ver logs: benchmark_intel.log y benchmark_standard.log"
else
    echo "Ejecutando benchmark único..."
    echo "Ver log: benchmark_standard.log"
fi

echo ""
echo "✅ Benchmark completado!"
echo "================================================================================"

