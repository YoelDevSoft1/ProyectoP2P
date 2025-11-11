'use client'

import { useEffect, useState } from 'react'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts'
import api from '@/lib/api'
import { parsePrometheusMetrics, getMetricValue, getMetricValues, sumMetricValues } from '../lib/prometheus'
import { Loader2, TrendingUp, Activity, Database, MessageSquare } from 'lucide-react'
import { formatColombiaTimeOnly } from '@/lib/dateUtils'

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

  // Debug: Log available metrics y valores (solo en desarrollo, opcional)
  useEffect(() => {
    // Comentado para evitar warnings innecesarios
    // Las métricas pueden no existir al inicio y eso es normal
    // if (process.env.NODE_ENV === 'development' && metrics.size > 0) {
    //   const metricNames = Array.from(metrics.keys())
    //   console.log('📊 Available metrics:', metricNames)
    // }
  }, [metrics])

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
  const totalCeleryTasks = sumMetricValues(metrics, 'celery_tasks_total') || 0
  const totalTrades = sumMetricValues(metrics, 'trades_executed_total') || 0

  // Obtener valores actuales
  const httpDurationP95 = getMetricValue(metrics, 'http_request_duration_seconds')
  
  // Para active_arbitrage_opportunities, es un Gauge, así que sumamos todos los valores actuales
  // (puede haber múltiples estrategias)
  const activeArbitrageSeries = metrics.get('active_arbitrage_opportunities')
  let activeArbitrage: number = 0
  if (activeArbitrageSeries && activeArbitrageSeries.length > 0) {
    // Para Gauges, sumar todos los valores actuales (cada estrategia tiene su propio gauge)
    const validValues = activeArbitrageSeries
      .filter(m => isFinite(m.value) && !isNaN(m.value))
      .map(m => m.value)
    if (validValues.length > 0) {
      activeArbitrage = validValues.reduce((sum, val) => sum + val, 0)
    }
  }

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
      value: activeArbitrage.toFixed(0),
      icon: TrendingUp,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-900/30',
      borderColor: 'border-yellow-500/50',
    },
  ]

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          
          // Mapear nombres de estadísticas a nombres de métricas
          const metricMap: Record<string, string> = {
            'HTTP Requests': 'http_requests_total',
            'DB Queries': 'db_queries_total',
            'Redis Ops': 'redis_operations_total',
            'Celery Tasks': 'celery_tasks_total',
            'Trades': 'trades_executed_total',
            'Active Arbitrage': 'active_arbitrage_opportunities',
          }
          
          const metricName = metricMap[stat.name] || ''
          const metricSeries = metricName ? metrics.get(metricName) : null
          const metricValue = parseFloat(stat.value.replace(/,/g, ''))
          
          // Determinar el estado de la métrica
          const metricNotFound = !metricSeries || metricSeries.length === 0
          const metricExistsButZero = metricSeries && metricSeries.length > 0 && metricValue === 0
          
          // Mensajes informativos según el tipo de métrica
          const metricInfo: Record<string, string> = {
            'DB Queries': 'Se registra cuando se ejecutan queries en la base de datos',
            'Celery Tasks': 'Se registra cuando se ejecutan tareas de Celery',
            'Trades': 'Se registra cuando se ejecutan trades',
            'Active Arbitrage': 'Muestra oportunidades activas (puede ser 0 si no hay)',
          }
          
          const infoMessage = metricInfo[stat.name]
          
          return (
            <div
              key={stat.name}
              className={`${stat.bgColor} rounded-lg p-4 border ${stat.borderColor} hover:opacity-80 transition-opacity relative ${
                metricNotFound ? 'opacity-60' : ''
              }`}
              title={
                metricNotFound 
                  ? `⚠️ Métrica no encontrada: ${metricName || 'N/A'}. ${infoMessage || 'Puede que no se haya registrado actividad aún.'}`
                  : metricExistsButZero 
                    ? `ℹ️ ${infoMessage || 'La métrica existe pero está en 0. Esto es normal si no ha habido actividad.'}`
                    : undefined
              }
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-xs sm:text-sm text-gray-400">{stat.name}</p>
                    {metricNotFound && (
                      <span className="text-xs text-yellow-500" title="Métrica no encontrada en el backend">
                        ⚠️
                      </span>
                    )}
                  </div>
                  <p className={`text-xl sm:text-2xl font-bold mt-1 ${
                    metricNotFound ? 'text-gray-500' : 'text-white'
                  }`}>
                    {stat.value}
                  </p>
                  {metricExistsButZero && (
                    <p className="text-xs text-gray-500 mt-1 italic">
                      Sin actividad
                    </p>
                  )}
                </div>
                <Icon className={`w-6 h-6 sm:w-8 sm:h-8 ${stat.color} flex-shrink-0 ${
                  metricNotFound ? 'opacity-50' : ''
                }`} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* HTTP Requests */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-xl border border-gray-700/50 p-4 sm:p-6 hover:border-blue-500/50 transition-all duration-300">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base sm:text-lg font-bold text-white">HTTP Requests</h3>
            <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse"></div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={httpRequestsData.slice(0, 20)} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorHttpRequests" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#60A5FA" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#60A5FA" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="time" 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <YAxis 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #60A5FA',
                  borderRadius: '8px',
                  color: '#F3F4F6',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)'
                }}
                labelStyle={{ color: '#60A5FA', fontWeight: 'bold' }}
                cursor={{ stroke: '#60A5FA', strokeWidth: 2 }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#60A5FA"
                strokeWidth={2}
                fill="url(#colorHttpRequests)"
                animationDuration={1000}
                animationBegin={0}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* HTTP Duration */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-xl border border-gray-700/50 p-4 sm:p-6 hover:border-green-500/50 transition-all duration-300">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base sm:text-lg font-bold text-white">HTTP Request Duration (p95)</h3>
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={httpDurationData.slice(0, 20)} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="time" 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <YAxis 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #34D399',
                  borderRadius: '8px',
                  color: '#F3F4F6',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)'
                }}
                labelStyle={{ color: '#34D399', fontWeight: 'bold' }}
                cursor={{ stroke: '#34D399', strokeWidth: 2 }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#34D399"
                strokeWidth={3}
                dot={{ fill: '#34D399', r: 4 }}
                activeDot={{ r: 6, fill: '#10B981' }}
                animationDuration={1000}
                animationBegin={0}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* DB Queries */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-xl border border-gray-700/50 p-4 sm:p-6 hover:border-red-500/50 transition-all duration-300">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base sm:text-lg font-bold text-white">Database Queries</h3>
            <div className="h-2 w-2 bg-red-500 rounded-full animate-pulse"></div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dbQueriesData.slice(0, 20)} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorDbQueries" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#F87171" stopOpacity={0.9}/>
                  <stop offset="95%" stopColor="#EF4444" stopOpacity={0.6}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="time" 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <YAxis 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #F87171',
                  borderRadius: '8px',
                  color: '#F3F4F6',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)'
                }}
                labelStyle={{ color: '#F87171', fontWeight: 'bold' }}
                cursor={{ fill: 'rgba(248, 113, 113, 0.1)' }}
              />
              <Bar 
                dataKey="value" 
                fill="url(#colorDbQueries)"
                radius={[4, 4, 0, 0]}
                animationDuration={1000}
                animationBegin={0}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Redis Operations */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-xl border border-gray-700/50 p-4 sm:p-6 hover:border-purple-500/50 transition-all duration-300">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base sm:text-lg font-bold text-white">Redis Operations</h3>
            <div className="h-2 w-2 bg-purple-500 rounded-full animate-pulse"></div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={redisOpsData.slice(0, 20)} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorRedisOps" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#A78BFA" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#A78BFA" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="time" 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <YAxis 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #A78BFA',
                  borderRadius: '8px',
                  color: '#F3F4F6',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)'
                }}
                labelStyle={{ color: '#A78BFA', fontWeight: 'bold' }}
                cursor={{ stroke: '#A78BFA', strokeWidth: 2 }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#A78BFA"
                strokeWidth={2}
                fill="url(#colorRedisOps)"
                animationDuration={1000}
                animationBegin={0}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Celery Tasks */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-xl border border-gray-700/50 p-4 sm:p-6 hover:border-yellow-500/50 transition-all duration-300">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base sm:text-lg font-bold text-white">Celery Tasks</h3>
            <div className="h-2 w-2 bg-yellow-500 rounded-full animate-pulse"></div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={celeryTasksData.slice(0, 20)} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCeleryTasks" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#FBBF24" stopOpacity={0.9}/>
                  <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.6}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="time" 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <YAxis 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #FBBF24',
                  borderRadius: '8px',
                  color: '#F3F4F6',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)'
                }}
                labelStyle={{ color: '#FBBF24', fontWeight: 'bold' }}
                cursor={{ fill: 'rgba(251, 191, 36, 0.1)' }}
              />
              <Bar 
                dataKey="value" 
                fill="url(#colorCeleryTasks)"
                radius={[4, 4, 0, 0]}
                animationDuration={1000}
                animationBegin={0}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Trades */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-xl border border-gray-700/50 p-4 sm:p-6 hover:border-orange-500/50 transition-all duration-300">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base sm:text-lg font-bold text-white">Trades Executed</h3>
            <div className="h-2 w-2 bg-orange-500 rounded-full animate-pulse"></div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tradesData.slice(0, 20)} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="time" 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <YAxis 
                stroke="#9CA3AF" 
                fontSize={12}
                tick={{ fill: '#9CA3AF' }}
                axisLine={{ stroke: '#4B5563' }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: '1px solid #F97316',
                  borderRadius: '8px',
                  color: '#F3F4F6',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)'
                }}
                labelStyle={{ color: '#F97316', fontWeight: 'bold' }}
                cursor={{ stroke: '#F97316', strokeWidth: 2 }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#F97316"
                strokeWidth={3}
                dot={{ fill: '#F97316', r: 4 }}
                activeDot={{ r: 6, fill: '#EA580C' }}
                animationDuration={1000}
                animationBegin={0}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Last Update */}
      <div className="text-center text-xs sm:text-sm text-gray-400">
        Última actualización: <span className="text-gray-300">{formatColombiaTimeOnly(lastUpdate)}</span>
      </div>
    </div>
  )
}

