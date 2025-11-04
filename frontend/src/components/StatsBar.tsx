'use client'

import { useQuery } from '@tanstack/react-query'
import { DollarSign, TrendingUp, Activity, CheckCircle } from 'lucide-react'
import api from '@/lib/api'

type CurrencyBreakdown = {
  count: number
  volume: number
  profit: number
}

type TradeStats = {
  period_days: number
  total_trades: number
  completed: number
  pending: number
  failed: number
  automated_trades: number
  manual_trades: number
  total_profit: number
  total_volume_usd: number
  average_profit_per_trade: number
  success_rate: number
  by_currency?: {
    COP: CurrencyBreakdown
    VES: CurrencyBreakdown
  }
}

interface StatsBarProps {
  initialStats?: TradeStats | null
}

export function StatsBar({ initialStats }: StatsBarProps) {
  const { data: stats } = useQuery({
    queryKey: ['trade-stats'],
    queryFn: () => api.getTradeStats(7),
    refetchInterval: 30000, // Cada 30 segundos
    initialData: initialStats ?? undefined,
  })

  if (!stats) {
    return (
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-gray-800/50">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-gray-700 rounded-lg p-6 animate-pulse">
                <div className="h-4 bg-gray-600 rounded w-1/2 mb-3"></div>
                <div className="h-8 bg-gray-600 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        </div>
      </section>
    )
  }

  const statItems = [
    {
      label: 'Operaciones (7d)',
      value: stats.completed,
      icon: Activity,
      color: 'text-blue-500',
    },
    {
      label: 'Ganancia Total',
      value: `$${stats.total_profit.toFixed(2)}`,
      icon: DollarSign,
      color: 'text-green-500',
    },
    {
      label: 'Volumen USDT',
      value: stats.total_volume_usd.toFixed(0),
      icon: TrendingUp,
      color: 'text-purple-500',
    },
    {
      label: 'Tasa de Éxito',
      value: `${stats.success_rate.toFixed(1)}%`,
      icon: CheckCircle,
      color: 'text-primary-500',
    },
  ]

  return (
    <section className="py-12 px-4 sm:px-6 lg:px-8 bg-gray-800/50">
      <div className="max-w-7xl mx-auto">
        <h3 className="text-2xl font-bold text-white text-center mb-8">
          Estadísticas de la Última Semana
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {statItems.map((item, index) => {
            const Icon = item.icon
            return (
              <div
                key={index}
                className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 hover:border-primary-500 transition-colors"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-400">{item.label}</span>
                  <Icon className={`h-5 w-5 ${item.color}`} />
                </div>
                <p className="text-3xl font-bold text-white">{item.value}</p>
              </div>
            )
          })}
        </div>

        {/* Breakdown by Currency */}
        {stats.by_currency && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-white mb-4">🇨🇴 Colombia (COP)</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Operaciones:</span>
                  <span className="text-white font-medium">{stats.by_currency.COP.count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Volumen:</span>
                  <span className="text-white font-medium">{stats.by_currency.COP.volume.toFixed(2)} USDT</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Ganancia:</span>
                  <span className="text-green-500 font-medium">${stats.by_currency.COP.profit.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-white mb-4">🇻🇪 Venezuela (VES)</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Operaciones:</span>
                  <span className="text-white font-medium">{stats.by_currency.VES.count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Volumen:</span>
                  <span className="text-white font-medium">{stats.by_currency.VES.volume.toFixed(2)} USDT</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Ganancia:</span>
                  <span className="text-green-500 font-medium">${stats.by_currency.VES.profit.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
