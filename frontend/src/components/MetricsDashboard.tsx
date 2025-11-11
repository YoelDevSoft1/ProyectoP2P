'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '@/lib/api'
import { parsePrometheusMetrics, getMetricValue, getMetricValues, sumMetricValues } from '../lib/prometheus'
import { Loader2, TrendingUp, Activity, Database, MessageSquare } from 'lucide-react'

interface MetricData {
  time: string
  value: number
  [key: string]: any
}

export function MetricsDashboard() {
  const [metrics, setMetrics] = useState<Map<string, any>>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchMetrics = async () => {
    try {
      setLoading(true)
      const metricsText = await api.getPrometheusMetrics()
      if (metricsText) {
        const parsed = parsePrometheusMetrics(metricsText)
        setMetrics(parsed)
        setLastUpdate(new Date())
        setError(null)
      }
    } catch (err: any) {
      setError(err.message || 'Error al obtener métricas')
      console.error('Metrics error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMetrics()
    // Actualizar cada 15 segundos
    const interval = setInterval(fetchMetrics, 15000)
    return () => clearInterval(interval)
  }, [])

  // Preparar datos para gráficos
  const httpRequestsData = getMetricValues(metrics, 'http_requests_total')
  const httpDurationData = getMetricValues(metrics, 'http_request_duration_seconds')
  const dbQueriesData = getMetricValues(metrics, 'db_queries_total')
  const redisOpsData = getMetricValues(metrics, 'redis_operations_total')
  const celeryTasksData = getMetricValues(metrics, 'celery_tasks_total')
  const tradesData = getMetricValues(metrics, 'trades_executed_total')
  const arbitrageData = getMetricValues(metrics, 'active_arbitrage_opportunities')

  // Obtener valores totales
  const totalHttpRequests = sumMetricValues(metrics, 'http_requests_total')
  const totalDbQueries = sumMetricValues(metrics, 'db_queries_total')
  const totalRedisOps = sumMetricValues(metrics, 'redis_operations_total')
  const totalCeleryTasks = sumMetricValues(metrics, 'celery_tasks_total')
  const totalTrades = sumMetricValues(metrics, 'trades_executed_total')

  // Obtener valores actuales
  const httpDurationP95 = getMetricValue(metrics, 'http_request_duration_seconds')
  const activeArbitrage = getMetricValue(metrics, 'active_arbitrage_opportunities')

  if (loading && metrics.size === 0) {
    return (
      <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      </div>
    )
  }

  if (error && metrics.size === 0) {
    return (
      <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-6">
        <div className="text-center text-red-400">
          <p>{error}</p>
          <button
            onClick={fetchMetrics}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  const stats = [
    {
      name: 'HTTP Requests',
      value: totalHttpRequests.toLocaleString(),
      icon: Activity,
      color: 'text-blue-400',
      bgColor: 'bg-blue-900/30',
      borderColor: 'border-blue-500/50',
    },
    {
      name: 'DB Queries',
      value: totalDbQueries.toLocaleString(),
      icon: Database,
      color: 'text-green-400',
      bgColor: 'bg-green-900/30',
      borderColor: 'border-green-500/50',
    },
    {
      name: 'Redis Ops',
      value: totalRedisOps.toLocaleString(),
      icon: Activity,
      color: 'text-red-400',
      bgColor: 'bg-red-900/30',
      borderColor: 'border-red-500/50',
    },
    {
      name: 'Celery Tasks',
      value: totalCeleryTasks.toLocaleString(),
      icon: MessageSquare,
      color: 'text-purple-400',
      bgColor: 'bg-purple-900/30',
      borderColor: 'border-purple-500/50',
    },
    {
      name: 'Trades',
      value: totalTrades.toLocaleString(),
      icon: TrendingUp,
      color: 'text-orange-400',
      bgColor: 'bg-orange-900/30',
      borderColor: 'border-orange-500/50',
    },
    {
      name: 'Active Arbitrage',
      value: activeArbitrage?.toFixed(0) || '0',
      icon: TrendingUp,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-900/30',
      borderColor: 'border-yellow-500/50',
    },
  ]

  // Debug: Log available metrics y valores
  useEffect(() => {
    if (metrics.size > 0) {
      const metricNames = Array.from(metrics.keys())
      console.log('📊 Available metrics:', metricNames)
      
      // Log detallado de cada métrica que buscamos
      const trackedMetrics = [
        'http_requests_total',
        'db_queries_total', 
        'redis_operations_total',
        'celery_tasks_total',
        'trades_executed_total',
        'active_arbitrage_opportunities'
      ]
      
      trackedMetrics.forEach(metricName => {
        const series = metrics.get(metricName)
        if (series) {
          const sum = sumMetricValues(metrics, metricName)
          console.log(`  ${metricName}:`, {
            series: series.length,
            sum,
            sample: series.slice(0, 2).map(s => ({
              value: s.value,
              labels: s.labels
            }))
          })
        } else {
          console.log(`  ${metricName}: NOT FOUND`)
        }
      })
    }
  }, [metrics])

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          // Obtener el valor real de la métrica
          let metricValue = stat.value
          let metricName = ''
          
          // Mapear nombres de estadísticas a nombres de métricas
          const metricMap: Record<string, string> = {
            'HTTP Requests': 'http_requests_total',
            'DB Queries': 'db_queries_total',
            'Redis Ops': 'redis_operations_total',
            'Celery Tasks': 'celery_tasks_total',
            'Trades': 'trades_executed_total',
            'Active Arbitrage': 'active_arbitrage_opportunities',
          }
          
          metricName = metricMap[stat.name] || ''
          const metricSeries = metricName ? metrics.get(metricName) : null
          
          // Si la métrica existe pero el valor es 0, mostrar información de depuración
          const hasMetricButZero = metricSeries && metricSeries.length > 0 && parseFloat(stat.value.replace(/,/g, '')) === 0
          
          return (
            <div
              key={stat.name}
              className={`${stat.bgColor} rounded-lg p-4 border ${stat.borderColor} hover:opacity-80 transition-opacity relative`}
              title={hasMetricButZero ? `Métrica encontrada con ${metricSeries?.length} series pero suma = 0` : undefined}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-xs sm:text-sm text-gray-400">{stat.name}</p>
                  <p className="text-xl sm:text-2xl font-bold text-white mt-1">{stat.value}</p>
                  {hasMetricButZero && process.env.NODE_ENV === 'development' && (
                    <p className="text-xs text-yellow-400 mt-1">
                      {metricSeries?.length} series
                    </p>
                  )}
                </div>
                <Icon className={`w-6 h-6 sm:w-8 sm:h-8 ${stat.color} flex-shrink-0`} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* HTTP Requests */}
        <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-4 text-white">HTTP Requests</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={httpRequestsData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }} 
              />
              <Legend wrapperStyle={{ color: '#F3F4F6' }} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#60A5FA"
                fill="#60A5FA"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* HTTP Duration */}
        <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-4 text-white">HTTP Request Duration (p95)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={httpDurationData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }} 
              />
              <Legend wrapperStyle={{ color: '#F3F4F6' }} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#34D399"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* DB Queries */}
        <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-4 text-white">Database Queries</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dbQueriesData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }} 
              />
              <Legend wrapperStyle={{ color: '#F3F4F6' }} />
              <Bar dataKey="value" fill="#F87171" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Redis Operations */}
        <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-4 text-white">Redis Operations</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={redisOpsData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }} 
              />
              <Legend wrapperStyle={{ color: '#F3F4F6' }} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#A78BFA"
                fill="#A78BFA"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Celery Tasks */}
        <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-4 text-white">Celery Tasks</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={celeryTasksData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }} 
              />
              <Legend wrapperStyle={{ color: '#F3F4F6' }} />
              <Bar dataKey="value" fill="#FBBF24" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Trades */}
        <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-4 text-white">Trades Executed</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tradesData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }} 
              />
              <Legend wrapperStyle={{ color: '#F3F4F6' }} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#F472B6"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Last Update */}
      <div className="text-center text-xs sm:text-sm text-gray-400">
        Última actualización: <span className="text-gray-300">{lastUpdate.toLocaleTimeString()}</span>
      </div>
    </div>
  )
}

