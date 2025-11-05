'use client'

import { useEffect, useState } from 'react'
import { DollarSign, TrendingUp, TrendingDown, ArrowRight, Activity, CheckCircle, AlertTriangle } from 'lucide-react'

interface MarketTRM {
  fiat: string
  asset: string
  buy_side: {
    average_price: number
    vwap: number
    median: number
    total_volume: number
    num_orders: number
  }
  sell_side: {
    average_price: number
    vwap: number
    median: number
    total_volume: number
    num_orders: number
  }
  market_trm: {
    simple_average: number
    vwap: number
    median: number
    p25: number
    p75: number
  }
  spread: {
    absolute: number
    percentage: number
  }
}

interface CompetitivePrices {
  our_prices: {
    buy_price: number
    sell_price: number
  }
  market_prices: {
    buy_vwap: number
    sell_vwap: number
  }
  competitiveness: {
    buy_advantage_pct: number
    sell_advantage_pct: number
    overall_score: number
    rating: string
  }
  profit_analysis: {
    gross_margin: number
    net_margin_after_fees: number
    binance_fees_total: number
    is_profitable: boolean
  }
}

interface PricingStrategy {
  market_trm: MarketTRM
  competitive_prices: CompetitivePrices
  recommendations: string[]
  risks: string[]
  action_plan: string[]
  timestamp: string
}

