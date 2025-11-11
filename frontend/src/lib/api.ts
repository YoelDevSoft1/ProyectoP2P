/**
 * Cliente de API para comunicación con el backend.
 * Usa el nuevo api-client con retry logic, circuit breaker y caché local.
 */
import { axiosInstance, requestWithRetry, requestWithCache } from './api-client'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_V1 = `${API_URL}/api/v1`

const api = {
  // Health Check
  healthCheck: async () => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.get('/health')
      )
      return data
    } catch (error: any) {
      console.error('Error fetching health:', error)
      return { status: 'error', error: error.message }
    }
  },

  // Health Checks Individuales
  getDatabaseHealth: async () => {
    try {
      const { data } = await axiosInstance.get('/health/db')
      return data
    } catch (error: any) {
      console.error('Error fetching database health:', error)
      return { status: 'error', error: error.message }
    }
  },

  getRedisHealth: async () => {
    try {
      const { data } = await axiosInstance.get('/health/redis')
      return data
    } catch (error: any) {
      console.error('Error fetching Redis health:', error)
      return { status: 'error', error: error.message }
    }
  },

  getRabbitMQHealth: async () => {
    try {
      const { data } = await axiosInstance.get('/health/rabbitmq')
      return data
    } catch (error: any) {
      console.error('Error fetching RabbitMQ health:', error)
      return { status: 'error', error: error.message }
    }
  },

  getCeleryHealth: async () => {
    try {
      const { data } = await axiosInstance.get('/health/celery')
      return data
    } catch (error: any) {
      console.error('Error fetching Celery health:', error)
      return { status: 'error', error: error.message }
    }
  },

  // Métricas Prometheus (texto plano)
  getPrometheusMetrics: async () => {
    try {
      const { data } = await axiosInstance.get('/metrics', {
        responseType: 'text',
        headers: {
          'Accept': 'text/plain',
        },
      })
      return data
    } catch (error: any) {
      console.error('Error fetching Prometheus metrics:', error)
      return null
    }
  },

  // Prices
  getCurrentPrices: async (asset = 'USDT', fiat?: string) => {
    try {
      const params = new URLSearchParams({ asset })
      if (fiat) params.append('fiat', fiat)

      return await requestWithCache(
        `prices_current_${asset}_${fiat || 'all'}`,
        async () => {
          const { data } = await requestWithRetry(() =>
            axiosInstance.get(`/prices/current?${params}`)
          )
          return data
        },
        {
          cacheTTL: 10 * 1000, // 10 segundos de caché
          useCache: true,
          fallbackToCache: true, // Usar caché si la API falla
        }
      )
    } catch (error: any) {
      console.error('Error fetching current prices:', error)
      // Retornar objeto vacío en lugar de lanzar error
      return {}
    }
  },

  getPriceHistory: async (asset = 'USDT', fiat = 'COP', hours = 24) => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.get('/prices/history', {
          params: { asset, fiat, hours },
        })
      )
      return data
    } catch (error: any) {
      console.error('Error fetching price history:', error)
      return []
    }
  },

  getTRM: async () => {
    try {
      return await requestWithCache(
        'trm_data',
        async () => {
          const { data } = await requestWithRetry(() =>
            axiosInstance.get('/prices/trm')
          )
          return data
        },
        {
          cacheTTL: 5 * 60 * 1000, // 5 minutos de caché (TRM cambia lentamente)
          useCache: true,
          fallbackToCache: true,
        }
      )
    } catch (error: any) {
      console.error('Error fetching TRM:', error)
      // Retornar null en lugar de lanzar error
      return null
    }
  },

  getSpreadAnalysis: async (asset = 'USDT') => {
    const { data } = await axiosInstance.get('/prices/spread-analysis', {
      params: { asset },
    })
    return data
  },

  // Trades
  getTrades: async (skip = 0, limit = 50, status?: string, fiat?: string) => {
    const params: any = { skip, limit }
    if (status) params.status = status
    if (fiat) params.fiat = fiat

    const { data } = await axiosInstance.get('/trades/', { params })
    return data
  },

  getTrade: async (tradeId: number) => {
    const { data } = await axiosInstance.get(`/trades/${tradeId}`)
    return data
  },

  getTradeStats: async (days = 7) => {
    try {
      return await requestWithCache(
        `trade_stats_${days}`,
        async () => {
          const { data } = await requestWithRetry(() =>
            axiosInstance.get('/trades/stats/summary', {
              params: { days },
            })
          )
          return data
        },
        {
          cacheTTL: 60 * 1000, // 1 minuto de caché
          useCache: true,
          fallbackToCache: true,
        }
      )
    } catch (error: any) {
      console.error('Error fetching trade stats:', error)
      // Retornar null en lugar de lanzar error
      return null
    }
  },

  // Analytics
  getDashboardData: async () => {
    const { data } = await axiosInstance.get('/analytics/dashboard')
    return data
  },

  getPerformanceMetrics: async (days = 30) => {
    const { data } = await axiosInstance.get('/analytics/performance', {
      params: { days },
    })
    return data
  },

  getAlerts: async (skip = 0, limit = 20, alertType?: string, isRead?: boolean) => {
    const params: any = { skip, limit }
    if (alertType) params.alert_type = alertType
    if (isRead !== undefined) params.is_read = isRead

    const { data } = await axiosInstance.get('/analytics/alerts', { params })
    return data
  },

  markAlertAsRead: async (alertId: number) => {
    const { data } = await axiosInstance.post(`/analytics/alerts/${alertId}/read`)
    return data
  },

  // Analytics - Triangle Arbitrage
  analyzeTriangleArbitrage: async (initialAmount = 200000) => {
    const { data } = await axiosInstance.get('/analytics/triangle-arbitrage/analyze', {
      params: { initial_amount: initialAmount },
    })
    return data
  },

  findTriangleRoutes: async (assets = ['USDT', 'BTC'], fiats = ['COP', 'VES']) => {
    const { data } = await axiosInstance.get('/analytics/triangle-arbitrage/find-all-routes', {
      params: { assets, fiats },
    })
    return data
  },

  getOptimalTriangleStrategy: async () => {
    const { data } = await axiosInstance.get('/analytics/triangle-arbitrage/optimal-strategy')
    return data
  },

  // Analytics - Liquidity
  analyzeMarketDepth: async (asset = 'USDT', fiat = 'COP', depthLevels = 20) => {
    const { data } = await axiosInstance.get('/analytics/liquidity/market-depth', {
      params: { asset, fiat, depth_levels: depthLevels },
    })
    return data
  },

  detectMarketMakers: async (asset = 'USDT', fiat = 'COP') => {
    const { data } = await axiosInstance.get('/analytics/liquidity/detect-market-makers', {
      params: { asset, fiat },
    })
    return data
  },

  estimateSlippage: async (asset = 'USDT', fiat = 'COP', tradeType = 'BUY', targetAmountUsd = 1000) => {
    const { data } = await axiosInstance.get('/analytics/liquidity/slippage-estimate', {
      params: { asset, fiat, trade_type: tradeType, target_amount_usd: targetAmountUsd },
    })
    return data
  },

  // Analytics - ML
  predictSpread: async (asset = 'USDT', fiat = 'COP', horizonMinutes = 10) => {
    const { data } = await axiosInstance.get('/analytics/ml/predict-spread', {
      params: { asset, fiat, horizon_minutes: horizonMinutes },
    })
    return data
  },

  classifyOpportunity: async (opportunityData: any) => {
    const { data } = await axiosInstance.post('/analytics/ml/classify-opportunity', opportunityData)
    return data
  },

  predictOptimalTiming: async (asset = 'USDT', fiat = 'COP') => {
    const { data } = await axiosInstance.get('/analytics/ml/optimal-timing', {
      params: { asset, fiat },
    })
    return data
  },

  // Machine Learning - Training (Gradient Boosting)
  trainMLSpreadPredictor: async () => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.post('/analytics/ml/train-spread-predictor')
      )
      return data
    } catch (error: any) {
      console.error('Error training ML spread predictor:', error)
      throw error
    }
  },

  // Deep Learning - Training (GRU)
  trainSpreadPredictor: async (epochs: number = 50, batchSize: number = 32, learningRate: number = 0.001) => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.post('/analytics/dl/train-spread-predictor', null, {
          params: {
            epochs,
            batch_size: batchSize,
            learning_rate: learningRate,
          },
        })
      )
      return data
    } catch (error: any) {
      console.error('Error training DL spread predictor:', error)
      throw error
    }
  },

  trainPricePredictor: async (epochs: number = 50, batchSize: number = 32, learningRate: number = 0.001) => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.post('/analytics/dl/train-price-predictor', null, {
          params: {
            epochs,
            batch_size: batchSize,
            learning_rate: learningRate,
          },
        })
      )
      return data
    } catch (error: any) {
      console.error('Error training price predictor:', error)
      throw error
    }
  },

  trainAnomalyDetector: async (epochs: number = 50, batchSize: number = 32, learningRate: number = 0.001) => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.post('/analytics/dl/train-anomaly-detector', null, {
          params: {
            epochs,
            batch_size: batchSize,
            learning_rate: learningRate,
          },
        })
      )
      return data
    } catch (error: any) {
      console.error('Error training anomaly detector:', error)
      throw error
    }
  },

  // Analytics - Risk
  calculateVaR: async (returns: number[], confidenceLevel = 0.95, timeHorizonDays = 1) => {
    const { data } = await axiosInstance.post('/analytics/risk/calculate-var', {
      returns,
      confidence_level: confidenceLevel,
      time_horizon_days: timeHorizonDays,
    })
    return data
  },

  calculateSharpe: async (returns: number[], riskFreeRate?: number) => {
    const { data } = await axiosInstance.post('/analytics/risk/calculate-sharpe', {
      returns,
      risk_free_rate: riskFreeRate,
    })
    return data
  },

  calculateSortino: async (returns: number[], targetReturn = 0.0) => {
    const { data } = await axiosInstance.post('/analytics/risk/calculate-sortino', {
      returns,
      target_return: targetReturn,
    })
    return data
  },

  calculateDrawdown: async (equityCurve: number[]) => {
    const { data } = await axiosInstance.post('/analytics/risk/calculate-drawdown', {
      equity_curve: equityCurve,
    })
    return data
  },

  calculateTradingMetrics: async (trades: any[]) => {
    const { data } = await axiosInstance.post('/analytics/risk/trading-metrics', { trades })
    return data
  },

  calculateKellyCriterion: async (winRate: number, avgWin: number, avgLoss: number) => {
    const { data } = await axiosInstance.get('/analytics/risk/kelly-criterion', {
      params: { win_rate: winRate, avg_win: avgWin, avg_loss: avgLoss },
    })
    return data
  },

  comprehensiveRiskAssessment: async (
    returns: number[],
    equityCurve: number[],
    trades: any[],
    currentPositionSize: number,
    totalCapital: number
  ) => {
    const { data } = await axiosInstance.post('/analytics/risk/comprehensive-assessment', {
      returns,
      equity_curve: equityCurve,
      trades,
      current_position_size: currentPositionSize,
      total_capital: totalCapital,
    })
    return data
  },

  // Analytics - Advanced Summary
  getAdvancedSummary: async () => {
    const { data } = await axiosInstance.get('/analytics/advanced-summary')
    return data
  },

  getTopOpportunities: async (limit = 10) => {
    const { data } = await axiosInstance.get('/analytics/top-opportunities', {
      params: { limit },
    })
    return data
  },

  // Analytics - Pricing
  getMarketTRM: async (asset = 'USDT', fiat = 'COP', sampleSize = 20) => {
    const { data } = await axiosInstance.get('/analytics/pricing/market-trm', {
      params: { asset, fiat, sample_size: sampleSize },
    })
    return data
  },

  getCompetitivePrices: async (asset = 'USDT', fiat = 'COP', ourMarginPct?: number) => {
    const params: any = { asset, fiat }
    if (ourMarginPct !== undefined) params.our_margin_pct = ourMarginPct
    const { data } = await axiosInstance.get('/analytics/pricing/competitive-prices', { params })
    return data
  },

  getPricingStrategySummary: async (asset = 'USDT', fiat = 'COP') => {
    const { data } = await axiosInstance.get('/analytics/pricing/strategy-summary', {
      params: { asset, fiat },
    })
    return data
  },

  // P2P Trading
  executeP2PTrade: async (request: {
    asset: string
    fiat: string
    trade_type: string
    amount: number
    price: number
    payment_methods: string[]
    min_amount?: number
    max_amount?: number
  }) => {
    const { data } = await axiosInstance.post('/p2p-trading/execute', request)
    return data
  },

  cancelP2PTrade: async (tradeId: number) => {
    const { data } = await axiosInstance.post('/p2p-trading/cancel', { trade_id: tradeId })
    return data
  },

  getP2POrders: async () => {
    const { data } = await axiosInstance.get('/p2p-trading/orders')
    return data
  },

  // Spot Trading
  getSpotBalance: async (asset = 'USDT') => {
    const { data } = await axiosInstance.get('/spot/balance', {
      params: { asset },
    })
    return data
  },

  getSpotBalances: async () => {
    const { data } = await axiosInstance.get('/spot/balances')
    return data
  },

  getSpotPrice: async (symbol: string) => {
    const { data } = await axiosInstance.get(`/spot/price/${symbol}`)
    return data
  },

  getSpotTicker: async (symbol: string) => {
    const { data } = await axiosInstance.get(`/spot/ticker/${symbol}`)
    return data
  },

  createMarketOrder: async (symbol: string, side: string, quantity: number) => {
    const { data } = await axiosInstance.post('/spot/order/market', {
      symbol,
      side,
      quantity,
    })
    return data
  },

  createLimitOrder: async (symbol: string, side: string, quantity: number, price: number) => {
    const { data } = await axiosInstance.post('/spot/order/limit', {
      symbol,
      side,
      quantity,
      price,
    })
    return data
  },

  getOpenOrders: async (symbol?: string) => {
    const params: any = {}
    if (symbol) params.symbol = symbol
    const { data } = await axiosInstance.get('/spot/orders/open', { params })
    return data
  },

  cancelOrder: async (symbol: string, orderId: string) => {
    const { data } = await axiosInstance.delete(`/spot/order/${symbol}/${orderId}`)
    return data
  },

  getOrder: async (symbol: string, orderId: string) => {
    const { data } = await axiosInstance.get(`/spot/order/${symbol}/${orderId}`)
    return data
  },

  getSymbolInfo: async (symbol: string) => {
    const { data } = await axiosInstance.get(`/spot/symbol/${symbol}`)
    return data
  },

  // Advanced Arbitrage
  scanOpportunities: async (minReturn = 1.0, maxRisk = 70.0, capital = 10000.0) => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/scan', {
      params: { min_return: minReturn, max_risk: maxRisk, capital },
    })
    return data
  },

  getBestOpportunity: async (rankingMethod = 'risk_adjusted') => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/best', {
      params: { ranking_method: rankingMethod },
    })
    return data
  },

  getArbitragePortfolio: async () => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/portfolio')
    return data
  },

  compareStrategies: async () => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/compare-strategies')
    return data
  },

  // Funding Rate
  getFundingRateOpportunities: async () => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/funding-rate/opportunities')
    return data
  },

  getBestFundingRate: async () => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/funding-rate/best')
    return data
  },

  getFundingRateHistory: async (symbol: string) => {
    const { data } = await axiosInstance.get(`/advanced-arbitrage/funding-rate/historical/${symbol}`)
    return data
  },

  // Statistical
  getStatisticalSignals: async () => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/statistical/signals')
    return data
  },

  getStatisticalPair: async (symbol1: string, symbol2: string) => {
    const { data } = await axiosInstance.get(`/advanced-arbitrage/statistical/pair/${symbol1}/${symbol2}`)
    return data
  },

  // Delta Neutral
  getDeltaNeutralOpportunities: async () => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/delta-neutral/opportunities')
    return data
  },

  getOptimalHolding: async (symbol: string) => {
    const { data } = await axiosInstance.get(`/advanced-arbitrage/delta-neutral/optimal-holding/${symbol}`)
    return data
  },

  // Triangle
  getTrianglePaths: async () => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/triangle/paths')
    return data
  },

  getOptimalTriangle: async () => {
    const { data } = await axiosInstance.get('/advanced-arbitrage/triangle/optimal')
    return data
  },

  compareTriangles: async (triangleData: any) => {
    const { data } = await axiosInstance.post('/advanced-arbitrage/triangle/compare', triangleData)
    return data
  },

  // Dynamic Pricing
  calculateDynamicPrice: async (
    asset = 'USDT',
    fiat = 'COP',
    tradeType = 'SELL',
    amountUsd = 1000.0,
    baseMargin?: number
  ) => {
    const params: any = { asset, fiat, trade_type: tradeType, amount_usd: amountUsd }
    if (baseMargin !== undefined) params.base_margin = baseMargin
    const { data } = await axiosInstance.get('/dynamic-pricing/calculate', { params })
    return data
  },

  getPricingSummary: async (asset = 'USDT', fiat = 'COP') => {
    const { data } = await axiosInstance.get('/dynamic-pricing/summary', {
      params: { asset, fiat },
    })
    return data
  },

  // Market Making
  startMarketMaking: async (asset = 'USDT', fiat = 'COP', updateIntervalSeconds = 30) => {
    const { data } = await axiosInstance.post('/market-making/start', null, {
      params: { asset, fiat, update_interval_seconds: updateIntervalSeconds },
    })
    return data
  },

  updateMarketMaking: async (asset = 'USDT', fiat = 'COP') => {
    const { data } = await axiosInstance.post('/market-making/update', null, {
      params: { asset, fiat },
    })
    return data
  },

  stopMarketMaking: async (asset = 'USDT', fiat = 'COP') => {
    const { data } = await axiosInstance.post('/market-making/stop', null, {
      params: { asset, fiat },
    })
    return data
  },

  getMarketMakingStatus: async (asset = 'USDT', fiat = 'COP') => {
    const { data } = await axiosInstance.get('/market-making/status', {
      params: { asset, fiat },
    })
    return data
  },

  getAllMarketMaking: async () => {
    const { data } = await axiosInstance.get('/market-making/all')
    return data
  },

  // Order Execution
  executeTWAP: async (
    asset = 'USDT',
    fiat = 'COP',
    tradeType = 'SELL',
    totalAmountUsd: number,
    durationMinutes = 30,
    chunks = 10
  ) => {
    const { data } = await axiosInstance.post('/order-execution/twap', null, {
      params: {
        asset,
        fiat,
        trade_type: tradeType,
        total_amount_usd: totalAmountUsd,
        duration_minutes: durationMinutes,
        chunks,
      },
    })
    return data
  },

  executeVWAP: async (
    asset = 'USDT',
    fiat = 'COP',
    tradeType = 'SELL',
    totalAmountUsd: number,
    durationMinutes = 30
  ) => {
    const { data } = await axiosInstance.post('/order-execution/vwap', null, {
      params: {
        asset,
        fiat,
        trade_type: tradeType,
        total_amount_usd: totalAmountUsd,
        duration_minutes: durationMinutes,
      },
    })
    return data
  },

  executeIceberg: async (
    asset = 'USDT',
    fiat = 'COP',
    tradeType = 'SELL',
    totalAmountUsd: number,
    visibleSizeUsd = 1000.0,
    refreshIntervalSeconds = 60
  ) => {
    const { data } = await axiosInstance.post('/order-execution/iceberg', null, {
      params: {
        asset,
        fiat,
        trade_type: tradeType,
        total_amount_usd: totalAmountUsd,
        visible_size_usd: visibleSizeUsd,
        refresh_interval_seconds: refreshIntervalSeconds,
      },
    })
    return data
  },

  smartOrderRouting: async (
    asset = 'USDT',
    fiat = 'COP',
    tradeType = 'SELL',
    amountUsd: number,
    exchanges = 'binance_p2p'
  ) => {
    const { data } = await axiosInstance.post('/order-execution/smart-routing', null, {
      params: {
        asset,
        fiat,
        trade_type: tradeType,
        amount_usd: amountUsd,
        exchanges,
      },
    })
    return data
  },

  // List Endpoints
  listEndpoints: async () => {
    const { data } = await axiosInstance.get('/health/endpoints')
    return data
  },

  // Forex Expert Trading System
  analyzeForexPair: async (pair: string, timeframe: string = 'daily') => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.get(`/forex/expert/analyze/${pair}`, {
          params: { timeframe },
        })
      )
      return data
    } catch (error: any) {
      console.error('Error analyzing forex pair:', error)
      return null
    }
  },

  getForexSignals: async (minConfidence: number = 70) => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.get('/forex/expert/signals', {
          params: { min_confidence: minConfidence },
        })
      )
      return data
    } catch (error: any) {
      console.error('Error fetching forex signals:', error)
      return { total_signals: 0, signals: [] }
    }
  },

  createVirtualOrder: async (orderData: {
    pair: string
    direction: string
    entry_price: number
    stop_loss: number
    take_profit: number
    lot_size: number
    risk_percent?: number
    signal_confidence?: number
  }) => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.post('/forex/expert/virtual-order', orderData)
      )
      return data
    } catch (error: any) {
      console.error('Error creating virtual order:', error)
      throw error
    }
  },

  getSessionStats: async () => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.get('/forex/expert/session-stats')
      )
      return data
    } catch (error: any) {
      console.error('Error fetching session stats:', error)
      return null
    }
  },

  // Configuration API
  getConfiguration: async () => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.get('/config')
      )
      return data
    } catch (error: any) {
      console.error('Error getting configuration:', error)
      throw error
    }
  },

  updateConfiguration: async (config: Partial<import('@/types/config').ConfigUpdateRequest>) => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.put('/config', config)
      )
      return data
    } catch (error: any) {
      console.error('Error updating configuration:', error)
      throw error
    }
  },

  getConfigSections: async () => {
    try {
      const { data } = await requestWithRetry(() =>
        axiosInstance.get('/config/sections')
      )
      return data
    } catch (error: any) {
      console.error('Error getting config sections:', error)
      throw error
    }
  },
}

export default api
