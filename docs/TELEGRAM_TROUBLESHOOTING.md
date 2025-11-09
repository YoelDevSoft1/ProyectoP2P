# Solución de Problemas del Bot de Telegram

## Diagnóstico Rápido

### 1. Verificar Configuración

Asegúrate de tener configuradas las siguientes variables de entorno:

```env
ENABLE_NOTIFICATIONS=true
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
```

### 2. Ejecutar Script de Diagnóstico

```bash
cd backend
python scripts/test_telegram.py
```

Este script verificará:
- ✅ Configuración de variables de entorno
- ✅ Estado del servicio
- ✅ Salud del bot
- ✅ Conexión con Telegram
- ✅ Envío de mensaje de prueba

### 3. Probar desde la API

```bash
curl -X POST http://localhost:8000/api/v1/analytics/test-notification
```

## Problemas Comunes

### ❌ Error: "Telegram disabled: TELEGRAM_BOT_TOKEN not configured"

**Solución:**
1. Obtén un token de @BotFather en Telegram
2. Agrega `TELEGRAM_BOT_TOKEN=tu_token` al archivo `.env`
3. Reinicia el backend

### ❌ Error: "Telegram disabled: TELEGRAM_CHAT_ID not configured"

**Solución:**
1. Inicia una conversación con tu bot en Telegram
2. Obtén tu chat ID usando @userinfobot o @getidsbot
3. Agrega `TELEGRAM_CHAT_ID=tu_chat_id` al archivo `.env`
4. Reinicia el backend

### ❌ Error: "python-telegram-bot not installed"

**Solución:**
```bash
cd backend
pip install python-telegram-bot==20.8
```

### ❌ Error: "Chat not found"

**Solución:**
1. Asegúrate de haber iniciado una conversación con el bot
2. Verifica que el chat ID sea correcto (debe ser un número, no un username)
3. Si el bot está en un grupo, asegúrate de que el bot tenga permisos para enviar mensajes

### ❌ Error: "Bot was blocked by the user"

**Solución:**
1. Desbloquea el bot en Telegram
2. Inicia una nueva conversación con el bot
3. Envía el comando `/start` al bot

### ❌ Error: "Invalid token"

**Solución:**
1. Verifica que el token sea correcto
2. Asegúrate de que no haya espacios extra en el token
3. Regenera el token desde @BotFather si es necesario

### ❌ Error: "Timeout" o "Connection error"

**Solución:**
1. Verifica tu conexión a Internet
2. Verifica que Telegram no esté bloqueado en tu red
3. Revisa los logs para más detalles

## Verificación Paso a Paso

### Paso 1: Crear el Bot

1. Abre Telegram y busca @BotFather
2. Envía `/newbot`
3. Sigue las instrucciones para crear el bot
4. Copia el token que te da BotFather

### Paso 2: Obtener Chat ID

**Opción 1: Usando @userinfobot**
1. Busca @userinfobot en Telegram
2. Inicia una conversación
3. El bot te dará tu chat ID

**Opción 2: Usando @getidsbot**
1. Busca @getidsbot en Telegram
2. Agrega el bot a tu chat o inicia una conversación
3. El bot te dará tu chat ID

**Opción 3: Desde el código**
```python
# Agrega esto temporalmente en tu código para obtener el chat ID
from telegram import Bot
import asyncio

async def get_chat_id():
    bot = Bot(token="TU_TOKEN")
    updates = await bot.get_updates()
    if updates:
        print(f"Chat ID: {updates[0].message.chat.id}")
    else:
        print("Envía un mensaje al bot primero")

asyncio.run(get_chat_id())
```

### Paso 3: Configurar Variables de Entorno

Crea o edita el archivo `.env` en la raíz del proyecto:

```env
ENABLE_NOTIFICATIONS=true
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### Paso 4: Iniciar Conversación con el Bot

1. Busca tu bot en Telegram (usando el username que le diste)
2. Inicia una conversación
3. Envía `/start` al bot

### Paso 5: Probar el Bot

```bash
# Ejecutar script de diagnóstico
cd backend
python scripts/test_telegram.py

# O probar desde la API
curl -X POST http://localhost:8000/api/v1/analytics/test-notification
```

## Verificación de Logs

Revisa los logs del backend para ver mensajes relacionados con Telegram:

```bash
# Ver logs del backend
docker-compose logs -f backend | grep -i telegram

# O si estás ejecutando localmente
tail -f logs/backend.log | grep -i telegram
```

## Múltiples Chat IDs

Para enviar notificaciones a múltiples chats, separa los IDs por comas:

```env
TELEGRAM_CHAT_ID=123456789,987654321,111222333
```

## Verificar Estado del Servicio

Puedes verificar el estado del servicio desde el código:

```python
from app.services.telegram_service import telegram_service

# Verificar si está habilitado
print(f"Enabled: {telegram_service.enabled}")

# Verificar chat IDs
print(f"Chat IDs: {telegram_service.chat_ids}")

# Verificar salud
import asyncio
health = asyncio.run(telegram_service.health_check())
print(f"Health: {health}")
```

## Soporte

Si sigues teniendo problemas:

1. Revisa los logs del backend
2. Ejecuta el script de diagnóstico
3. Verifica la configuración de variables de entorno
4. Asegúrate de que el bot esté funcionando correctamente en Telegram

