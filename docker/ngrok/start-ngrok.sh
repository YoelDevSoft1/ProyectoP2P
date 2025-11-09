#!/bin/sh
# Script de inicio para ngrok en Docker
# Reemplaza el authtoken en el archivo de configuración y luego inicia ngrok

set -e

CONFIG_FILE="/etc/ngrok/ngrok.yml"

# Verificar que NGROK_AUTHTOKEN esté configurado
if [ -z "$NGROK_AUTHTOKEN" ]; then
  echo "ERROR: NGROK_AUTHTOKEN no está configurado."
  echo "Por favor, agrega NGROK_AUTHTOKEN a tu archivo .env"
  exit 1
fi

# Verificar que el archivo de configuración existe
if [ ! -f "$CONFIG_FILE" ]; then
  echo "ERROR: Archivo de configuración no encontrado: $CONFIG_FILE"
  exit 1
fi

# Reemplazar el authtoken en el archivo de configuración
echo "Configurando authtoken de ngrok..."
sed -i "s|authtoken:.*|authtoken: $NGROK_AUTHTOKEN|" "$CONFIG_FILE"

# Verificar que el backend esté disponible
echo "Verificando que el backend esté disponible..."
until nc -z backend 8000; do
  echo "Esperando que el backend esté disponible..."
  sleep 2
done

echo "Backend está disponible. Iniciando ngrok..."

# Iniciar ngrok
exec ngrok start --all --config "$CONFIG_FILE"

