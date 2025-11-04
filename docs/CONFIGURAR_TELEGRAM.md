# 📱 Guía de Configuración del Bot de Telegram

Esta guía te ayudará a configurar el bot de Telegram para recibir notificaciones de tu sistema P2P.

## 📋 Prerrequisitos

- Tener Telegram instalado en tu teléfono o computadora
- Acceso a internet

---

## 🔧 Paso 1: Crear el Bot de Telegram

1. **Abre Telegram** y busca `@BotFather` en la búsqueda
2. **Inicia una conversación** con BotFather
3. **Envía el comando** `/newbot`
4. **Sigue las instrucciones**:
   - Proporciona un nombre para tu bot (ejemplo: "Mi Bot P2P")
   - Proporciona un username único que termine en `bot` (ejemplo: `mi_bot_p2p_bot`)
5. **BotFather te dará un TOKEN** que se verá así:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
6. **⚠️ IMPORTANTE**: Copia y guarda este token de forma segura. Lo necesitarás en el siguiente paso.

---

## 🔍 Paso 2: Obtener tu Chat ID

Tu Chat ID es tu identificador único en Telegram. Necesitas obtenerlo para que el bot sepa a quién enviar los mensajes.

### Método 1: Usando @userinfobot (Recomendado)

1. Busca `@userinfobot` en Telegram
2. Inicia una conversación con él
3. Envíale cualquier mensaje (por ejemplo: `/start`)
4. El bot te responderá con tu información, incluyendo tu **Chat ID** (un número como `123456789`)

### Método 2: Usando la API de Telegram

1. Primero, envía un mensaje a tu bot (el que creaste en el Paso 1)
2. Abre esta URL en tu navegador (reemplaza `TU_TOKEN` con el token que obtuviste):
   ```
   https://api.telegram.org/botTU_TOKEN/getUpdates
   ```
3. Busca en la respuesta JSON el campo `"chat":{"id":123456789}`
4. Copia ese número (el **Chat ID**)

---

## ⚙️ Paso 3: Configurar las Variables en .env

Ahora necesitas actualizar tu archivo `.env` con los valores reales:

1. Abre el archivo `.env` en la raíz del proyecto
2. Busca estas líneas:
   ```env
   ENABLE_NOTIFICATIONS=true
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```
3. Reemplaza los valores:
   - `TELEGRAM_BOT_TOKEN`: Pega el token que obtuviste de BotFather
   - `TELEGRAM_CHAT_ID`: Pega tu Chat ID que obtuviste en el Paso 2

**Ejemplo de cómo debería quedar:**
```env
ENABLE_NOTIFICATIONS=true
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

---

## ✅ Paso 4: Probar la Configuración

Una vez configuradas las variables, puedes probar que todo funciona correctamente.

### Opción 1: Usando el Endpoint de Prueba

Si el backend está corriendo:

```bash
# En Windows PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analytics/test-notification" -Method POST

# O usando curl (si está instalado)
curl -X POST http://localhost:8000/api/v1/analytics/test-notification
```

### Opción 2: Desde el Navegador

1. Abre: http://localhost:8000/api/v1/docs
2. Busca el endpoint `POST /api/v1/analytics/test-notification`
3. Haz clic en "Try it out" y luego "Execute"
4. Deberías recibir un mensaje de prueba en Telegram

### Opción 3: Reiniciar el Servicio

Si el backend ya estaba corriendo, reinícialo para que cargue las nuevas variables:

```bash
# Si usas Docker
docker-compose restart backend

# O si corres el backend directamente
# Detén el proceso (Ctrl+C) y vuelve a iniciarlo
```

---

## 🎯 Tipos de Notificaciones que Recibirás

Una vez configurado, recibirás notificaciones automáticas de:

1. **🚀 Oportunidades P2P**: Cuando se detecten spreads rentables
2. **💎 Arbitrajes**: Oportunidades de arbitraje Spot-P2P
3. **🟢 Trades Ejecutados**: Cuando se complete una operación
4. **🚨 Errores Críticos**: Alertas de problemas en el sistema
5. **📊 Resúmenes Diarios**: Estadísticas del día

---

## 🔧 Solución de Problemas

### El bot no envía mensajes

1. **Verifica que el token sea correcto**: Asegúrate de haber copiado el token completo sin espacios
2. **Verifica el Chat ID**: Debe ser un número, sin comillas ni espacios
3. **Verifica que hayas enviado `/start` al bot**: El bot necesita que inicies una conversación primero
4. **Revisa los logs**: 
   ```bash
   docker-compose logs backend | grep -i telegram
   ```

### Error: "Unauthorized" o "Invalid token"

- El token que ingresaste no es válido
- Verifica que lo copiaste correctamente desde BotFather
- Asegúrate de que no haya espacios extra al inicio o final

### Error: "Chat not found"

- El Chat ID no es correcto
- Asegúrate de haber enviado al menos un mensaje al bot primero
- Verifica que el Chat ID sea un número (no un string)

### No recibo notificaciones automáticas

- Verifica que `ENABLE_NOTIFICATIONS=true` en el `.env`
- Asegúrate de que el backend esté corriendo
- Verifica que las tareas de Celery estén activas (para notificaciones automáticas)

---

## 📝 Notas Importantes

- ⚠️ **NUNCA** compartas tu `TELEGRAM_BOT_TOKEN` ni lo subas a GitHub
- El archivo `.env` está en `.gitignore` por seguridad
- Si cambias el token o Chat ID, necesitas reiniciar el backend
- Puedes crear múltiples bots para diferentes propósitos usando BotFather

---

## 🎉 ¡Listo!

Una vez completados estos pasos, tu bot de Telegram estará configurado y recibirás notificaciones automáticas del sistema.

Si tienes problemas, revisa los logs del backend o verifica que todas las variables estén correctamente configuradas.

