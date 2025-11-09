# Cómo obtener tu Chat ID - Guía Manual

## Tu Token del Bot:
```
8519988770:AAHvjXA_goCW-vGz20K4Au_xT3naVF0UCBs
```

## Paso 1: Encontrar tu Bot en Telegram

1. Abre Telegram
2. En la barra de búsqueda, busca el **username** de tu bot
   - Si no recuerdas el username, BotFather te lo dio cuando creaste el bot
   - O puedes buscar `@BotFather` y enviarle `/mybots` para ver tus bots
3. Abre la conversación con tu bot

## Paso 2: Iniciar la Conversación

1. Una vez en la conversación con tu bot, envía cualquier mensaje:
   - Puedes escribir: `/start`
   - O simplemente: `Hola`
   - O cualquier mensaje

## Paso 3: Obtener el Chat ID

### Opción A: Usar el Script (Más fácil)

1. Ejecuta el script:
   ```powershell
   .\scripts\obtener_chat_id.ps1
   ```
2. Sigue las instrucciones en pantalla

### Opción B: Usar el Navegador (Manual)

1. Abre esta URL en tu navegador:
   ```
   https://api.telegram.org/bot8519988770:AAHvjXA_goCW-vGz20K4Au_xT3naVF0UCBs/getUpdates
   ```

2. Verás una respuesta JSON que se ve así:
   ```json
   {
     "ok": true,
     "result": [
       {
         "update_id": 123456789,
         "message": {
           "message_id": 1,
           "from": {
             "id": 987654321,
             "is_bot": false,
             "first_name": "Tu Nombre",
             "username": "tu_usuario"
           },
           "chat": {
             "id": 987654321,  <-- ESTE ES TU CHAT ID
             "first_name": "Tu Nombre",
             "username": "tu_usuario",
             "type": "private"
           },
           "date": 1234567890,
           "text": "/start"
         }
       }
     ]
   }
   ```

3. Busca el número que está en `"chat":{"id":` - ese es tu Chat ID

### Opción C: Usar @userinfobot (Alternativa)

1. Busca `@userinfobot` en Telegram
2. Envíale cualquier mensaje
3. Te responderá con tu Chat ID directamente

## Paso 4: Configurar en .env

Una vez tengas tu Chat ID, agrega esto a tu archivo `.env`:

```env
ENABLE_NOTIFICATIONS=true
TELEGRAM_BOT_TOKEN=8519988770:AAHvjXA_goCW-vGz20K4Au_xT3naVF0UCBs
TELEGRAM_CHAT_ID=tu_chat_id_aqui
```

---

## Problemas Comunes

### "No puedo encontrar mi bot"

- Busca `@BotFather` en Telegram
- Envíale `/mybots`
- Selecciona tu bot
- Verás el username y podrás iniciar la conversación desde ahí

### "No aparece nada en getUpdates"

- Asegúrate de haber enviado al menos un mensaje a tu bot primero
- Espera unos segundos y vuelve a abrir la URL
- Si sigue sin funcionar, el token puede estar incorrecto

### "El bot no responde"

- No importa, el bot no necesita responder
- Solo necesitas que Telegram registre que enviaste un mensaje
- El Chat ID es tuyo, no del bot

