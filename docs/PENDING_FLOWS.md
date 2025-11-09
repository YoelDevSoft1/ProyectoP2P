# Flujos pendientes de implementación

Este documento resume los flujos que aún no consumen datos reales o que deben crearse en el frontend a partir de los endpoints ya disponibles en el backend FastAPI.

## Resumen ejecutivo

- Los componentes marcados como ⚠️ en `docs/ROADMAP_INTEGRACION_API.md` y `docs/FRONTEND_IMPROVEMENTS.md` dependen de endpoints ya operativos: el bloqueo actual es exclusivamente de integración/frontend.
- Existen dos grupos de trabajo: **(1) componentes existentes que siguen usando datos mock** y **(2) módulos nuevos de control/operaciones avanzadas**.
- El diagrama incluido muestra cómo cada flujo conecta con los servicios del backend para facilitar priorización y pruebas end-to-end.

## 1. Componentes existentes por terminar (Fase 2)

| Flujo | Objetivo | Endpoints clave | Acción pendiente |
| --- | --- | --- | --- |
| Inventario spot y reservas (`InventoryManager`) | Mostrar balances reales, reservado y disponible | `/api/v1/spot/balances`<br>`/api/v1/trades/`<br>`/api/v1/trades/stats/summary` | Reemplazar datos mock, calcular inventario reservado desde trades `PENDING` y refrescar con React Query. |
| Control de trading (`TradingControl`) | Reflejar estado real del bot y market making | `/api/v1/market-making/status`<br>`/api/v1/market-making/all`<br>`POST /api/v1/market-making/update` | Consumir estado real, permitir start/stop y persistir configuraciones por API. |
| Operaciones recientes (`RecentTrades`) | Feed en vivo de trades | `/api/v1/trades/`<br>`/api/v1/trades/{trade_id}` | Eliminar datos estáticos, agregar paginación/búsqueda y estados vacíos. |
| Alertas operativas (`AlertsList`) | Listado y lectura de alertas del backend | `/api/v1/analytics/alerts`<br>`POST /api/v1/analytics/alerts/{id}/read` | Renderizar alertas reales, permitir marcar como leídas y mostrar timestamps reales. |
| Profundidad de mercado (`OrderbookDepth`) | Visualizar market depth por par | `/api/v1/analytics/liquidity/market-depth`<br>`/api/v1/analytics/liquidity/detect-market-makers` | Consumir datos reales, mostrar niveles bid/ask y detectar market makers. |
| Métricas de riesgo (`RiskMetricsDashboard`) | Mostrar VaR, Sharpe, Drawdown, Kelly | `POST /api/v1/analytics/risk/calculate-var`<br>`/.../calculate-sharpe`<br>`/.../trading-metrics` | Ejecutar cálculos contra el backend, manejar tiempos de respuesta y mostrar históricos. |
| Triángulos y arbitraje (`TriangleArbitrageOpportunities`) | Detectar rutas y mejores estrategias | `/api/v1/analytics/triangle-arbitrage/*`<br>`/api/v1/advanced-arbitrage/triangle/*` | Integrar tablas/gráficos a partir de la respuesta real y permitir selección de rutas. |
| Pricing competitivo (`CompetitivePricingDashboard`) | Comparar tarifas internas vs mercado | `/api/v1/analytics/pricing/*`<br>`/api/v1/dynamic-pricing/*`<br>`/api/v1/prices/trm` | Usar precios reales, generar comparativas y mostrar márgenes sugeridos. |

## 2. Nuevos paneles a crear (Fase 3)

