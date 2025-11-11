'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { Bell, TrendingUp, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import api from '@/lib/api'
import { formatColombiaDateTime } from '@/lib/dateUtils'

export function AlertsList() {
  const queryClient = useQueryClient()

  const { data: alertsData, isLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => api.getAlerts(0, 10, undefined, false), // Solo no leídas
    refetchInterval: 15000,
  })

  const markAsRead = useMutation({
    mutationFn: (alertId: number) => api.markAlertAsRead(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  if (isLoading) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Alertas</h3>
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

  const alerts = alertsData?.alerts || []

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'spread_opportunity':
        return TrendingUp
      case 'trade_completed':
        return CheckCircle
      case 'trade_failed':
        return XCircle
      default:
        return AlertTriangle
    }
  }

  const getAlertColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'border-red-500 bg-red-500/10'
      case 'high':
        return 'border-orange-500 bg-orange-500/10'
      case 'medium':
        return 'border-yellow-500 bg-yellow-500/10'
      default:
        return 'border-blue-500 bg-blue-500/10'
    }
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Bell className="h-5 w-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-white">Alertas</h3>
        </div>
        <span className="text-sm text-gray-400">{alerts.length} sin leer</span>
      </div>

      <div className="space-y-3">
        {alerts.length === 0 ? (
          <div className="text-center py-8">
            <Bell className="h-12 w-12 text-gray-600 mx-auto mb-2" />
            <p className="text-gray-400">No hay alertas pendientes</p>
          </div>
        ) : (
          alerts.slice(0, 5).map((alert: any) => {
            const Icon = getAlertIcon(alert.type)
            const colorClass = getAlertColor(alert.priority)

            return (
              <div
                key={alert.id}
                className={`border-l-4 ${colorClass} rounded-lg p-4 cursor-pointer hover:bg-opacity-20 transition-colors`}
                onClick={() => markAsRead.mutate(alert.id)}
              >
                <div className="flex items-start space-x-3">
                  <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium text-sm">{alert.title}</p>
                    <p className="text-gray-400 text-xs mt-1 line-clamp-2">
                      {alert.message}
                    </p>
                    <p className="text-gray-500 text-xs mt-2">
                      {formatColombiaDateTime(alert.created_at)}
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <span className={`text-xs px-2 py-1 rounded ${
                      alert.priority === 'critical'
                        ? 'bg-red-500/20 text-red-400'
                        : alert.priority === 'high'
                        ? 'bg-orange-500/20 text-orange-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {alert.priority}
                    </span>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {alerts.length > 5 && (
        <Link
          href="/alerts"
          className="mt-4 w-full flex items-center justify-center px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
        >
          Ver todas las alertas
        </Link>
      )}
    </div>
  )
}
