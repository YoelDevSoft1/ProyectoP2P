/**
 * Script para crear iconos PNG desde SVG usando sharp o canvas
 * Ejecutar: node create-icons.js
 */
const fs = require('fs');
const path = require('path');

// Crear iconos SVG como fallback
const createSVGIcon = (size) => {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="${size}" height="${size}" fill="#3b82f6"/>
  <circle cx="${size/2}" cy="${size/2}" r="${size/2 - 20}" fill="#1e40af"/>
  <text x="${size/2}" y="${size/2 + 10}" font-family="Arial, sans-serif" font-size="${size/3}" font-weight="bold" fill="white" text-anchor="middle">P2P</text>
</svg>`;
};

try {
  // Crear iconos SVG
  const icon192SVG = createSVGIcon(192);
  const icon512SVG = createSVGIcon(512);
  
  fs.writeFileSync(path.join(__dirname, 'icon-192.svg'), icon192SVG);
  fs.writeFileSync(path.join(__dirname, 'icon-512.svg'), icon512SVG);
  
  console.log('Iconos SVG creados exitosamente');
  console.log('Nota: Para producción, convierte estos SVG a PNG usando una herramienta como ImageMagick o una herramienta online');
  console.log('Ejemplo: convert icon-192.svg -background none icon-192.png');
} catch (error) {
  console.error('Error creando iconos:', error);
}

