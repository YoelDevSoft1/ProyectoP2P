# ⚡ Configuración Rápida de Alpha Vantage

## ❌ Error que estás viendo

```
{"detail":"Alpha Vantage service is not enabled. Configure ALPHA_VANTAGE_API_KEY in .env"}
```

Este error significa que la API key de Alpha Vantage no está configurada en tu archivo `.env`.

---

## ✅ Solución Rápida (3 pasos)

### Paso 1: Agregar API Key en `.env`

Abre el archivo `.env` en la raíz del proyecto y agrega estas líneas:

```env
# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF
ALPHA_VANTAGE_ENABLED=true
ALPHA_VANTAGE_CACHE_TTL=900
```

**⚠️ IMPORTANTE:**
- Asegúrate de que no haya espacios alrededor del `=`
- No uses comillas alrededor del valor
- El archivo `.env` está en la raíz del proyecto (mismo nivel que `docker-compose.yml`)

### Paso 2: Verificar que el archivo `.env` existe

Si no tienes un archivo `.env`, créalo:

```bash
# En la raíz del proyecto
touch .env
# O simplemente créalo con tu editor de texto
```

### Paso 3: Reiniciar el Backend

**Si usas Docker (recomendado):**

```bash
# Reiniciar solo el backend
docker-compose restart backend

# O reiniciar todos los servicios
docker-compose down
docker-compose up -d
```

**Si ejecutas el backend directamente:**

```bash
# Detén el servidor (Ctrl+C) y reinícialo
cd backend
python -m uvicorn app.main:app --reload
```

---

## 🔍 Verificar que Funciona

### Opción 1: Probar el Endpoint

```bash
curl http://localhost:8000/api/v1/forex/realtime/USD/COP
```

Deberías ver una respuesta como:

```json
{
  "from_currency": "USD",
  "to_currency": "COP",
  "exchange_rate": 4000.50,
  "source": "alpha_vantage",
  "timestamp": null
}
```

### Opción 2: Probar el Endpoint de Validación

```bash
curl http://localhost:8000/api/v1/forex/validate/COP
```

Deberías ver:

```json
{
  "fiat": "COP",
  "sources": {
    "alpha_vantage": {
      "rate": 4000.50,
      "status": "available"
    },
    "trm": {
      "rate": 4000.00,
      "status": "available"
    },
    "fx_service": {
      "rate": 4000.25,
      "status": "available",
      "note": "Uses multiple sources (TRM, Alpha Vantage, Binance P2P)"
    }
  },
  "discrepancies": [],
  "alpha_vantage_enabled": true
}
```

### Opción 3: Revisar los Logs

```bash
docker-compose logs -f backend | grep -i alpha
```

Deberías ver:

```
Alpha Vantage service initialized api_key_prefix=A828MZ96
Alpha Vantage forex rate fetched from_currency=USD to_currency=COP rate=4000.50
```

---

## 🐛 Troubleshooting

### Error: "Alpha Vantage service is not enabled"

**Causas posibles:**

1. **La API key no está en `.env`**
   - Verifica que el archivo `.env` existe
   - Verifica que la línea `ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF` está presente
   - Verifica que no hay espacios alrededor del `=`

2. **El backend no se reinició**
   - Reinicia el backend: `docker-compose restart backend`
   - O reinicia todos los servicios: `docker-compose down && docker-compose up -d`

3. **El archivo `.env` no se está leyendo**
   - Verifica que el archivo `.env` está en la raíz del proyecto
   - Verifica que Docker Compose está configurado para leer el `.env`
   - Revisa los logs: `docker-compose logs backend | grep -i env`

### Error: "API key not configured"

**Solución:**

1. Verifica que la API key está correctamente escrita:
   ```env
   ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF
   ```

2. Verifica que no hay caracteres especiales o espacios:
   ```env
   # ❌ Incorrecto
   ALPHA_VANTAGE_API_KEY="A828MZ96KHX5QJRF"
   ALPHA_VANTAGE_API_KEY = A828MZ96KHX5QJRF
   
   # ✅ Correcto
   ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF
   ```

3. Reinicia el backend después de cambiar el `.env`

### Error: "Rate limit exceeded"

**Causa:** Has alcanzado el límite de 25 requests/día del plan free de Alpha Vantage.

**Solución:**
- Espera hasta el día siguiente
- O considera actualizar a un plan premium
- El servicio usa caché de 15 minutos para reducir requests

---

## 📝 Ejemplo de Archivo `.env` Completo

```env
# Binance API
BINANCE_API_KEY=tu_api_key_de_binance
BINANCE_API_SECRET=tu_api_secret_de_binance

# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF
ALPHA_VANTAGE_ENABLED=true
ALPHA_VANTAGE_CACHE_TTL=900

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/p2p_exchange

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id
ENABLE_NOTIFICATIONS=true

# Otros...
```

---

## ✅ Checklist

- [ ] Archivo `.env` existe en la raíz del proyecto
- [ ] `ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF` está en `.env`
- [ ] `ALPHA_VANTAGE_ENABLED=true` está en `.env`
- [ ] No hay espacios alrededor del `=`
- [ ] El backend se reinició después de agregar la clave
- [ ] Los logs muestran "Alpha Vantage service initialized"
- [ ] El endpoint `/api/v1/forex/realtime/USD/COP` funciona

---

## 🎉 ¡Listo!

Una vez que hayas completado estos pasos, el servicio de Alpha Vantage estará funcionando y podrás:

- ✅ Obtener tasas de cambio en tiempo real
- ✅ Validar precios con múltiples fuentes
- ✅ Obtener indicadores técnicos
- ✅ Obtener datos históricos

---

## 📚 Más Información

- `docs/ALPHA_VANTAGE_QUICK_START.md` - Guía de inicio rápido
- `docs/ALPHA_VANTAGE_INTEGRATION.md` - Guía completa de integración
- `docs/ALPHA_VANTAGE_SETUP.md` - Guía de configuración detallada

---

**API Key:** A828MZ96KHX5QJRF  
**Fecha:** 2025-11-09

