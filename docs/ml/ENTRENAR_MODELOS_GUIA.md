# 🚀 Guía para Entrenar Modelos Avanzados

## ✅ Integración Completa

Se ha integrado Yahoo Finance y se han creado endpoints para entrenar modelos con datos de la BD o Yahoo Finance.

## 🎯 Opción 1: Entrenar con Datos de la BD (Recomendado)

**La forma más rápida y confiable** si tienes datos históricos en tu BD:

### **Endpoint**:
```bash
POST /api/v1/analytics/dl/advanced/train-with-db-data
```

### **Parámetros**:
- `model_type`: Tipo de modelo (default: "transformer")
  - `transformer`: Solo Transformer
  - `ensemble`: Solo Ensemble
  - `profit-aware`: Solo Profit-Aware
  - `all`: Todos los modelos
- `epochs`: Número de épocas (default: 50)
- `batch_size`: Tamaño de batch (default: 32)
- `learning_rate`: Tasa de aprendizaje (default: 0.0001)
- `min_records`: Mínimo de registros (default: 200)

### **Ejemplos**:

#### **1. Entrenar Transformer**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-db-data?model_type=transformer&epochs=50&batch_size=32&learning_rate=0.0001"
```

#### **2. Entrenar Ensemble**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-db-data?model_type=ensemble&epochs=30&batch_size=32"
```

#### **3. Entrenar Todos los Modelos**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-db-data?model_type=all&epochs=50&batch_size=32"
```

## 🎯 Opción 2: Entrenar con Yahoo Finance

**Si Yahoo Finance está disponible** (puede tener rate limiting):

### **Ejemplos**:

#### **1. Entrenar Transformer con BTC-USD**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-transformer?symbol=BTC-USD&period=1y&interval=1d&epochs=50&batch_size=32&use_yahoo=true"
```

#### **2. Entrenar Ensemble con ETH-USD**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-ensemble?symbol=ETH-USD&period=1y&epochs=30&batch_size=32&use_yahoo=true"
```

#### **3. Entrenar con Forex (USD/COP)**:
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-transformer?symbol=USDCOP=X&period=1y&interval=1d&epochs=50&use_yahoo=true"
```

## 📊 Símbolos Disponibles (Yahoo Finance)

### **Criptomonedas**:
- `BTC-USD`: Bitcoin
- `ETH-USD`: Ethereum
- `BNB-USD`: Binance Coin
- `ADA-USD`: Cardano
- `SOL-USD`: Solana

### **Forex**:
- `USDCOP=X`: USD/COP
- `EURUSD=X`: EUR/USD
- `GBPUSD=X`: GBP/USD

### **Acciones**:
- `AAPL`: Apple
- `MSFT`: Microsoft
- `GOOGL`: Google

## 💡 Recomendaciones

### **Para Empezar Rápido**:
1. **Usa datos de BD**: Más rápido y confiable
2. **Modelo**: Transformer (balance entre velocidad y precisión)
3. **Épocas**: 50 (suficiente para empezar)
4. **Batch size**: 32 (buen balance)

### **Para Máxima Precisión**:
1. **Modelo**: Ensemble (combina múltiples modelos)
2. **Épocas**: 100-200 (mejor precisión)
3. **Datos**: Mínimo 200 registros (mejor: 500+)

### **Para Máximo Profit**:
1. **Modelo**: Profit-Aware (optimizado para profit)
2. **Datos**: Máximo histórico disponible
3. **Épocas**: 100+

## 🚀 Pasos Recomendados

### **1. Verificar Datos en BD**:
```bash
# Ver cuántos registros tienes
curl "http://localhost:8000/api/v1/analytics/dl/advanced/profit-metrics?days=365"
```

### **2. Entrenar Transformer** (Recomendado para empezar):
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-db-data?model_type=transformer&epochs=50&batch_size=32"
```

### **3. Evaluar Resultados**:
- Revisar métricas de profit
- Hacer backtest
- Ajustar hiperparámetros

### **4. Entrenar Ensemble** (Si Transformer funciona bien):
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-with-db-data?model_type=ensemble&epochs=30&batch_size=32"
```

## ⚠️ Notas Importantes

1. **Yahoo Finance**: Puede tener rate limiting (429 errors). Usa datos de BD si tienes problemas.

2. **Tiempo de Entrenamiento**:
   - Transformer: ~5-10 minutos (50 épocas)
   - Ensemble: ~15-30 minutos (30 épocas)
   - Profit-Aware: ~5-10 minutos (50 épocas)

3. **Datos Mínimos**:
   - Mínimo: 100 registros
   - Recomendado: 200+ registros
   - Óptimo: 500+ registros

4. **Modelos Guardados**:
   - Ubicación: `ml_models/dl_advanced/`
   - Formato: `.pth` (PyTorch)
   - Scalers: `.pkl` (joblib)

## ✅ Estado

**¡Todo listo para entrenar!** 🚀

- ✅ Endpoints funcionando
- ✅ Servicio de Yahoo Finance integrado
- ✅ Fallback a datos de BD
- ✅ Manejo de errores mejorado
- ✅ Retry automático para Yahoo Finance

## 🎉 Próximos Pasos

1. **Entrenar modelos** con datos de BD
2. **Evaluar resultados** con métricas
3. **Backtest** estrategias
4. **Optimizar** hiperparámetros
5. **Implementar** en producción

