# Configuración para Acceso desde IP Pública

## Problema

Cuando accedes a la aplicación desde una IP pública, el frontend intenta conectarse a `localhost:8000`, que no existe en la máquina del cliente. El frontend necesita saber la URL pública del backend.

## Solución

### Opción 1: Usar Variable de Entorno (Recomendado)

1. **Obtén tu IP pública local:**
   ```bash
   # En Windows (PowerShell)
   ipconfig | findstr IPv4
   
   # O usa tu IP pública si tienes acceso directo
   # Ejemplo: 192.168.1.100 o tu IP pública real
   ```

2. **Crea/modifica `.env.local` en el frontend:**
   ```env
   NEXT_PUBLIC_API_URL=http://TU_IP_PUBLICA:8000
   # Ejemplo:
   # NEXT_PUBLIC_API_URL=http://192.168.1.100:8000
   # O si usas ngrok:
   # NEXT_PUBLIC_API_URL=https://denver-unbrooded-miley.ngrok-free.dev
   ```

3. **Reinicia el servidor de Next.js:**
   ```bash
   npm run dev
   # o
   yarn dev
   ```

### Opción 2: Usar ngrok (Ya configurado)

Si ya estás usando ngrok, configura la URL de ngrok:

```env
# En frontend/.env.local
NEXT_PUBLIC_API_URL=https://denver-unbrooded-miley.ngrok-free.dev
```

### Opción 3: Detección Automática (Script)

El script `detect-api-url.js` puede ayudarte a detectar automáticamente la IP local.

## Verificación

1. **Verifica que el backend esté accesible:**
   ```bash
   # Desde otra máquina en la red, prueba:
   curl http://TU_IP:8000/api/v1/health
   ```

2. **Verifica que el puerto 8000 esté abierto:**
   - Windows Firewall debe permitir conexiones entrantes en el puerto 8000
   - El router debe tener el puerto 8000 abierto si accedes desde internet

## Configuración del Firewall (Windows)

1. Abre "Firewall de Windows Defender"
2. Click en "Configuración avanzada"
3. Click en "Reglas de entrada" → "Nueva regla"
4. Selecciona "Puerto" → Siguiente
5. TCP → Puerto específico: 8000 → Siguiente
6. "Permitir la conexión" → Siguiente
7. Marca todas las opciones → Siguiente
8. Nombre: "Backend API Puerto 8000" → Finalizar

## Notas Importantes

- El backend ya está configurado para escuchar en `0.0.0.0:8000` (todas las interfaces)
- El problema es solo la configuración del frontend
- Si usas ngrok, no necesitas abrir puertos en el firewall
- Para producción, usa un dominio real en lugar de IPs

