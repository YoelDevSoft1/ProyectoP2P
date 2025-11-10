# 🚀 Script para Entrenar Modelos con Yahoo Finance

## ⚠️ Nota Importante

Yahoo Finance puede tener rate limiting (429 Too Many Requests). Se ha agregado:
- ✅ Retry automático con delays
- ✅ Manejo de errores mejorado
- ✅ Fallback a datos de BD si Yahoo Finance falla

## 🎯 Opción 1: Usar Datos de la Base de Datos

Si Yahoo Finance tiene problemas, puedes entrenar con datos de tu BD:

```bash
# Entrenar Transformer con datos de BD
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-transformer?use_yahoo=false&epochs=50&batch_size=32"

# Entrenar Ensemble con datos de BD
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-ensemble?use_yahoo=false&epochs=30&batch_size=32"
```

## 🎯 Opción 2: Esperar y Usar Yahoo Finance

Si quieres usar Yahoo Finance, espera unos minutos entre requests:

```bash
# 1. Entrenar Transformer (esperar 1-2 minutos después)
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-transformer?symbol=BTC-USD&period=6mo&interval=1d&epochs=50&batch_size=32"

# 2. Esperar 2-3 minutos

# 3. Entrenar Ensemble
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-ensemble?symbol=BTC-USD&period=6mo&epochs=30&batch_size=32"
```

## 🎯 Opción 3: Usar Períodos Más Cortos

Períodos más cortos = menos datos = menos rate limiting:

```bash
# Usar 3 meses en lugar de 1 año
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-transformer?symbol=BTC-USD&period=3mo&interval=1d&epochs=50&batch_size=32"
```

## ✅ Recomendación

**Para empezar rápido, usa datos de BD**:

```bash
# Entrenar con datos de BD (más rápido y confiable)
curl -X POST "http://localhost:8000/api/v1/analytics/dl/advanced/train-transformer?use_yahoo=false&epochs=50&batch_size=32&learning_rate=0.0001"
```

Luego, una vez que tengas datos históricos en tu BD, puedes entrenar con más datos.

## 🚀 Próximos Pasos

1. **Entrenar con datos de BD** (recomendado para empezar)
2. **Evaluar resultados** con métricas de profit
3. **Backtest** estrategias
4. **Optimizar** hiperparámetros
5. **Implementar** en producción

