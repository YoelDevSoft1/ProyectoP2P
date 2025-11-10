'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  BarChart3,
  DollarSign,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Zap,
  AlertCircle,
  CheckCircle2,
  XCircle,
  LayoutGrid,
} from 'lucide-react'

import api from '@/lib/api'
import { ForexTradingChart } from './ForexTradingChart'
import { ForexPairsList } from './ForexPairsList'
import { ForexOrderBook } from './ForexOrderBook'

// Pares Forex principales
const FOREX_PAIRS = [
  { id: 'EUR/USD', name: 'EUR/USD', base: 'EUR', quote: 'USD' },
  { id: 'GBP/USD', name: 'GBP/USD', base: 'GBP', quote: 'USD' },
  { id: 'USD/JPY', name: 'USD/JPY', base: 'USD', quote: 'JPY' },
  { id: 'AUD/USD', name: 'AUD/USD', base: 'AUD', quote: 'USD' },
  { id: 'USD/CAD', name: 'USD/CAD', base: 'USD', quote: 'CAD' },
  { id: 'USD/CHF', name: 'USD/CHF', base: 'USD', quote: 'CHF' },
  { id: 'NZD/USD', name: 'NZD/USD', base: 'NZD', quote: 'USD' },
  { id: 'EUR/GBP', name: 'EUR/GBP', base: 'EUR', quote: 'GBP' },
]

interface ForexAnalysis {
  ANÁLISIS_FOREX: {
    DATETIME: string
    PAR_ACTUAL: string
    DATOS_ACTUALES: {
      'Precio Actual': number
      Bid: number
      Ask: number
      'Rango 24H': string
      'Volatilidad (ATR-20)': string
      'Tendencia 4H': string
      Volumen: string
    }
    ANÁLISIS_TÉCNICO: {
      'RSI(14)': string
      RSI_Interpretation: string
      MACD: {
        Línea: number
        Señal: number
        Histograma: number
        Interpretation: string
      }
      'Bandas Bollinger': {
        Superior: number
        Media: number
        Inferior: number
        'Precio Posición': string
      }
      Soportes: {
        'Soporte 1': number
        'Soporte 2': number
      }
      Resistencias: {
        'Resistencia 1': number
        'Resistencia 2': number
      }
      'Medias Móviles': {
        'SMA 50': number
        'SMA 200': number
        Tendencia: string
      }
    }
    SEÑAL_GENERADA: {
      TIPO: string
      CONFIANZA: string
      CONFLUENCIA: string[]
    }
    RECOMENDACIÓN_OPERACIÓN: {
      Entrada: number
      'Stop Loss': number
      'Take Profit': number
      'Relación R:R': string
      Riesgo: string
      'Tamaño de Lote': string
      'Duración Esperada': string
      'Probabilidad Éxito': string
    }
    CONDICIONES_DE_SALIDA: Record<string, any>
  }
}

interface VirtualOrder {
  order_id: number
  pair: string
  direction: string
  entry_price: number
  stop_loss: number
  take_profit: number
  lot_size: number
  risk_amount: number
  potential_profit: number
  risk_reward_ratio: number
  status: string
  opened_at: string
  exit_price?: number
  exit_at?: string
  pnl?: number
  pips?: number
}

interface SessionStats {
  session_stats: {
    fecha: string
    duracion_minutos: number
    operaciones_totales: number
    operaciones_ganadoras: number
    operaciones_perdedoras: number
    win_rate: number
    profit_factor: number
    pip_totales: number
    pips_promedio_por_trade: number
    mayor_ganancia: number
    mayor_pérdida: number
    sharpe_ratio: number
    drawdown_máximo: number
    capital_inicial: number
    capital_final: number
    rentabilidad_diaria: number
  }
}

const BASE_CAPITAL = 10000

