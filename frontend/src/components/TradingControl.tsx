'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  DollarSign,
  RefreshCw,
  Settings,
  Shield,
  Target,
  TrendingDown,
  TrendingUp,
  Trophy,
  Zap,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import api from '@/lib/api'

type TradingMode = 'manual' | 'auto' | 'hybrid'
type TrendLabel = 'ALCISTA' | 'BAJISTA' | 'LATERAL'
type MacdSignal = 'positive' | 'negative' | 'neutral'

type SimulationResult = 'TP' | 'SL' | 'MANUAL'

interface TradingConfig {
  mode: TradingMode
  enabled: boolean
  maxDailyVolume: number
  maxPositionSize: number
  profitMarginCOP: number
  profitMarginVES: number
  minSpread: number
  riskLimit: number
}

interface SimulationPair {
  id: string
  fiat: string
  name: string
  marketPrice: number
  bid: number
  ask: number
  changePct: number
  rsi: number
  atr: number
  macdSignal: MacdSignal
  trend4h: TrendLabel
  trendD1: TrendLabel
  support1: number
  resistance1: number
  pipValue: number
  liquidityScore: number
}

interface SimulationSignal {
  type: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  reasons: string[]
}

interface SimulationOrder {
  id: number
  pairId: string
  pairName: string
  direction: 'BUY' | 'SELL'
  entryPrice: number
  stopLoss: number
  takeProfit: number
  lotSize: number
  riskAmount: number
  pipValue: number
  signalConfidence: number
  openedAt: string
  status: 'OPEN' | SimulationResult
  exitPrice?: number
  exitAt?: string
  pnl?: number
  pips?: number
}

interface SessionSummary {
  total: number
  wins: number
  losses: number
  profit: number
  profitWins: number
  profitLosses: number
  winRate: number
  profitFactor: number
}

const BASE_CAPITAL = 10000

const BASE_PAIR_BLUEPRINTS: Array<{
  fiat: string
  price: number
  rsi: number
  atr: number
  trend4h: TrendLabel
  trendD1: TrendLabel
  changePct: number
  macd: MacdSignal
  pipValue: number
  liquidity: number
}> = [
  {
    fiat: 'COP',
    price: 4000,
    rsi: 58,
    atr: 42,
    trend4h: 'ALCISTA',
    trendD1: 'ALCISTA',
    changePct: 0.35,
    macd: 'positive',
    pipValue: 1,
    liquidity: 0.9,
  },
  {
    fiat: 'VES',
    price: 36,
    rsi: 52,
    atr: 38,
    trend4h: 'LATERAL',
    trendD1: 'ALCISTA',
    changePct: 0.12,
    macd: 'neutral',
    pipValue: 0.05,
    liquidity: 0.75,
  },
  {
    fiat: 'BRL',
    price: 4.9,
    rsi: 48,
    atr: 31,
    trend4h: 'LATERAL',
    trendD1: 'BAJISTA',
    changePct: -0.2,
    macd: 'negative',
    pipValue: 0.0005,
    liquidity: 0.6,
  },
  {
    fiat: 'ARS',
    price: 900,
    rsi: 45,
    atr: 55,
    trend4h: 'BAJISTA',
    trendD1: 'BAJISTA',
    changePct: -0.45,
    macd: 'negative',
    pipValue: 0.1,
    liquidity: 0.4,
  },
  {
    fiat: 'MXN',
    price: 17,
    rsi: 50,
    atr: 28,
    trend4h: 'LATERAL',
    trendD1: 'ALCISTA',
    changePct: 0.08,
    macd: 'positive',
    pipValue: 0.005,
    liquidity: 0.7,
  },
]

const INITIAL_SUMMARY: SessionSummary = {
  total: 0,
  wins: 0,
  losses: 0,
  profit: 0,
  profitWins: 0,
  profitLosses: 0,
  winRate: 0,
  profitFactor: 0,
}

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value))

