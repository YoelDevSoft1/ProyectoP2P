# 🚀 Entrenar Modelos con Yahoo Finance

## ✅ Integración Completa

Se ha integrado Yahoo Finance para obtener datos históricos y entrenar los modelos avanzados.

## 📊 Servicio de Yahoo Finance

**Archivo**: `backend/app/services/yahoo_finance_service.py`

### **Funcionalidades**:
- ✅ Obtener datos de criptomonedas (BTC-USD, ETH-USD, etc.)
- ✅ Obtener datos de Forex (USDCOP=X, EURUSD=X, etc.)
- ✅ Obtener datos de acciones (AAPL, MSFT, etc.)
- ✅ Preparar datos para entrenamiento de ML
- ✅ Soporte para múltiples períodos e intervalos

## 🎯 Endpoints Actualizados

### **1. Entrenar Transformer con Yahoo Finance**:
```bash
POST /api/v1/analytics/dl/advanced/train-transformer
```

**Parámetros**:
- `symbol`: Símbolo de Yahoo Finance (default: "BTC-USD")
  - Criptomonedas: "BTC-USD", "ETH-USD", "BNB-USD"
  - Forex: "USDCOP=X", "EURUSD=X"
  - Acciones: "AAPL", "MSFT", "GOOGL"
- `period`: Período (default: "1y")
  - Opciones: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"
- `interval`: Intervalo (default: "1d")
  - Opciones: "1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"
- `use_yahoo`: Usar Yahoo Finance (default: true)
- `epochs`: Número de épocas (default: 100)
- `batch_size`: Tamaño de batch (default: 32)
- `learning_rate`: Tasa de aprendizaje (default: 0.0001)

**Ejemplo**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-transformer?symbol=BTC-USD&period=1y&interval=1d&epochs=100&batch_size=32&learning_rate=0.0001"
```

### **2. Entrenar Profit-Aware Model**:
```bash
POST /api/v1/analytics/dl/advanced/train-profit-aware
```

**Ejemplo**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-profit-aware?symbol=BTC-USD&period=1y&epochs=100"
```

### **3. Entrenar Ensemble**:
```bash
POST /api/v1/analytics/dl/advanced/train-ensemble
```

**Ejemplo**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-ensemble?symbol=BTC-USD&period=1y&epochs=50"
```

## 💡 Símbolos Disponibles

### **Criptomonedas**:
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
- `USDCAD=X`: USD/CAD

### **Acciones**:
- `AAPL`: Apple
- `MSFT`: Microsoft
- `GOOGL`: Google
- `AMZN`: Amazon
- `TSLA`: Tesla

## 🚀 Cómo Entrenar

### **Opción 1: Transformer (Recomendado)**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-transformer?symbol=BTC-USD&period=2y&interval=1d&epochs=100&batch_size=32"
```

### **Opción 2: Ensemble (Máxima Robustez)**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-ensemble?symbol=BTC-USD&period=2y&epochs=50&batch_size=32"
```

### **Opción 3: Profit-Aware (Optimizado para Profit)**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-profit-aware?symbol=BTC-USD&period=2y&epochs=100"
```

## 📊 Ventajas de Yahoo Finance

### **vs Alpha Vantage**:
- ✅ **Sin límites estrictos**: No hay límite de 25 requests/día
- ✅ **Más datos históricos**: Hasta 10 años de datos
- ✅ **Más símbolos**: Criptomonedas, Forex, Acciones
- ✅ **Gratis**: Sin necesidad de API key
- ✅ **Más rápido**: Menos latencia

### **vs Base de Datos Local**:
- ✅ **Más datos**: Miles de puntos de datos históricos
- ✅ **Mejor calidad**: Datos de mercado reales
- ✅ **Más símbolos**: Múltiples activos
- ✅ **Actualizado**: Datos en tiempo real

## 🎯 Recomendaciones

### **Para Máximo Profit**:
1. **Símbolo**: BTC-USD o ETH-USD (alta volatilidad)
2. **Período**: 2y o 5y (más datos = mejor modelo)
3. **Intervalo**: 1d (diario)
4. **Modelo**: Ensemble (máxima robustez)
5. **Épocas**: 100-200 (mejor precisión)

### **Para Forex Trading**:
1. **Símbolo**: USDCOP=X
2. **Período**: 2y
3. **Intervalo**: 1d
4. **Modelo**: Transformer
5. **Épocas**: 100

### **Para Acciones**:
1. **Símbolo**: AAPL, MSFT, GOOGL
2. **Período**: 5y
3. **Intervalo**: 1d
4. **Modelo**: Profit-Aware
5. **Épocas**: 100

## ✅ Estado

**¡Integración completa!** 🚀

- ✅ Yahoo Finance service implementado
- ✅ Endpoints actualizados
- ✅ yfinance instalado
- ✅ Preparación de datos implementada
- ✅ Listo para entrenar modelos

## 🎉 Próximos Pasos

1. **Entrenar modelos** con datos de Yahoo Finance
2. **Evaluar resultados** con métricas de profit
3. **Backtest** estrategias
4. **Implementar** en producción
5. **Monitorear** performance

