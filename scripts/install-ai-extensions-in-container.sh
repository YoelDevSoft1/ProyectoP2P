#!/bin/bash
# Script para instalar extensiones de IA DENTRO del contenedor Docker
# NO modifica el Dockerfile - se ejecuta después de que el contenedor está corriendo

echo "=========================================="
echo "Instalando extensiones de IA en el contenedor"
echo "=========================================="

# Verificar que estamos en un contenedor Docker
if [ ! -f /.dockerenv ]; then
    echo "⚠️  Este script está diseñado para ejecutarse dentro de un contenedor Docker"
    echo "   Usa: docker exec -it <container_name> bash -c './scripts/install-ai-extensions-in-container.sh'"
    exit 1
fi

echo "Instalando Intel Extension for PyTorch..."
pip install --no-cache-dir intel-extension-for-pytorch \
    --extra-index-url https://download.pytorch.org/whl/cpu

echo "Instalando OpenVINO..."
pip install --no-cache-dir openvino==2023.3.0 openvino-dev==2023.3.0

echo "Instalando optimizaciones Intel MKL..."
pip install --no-cache-dir mkl==2023.2.0 mkl-include==2023.2.0

echo "=========================================="
echo "✅ Instalación completa"
echo "=========================================="

# Verificar instalación
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import intel_extension_for_pytorch as ipex; print('Intel Extension: ✅')" 2>/dev/null || echo "Intel Extension: ⚠️"
python -c "from openvino.runtime import Core; print('OpenVINO: ✅')" 2>/dev/null || echo "OpenVINO: ⚠️"

