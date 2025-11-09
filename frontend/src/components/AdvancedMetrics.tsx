'use client'

import { useQuery } from '@tanstack/react-query'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Target,
  Zap,
  Shield,
  Clock,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'
import api from '@/lib/api'
import { TradeStats } from '@/types/prices'

export function AdvancedMetrics() {
  const { data: stats } = useQuery({
    queryKey: ['trade-stats-advanced'],
    queryFn: () => api.getTradeStats(30), // Últimos 30 días
    refetchInterval: 30000,
  })

  const { data: todayStats } = useQuery({
    queryKey: ['trade-stats-today'],
    queryFn: () => api.getTradeStats(1), // Hoy
    refetchInterval: 10000,
  })

  if (!stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-800 rounded-xl p-6 animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-700 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-700 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    )
  }

  // Calcular métricas avanzadas
  const dailyAverageProfit = stats.total_profit / (stats.period_days || 1)
  const profitPerTrade = stats.average_profit_per_trade || 0
  const winRate = stats.success_rate || 0
  const totalVolume = stats.total_volume_usd || 0
  const volumePerDay = totalVolume / (stats.period_days || 1)

  // Comparación con hoy
  const todayProfit = todayStats?.total_profit || 0
  const profitChange = todayStats ? ((todayProfit - dailyAverageProfit) / dailyAverageProfit) * 100 : 0

  const metrics = [
    {
      id: 'total-profit',
      label: 'Ganancia Total (30d)',
      value: `$${stats.total_profit.toFixed(2)}`,
      subValue: `Promedio diario: $${dailyAverageProfit.toFixed(2)}`,
      icon: DollarSign,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20',
      borderColor: 'border-green-500/50',
      trend: profitChange > 0 ? 'up' : profitChange < 0 ? 'down' : 'neutral',
      trendValue: profitChange !== 0 ? `${profitChange > 0 ? '+' : ''}${profitChange.toFixed(1)}%` : null,
    },
    {
      id: 'win-rate',
      label: 'Tasa de Éxito',
      value: `${winRate.toFixed(1)}%`,
      subValue: `${stats.completed || 0} de ${stats.total_trades || 0} operaciones`,
      icon: Target,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
      borderColor: 'border-blue-500/50',
      trend: winRate >= 80 ? 'up' : winRate >= 60 ? 'neutral' : 'down',
    },
    {
      id: 'volume',
      label: 'Volumen Total',
      value: `$${totalVolume.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
      subValue: `Promedio: $${volumePerDay.toLocaleString('en-US', { minimumFractionDigits: 0 })}/día`,
      icon: BarChart3,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20',
      borderColor: 'border-purple-500/50',
    },
    {
      id: 'profit-per-trade',
      label: 'Ganancia por Trade',
      value: `$${profitPerTrade.toFixed(2)}`,
      subValue: `Basado en ${stats.completed || 0} operaciones completadas`,
      icon: Zap,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/20',
      borderColor: 'border-yellow-500/50',
    },
    {
      id: 'total-trades',
      label: 'Operaciones Totales',
      value: stats.total_trades.toString(),
      subValue: `${stats.completed || 0} completadas, ${stats.pending || 0} pendientes`,
      icon: Activity,
      color: 'text-indigo-400',
      bgColor: 'bg-indigo-500/20',
      borderColor: 'border-indigo-500/50',
    },
    {
      id: 'automation-rate',
      label: 'Tasa de Automatización',
      value: stats.total_trades > 0
        ? `${((stats.automated_trades || 0) / stats.total_trades) * 100}%`
        : '0%',
      subValue: `${stats.automated_trades || 0} automatizadas, ${stats.manual_trades || 0} manuales`,
      icon: Zap,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/20',
      borderColor: 'border-orange-500/50',
    },
    {
      id: 'failure-rate',
      label: 'Tasa de Fallo',
      value: stats.total_trades > 0
        ? `${((stats.failed || 0) / stats.total_trades) * 100}%`
        : '0%',
      subValue: `${stats.failed || 0} fallidas de ${stats.total_trades || 0} totales`,
      icon: Shield,
      color: stats.failed && stats.failed > stats.total_trades * 0.1 ? 'text-red-400' : 'text-gray-400',
      bgColor: stats.failed && stats.failed > stats.total_trades * 0.1 ? 'bg-red-500/20' : 'bg-gray-500/20',
      borderColor: stats.failed && stats.failed > stats.total_trades * 0.1 ? 'border-red-500/50' : 'border-gray-500/50',
    },
    {
      id: 'avg-time',
      label: 'Tiempo Promedio',
      value: '< 10 min',
      subValue: 'Tiempo promedio por operación',
      icon: Clock,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/20',
      borderColor: 'border-cyan-500/50',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Métricas Avanzadas</h2>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock className="h-4 w-4" />
          <span>Actualizado cada 30 segundos</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric) => {
          const Icon = metric.icon
          return (
            <div
              key={metric.id}
              className={`bg-gradient-to-br from-gray-800 to-gray-900 border ${metric.borderColor} rounded-xl p-6 hover:shadow-xl hover:scale-105 transition-all duration-300`}
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-gray-400 font-medium">{metric.label}</span>
                <div className={`${metric.bgColor} p-2 rounded-lg`}>
                  <Icon className={`h-5 w-5 ${metric.color}`} />
                </div>
              </div>

              <div className="flex items-end gap-2 mb-2">
                <p className={`text-3xl font-bold ${metric.color}`}>{metric.value}</p>
                {metric.trend && metric.trendValue && (
                  <div
                    className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium mb-1 ${
                      metric.trend === 'up'
                        ? 'bg-green-500/20 text-green-400'
                        : metric.trend === 'down'
                        ? 'bg-red-500/20 text-red-400'
                        : 'bg-gray-500/20 text-gray-400'
                    }`}
                  >
                    {metric.trend === 'up' ? (
                      <ArrowUpRight className="h-3 w-3" />
                    ) : metric.trend === 'down' ? (
                      <ArrowDownRight className="h-3 w-3" />
                    ) : null}
                    {metric.trendValue}
                  </div>
                )}
              </div>

              <p className="text-xs text-gray-500">{metric.subValue}</p>
            </div>
          )
        })}
      </div>

      {/* Breakdown por Moneda */}
      {stats.by_currency && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(stats.by_currency).map(([currency, data]) => (
            <div
              key={currency}
              className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">
                  {currency === 'COP' ? '🇨🇴 Colombia (COP)' : '🇻🇪 Venezuela (VES)'}
                </h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-400">Profit:</span>
                  <span className="text-lg font-bold text-green-400">${data.profit.toFixed(2)}</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-gray-400 mb-1">Operaciones</p>
                  <p className="text-xl font-bold text-white">{data.count}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 mb-1">Volumen</p>
                  <p className="text-xl font-bold text-white">{data.volume.toFixed(0)} USDT</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 mb-1">Avg Profit</p>
                  <p className="text-xl font-bold text-green-400">
                    ${data.count > 0 ? (data.profit / data.count).toFixed(2) : '0.00'}
                  </p>
                </div>
              </div>

              {/* Barra de progreso visual */}
              <div className="mt-4">
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Rendimiento</span>
                  <span>{data.count > 0 ? ((data.profit / stats.total_profit) * 100).toFixed(1) : 0}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      currency === 'COP' ? 'bg-blue-500' : 'bg-yellow-500'
                    }`}
                    style={{
                      width: `${data.count > 0 ? (data.profit / stats.total_profit) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

