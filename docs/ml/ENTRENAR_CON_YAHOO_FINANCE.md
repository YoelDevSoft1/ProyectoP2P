# 🚀 Entrenar Modelos con Yahoo Finance - Guía Completa

## ✅ Configuración Optimizada

Se ha optimizado el sistema para usar **Yahoo Finance por defecto** con mejor manejo de datos y normalización.

## 🎯 Endpoint Principal (Recomendado)

### **`POST /api/v1/analytics/dl/advanced/train-with-yahoo`**

**Este es el endpoint principal** para entrenar con Yahoo Finance.

### **Parámetros**:
- `symbol`: Símbolo de Yahoo Finance (default: "BTC-USD")
- `period`: Período (default: "2y") - Opciones: "1y", "2y", "5y", "max"
- `interval`: Intervalo (default: "1d") - Opciones: "1d", "1h", "1wk"
- `model_type`: Tipo de modelo (default: "transformer")
  - `transformer`: Solo Transformer
  - `ensemble`: Solo Ensemble
  - `profit-aware`: Solo Profit-Aware
  - `all`: Todos los modelos
- `epochs`: Número de épocas (default: 50)
- `batch_size`: Tamaño de batch (default: 32)
- `learning_rate`: Tasa de aprendizaje (default: 0.0001)

## 🚀 Comandos para Entrenar

### **1. Entrenar Transformer (Recomendado para empezar)**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=transformer&epochs=50&batch_size=32&learning_rate=0.0001"
```

### **2. Entrenar Ensemble (Máxima Robustez)**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=ensemble&epochs=30&batch_size=32"
```

### **3. Entrenar Profit-Aware (Optimizado para Profit)**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=profit-aware&epochs=50&batch_size=32"
```

### **4. Entrenar Todos los Modelos**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=all&epochs=50&batch_size=32"
```

## 📊 Símbolos Disponibles

### **Criptomonedas** (Recomendado):
- `BTC-USD`: Bitcoin
- `ETH-USD`: Ethereum
- `BNB-USD`: Binance Coin
- `ADA-USD`: Cardano
- `SOL-USD`: Solana
- `XRP-USD`: Ripple
- `DOGE-USD`: Dogecoin

### **Forex**:
- `USDCOP=X`: USD/COP
- `EURUSD=X`: EUR/USD
- `GBPUSD=X`: GBP/USD
- `USDJPY=X`: USD/JPY

### **Acciones**:
- `AAPL`: Apple
- `MSFT`: Microsoft
- `GOOGL`: Google
- `AMZN`: Amazon
- `TSLA`: Tesla

## 💡 Mejoras Implementadas

### **1. Normalización de Targets**:
- ✅ Targets normalizados con StandardScaler
- ✅ Evita problemas con valores extremos
- ✅ Mejor convergencia del modelo
- ✅ Métricas de profit calculadas con valores originales

### **2. Limpieza de Datos Mejorada**:
- ✅ Detección y eliminación de outliers
- ✅ Manejo de valores infinitos
- ✅ Validación de datos antes de entrenar

### **3. Feature Engineering Optimizado**:
- ✅ Aprovecha datos OHLCV de Yahoo Finance
- ✅ 50+ features técnicas
- ✅ Features de mercado y temporales

## 🎯 Configuración Recomendada

### **Para Máximo Profit**:
```bash
# Símbolo: BTC-USD (alta volatilidad = más oportunidades)
# Período: 2y (más datos = mejor modelo)
# Modelo: Ensemble (máxima robustez)
# Épocas: 50-100
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=ensemble&epochs=50&batch_size=32"
```

### **Para Forex Trading**:
```bash
# Símbolo: USDCOP=X
# Período: 2y
# Modelo: Transformer
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=USDCOP=X&period=2y&interval=1d&model_type=transformer&epochs=50"
```

### **Para Empezar Rápido**:
```bash
# Período más corto: 1y
# Menos épocas: 20
# Modelo: Transformer
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=1y&interval=1d&model_type=transformer&epochs=20&batch_size=32"
```

## ⚠️ Manejo de Rate Limiting

Yahoo Finance puede tener rate limiting. El sistema incluye:
- ✅ Retry automático con delays
- ✅ Manejo de errores mejorado
- ✅ Mensajes de error informativos

Si encuentras problemas:
1. Espera 1-2 minutos entre requests
2. Usa períodos más largos (menos requests)
3. Usa el endpoint con datos de BD como fallback

## ✅ Ventajas de Yahoo Finance

### **vs Datos de BD**:
- ✅ **Más datos históricos**: Hasta 10 años
- ✅ **Mejor calidad**: Datos de mercado reales
- ✅ **Más símbolos**: Múltiples activos
- ✅ **OHLCV completo**: Open, High, Low, Close, Volume
- ✅ **Actualizado**: Datos en tiempo real

### **Mejoras en el Modelo**:
- ✅ Normalización correcta de targets
- ✅ Mejor convergencia
- ✅ Métricas de profit más precisas
- ✅ Modelos más robustos

## 🚀 Próximos Pasos

1. **✅ Entrenar Transformer con BTC-USD** (recomendado para empezar)
2. **✅ Evaluar resultados** con métricas de profit
3. **✅ Backtest** estrategias
4. **✅ Optimizar** hiperparámetros
5. **✅ Entrenar Ensemble** si Transformer funciona bien

## 📝 Ejemplo Completo

```bash
# 1. Entrenar Transformer con BTC-USD (2 años de datos)
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=transformer&epochs=50&batch_size=32&learning_rate=0.0001"

# 2. Esperar a que termine (puede tomar 5-15 minutos)

# 3. Ver métricas de profit
curl "http://localhost:8000/api/v1/analytics/dl/advanced/profit-metrics?days=30"

# 4. Backtest de estrategia
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/backtest?buy_threshold=0.02&sell_threshold=0.02&stop_loss=0.05&take_profit=0.10"
```

## ✅ Estado

**¡Sistema optimizado para Yahoo Finance!** 🚀

- ✅ Endpoint `train-with-yahoo` implementado
- ✅ Normalización de targets mejorada
- ✅ Manejo de rate limiting
- ✅ Feature engineering optimizado
- ✅ Listo para entrenar con datos de calidad

## 🎉 Conclusión

**Sistema completamente optimizado** para entrenar con Yahoo Finance. Usa el endpoint `train-with-yahoo` para obtener los mejores resultados. 🚀💰

