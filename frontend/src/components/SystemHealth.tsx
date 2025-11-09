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
        return 'bg-green-100 text-green-800 border-green-200'
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'unhealthy':
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  if (loading && !health) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      </div>
    )
  }

  if (error && !health) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-red-600">
          <XCircle className="w-8 h-8 mx-auto mb-2" />
          <p>{error}</p>
          <button
            onClick={fetchHealth}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
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
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Estado del Sistema</h2>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(health.status)}`}>
            {health.status.toUpperCase()}
          </span>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="p-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
            title="Actualizar"
          >
            <Loader2 className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {services.map((service) => {
          const serviceData = service.data
          const status = serviceData?.status || 'unknown'
          const latency = serviceData?.latency_ms
          const workerCount = serviceData?.worker_count
          const activeTasks = serviceData?.active_tasks

          return (
            <div
              key={service.key}
              className="border rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-700">{service.name}</h3>
                {getStatusIcon(status)}
              </div>
              
              <div className="mt-2 space-y-1 text-sm text-gray-600">
                <div className="flex items-center justify-between">
                  <span>Estado:</span>
                  <span className={`font-medium ${getStatusColor(status).split(' ')[1]}`}>
                    {status}
                  </span>
                </div>
                
                {latency !== undefined && (
                  <div className="flex items-center justify-between">
                    <span>Latencia:</span>
                    <span className="font-mono">{latency}ms</span>
                  </div>
                )}
                
                {workerCount !== undefined && (
                  <div className="flex items-center justify-between">
                    <span>Workers:</span>
                    <span className="font-mono">{workerCount}</span>
                  </div>
                )}
                
                {activeTasks !== undefined && (
                  <div className="flex items-center justify-between">
                    <span>Tareas activas:</span>
                    <span className="font-mono">{activeTasks}</span>
                  </div>
                )}
                
                {serviceData?.pool_size !== undefined && (
                  <div className="flex items-center justify-between">
                    <span>Pool size:</span>
                    <span className="font-mono">{serviceData.pool_size}</span>
                  </div>
                )}
              </div>

              {serviceData?.error && (
                <div className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded">
                  {serviceData.error}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="mt-6 pt-4 border-t">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Entorno: {health.environment}</span>
          <span>Versión: {health.version}</span>
        </div>
      </div>
    </div>
  )
}

