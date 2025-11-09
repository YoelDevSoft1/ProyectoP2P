'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '@/lib/api'
import { parsePrometheusMetrics, getMetricValue, getMetricValues, sumMetricValues } from '@/lib/prometheus'
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
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      </div>
    )
  }

  if (error && metrics.size === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-red-600">
          <p>{error}</p>
          <button
            onClick={fetchMetrics}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
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
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
    },
    {
      name: 'DB Queries',
      value: totalDbQueries.toLocaleString(),
      icon: Database,
      color: 'text-green-500',
      bgColor: 'bg-green-50',
    },
    {
      name: 'Redis Ops',
      value: totalRedisOps.toLocaleString(),
      icon: Activity,
      color: 'text-red-500',
      bgColor: 'bg-red-50',
    },
    {
      name: 'Celery Tasks',
      value: totalCeleryTasks.toLocaleString(),
      icon: MessageSquare,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50',
    },
    {
      name: 'Trades',
      value: totalTrades.toLocaleString(),
      icon: TrendingUp,
      color: 'text-orange-500',
      bgColor: 'bg-orange-50',
    },
    {
      name: 'Active Arbitrage',
      value: activeArbitrage?.toFixed(0) || '0',
      icon: TrendingUp,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-50',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div
              key={stat.name}
              className={`${stat.bgColor} rounded-lg p-4 border border-gray-200`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-bold text-gray-800">{stat.value}</p>
                </div>
                <Icon className={`w-8 h-8 ${stat.color}`} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* HTTP Requests */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">HTTP Requests</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={httpRequestsData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* HTTP Duration */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">HTTP Request Duration (p95)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={httpDurationData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#10b981"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* DB Queries */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Database Queries</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dbQueriesData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Redis Operations */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Redis Operations</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={redisOpsData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#8b5cf6"
                fill="#8b5cf6"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Celery Tasks */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Celery Tasks</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={celeryTasksData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Trades */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Trades Executed</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tradesData.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#ec4899"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Last Update */}
      <div className="text-center text-sm text-gray-500">
        Última actualización: {lastUpdate.toLocaleTimeString()}
      </div>
    </div>
  )
}

