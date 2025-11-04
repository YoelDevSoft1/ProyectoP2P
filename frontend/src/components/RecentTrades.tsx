'use client'

import { useQuery } from '@tanstack/react-query'
import { ArrowUpRight, ArrowDownRight, ExternalLink } from 'lucide-react'
import api from '@/lib/api'

export function RecentTrades() {
  const { data: tradesData, isLoading } = useQuery({
    queryKey: ['recent-trades'],
    queryFn: () => api.getTrades(0, 10),
    refetchInterval: 15000,
  })

  if (isLoading) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Operaciones Recientes</h3>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-16 bg-gray-700 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const trades = tradesData?.trades || []

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Operaciones Recientes</h3>
        <span className="text-sm text-gray-400">{trades.length} operaciones</span>
      </div>

      <div className="space-y-3">
        {trades.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No hay operaciones recientes</p>
        ) : (
          trades.slice(0, 5).map((trade: any) => (
            <div
              key={trade.id}
              className="bg-gray-900/50 border border-gray-700 rounded-lg p-4 hover:border-primary-500 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${
                    trade.type === 'buy'
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {trade.type === 'buy' ? (
                      <ArrowDownRight className="h-4 w-4" />
                    ) : (
                      <ArrowUpRight className="h-4 w-4" />
                    )}
                  </div>
                  <div>
                    <p className="text-white font-medium">
                      {trade.type.toUpperCase()} {trade.crypto_amount.toFixed(2)} {trade.asset}
                    </p>
                    <p className="text-sm text-gray-400">
                      {trade.fiat} • {new Date(trade.created_at).toLocaleDateString('es')}
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <p className={`font-semibold ${
                    trade.status === 'completed'
                      ? 'text-green-400'
                      : trade.status === 'pending'
                      ? 'text-yellow-400'
                      : 'text-red-400'
                  }`}>
                    {trade.actual_profit
                      ? `+$${trade.actual_profit.toFixed(2)}`
                      : trade.status}
                  </p>
                  {trade.is_automated && (
                    <span className="text-xs text-purple-400">AUTO</span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {trades.length > 5 && (
        <button className="mt-4 w-full flex items-center justify-center px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors">
          Ver todas las operaciones
          <ExternalLink className="ml-2 h-4 w-4" />
        </button>
      )}
    </div>
  )
}
