
# Instrucciones para generar iconos PNG

Los iconos SVG ya están creados. Para convertirlos a PNG, puedes:

## Opción 1: Usar una herramienta online
1. Visita https://cloudconvert.com/svg-to-png o https://convertio.co/svg-png/
2. Sube icon-192.svg y convierte a PNG 192x192
3. Sube icon-512.svg y convierte a PNG 512x512
4. Guarda los archivos como icon-192.png e icon-512.png en la carpeta public/

## Opción 2: Usar ImageMagick (si está instalado)
```bash
convert icon-192.svg -resize 192x192 icon-192.png
convert icon-512.svg -resize 512x512 icon-512.png
```

## Opción 3: Usar Node.js con sharp (requiere instalación)
```bash
npm install sharp --save-dev
node -e "const sharp = require('sharp'); sharp('icon-192.svg').resize(192, 192).png().toFile('icon-192.png'); sharp('icon-512.svg').resize(512, 512).png().toFile('icon-512.png');"
```

## Opción 4: Crear iconos manualmente
Crea iconos PNG de 192x192 y 512x512 píxeles con fondo azul (#3b82f6) y texto "P2P" en blanco.
