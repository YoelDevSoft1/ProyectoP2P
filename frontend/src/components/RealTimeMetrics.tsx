'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '@/lib/api'
import { parsePrometheusMetrics, getMetricValue, getMetricValues } from '../lib/prometheus'
import { Activity, TrendingUp, Database, MessageSquare } from 'lucide-react'

interface MetricPoint {
  time: number
  value: number
  label?: string
}

export function RealTimeMetrics() {
  const [metrics, setMetrics] = useState<Map<string, any>>(new Map())
  const [history, setHistory] = useState<{
    httpRequests: MetricPoint[]
    httpDuration: MetricPoint[]
    dbQueries: MetricPoint[]
    redisOps: MetricPoint[]
    celeryTasks: MetricPoint[]
    trades: MetricPoint[]
  }>({
    httpRequests: [],
    httpDuration: [],
    dbQueries: [],
    redisOps: [],
    celeryTasks: [],
    trades: [],
  })

  const maxHistoryPoints = 50

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const metricsText = await api.getPrometheusMetrics()
        if (metricsText) {
          const parsed = parsePrometheusMetrics(metricsText)
          setMetrics(parsed)

          // Agregar punto a la historia
          const now = Date.now()

          // HTTP Requests
          const httpRequests = getMetricValue(parsed, 'http_requests_total')
          if (httpRequests !== null) {
            setHistory((prev) => ({
              ...prev,
              httpRequests: [
                ...prev.httpRequests.slice(-maxHistoryPoints + 1),
                { time: now, value: httpRequests },
              ],
            }))
          }

          // HTTP Duration
          const httpDuration = getMetricValue(parsed, 'http_request_duration_seconds')
          if (httpDuration !== null) {
            setHistory((prev) => ({
              ...prev,
              httpDuration: [
                ...prev.httpDuration.slice(-maxHistoryPoints + 1),
                { time: now, value: httpDuration * 1000 }, // Convert to ms
              ],
            }))
          }

          // DB Queries
          const dbQueries = getMetricValue(parsed, 'db_queries_total')
          if (dbQueries !== null) {
            setHistory((prev) => ({
              ...prev,
              dbQueries: [
                ...prev.dbQueries.slice(-maxHistoryPoints + 1),
                { time: now, value: dbQueries },
              ],
            }))
          }

          // Redis Ops
          const redisOps = getMetricValue(parsed, 'redis_operations_total')
          if (redisOps !== null) {
            setHistory((prev) => ({
              ...prev,
              redisOps: [
                ...prev.redisOps.slice(-maxHistoryPoints + 1),
                { time: now, value: redisOps },
              ],
            }))
          }

          // Celery Tasks
          const celeryTasks = getMetricValue(parsed, 'celery_tasks_total')
          if (celeryTasks !== null) {
            setHistory((prev) => ({
              ...prev,
              celeryTasks: [
                ...prev.celeryTasks.slice(-maxHistoryPoints + 1),
                { time: now, value: celeryTasks },
              ],
            }))
          }

          // Trades
          const trades = getMetricValue(parsed, 'trades_executed_total')
          if (trades !== null) {
            setHistory((prev) => ({
              ...prev,
              trades: [
                ...prev.trades.slice(-maxHistoryPoints + 1),
                { time: now, value: trades },
              ],
            }))
          }
        }
      } catch (error) {
        console.error('Error fetching metrics:', error)
      }
    }

    fetchMetrics()
    // Actualizar cada 5 segundos para métricas en tiempo real
    const interval = setInterval(fetchMetrics, 5000)
    return () => clearInterval(interval)
  }, [])

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* HTTP Requests */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold">HTTP Requests</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={history.httpRequests}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tickFormatter={formatTime}
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => formatTime(value as number)}
                formatter={(value: any) => [value.toFixed(0), 'Requests']}
              />
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
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-green-500" />
            <h3 className="text-lg font-semibold">HTTP Duration (ms)</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={history.httpDuration}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tickFormatter={formatTime}
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => formatTime(value as number)}
                formatter={(value: any) => [`${value.toFixed(2)}ms`, 'Duration']}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* DB Queries */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-red-500" />
            <h3 className="text-lg font-semibold">Database Queries</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={history.dbQueries}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tickFormatter={formatTime}
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => formatTime(value as number)}
                formatter={(value: any) => [value.toFixed(0), 'Queries']}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Redis Operations */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-purple-500" />
            <h3 className="text-lg font-semibold">Redis Operations</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={history.redisOps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tickFormatter={formatTime}
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => formatTime(value as number)}
                formatter={(value: any) => [value.toFixed(0), 'Operations']}
              />
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
          <div className="flex items-center gap-2 mb-4">
            <MessageSquare className="w-5 h-5 text-orange-500" />
            <h3 className="text-lg font-semibold">Celery Tasks</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={history.celeryTasks}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tickFormatter={formatTime}
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => formatTime(value as number)}
                formatter={(value: any) => [value.toFixed(0), 'Tasks']}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#f59e0b"
                fill="#f59e0b"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Trades */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-pink-500" />
            <h3 className="text-lg font-semibold">Trades Executed</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={history.trades}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tickFormatter={formatTime}
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => formatTime(value as number)}
                formatter={(value: any) => [value.toFixed(0), 'Trades']}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#ec4899"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

