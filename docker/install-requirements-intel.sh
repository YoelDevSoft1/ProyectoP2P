#!/bin/bash
# Script para instalar requirements excluyendo PyTorch (ya viene en la imagen base)

set -e

echo "Instalando dependencias (excluyendo PyTorch e Intel Extension que ya están instalados)..."

# Crear archivo temporal sin torch, torchvision, torchaudio, intel-extension-for-pytorch
# Usar grep para excluir líneas que empiezan con estas dependencias
grep -v -E "^(torch|torchvision|torchaudio|intel-extension-for-pytorch)" requirements.txt > requirements_no_torch.txt || true

# Verificar que el archivo no esté vacío
if [ ! -s requirements_no_torch.txt ]; then
    echo "Error: No hay dependencias para instalar (archivo vacío después de excluir PyTorch)"
    exit 1
fi

# Instalar dependencias
echo "Instalando dependencias desde requirements_no_torch.txt..."
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r requirements_no_torch.txt

# Limpiar archivo temporal
rm -f requirements_no_torch.txt

echo "✅ Dependencias instaladas correctamente"
echo "✅ PyTorch e Intel Extension ya están instalados en la imagen base"