| Flujo | Objetivo | Endpoints/backend | Nota |
| --- | --- | --- | --- |
| Monitoreo de salud (`HealthMonitoring`) | Estado de cada servicio | `/api/v1/health/*`<br>`/api/v1/metrics` | Mostrar semáforos e historial de fallos. |
| Panel spot (`SpotTradingPanel`) | Consultar balances, crear/cancelar órdenes spot | `/api/v1/spot/balance(s)`<br>`/api/v1/spot/order/*`<br>`/api/v1/spot/ticker` | Requiere formularios seguros y confirmaciones antes de enviar órdenes. |
| Panel de arbitraje avanzado (`AdvancedArbitragePanel`) | Portafolio y comparación de estrategias | `/api/v1/advanced-arbitrage/*` | Permitir filtros por tipo (funding, delta-neutral, estadístico, triangulación). |
| Control de market making (`MarketMakingControl`) | Gestionar procesos de market making | `POST /api/v1/market-making/start|update|stop`<br>`GET /api/v1/market-making/status|all` | Complementa a `TradingControl` con formularios y logs de ejecución. |
| Ejecución algorítmica (`OrderExecutionPanel`) | TWAP/VWAP/Iceberg/Smart Routing | `/api/v1/order-execution/twap|vwap|iceberg|smart-routing` | Formularios multi-paso con validación de parámetros. |
| Análisis de liquidez (`LiquidityAnalysis`) | Market depth, slippage, market makers | `/api/v1/analytics/liquidity/*` | Visualizaciones comparativas y alertas de liquidez baja. |
| Predicciones ML (`MLPredictions`) | Predicción de spread y timing óptimo | `/api/v1/analytics/ml/*` | Gráficos con confianza del modelo y razones de la predicción. |
| Riesgo integral (`RiskAnalysis`) | Evaluación completa del portafolio | `/api/v1/analytics/risk/*` | Combina métricas cuantitativas con recomendaciones basadas en reglas. |

## 3. Diagrama de flujo general

```mermaid
flowchart LR
  subgraph Data Layer
    DB[(PostgreSQL + Timescale)]
    Redis[(Redis Cache)]
    Rabbit[(RabbitMQ)]
    Binance[(Binance P2P)]
  end

  subgraph Backend FastAPI
    API[/FastAPI API Layer/]
    Celery[(Celery Workers)]
  end

  Binance --> API
  DB --> API
  Redis --> API
  Rabbit --> Celery --> API

  API -->|/spot/balances + /trades| INV[InventoryManager\n(sync pendiente)]
  API -->|/market-making/*| TC[TradingControl\n+ MarketMakingControl]
  API -->|/trades/*| RT[RecentTrades]
  API -->|/analytics/alerts| AL[AlertsList]
  API -->|/analytics/liquidity/*| LQ[LiquidityAnalysis\n+ OrderbookDepth]
  API -->|/analytics/risk/*| RK[RiskMetrics/RiskAnalysis]
  API -->|/analytics/ml/*| ML[MLPredictions]
  API -->|/analytics/pricing/*\n/dynamic-pricing/*| PR[CompetitivePricing]
  API -->|/advanced-arbitrage/*\n/analytics/triangle-arbitrage/*| ARB[AdvancedArbitragePanel]
  API -->|/spot/*| SP[SpotTradingPanel]
  API -->|/order-execution/*| OE[OrderExecutionPanel]
  API -->|/health/* + /metrics| HL[HealthMonitoring]

  classDef pending fill:#fde68a,stroke:#ea580c,color:#0f172a,font-weight:bold;
  class INV,TC,RT,AL,LQ,RK,ML,PR,ARB,SP,OE,HL pending;
```

## 4. Próximos pasos recomendados

1. **Completar Flujos Fase 2**: eliminar datos mock siguiendo el orden inventario → trading control → pricing, validando cada componente con los endpoints indicados.
2. **Instrumentar cliente API**: asegurar que `frontend/src/lib/api.ts` expone todos los endpoints mencionados (health, spot, arbitrage, risk, etc.) con tipados y manejo de errores.
3. **Diseñar UI/UX de nuevos paneles**: basarse en `docs/FRONTEND_IMPROVEMENTS.md` para definir layouts, inputs y estados de carga antes de implementar lógica.
4. **Configurar pruebas end-to-end**: una vez que cada flujo consuma datos reales, crear escenarios de prueba (manuales o automáticos) que recorran el diagrama de arriba hacia abajo.
