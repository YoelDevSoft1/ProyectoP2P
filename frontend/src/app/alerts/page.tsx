'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { 
  Bell, 
  Home, 
  Filter, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  TrendingUp, 
  Zap,
  Activity,
  Brain,
  DollarSign,
  Menu,
  X,
  CheckCheck,
  RefreshCw,
  BarChart3,
  Settings
} from 'lucide-react'
import api from '@/lib/api'
import { formatColombiaDateTime } from '@/lib/dateUtils'
import { getCurrentColombiaTimeString } from '@/lib/dateUtils'

type AlertType = 'price_change' | 'spread_opportunity' | 'arbitrage_opportunity' | 'trade_completed' | 'trade_failed' | 'system_error' | 'ml_prediction' | 'high_volume' | 'all'
type AlertPriority = 'low' | 'medium' | 'high' | 'critical' | 'all'
type AlertStatus = 'all' | 'unread' | 'read'

interface Alert {
  id: number
  type: string
  priority: string
  title: string
  message: string
  is_read: boolean
  created_at: string
  asset?: string
  fiat?: string
  price?: number
  percentage?: number
}

export default function AlertsPage() {
  const [currentTime, setCurrentTime] = useState<string>('')
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false)
  const [page, setPage] = useState(0)
  const [limit] = useState(20)
  const [alertType, setAlertType] = useState<AlertType>('all')
  const [priority, setPriority] = useState<AlertPriority>('all')
  const [status, setStatus] = useState<AlertStatus>('unread')
  const [selectedAlerts, setSelectedAlerts] = useState<Set<number>>(new Set())

  const queryClient = useQueryClient()

  // Actualizar hora cada segundo
  useEffect(() => {
    const updateTime = () => {
      setCurrentTime(getCurrentColombiaTimeString())
    }
    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [])

  // Prevenir scroll cuando el sidebar está abierto
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [sidebarOpen])

  // Obtener alertas
  const { data: alertsData, isLoading, refetch } = useQuery({
    queryKey: ['alerts', page, limit, alertType, priority, status],
    queryFn: () => {
      const alertTypeParam = alertType === 'all' ? undefined : alertType
      const isReadParam = status === 'all' ? undefined : status === 'read'
      return api.getAlerts(page * limit, limit, alertTypeParam, isReadParam)
    },
    refetchInterval: 30000, // Actualizar cada 30 segundos
  })

  // Estadísticas de alertas
  const { data: allAlertsStats } = useQuery({
    queryKey: ['alerts-stats'],
    queryFn: async () => {
      const [all, unread, read] = await Promise.all([
        api.getAlerts(0, 1, undefined, undefined),
        api.getAlerts(0, 1, undefined, false),
        api.getAlerts(0, 1, undefined, true),
      ])
      return {
        total: all.total || 0,
        unread: unread.total || 0,
        read: read.total || 0,
      }
    },
    refetchInterval: 30000,
  })

  // Marcar alerta como leída
  const markAsRead = useMutation({
    mutationFn: (alertId: number) => api.markAlertAsRead(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alerts-stats'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setSelectedAlerts(new Set())
    },
  })

  // Marcar múltiples alertas como leídas
  const markMultipleAsRead = useMutation({
    mutationFn: async (alertIds: number[]) => {
      await Promise.all(alertIds.map(id => api.markAlertAsRead(id)))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alerts-stats'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setSelectedAlerts(new Set())
    },
  })

  const alerts: Alert[] = alertsData?.alerts || []
  const total = alertsData?.total || 0
  const totalPages = Math.ceil(total / limit)

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'spread_opportunity':
      case 'arbitrage_opportunity':
        return TrendingUp
      case 'trade_completed':
        return CheckCircle
      case 'trade_failed':
      case 'system_error':
        return XCircle
      case 'ml_prediction':
        return Brain
      case 'high_volume':
        return Activity
      case 'price_change':
        return DollarSign
      default:
        return AlertTriangle
    }
  }

  const getAlertColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return {
          border: 'border-red-500',
          bg: 'bg-red-500/10',
          text: 'text-red-400',
          badge: 'bg-red-500/20 text-red-400'
        }
      case 'high':
        return {
          border: 'border-orange-500',
          bg: 'bg-orange-500/10',
          text: 'text-orange-400',
          badge: 'bg-orange-500/20 text-orange-400'
        }
      case 'medium':
        return {
          border: 'border-yellow-500',
          bg: 'bg-yellow-500/10',
          text: 'text-yellow-400',
          badge: 'bg-yellow-500/20 text-yellow-400'
        }
      default:
        return {
          border: 'border-blue-500',
          bg: 'bg-blue-500/10',
          text: 'text-blue-400',
          badge: 'bg-blue-500/20 text-blue-400'
        }
    }
  }

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      price_change: 'Cambio de Precio',
      spread_opportunity: 'Oportunidad de Spread',
      arbitrage_opportunity: 'Oportunidad de Arbitraje',
      trade_completed: 'Trade Completado',
      trade_failed: 'Trade Fallido',
      system_error: 'Error del Sistema',
      ml_prediction: 'Predicción ML',
      high_volume: 'Alto Volumen'
    }
    return labels[type] || type
  }

  const toggleSelectAlert = (alertId: number) => {
    const newSelected = new Set(selectedAlerts)
    if (newSelected.has(alertId)) {
      newSelected.delete(alertId)
    } else {
      newSelected.add(alertId)
    }
    setSelectedAlerts(newSelected)
  }

  const selectAll = () => {
    if (selectedAlerts.size === alerts.length) {
      setSelectedAlerts(new Set())
    } else {
      setSelectedAlerts(new Set(alerts.map((a: Alert) => a.id)))
    }
  }

  const handleMarkSelectedAsRead = () => {
    if (selectedAlerts.size > 0) {
      markMultipleAsRead.mutate(Array.from(selectedAlerts))
    }
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 w-64 bg-gray-800 border-r border-gray-700 z-50
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-700">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-primary-500" />
            <span className="ml-2 text-xl font-bold text-white">P2P Dashboard</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-gray-400 hover:text-white"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-6 px-4 space-y-2">
          <Link
            href="/"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <Home className="h-5 w-5 mr-3" />
            Página Principal
          </Link>

          <Link
            href="/dashboard"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <BarChart3 className="h-5 w-5 mr-3" />
            Panel de Control
          </Link>

          <Link
            href="/monitoring"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <Activity className="h-5 w-5 mr-3" />
            Monitoreo
          </Link>

          <Link
            href="/alerts"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 bg-primary-600 text-white rounded-lg"
          >
            <Bell className="h-5 w-5 mr-3" />
            Alertas
            {allAlertsStats && allAlertsStats.unread > 0 && (
              <span className="ml-auto bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                {allAlertsStats.unread}
              </span>
            )}
          </Link>

          <Link
            href="/config"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
          >
            <Settings className="h-5 w-5 mr-3" />
            Configuración
          </Link>
        </nav>
      </div>

      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-30">
          <div className="px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="lg:hidden text-gray-400 hover:text-white"
                >
                  <Menu className="h-6 w-6" />
                </button>
                <div className="flex items-center gap-3">
                  <Bell className="h-6 w-6 sm:h-8 sm:w-8 text-primary-500" />
                  <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-white">
                    Alertas del Sistema
                  </h1>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <p className="text-white font-medium text-xs sm:text-sm lg:text-base hidden sm:block">
                  {currentTime || '--:--:--'}
                </p>
                <button
                  onClick={() => refetch()}
                  className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                  title="Actualizar"
                >
                  <RefreshCw className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Stats Cards */}
        {allAlertsStats && (
          <div className="px-4 sm:px-6 lg:px-8 py-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-4 sm:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Total Alertas</p>
                    <p className="text-2xl sm:text-3xl font-bold text-white mt-1">
                      {allAlertsStats.total.toLocaleString()}
                    </p>
                  </div>
                  <Bell className="h-8 w-8 sm:h-10 sm:w-10 text-blue-500" />
                </div>
              </div>
              <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-4 sm:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Sin Leer</p>
                    <p className="text-2xl sm:text-3xl font-bold text-orange-400 mt-1">
                      {allAlertsStats.unread.toLocaleString()}
                    </p>
                  </div>
                  <AlertTriangle className="h-8 w-8 sm:h-10 sm:w-10 text-orange-500" />
                </div>
              </div>
              <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-4 sm:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Leídas</p>
                    <p className="text-2xl sm:text-3xl font-bold text-green-400 mt-1">
                      {allAlertsStats.read.toLocaleString()}
                    </p>
                  </div>
                  <CheckCircle className="h-8 w-8 sm:h-10 sm:w-10 text-green-500" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters and Actions */}
        <div className="px-4 sm:px-6 lg:px-8 pb-6">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Filter className="h-5 w-5 text-gray-400" />
                <h2 className="text-lg font-semibold text-white">Filtros</h2>
              </div>
              {selectedAlerts.size > 0 && (
                <button
                  onClick={handleMarkSelectedAsRead}
                  disabled={markMultipleAsRead.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  <CheckCheck className="h-4 w-4" />
                  <span>Marcar {selectedAlerts.size} como leídas</span>
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Tipo de Alerta */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Tipo de Alerta</label>
                <select
                  value={alertType}
                  onChange={(e) => {
                    setAlertType(e.target.value as AlertType)
                    setPage(0)
                  }}
                  className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="all">Todos los tipos</option>
                  <option value="price_change">Cambio de Precio</option>
                  <option value="spread_opportunity">Oportunidad de Spread</option>
                  <option value="arbitrage_opportunity">Oportunidad de Arbitraje</option>
                  <option value="trade_completed">Trade Completado</option>
                  <option value="trade_failed">Trade Fallido</option>
                  <option value="system_error">Error del Sistema</option>
                  <option value="ml_prediction">Predicción ML</option>
                  <option value="high_volume">Alto Volumen</option>
                </select>
              </div>

              {/* Prioridad */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Prioridad</label>
                <select
                  value={priority}
                  onChange={(e) => {
                    setPriority(e.target.value as AlertPriority)
                    setPage(0)
                  }}
                  className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="all">Todas las prioridades</option>
                  <option value="critical">Crítica</option>
                  <option value="high">Alta</option>
                  <option value="medium">Media</option>
                  <option value="low">Baja</option>
                </select>
              </div>

              {/* Estado */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Estado</label>
                <select
                  value={status}
                  onChange={(e) => {
                    setStatus(e.target.value as AlertStatus)
                    setPage(0)
                  }}
                  className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="all">Todas</option>
                  <option value="unread">Sin leer</option>
                  <option value="read">Leídas</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Alerts List */}
        <div className="px-4 sm:px-6 lg:px-8 pb-8">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 sm:p-6">
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-24 bg-gray-700 rounded-lg"></div>
                  </div>
                ))}
              </div>
            ) : alerts.length === 0 ? (
              <div className="text-center py-12">
                <Bell className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">No hay alertas que mostrar</p>
                <p className="text-gray-500 text-sm mt-2">
                  {status === 'unread' ? 'No hay alertas sin leer' : 'Intenta cambiar los filtros'}
                </p>
              </div>
            ) : (
              <>
                {/* Select All */}
                <div className="mb-4 flex items-center justify-between">
                  <button
                    onClick={selectAll}
                    className="text-sm text-gray-400 hover:text-white transition-colors"
                  >
                    {selectedAlerts.size === alerts.length ? 'Deseleccionar todas' : 'Seleccionar todas'}
                  </button>
                  <p className="text-sm text-gray-400">
                    Mostrando {alerts.length} de {total} alertas
                  </p>
                </div>

                <div className="space-y-3">
                  {alerts.map((alert: Alert) => {
                    const Icon = getAlertIcon(alert.type)
                    const colors = getAlertColor(alert.priority)
                    const isSelected = selectedAlerts.has(alert.id)

                    return (
                      <div
                        key={alert.id}
                        className={`
                          border-l-4 ${colors.border} ${colors.bg} rounded-lg p-4 sm:p-6
                          transition-all duration-200
                          ${isSelected ? 'ring-2 ring-primary-500' : ''}
                          ${!alert.is_read ? 'hover:bg-opacity-20 cursor-pointer' : 'opacity-75'}
                        `}
                        onClick={() => !alert.is_read && markAsRead.mutate(alert.id)}
                      >
                        <div className="flex items-start gap-3 sm:gap-4">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => {
                              e.stopPropagation()
                              toggleSelectAlert(alert.id)
                            }}
                            className="mt-1 h-4 w-4 rounded border-gray-600 bg-gray-700 text-primary-600 focus:ring-primary-500"
                          />
                          <Icon className={`h-5 w-5 sm:h-6 sm:w-6 mt-0.5 flex-shrink-0 ${colors.text}`} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2 flex-wrap">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <p className="text-white font-semibold text-sm sm:text-base">
                                    {alert.title}
                                  </p>
                                  {!alert.is_read && (
                                    <span className="h-2 w-2 bg-primary-500 rounded-full animate-pulse"></span>
                                  )}
                                </div>
                                <p className="text-gray-400 text-xs sm:text-sm mt-1 line-clamp-2">
                                  {alert.message}
                                </p>
                                <div className="flex items-center gap-3 sm:gap-4 mt-2 flex-wrap">
                                  {alert.asset && alert.fiat && (
                                    <span className="text-xs text-gray-500">
                                      {alert.asset}/{alert.fiat}
                                    </span>
                                  )}
                                  {alert.price !== undefined && alert.price !== null && (
                                    <span className="text-xs text-gray-500">
                                      Precio: ${Number(alert.price).toLocaleString()}
                                    </span>
                                  )}
                                  {alert.percentage !== undefined && alert.percentage !== null && (
                                    <span className="text-xs text-gray-500">
                                      {alert.percentage > 0 ? '+' : ''}{Number(alert.percentage).toFixed(2)}%
                                    </span>
                                  )}
                                  <span className="text-xs text-gray-500">
                                    {formatColombiaDateTime(alert.created_at)}
                                  </span>
                                </div>
                              </div>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <span className={`text-xs px-2 py-1 rounded ${colors.badge}`}>
                                  {alert.priority}
                                </span>
                                <span className="text-xs px-2 py-1 rounded bg-gray-700 text-gray-300">
                                  {getTypeLabel(alert.type)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="mt-6 flex items-center justify-between">
                    <button
                      onClick={() => setPage(p => Math.max(0, p - 1))}
                      disabled={page === 0}
                      className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Anterior
                    </button>
                    <span className="text-sm text-gray-400">
                      Página {page + 1} de {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                      disabled={page >= totalPages - 1}
                      className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Siguiente
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

