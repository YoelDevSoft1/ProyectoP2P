# 🚀 Comando para Entrenar con Yahoo Finance

## ✅ Comando Recomendado

```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-yahoo?symbol=BTC-USD&period=2y&interval=1d&model_type=transformer&epochs=50&batch_size=32&learning_rate=0.0001"
```

## 📊 Opciones de Símbolos

### **Criptomonedas**:
- `BTC-USD`: Bitcoin (Recomendado)
- `ETH-USD`: Ethereum
- `BNB-USD`: Binance Coin
- `SOL-USD`: Solana

### **Forex**:
- `USDCOP=X`: USD/COP
- `EURUSD=X`: EUR/USD

## 🎯 Configuraciones Recomendadas

### **Rápido (Testing)**:
- `period=1y`
- `epochs=10`
- `batch_size=16`

### **Producción (Recomendado)**:
- `period=2y`
- `epochs=50`
- `batch_size=32`

### **Máxima Precisión**:
- `period=5y`
- `epochs=100`
- `batch_size=32`

## ✅ Ventajas

- ✅ **Datos de calidad**: Yahoo Finance
- ✅ **Más datos históricos**: Hasta 10 años
- ✅ **Normalización mejorada**: Targets normalizados
- ✅ **Mejor convergencia**: Modelos más estables
- ✅ **Métricas precisas**: Profit metrics correctas

## 🚀 ¡Listo para Entrenar!

Usa el comando de arriba para entrenar con Yahoo Finance. 🎯

