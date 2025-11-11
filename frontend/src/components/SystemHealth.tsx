'use client'

import { useEffect, useState } from 'react'
import api from '@/lib/api'
import { CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react'

interface ServiceHealth {
  status: string
  [key: string]: any
}

interface HealthData {
  status: string
  environment: string
  version: string
  services: {
    postgresql?: ServiceHealth
    postgresql_async?: ServiceHealth
    redis?: ServiceHealth
    rabbitmq?: ServiceHealth
    celery?: ServiceHealth
  }
}

export function SystemHealth() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = async () => {
    try {
      setLoading(true)
      const data = await api.healthCheck()
      setHealth(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Error al obtener el estado del sistema')
      console.error('Health check error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    // Actualizar cada 30 segundos
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'connected':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />
      case 'degraded':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
      case 'unhealthy':
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'connected':
        return 'bg-green-900/30 text-green-400 border-green-500/50'
      case 'degraded':
        return 'bg-yellow-900/30 text-yellow-400 border-yellow-500/50'
      case 'unhealthy':
      case 'error':
        return 'bg-red-900/30 text-red-400 border-red-500/50'
      default:
        return 'bg-gray-800 text-gray-400 border-gray-700'
    }
  }

  if (loading && !health) {
    return (
      <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      </div>
    )
  }

  if (error && !health) {
    return (
      <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-6">
        <div className="text-center text-red-400">
          <XCircle className="w-8 h-8 mx-auto mb-2" />
          <p>{error}</p>
          <button
            onClick={fetchHealth}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  if (!health) {
    return null
  }

  const services = [
    {
      name: 'PostgreSQL',
      key: 'postgresql',
      data: health.services.postgresql || health.services.postgresql_async,
    },
    {
      name: 'Redis',
      key: 'redis',
      data: health.services.redis,
    },
    {
      name: 'RabbitMQ',
      key: 'rabbitmq',
      data: health.services.rabbitmq,
    },
    {
      name: 'Celery',
      key: 'celery',
      data: health.services.celery,
    },
  ]

  return (
    <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-4 sm:p-6">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <h2 className="text-xl sm:text-2xl font-bold text-white">Estado del Sistema</h2>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs sm:text-sm font-medium border ${getStatusColor(health.status)}`}>
            {health.status.toUpperCase()}
          </span>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="p-2 text-gray-400 hover:text-white disabled:opacity-50 transition-colors"
            title="Actualizar"
          >
            <Loader2 className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {services.map((service) => {
          const serviceData = service.data
          const status = serviceData?.status || 'unknown'
          const latency = serviceData?.latency_ms
          const workerCount = serviceData?.worker_count
          const activeTasks = serviceData?.active_tasks

          return (
            <div
              key={service.key}
              className="bg-gray-700/50 border border-gray-600 rounded-lg p-4 hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-white text-sm sm:text-base">{service.name}</h3>
                {getStatusIcon(status)}
              </div>
              
              <div className="mt-2 space-y-1 text-xs sm:text-sm text-gray-300">
                <div className="flex items-center justify-between">
                  <span>Estado:</span>
                  <span className={`font-medium capitalize ${getStatusColor(status).split(' ')[1]}`}>
                    {status}
                  </span>
                </div>
                
                {latency !== undefined && (
                  <div className="flex items-center justify-between">
                    <span>Latencia:</span>
                    <span className="font-mono text-gray-200">{latency}ms</span>
                  </div>
                )}
                
                {workerCount !== undefined && (
                  <div className="flex items-center justify-between">
                    <span>Workers:</span>
                    <span className="font-mono text-gray-200">{workerCount}</span>
                  </div>
                )}
                
                {activeTasks !== undefined && (
                  <div className="flex items-center justify-between">
                    <span>Tareas activas:</span>
                    <span className="font-mono text-gray-200">{activeTasks}</span>
                  </div>
                )}
                
                {serviceData?.pool_size !== undefined && (
                  <div className="flex items-center justify-between">
                    <span>Pool size:</span>
                    <span className="font-mono text-gray-200">{serviceData.pool_size}</span>
                  </div>
                )}
              </div>

              {serviceData?.error && (
                <div className="mt-2 text-xs text-red-400 bg-red-900/30 border border-red-500/50 p-2 rounded">
                  {serviceData.error}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="flex items-center justify-between text-xs sm:text-sm text-gray-400 flex-wrap gap-2">
          <span>Entorno: <span className="text-gray-300">{health.environment}</span></span>
          <span>Versión: <span className="text-gray-300">{health.version}</span></span>
        </div>
      </div>
    </div>
  )
}

