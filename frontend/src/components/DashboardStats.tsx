'use client'

import { DollarSign, TrendingUp, Activity, AlertCircle } from 'lucide-react'

interface DashboardData {
  today: {
    total_trades: number
    completed_trades: number
    total_profit: number
    average_profit: number
  }
  week: {
    total_trades: number
    total_profit: number
    average_profit: number
  }
  alerts: {
    unread: number
  }
  latest_trade?: {
    id: number
    type: string
    status: string
    fiat: string
    amount: number
    created_at: string
  }
}

interface DashboardStatsProps {
  data?: DashboardData
}

export function DashboardStats({ data }: DashboardStatsProps) {
  if (!data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-800 rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-1/2 mb-3"></div>
            <div className="h-8 bg-gray-700 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    )
  }

  const stats = [
    {
      label: 'Ganancia Hoy',
      value: `$${data.today.total_profit.toFixed(2)}`,
      change: data.today.completed_trades > 0 ? `${data.today.completed_trades} operaciones` : 'Sin operaciones',
      icon: DollarSign,
      color: 'bg-green-500',
    },
    {
      label: 'Ganancia Semanal',
      value: `$${data.week.total_profit.toFixed(2)}`,
      change: `${data.week.total_trades} operaciones`,
      icon: TrendingUp,
      color: 'bg-blue-500',
    },
    {
      label: 'Promedio por Trade',
      value: `$${data.today.average_profit.toFixed(2)}`,
      change: 'Hoy',
      icon: Activity,
      color: 'bg-purple-500',
    },
    {
      label: 'Alertas Pendientes',
      value: data.alerts.unread,
      change: 'Sin revisar',
      icon: AlertCircle,
      color: data.alerts.unread > 0 ? 'bg-red-500' : 'bg-gray-500',
    },
  ]

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div
              key={index}
              className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-primary-500 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-gray-400">{stat.label}</span>
                <div className={`${stat.color} p-2 rounded-lg`}>
                  <Icon className="h-5 w-5 text-white" />
                </div>
              </div>
              <p className="text-3xl font-bold text-white mb-1">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.change}</p>
            </div>
          )
        })}
      </div>

      {/* Latest Trade Info */}
      {data.latest_trade && (
        <div className="bg-gradient-to-r from-primary-900/20 to-primary-800/20 border border-primary-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-2">Última Operación</h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-300">
                Trade #{data.latest_trade.id} - {data.latest_trade.type.toUpperCase()} {data.latest_trade.amount} USDT/{data.latest_trade.fiat}
              </p>
              <p className="text-sm text-gray-400 mt-1">
                {new Date(data.latest_trade.created_at).toLocaleString('es')}
              </p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              data.latest_trade.status === 'completed'
                ? 'bg-green-500/20 text-green-400 border border-green-500'
                : data.latest_trade.status === 'pending'
                ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500'
                : 'bg-red-500/20 text-red-400 border border-red-500'
            }`}>
              {data.latest_trade.status}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