const formatCurrency = (value: number, currency: string | null = 'USD') => {
  const symbol = currency === 'COP' ? '$' : currency === 'VES' ? 'Bs.' : '$'
  return `${symbol}${value.toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

const formatNumber = (value: number, decimals = 2) => value.toLocaleString('es-CO', {
  minimumFractionDigits: decimals,
  maximumFractionDigits: decimals,
})

const createInitialPairs = (): SimulationPair[] =>
  BASE_PAIR_BLUEPRINTS.map((blueprint) => {
    const bid = blueprint.price * 0.999
    const ask = blueprint.price * 1.001
    return {
      id: blueprint.fiat,
      fiat: blueprint.fiat,
      name: `USDT/${blueprint.fiat}`,
      marketPrice: blueprint.price,
      bid,
      ask,
      changePct: blueprint.changePct,
      rsi: blueprint.rsi,
      atr: blueprint.atr,
      macdSignal: blueprint.macd,
      trend4h: blueprint.trend4h,
      trendD1: blueprint.trendD1,
      support1: blueprint.price * 0.985,
      resistance1: blueprint.price * 1.015,
      pipValue: blueprint.pipValue,
      liquidityScore: blueprint.liquidity,
    }
  })

export function TradingControl() {
  const [config, setConfig] = useState<TradingConfig>({
    mode: 'hybrid',
    enabled: true,
    maxDailyVolume: 100000,
    maxPositionSize: 10000,
    profitMarginCOP: 2.5,
    profitMarginVES: 3,
    minSpread: 1,
    riskLimit: 5000,
  })

  const [isEditing, setIsEditing] = useState(false)
  const [pairs, setPairs] = useState<SimulationPair[]>(createInitialPairs)
  const [selectedPairId, setSelectedPairId] = useState<string>(pairs[0]?.id ?? 'COP')
  const [orderForm, setOrderForm] = useState({ stopLoss: 40, takeProfit: 70, riskPercent: 1 })
  const [capital, setCapital] = useState(BASE_CAPITAL)
  const [equity, setEquity] = useState(BASE_CAPITAL)
  const [peakCapital, setPeakCapital] = useState(BASE_CAPITAL)
  const [maxDrawdown, setMaxDrawdown] = useState(0)
  const [openOrders, setOpenOrders] = useState<SimulationOrder[]>([])
  const [closedOrders, setClosedOrders] = useState<SimulationOrder[]>([])
  const [sessionSummary, setSessionSummary] = useState<SessionSummary>(INITIAL_SUMMARY)
  const [message, setMessage] = useState<{ type: 'info' | 'error' | 'success'; text: string } | null>(null)

  const { data: currentPrices, isFetching: loadingPrices } = useQuery({
    queryKey: ['trading-control-prices'],
    queryFn: () => api.getCurrentPrices('USDT'),
    refetchInterval: 15000,
  })

  const pairsRef = useRef<SimulationPair[]>(pairs)
  const timeoutsRef = useRef<Array<ReturnType<typeof setTimeout>>>([])

  useEffect(() => {
    pairsRef.current = pairs
  }, [pairs])

  useEffect(() => {
    if (!currentPrices) return

    setPairs((prev) =>
      prev.map((pair) => {
        const remote = currentPrices[pair.fiat]
        if (!remote) return pair

        const nextPrice = remote.sell_price || remote.price || pair.marketPrice
        if (!nextPrice) return pair

        const prevPrice = pair.marketPrice || nextPrice
        const deltaPct = prevPrice > 0 ? ((nextPrice - prevPrice) / prevPrice) * 100 : 0
        const smoothedChange = clamp(pair.changePct * 0.6 + deltaPct * 0.4, -5, 5)
        const updatedRsi = clamp(pair.rsi + deltaPct * 0.8, 18, 85)
        const updatedAtr = clamp(pair.atr + Math.abs(deltaPct) * 0.6, 20, 90)
        const spread = remote.buy_price && remote.sell_price ? remote.sell_price - remote.buy_price : nextPrice * 0.002
        const bid = nextPrice - spread / 2
        const ask = nextPrice + spread / 2

        return {
          ...pair,
          marketPrice: nextPrice,
          bid,
          ask,
          changePct: smoothedChange,
          rsi: updatedRsi,
          atr: updatedAtr,
          support1: nextPrice * 0.985,
          resistance1: nextPrice * 1.015,
        }
      })
    )
  }, [currentPrices])

  useEffect(() => {
    if (!message) return
    const timeout = setTimeout(() => setMessage(null), 4000)
    return () => clearTimeout(timeout)
  }, [message])

  useEffect(() => () => {
    timeoutsRef.current.forEach((timeout) => clearTimeout(timeout))
  }, [])

  const selectedPair = useMemo(
    () => pairs.find((pair) => pair.id === selectedPairId) ?? pairs[0],
    [pairs, selectedPairId]
  )

  const signal = useMemo(() => (selectedPair ? calculateSignal(selectedPair) : null), [selectedPair])

  const updateCapitalAndStats = useCallback((pnl: number) => {
    setCapital((prev) => {
      const next = Number((prev + pnl).toFixed(2))
      setEquity(next)
      setPeakCapital((currentPeak) => {
        const updatedPeak = Math.max(currentPeak, next)
        const drawdown = updatedPeak > 0 ? ((updatedPeak - next) / updatedPeak) * 100 : 0
        setMaxDrawdown((prevDd) => Number(Math.max(prevDd, drawdown).toFixed(2)))
        return updatedPeak
      })
      return next
    })

    setSessionSummary((prev) => {
      const wins = prev.wins + (pnl > 0 ? 1 : 0)
      const losses = prev.losses + (pnl <= 0 ? 1 : 0)
      const total = wins + losses
      const profitWins = prev.profitWins + (pnl > 0 ? pnl : 0)
      const profitLosses = prev.profitLosses + (pnl < 0 ? pnl : 0)
      const profit = prev.profit + pnl
      const winRate = total ? (wins / total) * 100 : 0
      const profitFactor = profitLosses < 0 ? profitWins / Math.abs(profitLosses) : profitWins

      return {
        total,
        wins,
        losses,
        profitWins,
        profitLosses,
        profit,
        winRate,
        profitFactor,
      }
    })
  }, [])

  const finalizeOrder = useCallback(
    (orderId: number, manualExit = false) => {
      setOpenOrders((prev) => {
        const target = prev.find((order) => order.id === orderId)
        if (!target) return prev

        const pair = pairsRef.current.find((p) => p.id === target.pairId)
        const pipValue = target.pipValue || pair?.pipValue || 1
        const probability = manualExit
          ? 0.5
          : clamp((target.signalConfidence || 55) / 100, 0.15, 0.85)
        const didWin = Math.random() < probability

        const exitPrice = manualExit && pair?.marketPrice
          ? pair.marketPrice
          : didWin
          ? target.takeProfit
          : target.stopLoss

        const pipDiff = Math.abs(exitPrice - target.entryPrice) / pipValue
        const signedPips = didWin ? pipDiff : -pipDiff
        const pnl = Number((signedPips * 10 * target.lotSize).toFixed(2))

        const closedTrade: SimulationOrder = {
          ...target,
          status: manualExit ? 'MANUAL' : didWin ? 'TP' : 'SL',
          exitPrice: Number(exitPrice.toFixed(4)),
          exitAt: new Date().toISOString(),
          pnl,
          pips: Number(signedPips.toFixed(1)),
        }

        setClosedOrders((prevClosed) => [closedTrade, ...prevClosed].slice(0, 20))
        updateCapitalAndStats(pnl)
        setMessage({
          type: pnl >= 0 ? 'success' : 'error',
          text: `Orden #${target.id} ${pnl >= 0 ? 'cerró con ganancia' : 'registró pérdida'} (${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)} USD)`,
        })

        return prev.filter((order) => order.id !== orderId)
      })
    },
    [updateCapitalAndStats]
  )

  const handleSimulateOrder = (direction: 'BUY' | 'SELL') => {
    if (!selectedPair) return

    if (!config.enabled || config.mode !== 'auto') {
      setMessage({ type: 'error', text: 'Activa el modo automático para correr simulaciones.' })
      return
    }

    const stopLoss = Number(orderForm.stopLoss)
    const takeProfit = Number(orderForm.takeProfit)

    if (Number.isNaN(stopLoss) || Number.isNaN(takeProfit)) {
      setMessage({ type: 'error', text: 'Configura Stop Loss y Take Profit en pips.' })
      return
    }

    if (stopLoss < 15 || stopLoss > 120) {
      setMessage({ type: 'error', text: 'El Stop Loss debe estar entre 15 y 120 pips.' })
      return
    }

    const rr = takeProfit / stopLoss
    if (rr < 1.5) {
      setMessage({ type: 'error', text: 'El ratio riesgo/beneficio debe ser al menos 1:1.5.' })
      return
    }

    const pipValue = selectedPair.pipValue || 1
    const entryPrice = direction === 'BUY' ? selectedPair.ask : selectedPair.bid
    const riskPercent = clamp(orderForm.riskPercent, 0.5, 3)
    const riskAmount = Number(((capital * riskPercent) / 100).toFixed(2))
    const lotSize = Number((riskAmount / Math.max(1, stopLoss) / 10).toFixed(2))

    const stopLossPrice = direction === 'BUY'
      ? entryPrice - stopLoss * pipValue
      : entryPrice + stopLoss * pipValue
    const takeProfitPrice = direction === 'BUY'
      ? entryPrice + takeProfit * pipValue
      : entryPrice - takeProfit * pipValue

    const order: SimulationOrder = {
      id: Date.now(),
      pairId: selectedPair.id,
      pairName: selectedPair.name,
      direction,
      entryPrice,
      stopLoss: Number(stopLossPrice.toFixed(4)),
      takeProfit: Number(takeProfitPrice.toFixed(4)),
      lotSize,
      riskAmount,
      pipValue,
      signalConfidence: signal?.confidence ?? 55,
      openedAt: new Date().toISOString(),
      status: 'OPEN',
    }

    setOpenOrders((prev) => [order, ...prev])
    setMessage({ type: 'info', text: `Orden virtual #${order.id} abierta (${direction} ${order.pairName}).` })

    const timeout = setTimeout(() => finalizeOrder(order.id), 2500 + Math.random() * 3500)
    timeoutsRef.current.push(timeout)
  }

  const handleModeChange = (mode: TradingMode) => {
    if (!isEditing) return
    setConfig((prev) => ({ ...prev, mode }))
  }

  const handleToggle = () => {
    setConfig((prev) => ({ ...prev, enabled: !prev.enabled }))
  }

  const handleSave = () => {
    setIsEditing(false)
    setMessage({ type: 'success', text: 'Configuración de trading guardada.' })
  }

  const resetSimulator = () => {
    timeoutsRef.current.forEach((timeout) => clearTimeout(timeout))
    timeoutsRef.current = []
    setOpenOrders([])
    setClosedOrders([])
    setCapital(BASE_CAPITAL)
    setEquity(BASE_CAPITAL)
    setPeakCapital(BASE_CAPITAL)
    setMaxDrawdown(0)
    setSessionSummary({ ...INITIAL_SUMMARY })
    setMessage({ type: 'info', text: 'Simulador reiniciado. Capital restaurado.' })
  }

  const selectedPairStats = useMemo(() => {
    if (!selectedPair) {
      return { spread: 0, depth: 'Media', volatility: 'Normal' }
    }

    const spread = selectedPair.ask - selectedPair.bid
    const volatility = selectedPair.atr > 60 ? 'Alta' : selectedPair.atr < 35 ? 'Baja' : 'Normal'
    const depth = selectedPair.liquidityScore >= 0.75 ? 'Alta' : selectedPair.liquidityScore >= 0.5 ? 'Media' : 'Baja'

    return { spread, volatility, depth }
  }, [selectedPair])

  const statsCards = [
    {
      label: 'Capital actual',
      value: formatCurrency(capital),
      trend: capital >= BASE_CAPITAL ? 'positive' : 'negative',
    },
    {
      label: 'Profit sesión',
      value: `${sessionSummary.profit >= 0 ? '+' : ''}${formatNumber(sessionSummary.profit, 2)} USD`,
      trend: sessionSummary.profit >= 0 ? 'positive' : 'negative',
    },
    {
      label: 'Win rate',
      value: `${sessionSummary.winRate.toFixed(1)}%`,
      trend: sessionSummary.winRate >= 50 ? 'positive' : 'negative',
    },
    {
      label: 'Drawdown máximo',
      value: `${maxDrawdown.toFixed(1)}%`,
      trend: 'neutral',
    },
    {
      label: 'Órdenes abiertas',
      value: openOrders.length.toString(),
      trend: openOrders.length <= 3 ? 'positive' : 'warning',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Control de Trading</h2>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsEditing((prev) => !prev)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition"
          >
            <Settings className="h-4 w-4" />
            {isEditing ? 'Cancelar' : 'Editar'}
          </button>
          {isEditing && (
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition"
            >
              Guardar cambios
            </button>
          )}
        </div>
      </div>

      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Estado del Sistema</h3>
            <p className="text-sm text-gray-400">Controla el modo de operación del trading</p>
          </div>
          <button
            onClick={handleToggle}
            className={`relative inline-flex h-12 w-24 items-center rounded-full transition-colors ${
              config.enabled ? 'bg-green-500' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-10 w-10 transform rounded-full bg-white transition-transform ${
                config.enabled ? 'translate-x-12' : 'translate-x-1'
              }`}
            />
            <span className="absolute left-2 text-white text-xs font-medium">
              {config.enabled ? 'ON' : 'OFF'}
            </span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(['manual', 'auto', 'hybrid'] as TradingMode[]).map((mode) => {
            const isActive = config.mode === mode
            const info = modeInfo[mode]
            const Icon = info.icon
            return (
              <button
                key={mode}
                onClick={() => handleModeChange(mode)}
                disabled={!isEditing}
                className={`p-4 rounded-lg border-2 transition text-left ${
                  isActive ? 'border-primary-500 bg-primary-500/20' : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                } ${!isEditing ? 'cursor-not-allowed opacity-50' : ''}`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`${info.bgColor} p-2 rounded-lg`}>
                    <Icon className={`h-5 w-5 ${info.color}`} />
                  </div>
                  <span className="font-semibold text-white">{info.label}</span>
                  {isActive && (
                    <span className="ml-auto px-2 py-1 bg-primary-600 text-white text-xs rounded-full">
                      Activo
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-400">{info.description}</p>
              </button>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <DollarSign className="h-5 w-5 text-green-400" />
            <h3 className="text-lg font-bold text-white">Límites de Volumen</h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Volumen máximo diario (USD)</label>
              <input
                type="number"
                value={config.maxDailyVolume}
                onChange={(e) =>
                  setConfig({ ...config, maxDailyVolume: parseFloat(e.target.value) || 0 })
                }
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Tamaño máximo por posición (USD)</label>
              <input
                type="number"
                value={config.maxPositionSize}
                onChange={(e) =>
                  setConfig({ ...config, maxPositionSize: parseFloat(e.target.value) || 0 })
                }
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <TrendingUp className="h-5 w-5 text-yellow-400" />
            <h3 className="text-lg font-bold text-white">Márgenes de Ganancia</h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Margen COP (%)</label>
              <input
                type="number"
                step="0.1"
                value={config.profitMarginCOP}
                onChange={(e) =>
                  setConfig({ ...config, profitMarginCOP: parseFloat(e.target.value) || 0 })
                }
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Margen VES (%)</label>
              <input
                type="number"
                step="0.1"
                value={config.profitMarginVES}
                onChange={(e) =>
                  setConfig({ ...config, profitMarginVES: parseFloat(e.target.value) || 0 })
                }
                disabled={!isEditing}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-800 rounded-2xl p-6 space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-primary-300">Simulador experto</p>
            <h3 className="text-2xl font-semibold text-white mt-1">Modo de trading virtual</h3>
            <p className="text-sm text-gray-400">Opera con datos reales de P2P para validar la estrategia automática sin arriesgar capital.</p>
          </div>
          <button
            onClick={resetSimulator}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg"
          >
            <RefreshCw className="h-4 w-4" /> Reiniciar simulador
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {statsCards.map((card) => (
            <div
              key={card.label}
              className="bg-gray-800/60 border border-gray-700 rounded-xl p-4 flex flex-col gap-2"
            >
              <span className="text-xs text-gray-400 uppercase tracking-wide">{card.label}</span>
              <span
                className={`text-2xl font-bold ${
                  card.trend === 'positive'
                    ? 'text-green-400'
                    : card.trend === 'negative'
                    ? 'text-red-400'
                    : 'text-blue-300'
                }`}
              >
                {card.value}
              </span>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 h-full">
            <h4 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wide flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary-400" /> Mercados disponibles
            </h4>
            <div className="space-y-2">
              {pairs.map((pair) => (
                <button
                  key={pair.id}
                  onClick={() => setSelectedPairId(pair.id)}
                  className={`w-full p-3 rounded-lg border transition text-left ${
                    selectedPair?.id === pair.id
                      ? 'border-primary-500 bg-primary-500/10'
                      : 'border-gray-700 bg-gray-900/30 hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-white font-semibold">{pair.name}</span>
                    <span
                      className={`${pair.changePct >= 0 ? 'text-green-400' : 'text-red-400'} text-sm flex items-center gap-1`}
                    >
                      {pair.changePct >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                      {pair.changePct >= 0 ? '+' : ''}{pair.changePct.toFixed(2)}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1 flex items-center justify-between">
                    <span>Precio</span>
                    <span>{formatNumber(pair.marketPrice, pair.fiat === 'USD' ? 4 : 2)}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide">Análisis avanzado</p>
                <h4 className="text-xl text-white font-semibold">{selectedPair?.name}</h4>
              </div>
              <div className="px-3 py-1 rounded-full border border-primary-500 text-primary-300 text-xs font-semibold">
                {selectedPairStats.volatility} volatilidad
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-gray-900/40 rounded-lg p-3">
                <p className="text-xs text-gray-400">Bid / Ask</p>
                <p className="text-white font-semibold">
                  {formatNumber(selectedPair?.bid || 0, 4)} / {formatNumber(selectedPair?.ask || 0, 4)}
                </p>
              </div>
              <div className="bg-gray-900/40 rounded-lg p-3">
                <p className="text-xs text-gray-400">Spread</p>
                <p className="text-white font-semibold">{selectedPairStats.spread.toFixed(2)} {selectedPair?.fiat}</p>
              </div>
              <div className="bg-gray-900/40 rounded-lg p-3">
                <p className="text-xs text-gray-400">RSI</p>
                <p className="text-white font-semibold">{selectedPair?.rsi.toFixed(1)}</p>
              </div>
              <div className="bg-gray-900/40 rounded-lg p-3">
                <p className="text-xs text-gray-400">ATR</p>
                <p className="text-white font-semibold">{selectedPair?.atr.toFixed(1)} pips</p>
              </div>
              <div className="bg-gray-900/40 rounded-lg p-3">
                <p className="text-xs text-gray-400">Tendencia 4H</p>
                <p className="text-white font-semibold">{selectedPair?.trend4h}</p>
              </div>
              <div className="bg-gray-900/40 rounded-lg p-3">
                <p className="text-xs text-gray-400">Tendencia Diario</p>
                <p className="text-white font-semibold">
                  {selectedPair?.trendD1}
                </p>
              </div>
            </div>

            {signal && (
              <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wide">Señal automátizate</p>
                    <p className="text-lg font-bold text-white">{signal.type}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-primary-300">{signal.confidence}</p>
                    <p className="text-xs text-gray-400">Confianza</p>
                  </div>
                </div>
                <ul className="mt-3 space-y-2 text-xs text-gray-300">
                  {signal.reasons.slice(0, 3).map((reason) => (
                    <li key={reason} className="flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-primary-400" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 space-y-4">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide">Definición de trade</p>
              <h4 className="text-lg font-semibold text-white">Control de riesgo</h4>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Stop Loss (pips)</label>
                <input
                  type="number"
                  value={orderForm.stopLoss}
                  onChange={(e) =>
                    setOrderForm({ ...orderForm, stopLoss: parseFloat(e.target.value) || 0 })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-white focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Take Profit (pips)</label>
                <input
                  type="number"
                  value={orderForm.takeProfit}
                  onChange={(e) =>
                    setOrderForm({ ...orderForm, takeProfit: parseFloat(e.target.value) || 0 })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-white focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Riesgo por trade (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={orderForm.riskPercent}
                  onChange={(e) =>
                    setOrderForm({ ...orderForm, riskPercent: parseFloat(e.target.value) || 0 })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-white focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Liquidez</label>
                <div className="px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-white">
                  {selectedPairStats.depth}
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <button
                onClick={() => handleSimulateOrder('BUY')}
                disabled={loadingPrices}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white font-semibold"
              >
                Comprar simulada
              </button>
              <button
                onClick={() => handleSimulateOrder('SELL')}
                disabled={loadingPrices}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold"
              >
                Vender simulada
              </button>
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
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Órdenes abiertas</h4>
              <span className="text-xs text-gray-500">{openOrders.length} activas</span>
            </div>
            {openOrders.length === 0 ? (
              <p className="text-sm text-gray-500">No hay órdenes virtuales activas.</p>
            ) : (
              <div className="space-y-3">
                {openOrders.map((order) => (
                  <div key={order.id} className="border border-gray-700 rounded-lg p-3 bg-gray-900/50">
                    <div className="flex items-center justify-between text-sm text-gray-300">
                      <p>
                        #{order.id} • {order.direction} {order.pairName}
                      </p>
                      <span className="text-xs text-gray-400">
                        {new Date(order.openedAt).toLocaleTimeString('es-CO')}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs text-gray-400 mt-2">
                      <div>
                        <p>Entrada</p>
                        <p className="text-white font-semibold">{order.entryPrice.toFixed(4)}</p>
                      </div>
                      <div>
                        <p>TP / SL</p>
                        <p className="text-white font-semibold">
                          {order.takeProfit.toFixed(4)} / {order.stopLoss.toFixed(4)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => finalizeOrder(order.id, true)}
                      className="mt-3 w-full px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-xs text-gray-200"
                    >
                      Resolver ahora
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Historial reciente</h4>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <Trophy className="h-4 w-4 text-yellow-400" /> {sessionSummary.wins} / {sessionSummary.losses}
              </div>
            </div>
            {closedOrders.length === 0 ? (
              <p className="text-sm text-gray-500">Sin trades cerrados por ahora.</p>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {closedOrders.map((order) => (
                  <div key={`${order.id}-${order.exitAt}`} className="p-3 rounded-lg bg-gray-900/40 border border-gray-700">
                    <div className="flex items-center justify-between text-sm text-gray-300">
                      <span>
                        #{order.id} {order.direction} {order.pairName}
                      </span>
                      <span className="text-xs text-gray-400">
                        {order.exitAt ? new Date(order.exitAt).toLocaleTimeString('es-CO') : ''}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-gray-400">Resultado</span>
                      <span
                        className={`text-sm font-semibold ${order.pnl && order.pnl >= 0 ? 'text-green-300' : 'text-red-300'}`}
                      >
                        {order.pnl && order.pnl >= 0 ? '+' : ''}{order.pnl?.toFixed(2)} USD ({order.pips?.toFixed(1)} pips)
                      </span>
                    </div>
                    <span className="text-xs text-gray-500 capitalize">{order.status === 'TP' ? 'Take profit' : order.status === 'SL' ? 'Stop loss' : 'Manual'}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

const modeInfo: Record<TradingMode, { label: string; description: string; icon: LucideIcon; color: string; bgColor: string }> = {
  manual: {
    label: 'Manual',
    description: 'Todas las operaciones requieren aprobación manual',
    icon: Shield,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
  },
  auto: {
    label: 'Automático',
    description: 'El sistema ejecuta operaciones automáticamente',
    icon: Zap,
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
  },
  hybrid: {
    label: 'Híbrido',
    description: 'Trades menores automáticos, los grandes requieren confirmación',
    icon: Target,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
  },
}

const calculateSignal = (pair: SimulationPair): SimulationSignal => {
  let score = 55
  const reasons: string[] = []

  if (pair.rsi < 35) {
    score -= 10
    reasons.push('RSI en zona de sobreventa')
  } else if (pair.rsi > 65) {
    score += 10
    reasons.push('RSI en zona de fuerza compradora')
  }

  if (pair.changePct > 0.4) {
    score += 8
    reasons.push('Momentum positivo en las últimas 24h')
  } else if (pair.changePct < -0.3) {
    score -= 8
    reasons.push('Presión vendedora reciente')
  }

  if (pair.trend4h === 'ALCISTA' && pair.trendD1 === 'ALCISTA') {
    score += 12
    reasons.push('Tendencia sincronizada en 4H y D1')
  } else if (pair.trend4h === 'BAJISTA' && pair.trendD1 === 'BAJISTA') {
    score -= 12
    reasons.push('Sesgo bajista dominante')
  }

  if (pair.atr > 60) {
    score -= 5
    reasons.push('Volatilidad elevada - riesgo de latigazos')
  }

  if (pair.marketPrice < pair.support1) {
    score += 6
    reasons.push('Precio sobre soporte validado')
  } else if (pair.marketPrice > pair.resistance1) {
    score -= 6
    reasons.push('Precio cerca de resistencia clave')
  }

  score = clamp(score, 15, 90)

  let type: SimulationSignal['type'] = 'HOLD'
  if (score >= 65) type = 'BUY'
  else if (score <= 40) type = 'SELL'

  return {
    type,
    confidence: Math.round(score),
    reasons,
  }
}
