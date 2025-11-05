/**
 * Script para detectar automáticamente la IP local del servidor
 * y configurar NEXT_PUBLIC_API_URL
 */
const os = require('os')
const fs = require('fs')
const path = require('path')

function getLocalIP() {
  const interfaces = os.networkInterfaces()
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      // Ignorar direcciones IPv6 y localhost
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address
      }
    }
  }
  return 'localhost'
}

const localIP = getLocalIP()
const apiUrl = `http://${localIP}:8000`

console.log(`🌐 IP local detectada: ${localIP}`)
console.log(`🔗 URL del backend: ${apiUrl}`)

// Crear o actualizar .env.local
const envPath = path.join(__dirname, '.env.local')
const envContent = `# Auto-generado por detect-api-url.js
# Para usar ngrok, reemplaza con: NEXT_PUBLIC_API_URL=https://tu-url-ngrok.ngrok-free.dev
NEXT_PUBLIC_API_URL=${apiUrl}

# Para producción, usa tu dominio real
# NEXT_PUBLIC_API_URL=https://api.tudominio.com
`

try {
  // Leer .env.local existente si existe
  let existingContent = ''
  if (fs.existsSync(envPath)) {
    existingContent = fs.readFileSync(envPath, 'utf8')
    
    // Si ya existe NEXT_PUBLIC_API_URL, solo actualizarlo
    if (existingContent.includes('NEXT_PUBLIC_API_URL=')) {
      const updated = existingContent.replace(
        /NEXT_PUBLIC_API_URL=.*/g,
        `NEXT_PUBLIC_API_URL=${apiUrl}`
      )
      fs.writeFileSync(envPath, updated, 'utf8')
      console.log(`✅ Actualizado .env.local con URL: ${apiUrl}`)
    } else {
      // Agregar al final del archivo
      fs.appendFileSync(envPath, `\nNEXT_PUBLIC_API_URL=${apiUrl}\n`)
      console.log(`✅ Agregado NEXT_PUBLIC_API_URL a .env.local`)
    }
  } else {
    // Crear nuevo archivo
    fs.writeFileSync(envPath, envContent, 'utf8')
    console.log(`✅ Creado .env.local con URL: ${apiUrl}`)
  }
} catch (error) {
  console.error('❌ Error al escribir .env.local:', error.message)
  console.log('\n📝 Configura manualmente en .env.local:')
  console.log(`NEXT_PUBLIC_API_URL=${apiUrl}`)
  process.exit(1)
}

console.log('\n🚀 Reinicia el servidor de Next.js para aplicar los cambios:')
console.log('   npm run dev')