export function CompetitivePricingDashboard() {
  const [copStrategy, setCopStrategy] = useState<PricingStrategy | null>(null)
  const [vesStrategy, setVesStrategy] = useState<PricingStrategy | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPricingStrategies()
    const interval = setInterval(fetchPricingStrategies, 60000) // Refresh every minute

    return () => clearInterval(interval)
  }, [])

  const fetchPricingStrategies = async () => {
    try {
      setError(null)

      // Fetch COP strategy
      const copResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/pricing/strategy-summary?fiat=COP`,
        {
          headers: {
            'ngrok-skip-browser-warning': 'true',
          },
        }
      )
      const copData = await copResponse.json()

      // Fetch VES strategy
      const vesResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/pricing/strategy-summary?fiat=VES`,
        {
          headers: {
            'ngrok-skip-browser-warning': 'true',
          },
        }
      )
      const vesData = await vesResponse.json()

      if (copData.success) setCopStrategy(copData)
      if (vesData.success) setVesStrategy(vesData)

    } catch (error) {
      console.error('Error fetching pricing strategies:', error)
      setError('Error al cargar estrategias de pricing')
    } finally {
      setLoading(false)
    }
  }

  const getCompetitivenessColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-blue-400'
    if (score >= 40) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getCompetitivenessRatingColor = (rating: string) => {
    if (rating === 'MUY_COMPETITIVO') return 'bg-green-600/20 border-green-500/50 text-green-300'
    if (rating === 'COMPETITIVO') return 'bg-blue-600/20 border-blue-500/50 text-blue-300'
    if (rating === 'MODERADO') return 'bg-yellow-600/20 border-yellow-500/50 text-yellow-300'
    return 'bg-red-600/20 border-red-500/50 text-red-300'
  }

  const renderStrategyCard = (strategy: PricingStrategy | null, fiat: string) => {
    // Validación: si no hay strategy, no renderizar nada
    if (!strategy || !strategy.market_trm || !strategy.competitive_prices) {
      return (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <p className="text-gray-400 text-center">No hay datos disponibles para {fiat}</p>
        </div>
      )
    }

    const { market_trm, competitive_prices, recommendations, risks, action_plan } = strategy

    return (
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-gray-900/50 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-600/20 rounded-lg">
                <DollarSign className="h-6 w-6 text-primary-400" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">
                  Estrategia de Pricing - {fiat}
                </h3>
                <p className="text-sm text-gray-400">
                  USDT/{fiat} • Actualizado {new Date(strategy.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>

            <div className={`px-4 py-2 rounded-lg border ${getCompetitivenessRatingColor(competitive_prices?.competitiveness?.rating || 'MODERADO')}`}>
              <div className="text-xs font-medium text-center">
                {competitive_prices?.competitiveness?.rating ? competitive_prices.competitiveness.rating.replace('_', ' ') : 'N/A'}
              </div>
              <div className={`text-2xl font-bold text-center ${getCompetitivenessColor(competitive_prices?.competitiveness?.overall_score || 0)}`}>
                {competitive_prices?.competitiveness?.overall_score !== undefined 
                  ? competitive_prices.competitiveness.overall_score.toFixed(0)
                  : 'N/A'}
              </div>
              <div className="text-xs text-gray-400 text-center">Score</div>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Market TRM */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">
              TRM de Mercado (VWAP)
            </h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-900/50 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">VWAP</p>
                <p className="text-2xl font-bold text-white">
                  {market_trm?.market_trm?.vwap ? market_trm.market_trm.vwap.toLocaleString() : 'N/A'}
                </p>
                <p className="text-xs text-gray-400 mt-1">{fiat}/USDT</p>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Spread</p>
                <p className="text-2xl font-bold text-yellow-400">
                  {market_trm?.spread?.percentage ? market_trm.spread.percentage.toFixed(2) : 'N/A'}%
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {market_trm?.spread?.absolute ? market_trm.spread.absolute.toLocaleString() : 'N/A'} {fiat}
                </p>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Liquidez Total</p>
                <p className="text-2xl font-bold text-blue-400">
                  {market_trm?.buy_side?.total_volume && market_trm?.sell_side?.total_volume 
                    ? (market_trm.buy_side.total_volume + market_trm.sell_side.total_volume).toLocaleString(undefined, { maximumFractionDigits: 0 })
                    : 'N/A'}
                </p>
                <p className="text-xs text-gray-400 mt-1">USDT</p>
              </div>
            </div>
          </div>

          {/* Competitive Pricing */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">
              Precios Competitivos Recomendados
            </h4>

            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Our Buy Price */}
              <div className="bg-gradient-to-br from-green-900/20 to-green-800/10 rounded-lg p-4 border border-green-700/30">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  <p className="text-sm font-medium text-green-300">Nosotros Compramos</p>
                </div>
                <p className="text-3xl font-bold text-white mb-1">
                  {competitive_prices?.our_prices?.buy_price ? competitive_prices.our_prices.buy_price.toLocaleString() : 'N/A'}
                </p>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-gray-400">Mercado:</span>
                  <span className="text-gray-300">
                    {competitive_prices?.market_prices?.buy_vwap ? competitive_prices.market_prices.buy_vwap.toLocaleString() : 'N/A'}
                  </span>
                  <span className="text-green-400 font-medium">
                    {competitive_prices?.competitiveness?.buy_advantage_pct !== undefined 
                      ? `+${competitive_prices.competitiveness.buy_advantage_pct.toFixed(2)}%`
                      : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Our Sell Price */}
              <div className="bg-gradient-to-br from-blue-900/20 to-blue-800/10 rounded-lg p-4 border border-blue-700/30">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingDown className="h-5 w-5 text-blue-400" />
                  <p className="text-sm font-medium text-blue-300">Nosotros Vendemos</p>
                </div>
                <p className="text-3xl font-bold text-white mb-1">
                  {competitive_prices?.our_prices?.sell_price ? competitive_prices.our_prices.sell_price.toLocaleString() : 'N/A'}
                </p>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-gray-400">Mercado:</span>
                  <span className="text-gray-300">
                    {competitive_prices?.market_prices?.sell_vwap ? competitive_prices.market_prices.sell_vwap.toLocaleString() : 'N/A'}
                  </span>
                  <span className="text-blue-400 font-medium">
                    {competitive_prices?.competitiveness?.sell_advantage_pct !== undefined
                      ? `-${Math.abs(competitive_prices.competitiveness.sell_advantage_pct).toFixed(2)}%`
                      : 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Profit Analysis */}
            <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <h5 className="text-sm font-semibold text-gray-300">Análisis de Rentabilidad</h5>
                {competitive_prices?.profit_analysis?.is_profitable ? (
                  <span className="flex items-center gap-1 text-xs text-green-400">
                    <CheckCircle className="h-4 w-4" />
                    Rentable
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-red-400">
                    <AlertTriangle className="h-4 w-4" />
                    No Rentable
                  </span>
                )}
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-500 mb-1">Margen Bruto</p>
                  <p className="text-lg font-bold text-white">
                    {competitive_prices?.profit_analysis?.gross_margin !== undefined 
                      ? `${competitive_prices.profit_analysis.gross_margin.toFixed(2)}%`
                      : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">Fees Binance</p>
                  <p className="text-lg font-bold text-yellow-400">
                    {competitive_prices?.profit_analysis?.binance_fees_total !== undefined
                      ? `${competitive_prices.profit_analysis.binance_fees_total.toFixed(2)}%`
                      : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 mb-1">Margen Neto</p>
                  <p className={`text-lg font-bold ${competitive_prices?.profit_analysis?.net_margin_after_fees !== undefined && competitive_prices.profit_analysis.net_margin_after_fees >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {competitive_prices?.profit_analysis?.net_margin_after_fees !== undefined
                      ? `${competitive_prices.profit_analysis.net_margin_after_fees.toFixed(2)}%`
                      : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendations & Risks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Recommendations */}
            <div className="bg-blue-900/10 rounded-lg p-4 border border-blue-700/30">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="h-5 w-5 text-blue-400" />
                <h5 className="text-sm font-semibold text-blue-300">Recomendaciones</h5>
              </div>
              <ul className="space-y-2">
                {recommendations && recommendations.length > 0 ? (
                  recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                      <ArrowRight className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      <span>{rec}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-sm text-gray-500">No hay recomendaciones disponibles</li>
                )}
              </ul>
            </div>

            {/* Risks */}
            <div className="bg-yellow-900/10 rounded-lg p-4 border border-yellow-700/30">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                <h5 className="text-sm font-semibold text-yellow-300">Riesgos</h5>
              </div>
              <ul className="space-y-2">
                {risks && risks.length > 0 ? (
                  risks.map((risk, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                      <ArrowRight className="h-4 w-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                      <span>{risk}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-sm text-gray-500">No hay riesgos identificados</li>
                )}
              </ul>
            </div>
          </div>

          {/* Action Plan */}
          <div className="bg-green-900/10 rounded-lg p-4 border border-green-700/30">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="h-5 w-5 text-green-400" />
              <h5 className="text-sm font-semibold text-green-300">Plan de Acción</h5>
            </div>
            <ul className="space-y-2">
              {action_plan && action_plan.length > 0 ? (
                action_plan.map((action, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-green-600/20 text-green-400 text-xs font-bold flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{action}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-gray-500">No hay plan de acción disponible</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary-600/20 rounded-lg">
            <DollarSign className="h-8 w-8 text-primary-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">
              Competitive Pricing Strategy
            </h2>
            <p className="text-sm text-gray-400">
              Precios competitivos basados en el mercado P2P de Binance
            </p>
          </div>
        </div>
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-700 rounded w-1/3"></div>
            <div className="h-64 bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary-600/20 rounded-lg">
            <DollarSign className="h-8 w-8 text-primary-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">
              Competitive Pricing Strategy
            </h2>
            <p className="text-sm text-gray-400">
              Precios competitivos basados en el mercado P2P de Binance
            </p>
          </div>
        </div>
        <div className="bg-red-900/20 border border-red-500/50 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-8 w-8 text-red-400" />
            <div>
              <h3 className="text-xl font-bold text-red-300">Error</h3>
              <p className="text-red-400">{error}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-3 bg-primary-600/20 rounded-lg">
          <DollarSign className="h-8 w-8 text-primary-400" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white">
            Competitive Pricing Strategy
          </h2>
          <p className="text-sm text-gray-400">
            Precios competitivos basados en el mercado P2P de Binance
          </p>
        </div>
      </div>

      {/* COP Strategy */}
      {copStrategy && renderStrategyCard(copStrategy, 'COP')}

      {/* VES Strategy */}
      {vesStrategy && renderStrategyCard(vesStrategy, 'VES')}

      {/* Footer */}
      <div className="text-center text-xs text-gray-500">
        Actualizado cada minuto • Precios basados en VWAP del mercado P2P
      </div>
    </div>
  )
}
