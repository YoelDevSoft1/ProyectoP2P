# 🚀 Alpha Vantage - Guía de Inicio Rápido

## ✅ Tu API Key está lista

Tu API key de Alpha Vantage:
```
A828MZ96KHX5QJRF
```

---

## 🔧 Paso 1: Configurar en .env

Abre tu archivo `.env` en la raíz del proyecto y agrega:

```env
# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF
ALPHA_VANTAGE_ENABLED=true
ALPHA_VANTAGE_CACHE_TTL=900
```

**⚠️ IMPORTANTE:** 
- El archivo `.env` ya está en `.gitignore` (no se subirá a GitHub)
- **NUNCA** compartas esta clave públicamente
- Guarda esta clave en un lugar seguro

---

## 🧪 Paso 2: Probar la Configuración

### Opción A: Script de Prueba (Recomendado)

```bash
cd backend
python scripts/test_alpha_vantage.py
```

Este script verificará:
- ✅ Que la API key esté configurada
- ✅ Que el servicio funcione
- ✅ Que pueda obtener tasas USD/COP
- ✅ Que pueda obtener datos históricos
- ✅ Que pueda obtener indicadores técnicos

### Opción B: Probar desde la API

Una vez que reinicies el backend:

```bash
# Obtener tasa USD/COP
curl http://localhost:8000/api/v1/forex/realtime/USD/COP

# Validar tasa con múltiples fuentes
curl http://localhost:8000/api/v1/forex/validate/COP

# Obtener datos históricos
curl http://localhost:8000/api/v1/forex/historical/USD/COP

# Obtener RSI
curl http://localhost:8000/api/v1/forex/indicators/USDCOP/RSI
```

---

## 🔄 Paso 3: Reiniciar el Backend

Para que los cambios surtan efecto:

```bash
# Si usas Docker
docker-compose restart backend

# O reinicia el servidor FastAPI si lo ejecutas directamente
```

---

## ✅ Paso 4: Verificar que Funciona

### Revisar Logs

```bash
docker-compose logs -f backend | grep -i alpha
```

Deberías ver mensajes como:
```
Alpha Vantage forex rate fetched from_currency=USD to_currency=COP rate=4000.50
```

### Probar Endpoint de Validación

```bash
curl http://localhost:8000/api/v1/forex/validate/COP
```

Deberías ver una comparación entre:
- TRM (fuente oficial para COP)
- Alpha Vantage
- FX Service (que usa múltiples fuentes)

---

## 🎯 ¿Qué está Integrado?

### ✅ Validación Automática de Precios

El `FXService` ahora:
1. **Para COP:** Usa TRM (fuente oficial) y valida con Alpha Vantage
2. **Para otras monedas:** Usa Alpha Vantage primero, luego Binance P2P
3. **Detecta anomalías:** Alerta si hay discrepancias > 2%
4. **Fallback inteligente:** Si una fuente falla, usa otra

### ✅ Endpoints API Disponibles

1. **GET `/api/v1/forex/realtime/{from}/{to}`**
   - Obtener tasa de cambio en tiempo real
   - Ejemplo: `/api/v1/forex/realtime/USD/COP`

2. **GET `/api/v1/forex/historical/{from}/{to}`**
   - Obtener datos históricos diarios
   - Ejemplo: `/api/v1/forex/historical/USD/COP?outputsize=compact`

3. **GET `/api/v1/forex/indicators/{symbol}/{indicator}`**
   - Obtener indicadores técnicos (RSI, MACD, BBANDS)
   - Ejemplo: `/api/v1/forex/indicators/USDCOP/RSI`

4. **GET `/api/v1/forex/validate/{fiat}`**
   - Validar tasa comparando múltiples fuentes
   - Ejemplo: `/api/v1/forex/validate/COP`

---

## 📊 Ejemplos de Uso

### Ejemplo 1: Validar Precio USD/COP

```python
from app.services.fx_service import FXService

fx_service = FXService()
rate = await fx_service.get_rate("COP")
# Ahora usa TRM + validación Alpha Vantage automáticamente
```

### Ejemplo 2: Obtener Indicadores Técnicos

```python
from app.services.alpha_vantage_service import AlphaVantageService

av_service = AlphaVantageService()

# Obtener RSI
rsi = await av_service.get_rsi("USDCOP", interval="daily")

# Obtener MACD
macd = await av_service.get_macd("USDCOP", interval="daily")

# Obtener Bollinger Bands
bbands = await av_service.get_bollinger_bands("USDCOP", interval="daily")
```

### Ejemplo 3: Obtener Datos Históricos

```python
from app.services.alpha_vantage_service import AlphaVantageService

av_service = AlphaVantageService()

# Obtener últimos 100 días
historical = await av_service.get_forex_daily("USD", "COP", outputsize="compact")

# Obtener 20 años de datos
full_historical = await av_service.get_forex_daily("USD", "COP", outputsize="full")
```

---

## 📈 Monitoreo

### Verificar Uso de la API

Revisa los logs para ver:
- Cuántas requests se hacen
- Si hay rate limits
- Si hay errores
- Discrepancias entre fuentes

### Métricas Recomendadas

- Requests por día (límite: 25/día free tier)
- Cache hit rate (debería ser alto con caché de 15 min)
- Errores de API
- Discrepancias con TRM/Binance

---

## ⚠️ Troubleshooting

### Error: "API key not configured"
**Solución:**
- Verifica que `ALPHA_VANTAGE_API_KEY` esté en `.env`
- Verifica que el backend se haya reiniciado
- Verifica que no haya espacios en la clave

### Error: "Rate limit exceeded"
**Solución:**
- Has alcanzado el límite de 25 requests/día
- Espera hasta el día siguiente
- O considera actualizar a premium

### Error: "Alpha Vantage API error"
**Solución:**
- Verifica tu conexión a internet
- Verifica que la API key sea válida
- Revisa los logs para más detalles

### Los indicadores técnicos no funcionan
**Nota:** Alpha Vantage puede requerir formatos específicos de símbolos para Forex.
- Para Forex, el formato puede ser "USDCOP" en lugar de "USD/COP"
- Algunos indicadores pueden no estar disponibles para todos los pares
- Consulta la documentación de Alpha Vantage para formatos correctos

---

## 🎉 ¡Listo!

Tu API key de Alpha Vantage está configurada y el servicio está integrado.

**Próximos pasos:**
1. ✅ API key configurada
2. ✅ Servicio implementado
3. ✅ Integrado en FXService
4. ✅ Endpoints API disponibles
5. ⏭️ Probar con ejemplos
6. ⏭️ Monitorear uso

---

## 📚 Documentación Adicional

- `docs/ALPHA_VANTAGE_INTEGRATION.md` - Guía completa de integración
- `docs/ALPHA_VANTAGE_RESUMEN.md` - Resumen ejecutivo
- `docs/ALPHA_VANTAGE_SETUP.md` - Guía de configuración

---

**Fecha:** 2025-11-09  
**API Key:** A828MZ96KHX5QJRF  
**Estado:** ✅ Configurada y lista para usar

