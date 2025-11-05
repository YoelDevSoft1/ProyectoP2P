'use client'

import { useEffect, useState } from 'react'
import { TrendingUp, ArrowRight, Zap, AlertCircle, CheckCircle, XCircle } from 'lucide-react'

interface Opportunity {
  type: string
  route: string
  initial_investment: {
    amount: number
    currency: string
  }
  final_position: {
    amount: number
    currency: string
  }
  asset: string
  profit: {
    absolute: number
    roi_percentage: number
  }
  is_profitable: boolean
  step_1: any
  step_2: any
  timestamp: string
}

export function TriangleArbitrageOpportunities() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [optimalStrategy, setOptimalStrategy] = useState<any>(null)

  useEffect(() => {
    fetchOpportunities()
    const interval = setInterval(fetchOpportunities, 30000) // Refresh every 30s

    return () => clearInterval(interval)
  }, [])

  const fetchOpportunities = async () => {
    try {
      // Fetch all opportunities
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/top-opportunities?limit=10`,
        {
          headers: {
            'ngrok-skip-browser-warning': 'true',
          },
        }
      )
      const data = await response.json()

      if (data.success) {
        setOpportunities(data.opportunities || [])
      }

      // Fetch optimal strategy
      const strategyResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/triangle-arbitrage/optimal-strategy`,
        {
          headers: {
            'ngrok-skip-browser-warning': 'true',
          },
        }
      )
      const strategyData = await strategyResponse.json()

      if (strategyData.success) {
        setOptimalStrategy(strategyData)
      }
    } catch (error) {
      console.error('Error fetching opportunities:', error)
    } finally {
      setLoading(false)
    }
  }

  const getRecommendationIcon = (recommendation: string) => {
    if (recommendation?.includes('EJECUTAR INMEDIATAMENTE') || recommendation?.includes('EXCELENTE')) {
      return <Zap className="h-5 w-5 text-yellow-400 animate-pulse" />
    }
    if (recommendation?.includes('EJECUTAR') || recommendation?.includes('BUENA')) {
      return <CheckCircle className="h-5 w-5 text-green-400" />
    }
    if (recommendation?.includes('CONSIDERAR') || recommendation?.includes('EVALUAR')) {
      return <AlertCircle className="h-5 w-5 text-yellow-400" />
    }
    return <XCircle className="h-5 w-5 text-red-400" />
  }

  const getRecommendationColor = (recommendation: string) => {
    if (recommendation?.includes('EJECUTAR INMEDIATAMENTE')) {
      return 'bg-yellow-600/20 border-yellow-500/50 text-yellow-300'
    }
    if (recommendation?.includes('EJECUTAR')) {
      return 'bg-green-600/20 border-green-500/50 text-green-300'
    }
    if (recommendation?.includes('CONSIDERAR')) {
      return 'bg-orange-600/20 border-orange-500/50 text-orange-300'
    }
    return 'bg-red-600/20 border-red-500/50 text-red-300'
  }

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-700 rounded w-1/2"></div>
          <div className="h-32 bg-gray-700 rounded"></div>
          <div className="h-32 bg-gray-700 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp className="h-8 w-8 text-primary-400" />
          <div>
            <h2 className="text-2xl font-bold text-white">
              Triangle Arbitrage Opportunities
            </h2>
            <p className="text-sm text-gray-400">
              Oportunidades de arbitraje triangular en tiempo real
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 px-4 py-2 bg-primary-600/20 border border-primary-500/30 rounded-lg">
          <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-primary-300 font-medium">Live</span>
        </div>
      </div>

      {/* Optimal Strategy Card (if available) */}
      {optimalStrategy && optimalStrategy.best_opportunity && (
        <div className="bg-gradient-to-r from-yellow-900/30 to-orange-900/30 rounded-xl p-6 border-2 border-yellow-500/50">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-yellow-600/20 rounded-lg">
              <Zap className="h-8 w-8 text-yellow-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="text-xl font-bold text-white">Mejor Oportunidad</h3>
                <span className="px-3 py-1 bg-yellow-600/30 border border-yellow-500/50 rounded-full text-xs font-bold text-yellow-300">
                  RECOMENDADO
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Ruta</p>
                  <p className="text-lg font-bold text-white">
                    {optimalStrategy.best_opportunity.route}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400 mb-1">ROI Esperado</p>
                  <p className="text-2xl font-bold text-yellow-400">
                    {optimalStrategy.best_opportunity.profit?.roi_percentage?.toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400 mb-1">Liquidez</p>
                  <p className={`text-lg font-semibold ${
                    optimalStrategy.liquidity?.is_liquid ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {optimalStrategy.liquidity?.is_liquid ? 'SUFICIENTE' : 'INSUFICIENTE'}
                  </p>
                </div>
              </div>

              <div className={`p-4 rounded-lg border ${getRecommendationColor(optimalStrategy.recommendation)}`}>
                <div className="flex items-center gap-2 mb-2">
                  {getRecommendationIcon(optimalStrategy.recommendation)}
                  <span className="font-semibold">Recomendación</span>
                </div>
                <p className="text-sm">
                  {optimalStrategy.recommendation}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Opportunities List */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <div className="px-6 py-4 bg-gray-900/50 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white">
            Todas las Oportunidades ({opportunities.length})
          </h3>
        </div>

        {opportunities.length === 0 ? (
          <div className="p-12 text-center">
            <AlertCircle className="h-16 w-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-400 mb-2">
              No hay oportunidades disponibles
            </h3>
            <p className="text-gray-500">
              Las oportunidades aparecerán cuando las condiciones de mercado sean favorables
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-700">
            {opportunities.map((opp, index) => (
              <div
                key={index}
                className={`p-6 hover:bg-gray-700/30 transition-colors ${
                  opp.is_profitable ? '' : 'opacity-50'
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${
                      opp.profit.roi_percentage >= 3 ? 'bg-green-600/20' :
                      opp.profit.roi_percentage >= 1 ? 'bg-blue-600/20' : 'bg-gray-600/20'
                    }`}>
                      <TrendingUp className={`h-5 w-5 ${
                        opp.profit.roi_percentage >= 3 ? 'text-green-400' :
                        opp.profit.roi_percentage >= 1 ? 'text-blue-400' : 'text-gray-400'
                      }`} />
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold text-white">
                        {opp.route}
                      </h4>
                      <p className="text-sm text-gray-400">
                        Asset: {opp.asset}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <p className="text-sm text-gray-400 mb-1">ROI</p>
                    <p className={`text-2xl font-bold ${
                      opp.profit.roi_percentage >= 3 ? 'text-green-400' :
                      opp.profit.roi_percentage >= 1 ? 'text-blue-400' :
                      opp.profit.roi_percentage > 0 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {opp.profit.roi_percentage.toFixed(2)}%
                    </p>
                  </div>
                </div>

                {/* Execution Steps */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  {/* Step 1 */}
                  <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary-600/20 text-primary-400 text-xs font-bold">
                        1
                      </span>
                      <span className="text-sm font-medium text-gray-300">
                        {opp.step_1?.action}
                      </span>
                    </div>
                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Price:</span>
                        <span className="text-white font-medium">
                          {opp.step_1?.price?.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Amount:</span>
                        <span className="text-white font-medium">
                          {opp.step_1?.amount?.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary-600/20 text-primary-400 text-xs font-bold">
                        2
                      </span>
                      <span className="text-sm font-medium text-gray-300">
                        {opp.step_2?.action}
                      </span>
                    </div>
                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Price:</span>
                        <span className="text-white font-medium">
                          {opp.step_2?.price?.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Final Amount:</span>
                        <span className="text-white font-medium">
                          {opp.step_2?.amount?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Profit Summary */}
                <div className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg border border-gray-700">
                  <div className="flex items-center gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Inversión: </span>
                      <span className="text-white font-medium">
                        {opp.initial_investment.amount.toLocaleString()} {opp.initial_investment.currency}
                      </span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-gray-600" />
                    <div>
                      <span className="text-gray-400">Final: </span>
                      <span className="text-white font-medium">
                        {opp.final_position.amount.toLocaleString(undefined, { maximumFractionDigits: 0 })} {opp.final_position.currency}
                      </span>
                    </div>
                  </div>

                  {opp.is_profitable ? (
                    <span className="px-3 py-1 bg-green-600/20 border border-green-500/50 rounded-full text-xs font-medium text-green-300">
                      RENTABLE
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-red-600/20 border border-red-500/50 rounded-full text-xs font-medium text-red-300">
                      NO RENTABLE
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer note */}
      <div className="text-center text-xs text-gray-500">
        Actualizado cada 30 segundos • Las oportunidades son indicativas y están sujetas a disponibilidad de liquidez
      </div>
    </div>
  )
}
