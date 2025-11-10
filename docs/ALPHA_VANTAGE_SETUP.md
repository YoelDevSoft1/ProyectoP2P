# 🚀 Configuración de Alpha Vantage API

## ✅ Tu API Key

Tu API key de Alpha Vantage es:
```
A828MZ96KHX5QJRF
```

**⚠️ IMPORTANTE:** 
- Guarda esta clave en un lugar seguro
- **NUNCA** la compartas públicamente
- **NUNCA** la subas a GitHub
- Solo úsala en tu archivo `.env` (que está en `.gitignore`)

---

## 🔧 Paso 1: Configurar en .env

Abre tu archivo `.env` en la raíz del proyecto y agrega:

```env
# Alpha Vantage API
ALPHA_VANTAGE_API_KEY=A828MZ96KHX5QJRF
ALPHA_VANTAGE_ENABLED=true
ALPHA_VANTAGE_CACHE_TTL=900
```

### Si no tienes archivo .env:

1. Crea un archivo `.env` en la raíz del proyecto
2. Agrega las líneas de arriba
3. Asegúrate de que `.env` esté en `.gitignore` (ya está configurado)

---

## 🧪 Paso 2: Probar la Configuración

### Opción A: Usando Python (Recomendado)

Crea un archivo de prueba `test_alpha_vantage.py`:

```python
import asyncio
from app.services.alpha_vantage_service import AlphaVantageService

async def test():
    service = AlphaVantageService()
    
    # Probar obtener tasa USD/COP
    rate = await service.get_forex_realtime("USD", "COP")
    print(f"USD/COP: {rate}")
    
    # Probar obtener RSI
    rsi = await service.get_rsi("USD/COP", interval="daily")
    print(f"RSI: {rsi}")

if __name__ == "__main__":
    asyncio.run(test())
```

Ejecuta:
```bash
cd backend
python test_alpha_vantage.py
```

### Opción B: Usando el Endpoint API

Una vez que reinicies el backend, puedes probar:

```bash
# Obtener tasa USD/COP
curl http://localhost:8000/api/v1/forex/realtime/USD/COP

# Obtener datos históricos
curl http://localhost:8000/api/v1/forex/historical/USD/COP

# Obtener RSI
curl http://localhost:8000/api/v1/forex/indicators/USD/COP/RSI
```

---

## 🔄 Paso 3: Reiniciar el Backend

Para que los cambios surtan efecto:

```bash
# Si usas Docker
docker-compose restart backend

# Si ejecutas directamente
# Reinicia el servidor FastAPI
```

---

## ✅ Paso 4: Verificar que Funciona

Revisa los logs del backend:

```bash
docker-compose logs -f backend | grep -i alpha
```

Deberías ver mensajes como:
```
Alpha Vantage forex rate fetched from_currency=USD to_currency=COP rate=4000.50
```

---

## 🎯 Casos de Uso

### 1. Validación de Precios

Alpha Vantage se integrará automáticamente en `FXService` para:
- Validar USD/COP con TRM
- Validar USD/VES, USD/BRL, USD/ARS
- Detectar anomalías en precios
- Alertar si hay discrepancias > 2%

### 2. Indicadores Técnicos

Para el sistema de trading:
- RSI, MACD, Bollinger Bands precalculados
- Menos carga computacional
- Mayor precisión

### 3. Datos Históricos

Para análisis:
- Datos históricos diarios
- Análisis de tendencias
- Backtesting de estrategias

---

## 📊 Límites de la API

### Free Tier (Tu plan actual)
- ✅ 25 requests/día
- ✅ 5 requests/minuto
- ✅ Caché de 15 minutos (reduce requests)
- ✅ Suficiente para validación de precios

### Premium Tier (Opcional)
- 💰 Hasta 1200 requests/día
- 💰 Mayor velocidad
- 💰 ~$50/mes
- **Recomendación:** Solo si necesitas más requests

---

## 🔍 Monitoreo

### Verificar Uso de la API

Revisa los logs para ver:
- Cuántas requests se hacen
- Si hay rate limits
- Si hay errores

### Métricas Recomendadas

- Requests por día
- Cache hit rate
- Errores de API
- Discrepancias con TRM/Binance

---

## ⚠️ Troubleshooting

### Error: "API key not configured"
- Verifica que `ALPHA_VANTAGE_API_KEY` esté en `.env`
- Verifica que el backend se haya reiniciado
- Verifica que no haya espacios en la clave

### Error: "Rate limit exceeded"
- Has alcanzado el límite de 25 requests/día
- Espera hasta el día siguiente
- O considera actualizar a premium

### Error: "Alpha Vantage API error"
- Verifica tu conexión a internet
- Verifica que la API key sea válida
- Revisa los logs para más detalles

---

## 🎉 ¡Listo!

Tu API key de Alpha Vantage está configurada y lista para usar.

**Próximos pasos:**
1. ✅ API key configurada en `.env`
2. ✅ Servicio implementado
3. ⏭️ Probar con un ejemplo
4. ⏭️ Integrar validación en `FXService`
5. ⏭️ Monitorear uso

---

**Fecha:** 2025-11-09  
**API Key:** A828MZ96KHX5QJRF  
**Estado:** Configurada y lista para usar

