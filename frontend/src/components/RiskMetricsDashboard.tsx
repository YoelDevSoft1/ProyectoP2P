'use client'

import { useState } from 'react'
import { AlertTriangle, Shield, TrendingDown, Target, Award, Activity } from 'lucide-react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface RiskMetricsProps {
  returns?: number[]
  equityCurve?: number[]
  trades?: Array<{
    profit: number
    is_win: boolean
  }>
}

export function RiskMetricsDashboard({ returns = [], equityCurve = [], trades = [] }: RiskMetricsProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'detailed'>('overview')
  const [metrics, setMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // Calcular métricas si hay datos
  const calculateMetrics = async () => {
    if (returns.length < 30 || equityCurve.length < 10 || trades.length < 10) {
      return
    }

    setLoading(true)

    try {
      // Calcular VaR
      const varResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/risk/calculate-var`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true',
          },
          body: JSON.stringify({ returns, confidence_level: 0.95, time_horizon_days: 1 }),
        }
      )
      const varData = await varResponse.json()

      // Calcular Sharpe
      const sharpeResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/risk/calculate-sharpe`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true',
          },
          body: JSON.stringify({ returns }),
        }
      )
      const sharpeData = await sharpeResponse.json()

      // Calcular Sortino
      const sortinoResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/risk/calculate-sortino`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true',
          },
          body: JSON.stringify({ returns }),
        }
      )
      const sortinoData = await sortinoResponse.json()

      // Calcular Drawdown
      const drawdownResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/risk/calculate-drawdown`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true',
          },
          body: JSON.stringify({ equity_curve: equityCurve }),
        }
      )
      const drawdownData = await drawdownResponse.json()

      // Calcular Trading Metrics
      const tradingResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/analytics/risk/trading-metrics`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true',
          },
          body: JSON.stringify({ trades }),
        }
      )
      const tradingData = await tradingResponse.json()

      setMetrics({
        var: varData,
        sharpe: sharpeData,
        sortino: sortinoData,
        drawdown: drawdownData,
        trading: tradingData,
      })
    } catch (error) {
      console.error('Error calculating risk metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  // Preparar datos de equity curve para el chart
  const equityChartData = equityCurve.map((value, index) => ({
    period: index,
    equity: value,
  }))

  // Preparar datos de drawdown
  const drawdownChartData = equityCurve.map((value, index, arr) => {
    const peak = Math.max(...arr.slice(0, index + 1))
    const drawdown = ((value - peak) / peak) * 100
    return {
      period: index,
      drawdown,
    }
  })

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'EXCELENTE':
        return 'text-green-400'
      case 'MUY BUENO':
      case 'BUENO':
        return 'text-blue-400'
      case 'ACEPTABLE':
      case 'MODERADO':
        return 'text-yellow-400'
      case 'POBRE':
      case 'BAJO':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="h-8 w-8 text-primary-400" />
          <div>
            <h2 className="text-2xl font-bold text-white">Risk Management Dashboard</h2>
            <p className="text-sm text-gray-400">
              Métricas profesionales de gestión de riesgo
            </p>
          </div>
        </div>

        <button
          onClick={calculateMetrics}
          disabled={loading || returns.length < 30}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all"
        >
          {loading ? 'Calculando...' : 'Calcular Métricas'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-700">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 font-medium transition-all ${
            activeTab === 'overview'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('detailed')}
          className={`px-4 py-2 font-medium transition-all ${
            activeTab === 'detailed'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          Detailed Analysis
        </button>
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Key Risk Metrics Grid */}
          {metrics && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* VaR Card */}
              {metrics.var?.success && (
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-red-400" />
                      <h3 className="text-lg font-semibold text-white">Value at Risk</h3>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-400">VaR (95% confianza)</p>
                      <p className="text-3xl font-bold text-red-400">
                        {Math.abs(metrics.var.var_parametric).toFixed(2)}%
                      </p>
                    </div>
                    <div className="pt-3 border-t border-gray-700">
                      <p className="text-xs text-gray-500">
                        {metrics.var.interpretation}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Sharpe Ratio Card */}
              {metrics.sharpe?.success && (
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Award className="h-5 w-5 text-blue-400" />
                      <h3 className="text-lg font-semibold text-white">Sharpe Ratio</h3>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-400">Anualizado</p>
                      <p className={`text-3xl font-bold ${getRatingColor(metrics.sharpe.rating)}`}>
                        {metrics.sharpe.sharpe_ratio_annualized.toFixed(2)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getRatingColor(metrics.sharpe.rating)}`}>
                        {metrics.sharpe.rating}
                      </span>
                    </div>
                    <div className="pt-3 border-t border-gray-700">
                      <p className="text-xs text-gray-500">
                        {metrics.sharpe.interpretation}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Sortino Ratio Card */}
              {metrics.sortino?.success && (
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-green-400" />
                      <h3 className="text-lg font-semibold text-white">Sortino Ratio</h3>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-400">Anualizado</p>
                      <p className={`text-3xl font-bold ${getRatingColor(metrics.sortino.rating)}`}>
                        {metrics.sortino.sortino_ratio_annualized.toFixed(2)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getRatingColor(metrics.sortino.rating)}`}>
                        {metrics.sortino.rating}
                      </span>
                    </div>
                    <div className="pt-3 border-t border-gray-700">
                      <p className="text-xs text-gray-500">
                        Períodos negativos: {metrics.sortino.downside_percentage.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Maximum Drawdown Card */}
              {metrics.drawdown?.success && (
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <TrendingDown className="h-5 w-5 text-orange-400" />
                      <h3 className="text-lg font-semibold text-white">Max Drawdown</h3>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-400">Pérdida máxima</p>
                      <p className="text-3xl font-bold text-orange-400">
                        {Math.abs(metrics.drawdown.maximum_drawdown_pct).toFixed(2)}%
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getRatingColor(metrics.drawdown.risk_level)}`}>
                        {metrics.drawdown.risk_level} RIESGO
                      </span>
                    </div>
                    <div className="pt-3 border-t border-gray-700">
                      <p className="text-xs text-gray-500">
                        Duración: {metrics.drawdown.duration_days} períodos
                      </p>
                      {metrics.drawdown.recovered && (
                        <p className="text-xs text-green-400 mt-1">
                          ✓ Recuperado en {metrics.drawdown.recovery_days} períodos
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Trading Metrics Card */}
              {metrics.trading?.success && (
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Activity className="h-5 w-5 text-purple-400" />
                      <h3 className="text-lg font-semibold text-white">Win Rate</h3>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-400">Tasa de éxito</p>
                      <p className="text-3xl font-bold text-purple-400">
                        {metrics.trading.win_rate_pct.toFixed(1)}%
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <p className="text-gray-500">Wins</p>
                        <p className="text-green-400 font-medium">{metrics.trading.winning_trades}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Losses</p>
                        <p className="text-red-400 font-medium">{metrics.trading.losing_trades}</p>
                      </div>
                    </div>
                    <div className="pt-3 border-t border-gray-700">
                      <p className="text-xs text-gray-500">
                        Profit Factor: {metrics.trading.profit_factor.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Risk:Reward Card */}
              {metrics.trading?.success && (
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-cyan-400" />
                      <h3 className="text-lg font-semibold text-white">Risk:Reward</h3>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-400">R:R Ratio</p>
                      <p className="text-3xl font-bold text-cyan-400">
                        1:{metrics.trading.risk_reward_ratio.toFixed(2)}
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <p className="text-gray-500">Avg Win</p>
                        <p className="text-green-400 font-medium">
                          {metrics.trading.average_win.toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Avg Loss</p>
                        <p className="text-red-400 font-medium">
                          {Math.abs(metrics.trading.average_loss).toFixed(2)}
                        </p>
                      </div>
                    </div>
                    <div className="pt-3 border-t border-gray-700">
                      <p className="text-xs text-gray-500">
                        Expectancy: {metrics.trading.expectancy.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Charts */}
          {equityCurve.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Equity Curve */}
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Equity Curve</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={equityChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="period" stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
                      <YAxis stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1F2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="equity"
                        stroke="#10B981"
                        fill="#10B98150"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Drawdown Chart */}
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Drawdown Analysis</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={drawdownChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="period" stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
                      <YAxis stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1F2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                        }}
                        formatter={(value: number) => [`${value.toFixed(2)}%`, 'Drawdown']}
                      />
                      <ReferenceLine y={0} stroke="#6B7280" strokeDasharray="3 3" />
                      <Area
                        type="monotone"
                        dataKey="drawdown"
                        stroke="#EF4444"
                        fill="#EF444450"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {activeTab === 'detailed' && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <p className="text-gray-400">
            Análisis detallado disponible próximamente...
          </p>
        </div>
      )}

      {!metrics && !loading && (
        <div className="bg-gray-800/50 rounded-xl p-12 border border-gray-700 text-center">
          <Shield className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-400 mb-2">
            No hay datos de riesgo
          </h3>
          <p className="text-gray-500 mb-4">
            Necesitas al menos 30 retornos, 10 puntos de equity y 10 trades para calcular métricas de riesgo
          </p>
          <p className="text-sm text-gray-600">
            Los datos se generarán automáticamente a medida que operes
          </p>
        </div>
      )}
    </div>
  )
}
