# 🚀 Comando Rápido para Entrenar con Yahoo Finance

## ✅ Sistema Listo

El sistema está **completamente optimizado** para entrenar con Yahoo Finance. 

## 🎯 Comando Principal

```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=transformer&epochs=50&batch_size=32&learning_rate=0.0001"
```

## 📊 Opciones de Símbolos

### **Criptomonedas** (Recomendado):
- `BTC-USD`: Bitcoin
- `ETH-USD`: Ethereum  
- `SOL-USD`: Solana

### **Forex**:
- `USDCOP=X`: USD/COP
- `EURUSD=X`: EUR/USD

### **Acciones**:
- `AAPL`: Apple
- `MSFT`: Microsoft
- `TSLA`: Tesla

## ⚙️ Parámetros

- `symbol`: Símbolo (default: BTC-USD)
- `period`: Período - `1y`, `2y`, `5y`, `max` (default: 2y)
- `interval`: Intervalo - `1d`, `1h`, `1wk` (default: 1d)
- `model_type`: `transformer`, `ensemble`, `profit-aware`, `all` (default: transformer)
- `epochs`: Número de épocas (default: 50)
- `batch_size`: Tamaño de batch (default: 32)
- `learning_rate`: Tasa de aprendizaje (default: 0.0001)

## 🚀 Configuraciones Recomendadas

### **Testing Rápido**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=1y&interval=1d&model_type=transformer&epochs=10&batch_size=16"
```

### **Producción**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=transformer&epochs=50&batch_size=32"
```

### **Máxima Robustez (Ensemble)**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=ensemble&epochs=30&batch_size=32"
```

## ✅ Ventajas

- ✅ **Datos de calidad**: Yahoo Finance
- ✅ **Más datos históricos**: Hasta 10 años
- ✅ **Normalización optimizada**: Targets normalizados
- ✅ **Mejor convergencia**: Modelos más estables
- ✅ **Métricas precisas**: Profit metrics correctas

## 📝 Ver Logs

```bash
docker logs p2p_backend -f
```

## 🎉 ¡Listo para Entrenar!

El sistema está completamente configurado y optimizado. Solo ejecuta el comando de arriba para empezar a entrenar. 🚀💰


