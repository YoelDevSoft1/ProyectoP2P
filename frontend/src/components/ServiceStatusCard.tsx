'use client'

import { CheckCircle2, XCircle, AlertCircle, Clock } from 'lucide-react'

interface ServiceStatusCardProps {
  name: string
  status: string
  latency?: number
  details?: Record<string, any>
  lastChecked?: Date
}

export function ServiceStatusCard({
  name,
  status,
  latency,
  details,
  lastChecked,
}: ServiceStatusCardProps) {
  const getStatusIcon = () => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'connected':
        return <CheckCircle2 className="w-6 h-6 text-green-500" />
      case 'degraded':
        return <AlertCircle className="w-6 h-6 text-yellow-500" />
      case 'unhealthy':
      case 'error':
        return <XCircle className="w-6 h-6 text-red-500" />
      default:
        return <Clock className="w-6 h-6 text-gray-400" />
    }
  }

  const getStatusColor = () => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'connected':
        return 'border-green-200 bg-green-50'
      case 'degraded':
        return 'border-yellow-200 bg-yellow-50'
      case 'unhealthy':
      case 'error':
        return 'border-red-200 bg-red-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  return (
    <div className={`border-2 rounded-lg p-4 ${getStatusColor()}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-800">{name}</h3>
        {getStatusIcon()}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Estado:</span>
          <span className="font-medium text-gray-800 capitalize">{status}</span>
        </div>

        {latency !== undefined && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Latencia:</span>
            <span className="font-mono text-gray-800">{latency}ms</span>
          </div>
        )}

        {details &&
          Object.entries(details).map(([key, value]) => {
            if (key === 'status' || key === 'error' || key === 'latency_ms') {
              return null
            }
            return (
              <div key={key} className="flex items-center justify-between text-sm">
                <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}:</span>
                <span className="font-mono text-gray-800">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            )
          })}

        {lastChecked && (
          <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t">
            <span>Última verificación:</span>
            <span>{lastChecked.toLocaleTimeString()}</span>
          </div>
        )}
      </div>
    </div>
  )
}