export function ForexExpertTrading() {
  const [selectedPair, setSelectedPair] = useState<string>('EUR/USD')
  const [analysis, setAnalysis] = useState<ForexAnalysis | null>(null)
  const [virtualOrders, setVirtualOrders] = useState<VirtualOrder[]>([])
  const [closedOrders, setClosedOrders] = useState<VirtualOrder[]>([])
  const [capital, setCapital] = useState(BASE_CAPITAL)
  const [sessionStats, setSessionStats] = useState<SessionStats | null>(null)
  const [message, setMessage] = useState<{ type: 'info' | 'error' | 'success'; text: string } | null>(null)

  // Cargar análisis del par seleccionado
  const { data: analysisData, refetch: refetchAnalysis, isLoading: loadingAnalysis } = useQuery({
    queryKey: ['forex-analysis', selectedPair],
    queryFn: () => api.analyzeForexPair(selectedPair, 'daily'),
    enabled: !!selectedPair,
    refetchInterval: 60000, // Actualizar cada minuto
    retry: 2,
  })

  // Cargar estadísticas de sesión
  const { data: statsData } = useQuery({
    queryKey: ['forex-session-stats'],
    queryFn: () => api.getSessionStats(),
    refetchInterval: 30000,
  })

  useEffect(() => {
    if (analysisData) {
      setAnalysis(analysisData)
    }
  }, [analysisData])

  useEffect(() => {
    if (statsData) {
      setSessionStats(statsData)
      if (statsData.session_stats) {
        setCapital(statsData.session_stats.capital_final || BASE_CAPITAL)
      }
    }
  }, [statsData])

  useEffect(() => {
    if (message) {
      const timeout = setTimeout(() => setMessage(null), 5000)
      return () => clearTimeout(timeout)
    }
  }, [message])

  const handleExecuteOrder = useCallback(async () => {
    if (!analysis || !analysis.ANÁLISIS_FOREX) return

    const signal = analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA
    const recommendation = analysis.ANÁLISIS_FOREX.RECOMENDACIÓN_OPERACIÓN

    if (signal.TIPO === 'HOLD') {
      setMessage({ type: 'error', text: 'No hay señal de trading válida. Señal actual: HOLD' })
      return
    }

    try {
      const orderData = {
        pair: analysis.ANÁLISIS_FOREX.PAR_ACTUAL,
        direction: signal.TIPO,
        entry_price: recommendation.Entrada,
        stop_loss: recommendation['Stop Loss'],
        take_profit: recommendation['Take Profit'],
        lot_size: parseFloat(recommendation['Tamaño de Lote'].split(' ')[0]),
        risk_percent: 1.0,
        signal_confidence: parseInt(signal.CONFIANZA.split('/')[0]),
      }

      const order = await api.createVirtualOrder(orderData)
      setVirtualOrders((prev) => [order, ...prev])
      setMessage({
        type: 'success',
        text: `Orden virtual #${order.order_id} ejecutada (${order.direction} ${order.pair})`,
      })
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Error al ejecutar orden virtual',
      })
    }
  }, [analysis])

  const handleCloseOrder = useCallback((orderId: number) => {
    setVirtualOrders((prev) => {
      const order = prev.find((o) => o.order_id === orderId)
      if (!order) return prev

      // Simular cierre de orden
      const pipValue = order.pair.includes('JPY') ? 0.01 : 0.0001
      const currentPrice = analysis?.ANÁLISIS_FOREX?.DATOS_ACTUALES?.['Precio Actual'] || order.entry_price
      const priceDiff = order.direction === 'BUY' ? currentPrice - order.entry_price : order.entry_price - currentPrice
      const pips = priceDiff / pipValue
      const pnl = pips * 10 * order.lot_size

      const closedOrder: VirtualOrder = {
        ...order,
        status: 'CLOSED',
        exit_price: currentPrice,
        exit_at: new Date().toISOString(),
        pnl,
        pips,
      }

      setClosedOrders((prev) => [closedOrder, ...prev].slice(0, 20))
      setCapital((prev) => prev + pnl)

      return prev.filter((o) => o.order_id !== orderId)
    })
  }, [analysis])

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('es-CO', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  }

  const formatNumber = (value: number, decimals = 4) => {
    return value.toLocaleString('es-CO', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  const getSignalColor = (type: string) => {
    if (type === 'BUY') return 'text-green-400'
    if (type === 'SELL') return 'text-red-400'
    return 'text-gray-400'
  }

  const getSignalBg = (type: string) => {
    if (type === 'BUY') return 'bg-green-500/20 border-green-500'
    if (type === 'SELL') return 'bg-red-500/20 border-red-500'
    return 'bg-gray-500/20 border-gray-500'
  }

  const [viewMode, setViewMode] = useState<'expert' | 'trading'>('trading')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Sistema Experto de Trading Forex</h2>
          <p className="text-sm text-gray-400 mt-1">
            Análisis técnico avanzado con simulación en tiempo real
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('trading')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                viewMode === 'trading'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <LayoutGrid className="h-4 w-4 inline mr-2" />
              Trading
            </button>
            <button
              onClick={() => setViewMode('expert')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                viewMode === 'expert'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <BarChart3 className="h-4 w-4 inline mr-2" />
              Análisis Experto
            </button>
          </div>
          <button
            onClick={() => refetchAnalysis()}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition"
          >
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </button>
        </div>
      </div>

      {viewMode === 'trading' ? (
        <TradingViewLayout selectedPair={selectedPair} onPairSelect={setSelectedPair} />
      ) : (
        <ExpertAnalysisView selectedPair={selectedPair} onPairSelect={setSelectedPair} />
      )}
    </div>
  )
}

function TradingViewLayout({
  selectedPair,
  onPairSelect,
}: {
  selectedPair: string
  onPairSelect: (pair: string) => void
}) {
  const [currentPrice, setCurrentPrice] = useState<number>(1.0850)

  // Obtener precio actual del par
  useEffect(() => {
    const basePrices: Record<string, number> = {
      'EUR/USD': 1.0850,
      'GBP/USD': 1.2750,
      'USD/JPY': 145.50,
      'AUD/USD': 0.6550,
      'USD/CAD': 1.3550,
      'USD/CHF': 0.8850,
      'NZD/USD': 0.6050,
      'EUR/GBP': 0.8510,
    }
    setCurrentPrice(basePrices[selectedPair] || 1.0850)
  }, [selectedPair])

  return (
    <div className="grid grid-cols-12 gap-4">
      {/* Lista de pares - Columna izquierda */}
      <div className="col-span-12 lg:col-span-3">
        <ForexPairsList onPairSelect={onPairSelect} selectedPair={selectedPair} />
      </div>

      {/* Gráfico principal - Columna central */}
      <div className="col-span-12 lg:col-span-6">
        <ForexTradingChart pair={selectedPair} height={600} />
      </div>

      {/* Order Book - Columna derecha */}
      <div className="col-span-12 lg:col-span-3">
        <ForexOrderBook pair={selectedPair} currentPrice={currentPrice} />
      </div>
    </div>
  )
}

function ExpertAnalysisView({
  selectedPair,
  onPairSelect,
}: {
  selectedPair: string
  onPairSelect: (pair: string) => void
}) {
  const [analysis, setAnalysis] = useState<ForexAnalysis | null>(null)
  const [virtualOrders, setVirtualOrders] = useState<VirtualOrder[]>([])
  const [closedOrders, setClosedOrders] = useState<VirtualOrder[]>([])
  const [capital, setCapital] = useState(BASE_CAPITAL)
  const [sessionStats, setSessionStats] = useState<SessionStats | null>(null)
  const [message, setMessage] = useState<{ type: 'info' | 'error' | 'success'; text: string } | null>(null)

  // Cargar análisis del par seleccionado
  const { data: analysisData, refetch: refetchAnalysis, isLoading: loadingAnalysis } = useQuery({
    queryKey: ['forex-analysis', selectedPair],
    queryFn: () => api.analyzeForexPair(selectedPair, 'daily'),
    enabled: !!selectedPair,
    refetchInterval: 60000,
    retry: 2,
  })

  // Cargar estadísticas de sesión
  const { data: statsData } = useQuery({
    queryKey: ['forex-session-stats'],
    queryFn: () => api.getSessionStats(),
    refetchInterval: 30000,
  })

  useEffect(() => {
    if (analysisData) {
      setAnalysis(analysisData)
    }
  }, [analysisData])

  useEffect(() => {
    if (statsData) {
      setSessionStats(statsData)
      if (statsData.session_stats) {
        setCapital(statsData.session_stats.capital_final || BASE_CAPITAL)
      }
    }
  }, [statsData])

  useEffect(() => {
    if (message) {
      const timeout = setTimeout(() => setMessage(null), 5000)
      return () => clearTimeout(timeout)
    }
  }, [message])

  const handleExecuteOrder = useCallback(async () => {
    if (!analysis || !analysis.ANÁLISIS_FOREX) return

    const signal = analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA
    const recommendation = analysis.ANÁLISIS_FOREX.RECOMENDACIÓN_OPERACIÓN

    if (signal.TIPO === 'HOLD') {
      setMessage({ type: 'error', text: 'No hay señal de trading válida. Señal actual: HOLD' })
      return
    }

    try {
      const orderData = {
        pair: analysis.ANÁLISIS_FOREX.PAR_ACTUAL,
        direction: signal.TIPO,
        entry_price: recommendation.Entrada,
        stop_loss: recommendation['Stop Loss'],
        take_profit: recommendation['Take Profit'],
        lot_size: parseFloat(recommendation['Tamaño de Lote'].split(' ')[0]),
        risk_percent: 1.0,
        signal_confidence: parseInt(signal.CONFIANZA.split('/')[0]),
      }

      const order = await api.createVirtualOrder(orderData)
      setVirtualOrders((prev) => [order, ...prev])
      setMessage({
        type: 'success',
        text: `Orden virtual #${order.order_id} ejecutada (${order.direction} ${order.pair})`,
      })
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Error al ejecutar orden virtual',
      })
    }
  }, [analysis])

  const handleCloseOrder = useCallback((orderId: number) => {
    setVirtualOrders((prev) => {
      const order = prev.find((o) => o.order_id === orderId)
      if (!order) return prev

      const pipValue = order.pair.includes('JPY') ? 0.01 : 0.0001
      const currentPrice = analysis?.ANÁLISIS_FOREX?.DATOS_ACTUALES?.['Precio Actual'] || order.entry_price
      const priceDiff = order.direction === 'BUY' ? currentPrice - order.entry_price : order.entry_price - currentPrice
      const pips = priceDiff / pipValue
      const pnl = pips * 10 * order.lot_size

      const closedOrder: VirtualOrder = {
        ...order,
        status: 'CLOSED',
        exit_price: currentPrice,
        exit_at: new Date().toISOString(),
        pnl,
        pips,
      }

      setClosedOrders((prev) => [closedOrder, ...prev].slice(0, 20))
      setCapital((prev) => prev + pnl)

      return prev.filter((o) => o.order_id !== orderId)
    })
  }, [analysis])

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('es-CO', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  }

  const formatNumber = (value: number, decimals = 4) => {
    return value.toLocaleString('es-CO', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  const getSignalColor = (type: string) => {
    if (type === 'BUY') return 'text-green-400'
    if (type === 'SELL') return 'text-red-400'
    return 'text-gray-400'
  }

  const getSignalBg = (type: string) => {
    if (type === 'BUY') return 'bg-green-500/20 border-green-500'
    if (type === 'SELL') return 'bg-red-500/20 border-red-500'
    return 'bg-gray-500/20 border-gray-500'
  }

  return (
    <div className="space-y-6">
      {/* Estadísticas de sesión */}
      {sessionStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <p className="text-xs text-gray-400 uppercase tracking-wide">Capital</p>
            <p className="text-2xl font-bold text-white mt-1">{formatCurrency(capital)}</p>
          </div>
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <p className="text-xs text-gray-400 uppercase tracking-wide">Win Rate</p>
            <p className="text-2xl font-bold text-green-400 mt-1">
              {(sessionStats.session_stats.win_rate * 100).toFixed(1)}%
            </p>
          </div>
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <p className="text-xs text-gray-400 uppercase tracking-wide">Profit Factor</p>
            <p className="text-2xl font-bold text-blue-400 mt-1">
              {sessionStats.session_stats.profit_factor.toFixed(2)}
            </p>
          </div>
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <p className="text-xs text-gray-400 uppercase tracking-wide">Sharpe Ratio</p>
            <p className="text-2xl font-bold text-purple-400 mt-1">
              {sessionStats.session_stats.sharpe_ratio.toFixed(2)}
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Panel de pares */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <h4 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wide flex items-center gap-2">
            <Activity className="h-4 w-4 text-primary-400" /> Pares Forex
          </h4>
          <div className="space-y-2">
            {FOREX_PAIRS.map((pair) => (
              <button
                key={pair.id}
                onClick={() => setSelectedPair(pair.id)}
                className={`w-full p-3 rounded-lg border transition text-left ${
                  selectedPair === pair.id
                    ? 'border-primary-500 bg-primary-500/10'
                    : 'border-gray-700 bg-gray-900/30 hover:border-gray-600'
                }`}
              >
                <span className="text-white font-semibold">{pair.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Análisis técnico */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-4">
          {loadingAnalysis ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 text-primary-400 animate-spin" />
            </div>
          ) : analysis && analysis.ANÁLISIS_FOREX ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wide">Análisis Experto</p>
                  <h4 className="text-xl text-white font-semibold">{analysis.ANÁLISIS_FOREX.PAR_ACTUAL}</h4>
                  <p className="text-xs text-gray-500">{analysis.ANÁLISIS_FOREX.DATETIME}</p>
                </div>
                <div
                  className={`px-3 py-1 rounded-full border ${getSignalBg(
                    analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO
                  )}`}
                >
                  <span className={`text-xs font-semibold ${getSignalColor(analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO)}`}>
                    {analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO}
                  </span>
                </div>
              </div>

              {/* Datos actuales */}
              <div className="bg-gray-900/40 rounded-lg p-3 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Precio Actual</span>
                  <span className="text-white font-semibold">
                    {formatNumber(analysis.ANÁLISIS_FOREX.DATOS_ACTUALES['Precio Actual'])}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Bid / Ask</span>
                  <span className="text-white font-semibold">
                    {formatNumber(analysis.ANÁLISIS_FOREX.DATOS_ACTUALES.Bid)} /{' '}
                    {formatNumber(analysis.ANÁLISIS_FOREX.DATOS_ACTUALES.Ask)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Rango 24H</span>
                  <span className="text-white font-semibold">{analysis.ANÁLISIS_FOREX.DATOS_ACTUALES['Rango 24H']}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Volatilidad (ATR)</span>
                  <span className="text-white font-semibold">
                    {analysis.ANÁLISIS_FOREX.DATOS_ACTUALES['Volatilidad (ATR-20)']}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Tendencia 4H</span>
                  <span className="text-white font-semibold">{analysis.ANÁLISIS_FOREX.DATOS_ACTUALES['Tendencia 4H']}</span>
                </div>
              </div>

              {/* Indicadores técnicos */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-gray-900/40 rounded-lg p-3">
                  <p className="text-xs text-gray-400">RSI(14)</p>
                  <p className="text-white font-semibold">{analysis.ANÁLISIS_FOREX.ANÁLISIS_TÉCNICO['RSI(14)']}</p>
                  <p className="text-xs text-gray-500">{analysis.ANÁLISIS_FOREX.ANÁLISIS_TÉCNICO.RSI_Interpretation}</p>
                </div>
                <div className="bg-gray-900/40 rounded-lg p-3">
                  <p className="text-xs text-gray-400">MACD</p>
                  <p className="text-white font-semibold">
                    {analysis.ANÁLISIS_FOREX.ANÁLISIS_TÉCNICO.MACD.Interpretation}
                  </p>
                  <p className="text-xs text-gray-500">
                    Hist: {analysis.ANÁLISIS_FOREX.ANÁLISIS_TÉCNICO.MACD.Histograma.toFixed(3)}
                  </p>
                </div>
                <div className="bg-gray-900/40 rounded-lg p-3">
                  <p className="text-xs text-gray-400">SMA 50</p>
                  <p className="text-white font-semibold">
                    {formatNumber(analysis.ANÁLISIS_FOREX.ANÁLISIS_TÉCNICO['Medias Móviles']['SMA 50'])}
                  </p>
                </div>
                <div className="bg-gray-900/40 rounded-lg p-3">
                  <p className="text-xs text-gray-400">SMA 200</p>
                  <p className="text-white font-semibold">
                    {formatNumber(analysis.ANÁLISIS_FOREX.ANÁLISIS_TÉCNICO['Medias Móviles']['SMA 200'])}
                  </p>
                </div>
              </div>

              {/* Señal generada */}
              <div className={`bg-gray-900/60 border rounded-xl p-4 ${getSignalBg(analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO)}`}>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide">Señal Generada</p>
                    <p className={`text-lg font-bold ${getSignalColor(analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO)}`}>
                      {analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-primary-300">
                      {analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.CONFIANZA}
                    </p>
                    <p className="text-xs text-gray-400">Confianza</p>
                  </div>
                </div>
                <ul className="space-y-1 text-xs text-gray-300">
                  {analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.CONFLUENCIA.map((reason, idx) => (
                    <li key={idx} className="flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-primary-400" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>No hay análisis disponible</p>
            </div>
          )}
        </div>

        {/* Recomendación y ejecución */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-4">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Recomendación de Operación</p>
            <h4 className="text-lg font-semibold text-white">Control de Riesgo</h4>
          </div>

          {analysis && analysis.ANÁLISIS_FOREX && (
            <>
              <div className="bg-gray-900/40 rounded-lg p-3 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Entrada</span>
                  <span className="text-white font-semibold">
                    {formatNumber(analysis.ANÁLISIS_FOREX.RECOMENDACIÓN_OPERACIÓN.Entrada)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Stop Loss</span>
                  <span className="text-red-300 font-semibold">
                    {formatNumber(analysis.ANÁLISIS_FOREX.RECOMENDACIÓN_OPERACIÓN['Stop Loss'])}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Take Profit</span>
                  <span className="text-green-300 font-semibold">
                    {formatNumber(analysis.ANÁLISIS_FOREX.RECOMENDACIÓN_OPERACIÓN['Take Profit'])}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Ratio R:R</span>
                  <span className="text-white font-semibold">
                    {analysis.ANÁLISIS_FOREX.RECOMENDACIÓN_OPERACIÓN['Relación R:R']}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Riesgo</span>
                  <span className="text-white font-semibold">
                    {analysis.ANÁLISIS_FOREX.RECOMENDACIÓN_OPERACIÓN.Riesgo.split('=')[0].trim()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Probabilidad</span>
                  <span className="text-white font-semibold">
                    {analysis.ANÁLISIS_FOREX.RECOMENDACIÓN_OPERACIÓN['Probabilidad Éxito']}
                  </span>
                </div>
              </div>

              <button
                onClick={handleExecuteOrder}
                disabled={analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO === 'HOLD'}
                className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-semibold transition ${
                  analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO === 'BUY'
                    ? 'bg-green-600 hover:bg-green-500 text-white'
                    : analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO === 'SELL'
                    ? 'bg-red-600 hover:bg-red-500 text-white'
                    : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                }`}
              >
                {analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO === 'BUY' && (
                  <>
                    <TrendingUp className="h-4 w-4" />
                    Ejecutar COMPRA
                  </>
                )}
                {analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO === 'SELL' && (
                  <>
                    <TrendingDown className="h-4 w-4" />
                    Ejecutar VENTA
                  </>
                )}
                {analysis.ANÁLISIS_FOREX.SEÑAL_GENERADA.TIPO === 'HOLD' && 'Esperar señal válida'}
              </button>
            </>
          )}

          {message && (
            <div
              className={`text-sm px-3 py-2 rounded-lg border ${
                message.type === 'error'
                  ? 'bg-red-500/10 border-red-500 text-red-200'
                  : message.type === 'success'
                  ? 'bg-green-500/10 border-green-500 text-green-200'
                  : 'bg-blue-500/10 border-blue-500 text-blue-200'
              }`}
            >
              {message.text}
            </div>
          )}
        </div>
      </div>

      {/* Órdenes virtuales */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Órdenes Abiertas</h4>
            <span className="text-xs text-gray-500">{virtualOrders.length} activas</span>
          </div>
          {virtualOrders.length === 0 ? (
            <p className="text-sm text-gray-500">No hay órdenes virtuales activas.</p>
          ) : (
            <div className="space-y-3">
              {virtualOrders.map((order) => (
                <div key={order.order_id} className="border border-gray-700 rounded-lg p-3 bg-gray-900/50">
                  <div className="flex items-center justify-between text-sm text-gray-300">
                    <p>
                      #{order.order_id} • {order.direction} {order.pair}
                    </p>
                    <span className="text-xs text-gray-400">{new Date(order.opened_at).toLocaleTimeString('es-CO')}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs text-gray-400 mt-2">
                    <div>
                      <p>Entrada</p>
                      <p className="text-white font-semibold">{formatNumber(order.entry_price)}</p>
                    </div>
                    <div>
                      <p>TP / SL</p>
                      <p className="text-white font-semibold">
                        {formatNumber(order.take_profit)} / {formatNumber(order.stop_loss)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleCloseOrder(order.order_id)}
                    className="mt-3 w-full px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs text-gray-200"
                  >
                    Cerrar Orden
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Historial Reciente</h4>
            <span className="text-xs text-gray-500">{closedOrders.length} cerradas</span>
          </div>
          {closedOrders.length === 0 ? (
            <p className="text-sm text-gray-500">Sin trades cerrados por ahora.</p>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {closedOrders.map((order) => (
                <div key={`${order.order_id}-${order.exit_at}`} className="p-3 rounded-lg bg-gray-900/40 border border-gray-700">
                  <div className="flex items-center justify-between text-sm text-gray-300">
                    <span>
                      #{order.order_id} {order.direction} {order.pair}
                    </span>
                    <span className="text-xs text-gray-400">
                      {order.exit_at ? new Date(order.exit_at).toLocaleTimeString('es-CO') : ''}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-400">Resultado</span>
                    <span className={`text-sm font-semibold ${order.pnl && order.pnl >= 0 ? 'text-green-300' : 'text-red-300'}`}>
                      {order.pnl && order.pnl >= 0 ? '+' : ''}
                      {order.pnl?.toFixed(2)} USD ({order.pips?.toFixed(1)} pips)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

